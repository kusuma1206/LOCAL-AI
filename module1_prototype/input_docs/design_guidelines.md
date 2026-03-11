# Course Platform Design Guidelines

These guidelines summarize the visual language so new components match the existing experience.

## 1. Visual principles
1. High-contrast hero sections: dark backgrounds with warm accent highlights (#bf2f1f, #f8f1e6).
2. Education-first tone: clean typography and whitespace, with accents reserved for CTAs.
3. Responsive-first: layouts collapse cleanly on mobile and tablet.
4. Accessible interactions: buttons and text maintain AA contrast.

## 2. Color tokens
| Token | Hex | Usage |
| --- | --- | --- |
| Background | #f8f1e6 | Body backgrounds, cards |
| Foreground | #000000 | Primary text |
| Accent | #bf2f1f | CTAs and status badges |
| Muted | #4a4845 | Secondary text |
| Sidebar | #000000 | Course player sidebar |

## 3. Typography
- Primary font: Inter (400-800).
- Headings use tight tracking and uppercase micro labels for section headers.

## 4. Course player layout rules
- The Study Material header must appear immediately before the first text block.
- If the first block is video, show the video without any Study header above it.
- When the first text block is followed by an image block, render the image attached under that first text card.
- Read Mode collapses the video block with a smooth height/opacity transition.
- When Read Mode is enabled, auto-scroll to the top of the lesson pane.
- Cohort Project button sits on the top bar near the progress label and opens a modal with title, tagline, description, and notes.

## 5. Components
- Buttons: shadcn variants with bold labels and consistent border radius.
- Cards: rounded corners, subtle shadows, and warm backgrounds.
- Modals: centered, strong header, clear close affordance.

## 6. Motion
- Use `transition` classes for hover and Read Mode toggles.
- Avoid heavy animation; keep it subtle and purposeful.

## 7. Accessibility
- Body copy at least 16px with 1.5 line height in reading contexts.
- Provide keyboard and focus states for dialogs and buttons.

## Addendum - 2026-03-04 (No Previous Lines Removed)
- Verified current runtime architecture: one `frontend/` app and one `backend/` API in this repository.
- Verified async AI flow: request -> `background_jobs` queue -> `aiWorker` processing -> SSE response stream.
- Verified cohort access-state source endpoint: `GET /courses/:courseKey/access-status` returning `isAuthenticated`, `hasApplied`, `isApprovedMember`.
- Verified registration identity linkage: `POST /registrations` normalizes email and resolves/writes `registrations.user_id` using auth-user match or `users.email` lookup.
- Verified course details CTA progression for cohort flow: `Register Now` -> `Apply for Cohort` -> `Application is under review` -> `Start Learning`.

