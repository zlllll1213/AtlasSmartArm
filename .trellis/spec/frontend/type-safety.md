# Type Safety

> Type safety patterns in this project.

---

## Overview

The frontend uses strict TypeScript. API-facing types live in one file and are
kept aligned with `docs/api/openapi.yaml` and backend Pydantic models.

---

## Type Organization

- Put shared API types in `frontend/src/api/types.ts`.
- Keep component prop types next to the component when they are only used once.
- Use stable string-union types for backend enums such as task states, material
  categories, and error codes.

---

## Validation

Runtime validation is currently performed by the backend. The frontend unwraps
the unified API envelope and throws `ApiError` when `success=false` or `error`
is present.

---

## Common Patterns

- Use `ApiResponse<T>` and `unwrapResponse<T>()` for all REST responses.
- Use `SystemEvent` for WebSocket events and treat REST as the source of truth.
- Prefer explicit return types for API client methods when the shape is used by
  multiple components.

---

## Forbidden Patterns

- Do not use `any` for backend data.
- Do not construct API request or response shapes inside components.
- Do not rename unit-bearing backend fields for presentation convenience.
