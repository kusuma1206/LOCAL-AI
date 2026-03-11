# Course Platform Walkthrough - From Landing to Certificate

This walkthrough pairs UX steps with code references so another engineer (or LLM) can reproduce the learner journey.

## 1. Sign-in flow
1. Learner clicks "Login / Signup" on the marketing navbar (`frontend/src/components/layout/Navbar.tsx`).
2. Browser hits `/auth/google` (`backend/src/routes/auth.ts`) and is redirected to Google OAuth.
3. `/auth/google/callback` exchanges the code, upserts the user, and issues JWTs.
4. `AuthCallbackPage.tsx` stores the session and routes the learner to `postLoginRedirect`.

## 2. Landing page assistance
1. `LandingPage.tsx` renders `<LandingChatBot />`.
2. Visitor interaction triggers `/api/landing-assistant/query` (enqueues job, returns 202).
3. Chatbot subscribes to SSE (`/stream/:jobId`) to receive the answer.
4. If signed in, the bot greets the user by name (`user.fullName`).
4. Follow-up suggestions appear for the first 4 turns (Tier 1), then fallback to static CTA buttons (Tier 2).


## 2. Enrollment and cohort gate
1. `CourseDetailsPage.tsx` fetches `/courses/:courseKey` and `/lessons/courses/:courseKey/topics`.
2. Clicking Enroll calls `POST /courses/:courseKey/enroll?checkOnly=true`.
3. If eligible, the Ottolearn modal opens and `POST /courses/:courseKey/enroll` writes the enrollment.
4. If `GET /lessons/courses/:courseKey/personalization` returns `hasPreference=false`, the learner is routed to `/course/:courseKey/path`.

## 3. Study persona questionnaire
1. `LearningPathPage.tsx` displays the three-question survey.
2. "Use this style" posts `{ persona }` to `/lessons/courses/:courseKey/personalization`.
3. The selected study persona is stored in `topic_personalization` and cached client-side for fast toggles.

## 4. Course player content flow
1. `GET /lessons/courses/:courseKey/topics` returns all topics sorted by module and topic number.
2. For block-based topics, `topics.text_content` contains derived JSON with `contentKey` references.
3. `lessonsRouter` resolves each `contentKey` against `topic_content_assets` using the learner tutor persona (from `learner_persona_profiles`), then returns resolved block data. The frontend never sees persona keys.
4. `CoursePlayerPage.tsx` renders blocks sequentially. The Study Material header appears before the first text block, and the first text block can attach an adjacent image block.
5. Read Mode collapses the video block with a smooth transition and scrolls the main pane to the top.
6. The Cohort Project button fetches `/cohort-projects/:courseKey` and opens a modal with the project brief.

## 5. Cold calling checkpoint
1. Client loads `/cold-call/prompts/:topicId`.
2. Learner must submit before seeing cohort responses.
3. Replies and stars are then available.

## 6. Quiz cadence
1. `GET /quiz/sections/:courseKey` and `GET /quiz/progress/:courseKey` determine unlock state.
2. `POST /quiz/attempts` creates a frozen attempt; submit via `/quiz/attempts/:id/submit`.
3. Passing the final topic pair of a module updates `module_progress` and unlocks the next module.

## 7. Tutor chat
1. Chat dock loads suggestions via `/lessons/courses/:courseKey/prompts`.
2. History is hydrated from `/assistant/session?courseId=...&topicId=...`.
3. Typed prompts go to `/assistant/query` (async job).
4. Player receives `jobId`, subscribes to SSE, and updates chat upon completion.

## 8. Certificate preview
1. After all modules pass, the player links to `/course/:courseKey/congrats/certificate`.
2. The certificate page shows a blurred preview and a payment placeholder.

## 9. Troubleshooting
- OAuth errors: verify redirect URIs and `FRONTEND_APP_URLS`.
- Missing study content: confirm `topics.text_content` JSON parses and `topic_content_assets` rows exist for each `contentKey`.
- Cohort project missing: ensure `cohort_members.batch_no` and `cohort_batch_projects` rows exist for the cohort.
- Tutor 429: typed prompt quota hit for the current module.
- RAG results missing: `course_chunks.course_id` must match the resolved course ID used by `/assistant/query`.

## Addendum - 2026-03-04 (No Previous Lines Removed)
- Verified current runtime architecture: one `frontend/` app and one `backend/` API in this repository.
- Verified async AI flow: request -> `background_jobs` queue -> `aiWorker` processing -> SSE response stream.
- Verified cohort access-state source endpoint: `GET /courses/:courseKey/access-status` returning `isAuthenticated`, `hasApplied`, `isApprovedMember`.
- Verified registration identity linkage: `POST /registrations` normalizes email and resolves/writes `registrations.user_id` using auth-user match or `users.email` lookup.
- Verified course details CTA progression for cohort flow: `Register Now` -> `Apply for Cohort` -> `Application is under review` -> `Start Learning`.

