# AI Tutor Streaming + Typewriter Rendering (Concise Implementation Notes)

## Scope of this document
This version is intentionally concise.

- It explains the complete improvement journey (before -> plan -> implementation -> final behavior).
- It includes code snippets **only** for the token/typewriter rendering behavior in the chatbot UI.
- It omits long backend code dumps.

---

## 1) What was happening before

In the Course Player AI Tutor flow, users were seeing:

1. A visible wait after submitting a question.
2. Then the full answer appearing all at once (instant pop-in).

Even when backend processing was running correctly, this made the experience feel slower than it actually was.

---

## 2) What we planned to fix

We set two goals:

1. **Perceived speed improvement**
   Show progress while response is being generated.

2. **Incremental answer rendering**
   Render the answer as a stream/typewriter effect instead of a single final pop-in.

Implementation direction:

- Keep async job + SSE flow.
- Consume streamed chunks in frontend.
- Buffer chunks and render them at controlled speed in the chat bubble.
- Add a fallback path: even if only final answer arrives, still animate it with typewriter playback.

---

## 3) What we changed (high-level)

### Backend-side changes (explained only)

- Worker emits response chunks during generation.
- SSE endpoint forwards status/chunk/completed events.
- Queue + worker timing tuned for faster pickup and delivery.

### Frontend-side changes (where token rendering happens)

- Added parsing for `chunk` events from stream.
- Added queue-based playback loop in `CoursePlayerPage.tsx`.
- Added controlled render speed using constants.
- Added fallback typewriter rendering when only final completed answer is present.

---

## 4) Token/typewriter rendering code snippets

> File reference: `frontend/src/pages/CoursePlayerPage.tsx`

### 4.1 Rendering speed controls

```ts
const CHAT_STREAM_TICK_MS = 30;
const CHAT_STREAM_CHARS_PER_TICK = 2;
```

These two values control the visible typing speed.

- `CHAT_STREAM_TICK_MS`: how often UI updates.
- `CHAT_STREAM_CHARS_PER_TICK`: how many characters are appended per tick.

---

### 4.2 Core playback queue logic

```ts
let streamedAnswer = "";
let pendingChunkQueue = "";
let streamEnded = false;
let playbackInterval: ReturnType<typeof setInterval> | null = null;
let resolvePlayback: (() => void) | null = null;

const playbackDone = new Promise<void>((resolve) => {
  resolvePlayback = resolve;
});

const stopPlayback = () => {
  if (playbackInterval) {
    clearInterval(playbackInterval);
    playbackInterval = null;
  }
  if (resolvePlayback) {
    resolvePlayback();
    resolvePlayback = null;
  }
};

const applyQueuedChunk = () => {
  if (!pendingChunkQueue) {
    if (streamEnded) {
      stopPlayback();
    }
    return;
  }

  const nextSlice = pendingChunkQueue.slice(0, CHAT_STREAM_CHARS_PER_TICK);
  pendingChunkQueue = pendingChunkQueue.slice(CHAT_STREAM_CHARS_PER_TICK);
  streamedAnswer += nextSlice;

  setChatMessages((prev) =>
    prev.map((msg) =>
      msg.id === botId
        ? { ...msg, text: streamedAnswer }
        : msg,
    ),
  );

  if (!pendingChunkQueue && streamEnded) {
    stopPlayback();
  }
};

const ensurePlaybackLoop = () => {
  if (playbackInterval) return;
  playbackInterval = setInterval(applyQueuedChunk, CHAT_STREAM_TICK_MS);
};
```

What this does:

- Stores incoming chunks in `pendingChunkQueue`.
- Gradually drains the queue.
- Updates the active bot message text incrementally.
- Stops cleanly when stream is over and queue is empty.

---

### 4.3 Stream chunk ingestion

```ts
const result = await streamJobResult(
  buildApiUrl(`/assistant/stream/${jobId}`),
  { Authorization: `Bearer ${session.accessToken}` },
  {
    onStatus: () => {
      // Status used for UX text only; raw backend queue text hidden.
    },
    onChunk: (chunkText) => {
      pendingChunkQueue += chunkText;
      ensurePlaybackLoop();
    },
  },
);
```

What this does:

- Receives incremental chunk payloads from SSE.
- Appends each chunk to local queue.
- Starts playback loop if not already running.

---

### 4.4 Fallback typewriter path (important)

```ts
const resolvedAnswer = typeof result?.answer === "string" ? result.answer : "";
if (streamedAnswer.trim().length === 0 && resolvedAnswer.trim().length > 0) {
  // If no chunk events arrived, still animate final answer
  pendingChunkQueue += resolvedAnswer;
  ensurePlaybackLoop();
}
streamEnded = true;
ensurePlaybackLoop();
applyQueuedChunk();
await playbackDone;
```

Why this is important:

- Prevents a sudden pop-in when chunk events are absent.
- Guarantees consistent typewriter UX in both stream and non-stream completion cases.

---

### 4.5 Final resolved answer assignment

```ts
answer = streamedAnswer.trim().length > 0
  ? streamedAnswer
  : resolvedAnswer.trim().length > 0
    ? resolvedAnswer
    : answer;
```

This ensures final output correctness after playback.

---

## 5) How it works now (final behavior)

Current learner experience:

1. Ask question.
2. AI Tutor immediately enters active generation state.
3. Response appears incrementally in the same bot message bubble.
4. User sees natural progressive answer growth.
5. Follow-up chips are shown only after answer is complete.

Net result:

- Better perceived responsiveness.
- Better conversational quality.
- No abrupt full-text pop-in.

---

## 6) Tuning guide

If you want slower/faster typewriter effect:

- Increase `CHAT_STREAM_TICK_MS` -> slower updates.
- Decrease `CHAT_STREAM_CHARS_PER_TICK` -> finer, slower typing.
- Opposite changes make rendering faster.

Current values are balanced for readability and responsiveness.

