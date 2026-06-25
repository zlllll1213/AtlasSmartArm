# Hook Guidelines

> How hooks are used in this project.

---

## Overview

Frontend hooks wrap recurring runtime behavior such as polling and event streams.
Components decide when a hook is enabled; hooks own setup and cleanup.

---

## Custom Hook Patterns

- Hooks that open external connections must accept an `enabled` gate when the
  connection depends on backend availability.
- When disabled, the hook must return without opening network connections.
- Cleanup must close timers, sockets, or previews created by the hook.

```typescript
export function useEventStream(onEvent: (event: SystemEvent) => void, enabled = true): void {
  useEffect(() => {
    if (!enabled) {
      return undefined
    }
    const disconnect = connectEventStream(onEvent)
    return disconnect
  }, [enabled, onEvent])
}
```

---

## Data Fetching

- REST polling is driven by `usePolling(load, delayMs)`.
- WebSocket event streams should start only after a successful backend status
  read proves the backend is reachable.
- Pure frontend preview must not spam unavailable WebSocket or camera preview
  endpoints.

---

## Naming Conventions

Use the `use*` prefix for hooks and keep public hook arguments primitive or
stable callback references where possible.

---

## Common Mistakes

- Do not open WebSocket connections unconditionally on first render when the app
  also supports backend-offline preview.
- Do not leave interval or socket cleanup to component unmount side effects
  outside the hook.
