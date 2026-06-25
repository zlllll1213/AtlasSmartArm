# Quality Guidelines

> Code quality standards for frontend development.

---

## Overview

Frontend changes must preserve the operator's ability to understand device
state and must not weaken safety-relevant UI guards for task execution.

---

## Forbidden Patterns

- Do not expose raw network errors such as `Failed to fetch` as primary operator
  copy. Convert them to product language such as `Backend disconnected` or a
  localized equivalent.
- Do not enable task start controls while a task is active or while the UI is
  busy.
- Do not enable task interrupt controls when there is no active task.
- Do not request camera preview media while the camera is offline, backend
  status is unknown, or a running task owns the camera.

---

## Required Patterns

- Backend-offline preview must remain usable. Render explicit offline or empty
  states for status, event streams, camera preview, logs, and task detail.
- Safety-relevant disabled-state decisions should be expressed through small
  pure helpers when shared across command surfaces.

```typescript
export function canStartProgramAction(view: View, activeTask: boolean, busy: boolean): boolean {
  return (view === 'pick-sort' || view === 'stack') && !activeTask && !busy
}
```

---

## Testing Requirements

- Add unit tests for pure task-control guards that protect start/interrupt
  enabled states.
- Run `npm test` after behavior-affecting frontend changes.
- Run `npm run build` before handoff to confirm TypeScript and Vite output.

---

## Code Review Checklist

- Verify all task start, interrupt, refresh, capture, and navigation controls
  still point to the intended API actions.
- Verify backend-offline rendering does not create unhandled promise rejections,
  unconditional WebSocket loops, or broken camera image requests.
- Check desktop and mobile screenshots for clipped text, overlapping controls,
  and unreadable state labels.
