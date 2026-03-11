# Technical Requirements — Course Platform

**Document ID**: TR-CP-001  
**Version**: 1.0  
**Status**: Draft (for internal review)  
**Owner**: Engineering  
**Last Updated**: 2026-02-09

## **1. Purpose**
This document defines the technical requirements for the Course Platform application. It translates product intent into implementable engineering requirements across frontend, backend, data, integrations, security, and operations. It is the authoritative engineering baseline for scope, behavior, quality, and deployment expectations.

## **2. Scope**
The system delivers a learner‑focused course platform with cohort gating, course playback, quizzes, tutoring assistance, and personalized content. It includes a React SPA, Express API, PostgreSQL data store, and RAG-based tutor support.

## **3. Out of Scope**
Items explicitly not required in this release unless separately approved:
- Multi‑tenant organization accounts and billing.
- In‑platform payment processing (beyond existing cart data models).
- Native mobile applications.
- Real‑time video conferencing or classroom streaming.

## **4. Definitions and Canonical Identifiers**
- Course name (canonical): **AI Native Full Stack Developer**.
- Course slug (canonical identifier): `ai-in-web-development`.
- Course UUID (seeded): `f26180b2-5dda-495a-a014-ae02e63f172f`.
- API base URL (local): `http://localhost:4000`.
- Frontend base URL (local): `http://localhost:5173`.
- RAG sources: `AI Native Full Stack Developer.pdf`.

## **5. System Context**
The platform consists of:
- Web frontend (React + Vite) for learner, tutor, and marketing experiences.
- API backend (Node + Express) for authentication, enrollment, content, quizzes, tutoring, and telemetry.
- PostgreSQL for core data, including pgvector for retrieval‑augmented tutoring.

## **6. Roles and Permissions**
- **Learner**: Can authenticate, enroll, consume content, complete quizzes, and use the tutor chat.
- **Tutor**: Can access tutor dashboard tools and course monitoring endpoints.
- **Admin**: Can approve tutor applications and access admin endpoints.

## **7. Functional Requirements**
Each requirement includes priority tags: **MUST / SHOULD / COULD**.

### **7.1 Authentication and Sessions**
- **MUST** support Google OAuth login and callback flows.
- **MUST** issue JWT access and refresh tokens with configurable TTLs.
- **MUST** enforce token validation for protected endpoints.
- **SHOULD** handle token refresh without requiring manual re‑login.

### **7.2 Course Catalog and Details**
- **MUST** expose course list and course detail endpoints (`/courses`, `/courses/:courseKey`).
- **MUST** resolve courses by UUID, canonical slug alias, or course name.
- **SHOULD** provide consistent response shapes with `courseId`, `slug`, and `courseName`.

### **7.3 Enrollment and Cohort Gating**
- **MUST** validate cohort membership before enrollment.
- **MUST** provide `checkOnly` enrollment validation via `/courses/:courseKey/enroll?checkOnly=true`.
- **MUST** persist enrollments upon approved enrollment.
- **SHOULD** return descriptive rejection messages on cohort denial.

### **7.4 Learning Path and Study Persona**
- **MUST** support study persona selection per learner/course (`normal`, `sports`, `cooking`, `adventure`).
- **MUST** persist persona to `topic_personalization`.
- **SHOULD** allow returning learners to continue with existing persona without re‑prompting.

### **7.5 Course Player and Content Rendering**
- **MUST** render a topic sequence grouped by module and topic number.
- **MUST** support block-based content in `topics.text_content` (JSON layout).
- **MUST** support legacy text content via `text_content` and persona columns.
- **MUST** render supported block types: `text`, `image`, `video`, `ppt`.
- **MUST** support “read mode” behavior as implemented in the course player.
- **SHOULD** normalize YouTube URLs to embed format for the video block.

### **7.6 Content Asset Resolution (Persona‑Aware)**
- **MUST** resolve `contentKey` blocks using `topic_content_assets`.
- **MUST** select persona‑specific assets when `learner_persona_profiles` exists; fall back to default assets otherwise.
- **MUST** return resolved block payloads to the frontend without exposing persona keys.

### **7.7 Quizzes and Module Gating**
- **MUST** provide quiz section and attempt lifecycle endpoints.
- **MUST** enforce passing threshold of 70% for module completion.
- **MUST** apply module cooldown windows (default 7 days).
- **SHOULD** provide progress visibility for all modules via `/quiz/progress/:courseKey`.

### **7.8 Tutor Chat and RAG**
- **MUST** provide tutor chat endpoint (`/assistant/query`) with RAG retrieval.
- **MUST** store chat sessions and messages for continuity.
- **MUST** enforce typed prompt quota per module (default 5).
- **SHOULD** rewrite follow‑up queries when they are too ambiguous.
- **SHOULD** summarize chat sessions after a minimum message count (default 16).

### **7.9 Cold Calling and Cohort Interaction**
- **MUST** support cold-call prompts per topic.
- **MUST** enforce that a learner submits before seeing cohort responses.
- **SHOULD** support starring and threaded replies.

### **7.10 Tutor Dashboard and Monitoring**
- **MUST** expose tutor-specific endpoints for enrollments and progress.
- **SHOULD** provide learner activity history for monitoring.

### **7.11 Telemetry**
- **MUST** accept client telemetry events in batches.
- **SHOULD** enforce max events per request (default 50).

## **8. Non‑Functional Requirements**
### **8.1 Performance**
- **MUST** return primary API responses within 500–1000ms under nominal load.
- **SHOULD** keep landing page LCP under 2.5 seconds on broadband.

### **8.2 Scalability**
- **SHOULD** support concurrent cohort users without functional degradation.
- **SHOULD** allow RAG queries at 8 requests per 60 seconds per user.

### **8.3 Availability and Reliability**
- **SHOULD** target ≥ 99.5% uptime for the API.
- **MUST** fail gracefully on RAG or third‑party outages.

### **8.4 Security**
- **MUST** validate JWTs on protected endpoints.
- **MUST** avoid storing raw refresh tokens (hashed storage required).
- **SHOULD** enforce CORS and allowed origins.

## **9. Data Requirements**
- **MUST** store core entities in PostgreSQL with Prisma schema as source of truth.
- **MUST** retain `topic_content_assets` for content-key resolution.
- **MUST** store course chunks in pgvector with a stable `course_id` reference.
- **SHOULD** provide auditability for learner activity events.

## **10. API Requirements**
- **MUST** provide REST endpoints as implemented under `/api`.
- **MUST** return consistent JSON error shapes (`{ message: string }`).
- **SHOULD** use standard HTTP status codes for auth, validation, and resource errors.

## **11. Configuration Requirements**
- **MUST** load configuration from environment variables.
- **MUST** support separate envs for dev/stage/prod with consistent variable names.
- **SHOULD** document config in `.env.example` and docs.

## **12. Observability**
- **MUST** log server errors with structured output.
- **SHOULD** include request IDs for traceability.
- **SHOULD** capture client telemetry for learning flow analytics.

## **13. Testing and Quality**
- **MUST** validate core flows with smoke tests:
  - OAuth login
  - Enrollment with cohort gate
  - Course player load
  - Quiz attempt lifecycle
  - Tutor chat query
- **SHOULD** include regression tests for content rendering and RAG retrieval.

## **14. Deployment Requirements**
- **MUST** deploy frontend and backend independently.
- **MUST** apply Prisma migrations before release.
- **MUST** ensure pgvector extension is enabled.
- **SHOULD** include rollback procedure for faulty deployments.

## **15. Risks and Mitigations**
- **Risk**: Mismatch between course ID used in RAG ingestion and runtime course resolution.
  - **Mitigation**: Enforce consistent `course_id` usage in ingestion scripts and API.
- **Risk**: Persona content keys missing.
  - **Mitigation**: Validate `topics.text_content` layouts and asset availability in CI checks.

## **16. Open Questions / TBD**
- Final SLO targets for API latency and uptime.
- Production scale assumptions (concurrent learners, cohort sizes).
- Long‑term data retention and archival policy.

---
**End of Document**

## Addendum - 2026-03-04 (No Previous Lines Removed)
- Verified current runtime architecture: one `frontend/` app and one `backend/` API in this repository.
- Verified async AI flow: request -> `background_jobs` queue -> `aiWorker` processing -> SSE response stream.
- Verified cohort access-state source endpoint: `GET /courses/:courseKey/access-status` returning `isAuthenticated`, `hasApplied`, `isApprovedMember`.
- Verified registration identity linkage: `POST /registrations` normalizes email and resolves/writes `registrations.user_id` using auth-user match or `users.email` lookup.
- Verified course details CTA progression for cohort flow: `Register Now` -> `Apply for Cohort` -> `Application is under review` -> `Start Learning`.

