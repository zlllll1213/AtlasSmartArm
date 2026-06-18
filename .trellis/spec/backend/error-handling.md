# Error Handling

> How errors are handled in this project.

---

## Overview

Backend errors are returned through the unified envelope required by
`docs/DEVELOPMENT_GUIDE.md`: every response has `request_id`, `success`,
`data`, and `error`. Routes and services raise `ApiError` for business failures
instead of returning ad-hoc error dictionaries.

---

## Error Types

`src/backend/errors.py` defines `ApiError` with:

- `code`: stable public error code such as `OUT_OF_RANGE` or `NOT_FOUND`
- `message`: human-readable English message
- `status_code`: HTTP status code
- `details`: machine-readable context

---

## Error Handling Patterns

- Services raise `ApiError` when validation or state checks fail.
- FastAPI validation errors are mapped to `INVALID_ARGUMENT` with HTTP 400.
- Unknown exceptions are mapped to `INTERNAL` with HTTP 500 and no stack trace
  in the client response.
- Hardware/vision adapters must wrap lower-level exceptions before they cross
  into routes.

---

## API Error Responses

```json
{
  "request_id": "req_7baa80db0efc479f",
  "success": false,
  "data": null,
  "error": {
    "code": "OUT_OF_RANGE",
    "message": "duration_ms must be between 100 and 3000.",
    "details": { "field": "duration_ms", "min": 100, "max": 3000 }
  }
}
```

---

## Common Mistakes

- Returning raw FastAPI/Pydantic validation payloads instead of the unified
  envelope.
- Leaking ROS2, serial, camera, or model exception details to frontend clients.
- Omitting unit-bearing field names in `details` for safety failures.
