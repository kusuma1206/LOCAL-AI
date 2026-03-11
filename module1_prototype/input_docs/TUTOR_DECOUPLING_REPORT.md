# Tutor Decoupling Report: Before & After

This document details the architectural transformation of the Course Platform from a monolithic application into a decoupled system with dedicated Tutor services.

---

## 1. The Original State ("Before")

**Architecture**: Monolithic
**Scope**: Single Backend (`port 4000`), Single Frontend (`port 5173`)
**Database**: Single PostgreSQL instance
**Auth**: Shared JWT logic for Students, Tutors, and Admins

### Original Directory Structure
Everything lived in two top-level folders:
```
/
├── backend/            # Handled ALL API requests (Student + Tutor)
│   └── src/
│       ├── routes/     # Mixed routes (users.ts, tutors.ts, courses.ts)
│       └── services/   # Mixed business logic
└── frontend/           # Handled ALL UI pages
    └── src/
        ├── pages/      # Mixed pages (StudentDashboard.tsx, TutorDashboardPage.tsx)
        └── App.tsx     # Single router for the entire application
```

### The Problem
-   **Security Risk**: Tutors and Students shared the same authentication token scope.
-   **Complexity**: Tutor logic (analytics, copilot) was entangled with Student logic (learning path, quizzes).
-   **Scalability**: Scaling the student platform meant unnecessarily scaling the tutor platform code.

---

## 2. All Changes Made ("Execution Log")

We executed a "Split & Decouple" strategy. Here is the exact log of changes:

### Phase A: Tutor Backend Construction
**Action**: Created `tutor-backend/` (Port `4001`)

1.  **Infrastructure Copy** (Shared Logic):
    *   Copied `prisma.ts`, `sessionService.ts`, `asyncHandler.ts`, `password.ts` from core backend.
    *   *Why*: These utilize the same database and crypto logic but need to run independently.

2.  **File Extraction** (Moved from Core):
    *   Moved `backend/src/routes/tutors.ts` → `tutor-backend/src/routes/tutors.ts`
    *   Moved `backend/src/routes/tutorApplications.ts` → `tutor-backend/src/routes/tutorApplications.ts`
    *   Moved `backend/src/services/tutorInsights.ts` → `tutor-backend/src/services/tutorInsights.ts`

3.  **New Configuration**:
    *   Created `tutor-backend/.env` with **separate JWT Secrets** (`JWT_SECRET`, `JWT_REFRESH_SECRET`).
    *   Created `tutor-backend/prisma/schema.prisma` containing **only 8 models** (read-only views of student data + R/W tutor tables).

### Phase B: Tutor Frontend Construction
**Action**: Created `tutor-frontend/` (Port `5174`)

1.  **Component Migration**:
    *   Copied 48 shared UI/Radix components (`components/ui/*`) from core.
    *   Copied `lib/utils.ts`, `lib/api.ts`, `lib/queryClient.ts`.
    *   *Why*: To ensure the Tutor UI looks identical to the Core UI without importing cross-project files.

2.  **Page Extraction** (Moved from Core):
    *   Moved `frontend/src/pages/TutorDashboardPage.tsx` → `tutor-frontend/src/pages/TutorDashboardPage.tsx`
    *   Moved `frontend/src/pages/TutorLoginPage.tsx` → `tutor-frontend/src/pages/TutorLoginPage.tsx`

3.  **New Configuration**:
    *   Created `tutor-frontend/.env` pointing `VITE_API_BASE_URL` to `http://localhost:4001`.

### Phase C: Core Platform Cleanup
**Action**: Removed Tutor Code from Core

1.  **Backend Cleanup**:
    *   Edited `backend/src/app.ts`: Removed `/tutors` and `/tutor-applications` route mounts.
    *   *Result*: Core backend no longer responds to Tutor API requests.

2.  **Frontend Cleanup**:
    *   Edited `frontend/src/App.tsx`: Removed `TutorDashboardPage` route.
    *   *Result*: Core frontend no longer serves the Tutor Dashboard.
    *   *Note*: `BecomeTutorPage` was **kept** in Core as it is a public marketing page.

---

## 3. The Current State ("After")

**Architecture**: Decoupled Service-Based
**Scope**: Distinct Student and Tutor Applications
**Database**: Shared PostgreSQL (Core=R/W, Tutor=Read-Only on Student Data)

### Final Directory Structure
We now have **four** top-level projects (excluding shared docs).

#### 1. Core Backend (`backend/`) - Port 4000
*   **Responsibility**: Student Learning, auth, payments, content delivery.
*   **Status**: Purely student-focused. No tutor API routes.

#### 2. Core Frontend (`frontend/`) - Port 5173
*   **Responsibility**: Student Dashboard, Course Player, Landing Pages.
*   **Status**: Contains `BecomeTutor` (Application form) but no Dashboard.

#### 3. Tutor Backend (`tutor-backend/`) - Port 4001
*   **Responsibility**: Tutor Analytics, AI Copilot, Roster Management.
*   **Structure**:
    ```
    tutor-backend/
    ├── package.json         # Lightweight (No PDF/CSV/Google deps)
    ├── .env                 # Has OWN JWT Secrets
    ├── prisma/
    │   └── schema.prisma    # Subset Schema (8 Models)
    └── src/
        ├── routes/
        │   ├── tutors.ts    # /login, /me/courses, /assistant
        │   └── list...
        └── services/
            └── tutorInsights.ts
    ```

#### 4. Tutor Frontend (`tutor-frontend/`) - Port 5174
*   **Responsibility**: Dedicated generic SPA for Tutors.
*   **Structure**:
    ```
    tutor-frontend/
    ├── .env                 # API -> localhost:4001
    └── src/
        ├── pages/
        │   ├── TutorDashboardPage.tsx
        │   └── TutorLoginPage.tsx
        └── components/      # Independent copy of UI kit
    ```

## Key Architectural Decisions

| Feature | Implementation | Why? |
| :--- | :--- | :--- |
| **Database** | **Shared Instance** | Simplicity. Tutor backend reads student progress directly without complex API syncing. |
| **Authentication** | **Separate Secrets** | Security. A Student JWT cannot be used to hack the Tutor Dashboard, and vice-versa. |
| **Code Sharing** | **Duplication** | Decoupling. UI components were copied so future Tutor UI changes don't break Student UI. |
| **AI Features** | **Shared Key** | Cost. Both backends use the same OpenAI Key, but the Tutor Client is simplified (no RAG). |

## Addendum - 2026-03-04 (No Previous Lines Removed)
- Verified current runtime architecture: one `frontend/` app and one `backend/` API in this repository.
- Verified async AI flow: request -> `background_jobs` queue -> `aiWorker` processing -> SSE response stream.
- Verified cohort access-state source endpoint: `GET /courses/:courseKey/access-status` returning `isAuthenticated`, `hasApplied`, `isApprovedMember`.
- Verified registration identity linkage: `POST /registrations` normalizes email and resolves/writes `registrations.user_id` using auth-user match or `users.email` lookup.
- Verified course details CTA progression for cohort flow: `Register Now` -> `Apply for Cohort` -> `Application is under review` -> `Start Learning`.

