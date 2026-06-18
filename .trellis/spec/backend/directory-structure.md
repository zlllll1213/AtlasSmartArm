# Directory Structure

> How backend code is organized in this project.

---

## Overview

The backend is a FastAPI application under `src/backend/`. HTTP and
WebSocket routes stay thin and delegate behavior to service classes. Hardware,
vision, and integration code live outside the backend package behind stable
interfaces so API code does not import ROS2, serial, or camera details directly.

---

## Directory Layout

```text
src/
├── backend/
│   ├── api/              # FastAPI REST and WebSocket routes
│   ├── models/           # API schemas and enums
│   ├── services/         # Mock/real service boundaries used by routes
│   ├── app.py            # FastAPI app factory and middleware
│   ├── config.py         # Environment-backed settings
│   ├── errors.py         # ApiError and exception handlers
│   └── response.py       # Unified response envelope helpers
├── hardware/             # Arm adapter, kinematics, serial boundaries
├── integration/          # Task state machine and coordinate transforms
└── vision/               # Camera, detector, calibration boundaries
```

---

## Module Organization

- Add new public endpoints in `src/backend/api/routes.py` or split into a new
  router file under `src/backend/api/` when the file becomes hard to scan.
- Put request/response shapes in `src/backend/models/schemas.py` and stable
  string enums in `src/backend/models/enums.py`.
- Put behavior and state in `src/backend/services/`; routes should only parse
  inputs, call a service, and wrap the result.
- Put hardware-specific code in `src/hardware/`, vision-specific code in
  `src/vision/`, and closed-loop orchestration in `src/integration/`.

---

## Naming Conventions

Use lowercase snake_case for Python files. Public API fields must include units
where safety depends on units, such as `duration_ms`, `joint1_deg`, `x_m`, and
`x_px`.

---

## Examples

- `src/backend/services/arm_service.py` validates safety ranges before mock or
  real motion.
- `src/integration/coordinate_transform.py` centralizes pixel-to-arm unit
  conversion.
