# Directory Structure

> How frontend code is organized in this project.

---

## Overview

The frontend is a React + TypeScript + Vite app under `frontend/`. It uses a
single API client layer for backend communication and keeps dashboard panels as
small focused components.

---

## Directory Layout

```text
src/
├── api/
│   ├── client.ts         # Fetch/WebSocket helpers and endpoint methods
│   ├── client.test.ts    # API envelope behavior tests
│   └── types.ts          # Frontend contract types matching OpenAPI/backend
├── components/           # Dashboard panels and reusable UI surfaces
├── hooks/                # Polling and event-stream hooks
├── App.tsx               # Dashboard composition and local workflow state
├── main.tsx              # React root
└── styles.css            # App-level design tokens and layout
```

---

## Module Organization

- Add backend calls only in `src/api/client.ts`; components should not call
  `fetch` directly.
- Put shared API shapes in `src/api/types.ts`.
- Keep each dashboard region in its own component under `src/components/`.
- Put reusable data-refresh behavior in hooks under `src/hooks/`.

---

## Naming Conventions

Use PascalCase for React components and camelCase for functions, hooks, and
local variables. API field names must match backend/OpenAPI names exactly,
including unit suffixes such as `_ms`, `_deg`, `_m`, and `_px`.

---

## Examples

- `frontend/src/api/client.ts` centralizes REST and WebSocket access.
- `frontend/src/components/TaskPanel.tsx` keeps task UI separate from API
  request construction.
