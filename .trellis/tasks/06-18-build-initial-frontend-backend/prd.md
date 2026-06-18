# Build Initial Frontend And Backend PRD

## Goal

Build the first runnable full-stack skeleton for the AtlasSmartArm project based on `docs/PRD.md` and `docs/DEVELOPMENT_GUIDE.md`.

## Scope

- Create the API-first contract at `docs/api/openapi.yaml`.
- Implement a FastAPI backend with unified response envelopes, stable error codes, mock hardware/vision services, task state, inventory state, and WebSocket events.
- Implement a React + TypeScript frontend that consumes the backend through a single API layer and shows system status, detections, tasks, arm controls, inventory, and event logs.
- Keep real Atlas, ROS2, serial, camera, and OM inference behind service boundaries so the app runs without hardware in mock mode.
- Add tests for backend response shape, task flow, inventory operations, and safety validation.

## Out Of Scope

- Real ROS2 `Kinemarics.srv` integration.
- Real serial servo movement.
- Real camera capture, calibration file parsing, or OM model inference.
- Persistent database storage.
- Authentication and role-based permissions.

## Acceptance Criteria

- `GET /api/v1/health` and the main API endpoints return the unified envelope with `request_id`, `success`, `data`, and `error`.
- Mock mode supports system status, vision detection, FK/IK, safe move dry-run, emergency stop, pick-sort task creation, stack task creation, task lookup/cancel, inventory CRUD, inbound/outbound/audit, and WebSocket event format.
- Frontend strict TypeScript build succeeds and uses a central API client instead of direct component-level fetch code.
- Backend tests pass for core contract behavior and state transitions.
- The project has clear run commands and environment examples.
