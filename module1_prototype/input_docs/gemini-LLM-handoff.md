# Handoff Pack - Course_Platform_Test

This document is the entry point for any LLM thread that must build a complete mental model of the codebase using documentation only.

## 1) Recommended reading order
1. `README.md`
2. `Course_Platform.md`
3. `CP_Arc.md`
4. `Frontend.md`
5. `docs/project-structure.md`
6. `docs/databaseSchema.md`
7. `docs/project-walkthrough.md`
8. `docs/App Changes.md`
9. `docs/backend-dev-log.md`
10. `task_progress.md`
11. `frontend/README.md` and `backend/README.md`
12. `docs/design_guidelines.md`

## 2) Canonical identifiers and invariants
- Primary course name: `AI Native Full Stack Developer`.
- Primary course slug (DB seed): `ai-in-web-development`.
- Primary course UUID (seed): `f26180b2-5dda-495a-a014-ae02e63f172f`.
- Additional seed courses also exist (see `backend/prisma/seed.ts`).
- RAG source PDFs in repo root:
  - `Web Dev using AI Course Content.pdf` (default in ingest script)
  - `AI Native Full Stack Developer.pdf` (alternate source)
- Frontend dev URL: `http://localhost:5173`.
- Backend dev URL: `http://localhost:4000` (API mounted at `/` and `/api`).

## 3) Frontend routes (from `frontend/src/App.tsx`)
- `/` - LandingPage
- `/become-a-tutor` - BecomeTutorPage
- `/methodology` - MethodologyPage
- `/more-info` - MoreInfoPage
- `/our-courses/cohort` - CohortPage
- `/our-courses/on-demand` - OnDemandPage
- `/our-courses/workshops` - WorkshopPage
- `/tutors` - TutorDashboardPage (tutor/admin only)
- `/auth/callback` - AuthCallbackPage
- `/course/:id` - CourseDetailsPage
- `/course/:id/enroll` - EnrollmentPage (legacy flow)
- `/course/:id/path` - LearningPathPage (study persona questionnaire flow)
- `/course/:id/learn/:lesson` - CoursePlayerPage
- `/course/:id/assessment` - AssessmentPage (legacy flow)
- `/course/:id/congrats` - CongratsPage
- `/course/:id/congrats/feedback` - CongratsFeedbackPage
- `/course/:id/congrats/certificate` - CourseCertificatePage
- `*` - NotFound

Notes:
- The marketing navbar is hidden on `/course/*` routes.
- `AuthPage.tsx`, `TutorLoginPage.tsx`, `CoursesPage.tsx`, `DashboardPage.tsx`, `CartPage.tsx`, `AboutPage.tsx` exist but are not wired in `App.tsx`.
- `frontend/src/pages/examples/*` are local examples only.

## 4) Backend routers and endpoints
Routers are mounted at both `/` and `/api`.

Auth + sessions:
- `POST /auth/login` (tutor/admin password login)
- `GET /auth/google`, `GET /auth/google/callback`
- `POST /auth/google/exchange`, `POST /auth/google/id-token`
- `POST /auth/refresh`, `POST /auth/logout`

Catalog + enrollment:
- `GET /courses`
- `GET /courses/:courseKey`
- `POST /courses/:courseKey/enroll` (supports `?checkOnly=true`)

Lessons + personalization:
- `GET /lessons/modules/:moduleNo/topics`
- `GET /lessons/courses/:courseKey/topics`
- `GET /lessons/courses/:courseKey/personalization`
- `POST /lessons/courses/:courseKey/personalization`
- `GET /lessons/courses/:courseKey/prompts`
- `GET /lessons/courses/:courseKey/progress`
- `GET /lessons/:lessonId/progress`
- `PUT /lessons/:lessonId/progress`

Cohort projects:
- `GET /cohort-projects/:courseKey` (auth + cohort membership required)

AI tutor (learner):
- `POST /assistant/query` (Async: returns 202 + jobId)
- `GET /assistant/stream/:jobId` (SSE Result Stream)
- `GET /assistant/session`

Persona profile analysis (tutor personas):
- `GET /persona-profiles/:courseKey/status`
- `POST /persona-profiles/:courseKey/analyze`

Quizzes:
- `GET /quiz/questions`
- `GET /quiz/sections/:courseKey`
- `GET /quiz/progress/:courseKey`
- `POST /quiz/attempts`
- `POST /quiz/attempts/:attemptId/submit`

Cold calling:
- `GET /cold-call/prompts/:topicId`
- `POST /cold-call/messages`
- `POST /cold-call/replies`
- `POST /cold-call/stars`
- `DELETE /cold-call/stars/:messageId`

Telemetry + tutor monitor:
- `POST /activity/events`
- `GET /activity/courses/:courseId/learners`
- `GET /activity/learners/:learnerId/history`

Tutor dashboard:
- `POST /tutors/login`
- `POST /tutors/assistant/query`
- `GET /tutors/me/courses`
- `GET /tutors/:courseId/enrollments`
- `GET /tutors/:courseId/progress`

Admin:
- `GET /admin/tutor-applications`
- `POST /admin/tutor-applications/:applicationId/approve`

Other supporting:
- `/cart/*`, `/pages/*`, `/tutor-applications/*`, `/users/*`, `/health`

## 5) Content storage and rendering
- `topics.text_content` is either plain text or a JSON layout.
- Persona variants live in `text_content_sports`, `text_content_cooking`, `text_content_adventure`.
- Video and PPT assets live in `video_url` and `ppt_url`.
- `topics.text_content` JSON layout supports ordered `blocks` with `type` (`text|image|video|ppt`).
- Two layout modes are supported by the backend:
  - `contentKey` mode: blocks include a `contentKey`, which is resolved via `topic_content_assets` using the learner tutor persona (from `learner_persona_profiles`). The backend returns resolved block `data` payloads.
  - inline `data` mode: blocks include `data` directly and can optionally include `tutorPersona`. The backend filters blocks by `tutorPersona` when present.
- The frontend never sees `contentKey` or persona keys; it renders the resolved JSON it receives.
- In the course player:
  - If `text_content` parses as JSON, blocks render in order.
  - `data.variants` may include study persona variants (`normal`, `sports`, `cooking`, `adventure`) and the UI chooses the correct copy.
  - If `text_content` is plain text, the UI selects the study persona column (`text_content_*`) and falls back to `text_content`.

## 6) Data model focus (see `docs/databaseSchema.md`)
Core learner tables:
- `courses`, `topics`, `topic_progress`, `module_progress`
- `topic_personalization` (study persona: `normal|sports|cooking|adventure`)
- `learner_persona_profiles` (tutor persona)
- `topic_content_assets` (content payloads keyed by `content_key` + persona)
- `topic_prompt_suggestions`, `module_prompt_usage`
- `quiz_questions`, `quiz_options`, `quiz_attempts`
- `enrollments`

Cohort + cold calling:
- `cohorts`, `cohort_members`, `cohort_batch_projects`
- `cold_call_prompts`, `cold_call_messages`, `cold_call_stars`

AI tutor + memory:
- `course_chunks` (pgvector embeddings)
- `cp_rag_chat_sessions`, `cp_rag_chat_messages`

Telemetry + tutor monitor:
- `learner_activity_events`

Tutor/admin + CMS + commerce:
- `tutor_applications`, `tutors`, `course_tutors`
- `page_content`
- `cart_items`, `cart_lines`

## 7) Runtime constants (code-level truth)
RAG + tutor:
- Vector top-K: 5
- Embedding dims: 1536
- Insert batch size: 50
- Chunk size: 900, overlap: 150
- Rate limit: 8 requests / 60 seconds per user
- Typed prompt quota: 5 per module
- Chat history: last 10 turns; session load limit 40
- Summary starts after 16 messages

Quiz gating:
- Pass threshold: 70%
- Default question limit: 5 (max 20)
- Module cooldown window: 7 days
- Frontend quiz timer: 150 seconds (2:30) in `CoursePlayerPage.tsx`

Auth/session defaults (see `backend/src/config/env.ts`):
- Access token TTL: 900s
- Refresh token TTL: 30 days

Telemetry:
- Max events per request: 50
- History query limit max: 100

## 8) Course resolution rules
- `coursesRouter` and `lessonsRouter`: resolve by UUID, legacy alias (`ai-in-web-development`), or `courseName`. They do not resolve arbitrary slugs.
- `assistantRouter` and `quizRouter`: resolve by UUID, legacy alias, `slug`, or `courseName`.
- `cohortProjectsRouter`: resolve by UUID, legacy alias, or `courseName`.
- RAG retrieval uses the raw `courseId` passed to `/assistant/query` after router resolution. Ensure `course_chunks.course_id` matches that value.

## 9) RAG ingestion and imports
- Ingest PDF to pgvector (default script uses `Web Dev using AI Course Content.pdf`):
  - `cd backend`
  - `npm run rag:ingest "../Web Dev using AI Course Content.pdf" ai-in-web-development "AI Native Full Stack Developer"`
- Import precomputed embeddings:
  - `npm run rag:import <json>`

## 10) Build + run (quick reference)
Frontend:
- `cd frontend && npm run dev`

Backend:
- `cd backend && npm run dev`

This handoff should be treated as authoritative for LLM context building.

## Addendum - 2026-03-04 (No Previous Lines Removed)
- Verified current runtime architecture: one `frontend/` app and one `backend/` API in this repository.
- Verified async AI flow: request -> `background_jobs` queue -> `aiWorker` processing -> SSE response stream.
- Verified cohort access-state source endpoint: `GET /courses/:courseKey/access-status` returning `isAuthenticated`, `hasApplied`, `isApprovedMember`.
- Verified registration identity linkage: `POST /registrations` normalizes email and resolves/writes `registrations.user_id` using auth-user match or `users.email` lookup.
- Verified course details CTA progression for cohort flow: `Register Now` -> `Apply for Cohort` -> `Application is under review` -> `Start Learning`.

