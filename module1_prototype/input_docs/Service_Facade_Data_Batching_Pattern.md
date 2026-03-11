# Service Facade & Data Batching (Data Loader) Pattern

## 1. Overview

**The Anti-Pattern (The N+1 Query Problem):**
In many applications, especially when returning lists of data, a common mistake is fetching a list of parent records (the "1" query) and then creating a loop that iterates over these records to fetch associated child records (the "N" queries). If you have 1,000 users, finding their progress metrics inside a loop results in 1,001 individual database round-trips. This saturates the database connection pool, creates immense network latency, and severely throttles overall application scalability. 

**The Solution (Service Facade + Data Batching):**
The **Service Facade & Data Batching** pattern eliminates the N+1 problem by fundamentally shifting *when* and *how* the database is accessed.
1.  **Data Batching**: Instead of querying inside a loop, you make a single, bulk database query to fetch *all* associated records at once using the SQL `IN` operator (or equivalent). You then pivot this flat list into an in-memory Hash Map (dictionary) for instant, `O(1)` memory lookups.
2.  **Service Facade**: This heavily optimized, structurally complex data fetching logic is deliberately hidden behind a clean interface called a "Facade." The routing and controller layers remain blissfully ignorant of query optimizations; they simply call the facade function.

---

## 2. Infographic Representation

This architectural diagram illustrates the drastic difference in system behavior between the naive N+1 approach and the optimized Data Batching pattern, as well as the flow of the Service Facade.




---

## 3. Code Snippets

The following code is a real-world implementation of this pattern taken directly from our codebase's Tutor Insights module (`tutorInsights.ts`). It handles fetching a course's enrolled learners and their module progress.

### Snippet A: The Consumer (Controller Route)
This snippet shows how the HTTP Route uses the Facade. It assumes no responsibility for how the data is obtained.

```typescript
// backend/src/routes/tutors.ts
tutorsRouter.get(
  "/me/courses/:courseId/progress",
  requireAuth,
  requireTutor,
  asyncHandler(async (req, res) => {
    const { courseId } = req.params;
    
    // The Controller cleanly delegates work to the Service Facade
    const snapshot = await buildTutorCourseSnapshot(courseId);
    
    res.json(snapshot);
  })
);
```

### Snippet B: The Service Facade & Batching Implementation
This function encapsulates the complex bulk querying and memory mapping logic.

```typescript
// backend/src/services/tutorInsights.ts
export async function buildTutorCourseSnapshot(courseId: string): Promise<TutorCourseSnapshot> {
  // Step 1: Fetch the primary "1" list (All enrollments)
  const enrollments = await prisma.enrollment.findMany({
    where: { courseId },
    select: {
      enrollmentId: true,
      userId: true,
      enrolledAt: true,
      user: {
        select: { fullName: true, email: true },
      },
    },
    orderBy: { enrolledAt: "asc" },
  });

  // Step 2: Perform the bulk "N" query (The Batch Fetch)
  // Instead of querying per-user, we bulk-fetch ALL progress rows for the course
  const progressRows = await prisma.$queryRaw<
    { user_id: string; module_no: number; quiz_passed: boolean; updated_at: Date | null }[]
  >(Prisma.sql`
    SELECT user_id, module_no, quiz_passed, updated_at
    FROM module_progress
    WHERE course_id = ${courseId}::uuid
  `);

  // Step 3: Create an in-memory O(1) lookup map keyed by userId
  const progressByUser = new Map<string, { passedModules: Set<number>; lastActivity?: Date | null }>();
  
  progressRows.forEach((row) => {
    // Upsert pattern for Maps
    const entry = progressByUser.get(row.user_id) ?? { passedModules: new Set<number>(), lastActivity: null };
    
    if (row.quiz_passed) {
      entry.passedModules.add(row.module_no);
    }
    
    if (!entry.lastActivity || (row.updated_at && row.updated_at > entry.lastActivity)) {
      entry.lastActivity = row.updated_at;
    }
    
    // Save updated entry back to Map
    progressByUser.set(row.user_id, entry);
  });

  // Step 4: Assemble and map the results entirely in memory
  const learners = enrollments.map((enrollment) => {
    // Instant O(1) lookup from our Map. No database queries permitted here!
    const progress = progressByUser.get(enrollment.userId);
    
    const completedModules = progress ? progress.passedModules.size : 0;
    
    return {
      userId: enrollment.userId,
      fullName: enrollment.user.fullName,
      email: enrollment.user.email,
      enrolledAt: enrollment.enrolledAt,
      completedModules,
      lastActivity: progress?.lastActivity ?? enrollment.enrolledAt,
    };
  });

  return { learners }; // Returns standard JSON DTO
}
```

---

## 4. Technical Explanation

### How and Why This Works (Step-by-Step Breakdown)

If you need to plug this architecture into your own module, follow this exact sequence of technical steps:

#### 1. Abstraction of Concern (The Facade Wrapper)
Look at **Snippet A**. The API route `tutorsRouter.get` knows absolutely nothing about Prisma queries, `Map()` objects, or SQL raw strings. It simply executes `buildTutorCourseSnapshot(courseId)`. 
*   **Why?** By decoupling the HTTP layer from the data layer, the business logic becomes perfectly reusable. If another part of the system (like a daily Cron job that emails reports to tutors) needs this data, it can invoke `buildTutorCourseSnapshot()` directly without faking an HTTP request.

#### 2. The Bulk Data Extraction (The Batch Fetch)
Look at **Step 2** in Snippet B: the `$queryRaw` call.
Instead of querying progress sequentially based on the users we just fetched, we shift the responsibility to the database engine. We ask Postgres to return *every single progress row* that relates to the specific `courseId`.
*   **Why?** Network latency is the enemy of backend scale. Making 1,000 DB queries that take 2ms each will cost 2,000ms (2 seconds) of pure connection waiting. Making 1 DB query that returns 10,000 rows will likely take less than 50ms, as all the data is serialized and sent over the wire payload in a single stream. 

#### 3. Transforming Data into Lookups (The Map)
Look at **Step 3** in Snippet B: `new Map<string, ...>()`.
We now hold thousands of progress rows in Node.js memory. If we want to assign them to their parent user, a naive developer might write:
```typescript
enrollments.map(enr => {
   // NAIVE: O(N) Array searching inside a loop
   const myProgress = progressRows.filter(row => row.user_id === enr.userId); 
})
```
Doing an array `filter()` over 10,000 rows, repeated 1,000 times for each user, results in 10,000,000 iteration cycles (`O(N * M)` complexity). This blocks the single-threaded Node.js event loop and crashes the server.

Instead, we construct a JavaScript `Map` (a hash table graph). We loop through the 10,000 `progressRows` exactly **once**, grouping them under their `user_id` key (`O(M)` complexity).

#### 4. The `O(1)` Assembly Phase
Look at **Step 4** in Snippet B.
Finally, we map over our parent list (`enrollments`). To find the children (progress), we bypass searching entirely and use a direct memory pointer: `progressByUser.get(enrollment.userId)`.
*   **Why?** Retrieving data from a `Map` by its key has an `O(1)` (instant, constant) time complexity. The server CPU only needs to execute 1,000 fast memory lookups, which finishes in less than a millisecond. 

### Summary for Implementation
Whenever you find yourself about to place a `db.find()` or `prisma.query()` inside a `for` loop or `.map()`, stop. 
1. Build a facade function.
2. Formulate a bulk query to fetch all required child data at once using an `IN` clause or shared parent ID context.
3. Build a `Map()` of the children.
4. Loop through the parents in memory and `.get()` the children instantly from the Map.

## Addendum - 2026-03-04 (No Previous Lines Removed)
- Verified current runtime architecture: one `frontend/` app and one `backend/` API in this repository.
- Verified async AI flow: request -> `background_jobs` queue -> `aiWorker` processing -> SSE response stream.
- Verified cohort access-state source endpoint: `GET /courses/:courseKey/access-status` returning `isAuthenticated`, `hasApplied`, `isApprovedMember`.
- Verified registration identity linkage: `POST /registrations` normalizes email and resolves/writes `registrations.user_id` using auth-user match or `users.email` lookup.
- Verified course details CTA progression for cohort flow: `Register Now` -> `Apply for Cohort` -> `Application is under review` -> `Start Learning`.

