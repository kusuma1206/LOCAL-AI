# Database Schema - Course Platform

Source of truth: `backend/prisma/schema.prisma`. Physical tables are snake_case; Prisma maps them to camelCase fields.

## 1. Entity overview
| Group | Tables | Highlights |
| --- | --- | --- |
| Accounts and sessions | `users`, `user_sessions`, `tutors`, `tutor_applications`, `course_tutors` | OAuth identities, hashed refresh tokens, tutor staffing |
| Course catalog | `courses`, `topics`, `simulation_exercises`, `page_content` | Module/topic metadata, legacy persona text, simulations, CMS pages |
| Content assets | `topic_content_assets` | Master content store keyed by `content_key` + `persona_key` |
| Cohort access | `cohorts`, `cohort_members`, `cohort_batch_projects` | Allowlist batches and assigned project briefs |
| Cohort interaction | `cold_call_prompts`, `cold_call_messages`, `cold_call_stars` | Blind-response prompts and reactions |
| Knowledge store | `course_chunks` | RAG embeddings stored in pgvector |
| Tutor memory | `cp_rag_chat_sessions`, `cp_rag_chat_messages` | Persistent chat history and summaries |
| Personalization | `topic_personalization`, `learner_persona_profiles`, `topic_prompt_suggestions`, `module_prompt_usage` | Study personas, tutor personas, prompt trees, quotas |
| Progress and assessments | `topic_progress`, `quiz_questions`, `quiz_options`, `quiz_attempts`, `module_progress` | Lesson completion and module unlock state |
| Certificates | `course_certificates` | Certificate issuance metadata and learner feedback |
| Commerce and enrollment | `enrollments`, `cart_items`, `cart_lines` | Enrollment writes and cart storage |
| Async Job Queue | `background_jobs` | Persistent job queue for long-running AI tasks |

## 2. Mermaid diagram (abridged)
```
classDiagram
    class User {
        +UUID userId
        +String email
        +Role role
    }
    class Course {
        +UUID courseId
        +String courseName
        +String slug
    }
    class Topic {
        +UUID topicId
        +UUID courseId
        +Int moduleNo
        +Int topicNumber
        +String topicName
        +String textContent (derived JSON)
    }
    class TopicContentAsset {
        +UUID assetId
        +UUID topicId
        +UUID courseId
        +String contentKey
        +String contentType
        +PersonaKey? personaKey
        +Json payload
    }
    class Cohort {
        +UUID cohortId
        +UUID courseId
        +String name
        +Bool isActive
    }
    class CohortMember {
        +UUID memberId
        +UUID cohortId
        +UUID? userId
        +String email
        +Int batchNo
    }
    class CohortBatchProject {
        +UUID projectId
        +UUID cohortId
        +Int batchNo
        +Json payload
    }
    class TopicPersonalization {
        +UUID userId
        +UUID courseId
        +StudyPersona persona
    }
    class LearnerPersonaProfile {
        +UUID profileId
        +UUID userId
        +UUID courseId
        +PersonaKey personaKey
    }

    User "1" -- "*" TopicPersonalization
    User "1" -- "*" LearnerPersonaProfile
    User "1" -- "*" CohortMember
    Course "1" -- "*" Topic
    Course "1" -- "*" Cohort
    Topic "1" -- "*" TopicContentAsset
    Cohort "1" -- "*" CohortMember
    Cohort "1" -- "*" CohortBatchProject
```

## 3. Table notes
### topics
- Stores module/topic metadata and legacy content fields (`video_url`, `ppt_url`, `text_content_*`).
- `text_content` may hold a derived JSON layout with blocks and `contentKey` references.

### topic_content_assets
- Master store for persona-specific assets referenced by `contentKey`.
- `content_type` is one of `text`, `image`, `video`, `ppt`.
- `persona_key` uses `LearnerPersonaProfileKey` and can be null to represent default content.
- Payload is JSON and is returned to the frontend after backend filtering.

### course_chunks
- Stores RAG embeddings for tutor retrieval.
- `course_id` is a UUID string; must match the resolved course UUID used by `/assistant/query`.

### cohorts and cohort_members
- Cohort allowlists are tracked per course.
- `cohort_members.batch_no` assigns learners to batches used for project briefs.

### cohort_batch_projects
- One row per `(cohort_id, batch_no)` storing a project brief payload.
- Payload format is `{ title, tagline, description, notes? }`.

### topic_personalization
- Study narrator preference per learner/course (`normal`, `sports`, `cooking`, `adventure`).

### learner_persona_profiles
- LLM-derived tutor persona per learner/course (non_it_migrant, rote_memorizer, english_hesitant, last_minute_panic, pseudo_coder).
- Used by the backend to select persona-specific content assets.

### course_certificates
- Stores issued certificates per learner/course/program type (unique by `user_id`, `course_id`, `program_type`).
- Captures display name, course title snapshot, optional feedback rating/text, and issued timestamp.

## 4. Schema tips
- Run `npx prisma format` after editing `schema.prisma`.
- Prefer Prisma migrations over manual SQL in repo workflows.
- Enable pgvector with `CREATE EXTENSION vector;`.

## Addendum - 2026-03-04 (No Previous Lines Removed)
- Verified current runtime architecture: one `frontend/` app and one `backend/` API in this repository.
- Verified async AI flow: request -> `background_jobs` queue -> `aiWorker` processing -> SSE response stream.
- Verified cohort access-state source endpoint: `GET /courses/:courseKey/access-status` returning `isAuthenticated`, `hasApplied`, `isApprovedMember`.
- Verified registration identity linkage: `POST /registrations` normalizes email and resolves/writes `registrations.user_id` using auth-user match or `users.email` lookup.
- Verified course details CTA progression for cohort flow: `Register Now` -> `Apply for Cohort` -> `Application is under review` -> `Start Learning`.

