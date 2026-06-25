# Industrial Workbench Frontend Redesign

## Goal

Redesign the existing AtlasSmartArm main workbench into a clearer industrial-style control console while preserving the current five views, API behavior, and safety-relevant task controls.

## What I Already Know

- The target surface is the current React/Vite main workbench in `frontend/src/App.tsx`.
- The existing views are pick/sort, stack, camera, management, and status.
- The user wants an industrial visual direction and complete preservation of current interactivity.
- Product Design requires three visual redesign directions before implementation because no concrete visual target was supplied.

## Requirements

- Preserve all existing user flows: switch views, submit pick-sort, submit stack, cancel active task, capture photos, refresh status, inspect task detail, recognition output, event stream, and system status.
- Improve hierarchy so operators can quickly distinguish command controls, machine state, active task, camera availability, logs, and historical data.
- Use an industrial control-room visual language: technical typography, clear status signals, utilitarian surfaces, restrained color, and robust spacing.
- Keep safety-relevant disabled states intact: no duplicate start for an active program, no cancel without an active task, no capture while a task owns the camera.
- Keep API request semantics unchanged.

## Acceptance Criteria

- [ ] The workbench renders the same five views and all current navigation buttons remain usable.
- [ ] Start, cancel, refresh, label input, and capture controls preserve their current enabled/disabled rules.
- [ ] Empty, loading, error, and unavailable states are visible and understandable.
- [ ] Long task IDs, long logs, empty lists, and mobile widths do not break layout.
- [ ] `npm test` passes.
- [ ] `npm run build` passes.
- [ ] The implemented screen is visually checked in a browser at desktop and mobile widths.

## Definition Of Done

- Tests or automated checks cover critical behavior where practical.
- Build/typecheck succeeds.
- Visual QA is performed against the selected design direction.
- A git commit records the completed change.

## Technical Approach

- First capture the current app visually and generate three Product Design options.
- After the user selects one direction, edit the existing React/CSS implementation directly without changing the backend contract.
- Prefer existing dependencies; do not add a UI framework unless the selected design cannot be achieved with current CSS and `lucide-react`.

## Out Of Scope

- Backend API changes.
- New routes or new product features.
- Real robot safety interlocks beyond preserving existing frontend blocking behavior.
- Persistent design-system extraction unless implementation naturally reveals a small reusable pattern.

## Technical Notes

- Frontend stack: React 19, Vite 7, TypeScript, plain CSS, `lucide-react`.
- Existing design files inspected: `frontend/src/App.tsx`, `frontend/src/styles.css`, component files under `frontend/src/components`.
- Frontend spec layer exists but is mostly placeholder; use current code patterns and Product Design guidance as primary implementation constraints.
