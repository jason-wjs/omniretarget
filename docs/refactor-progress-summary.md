# OmniRetarget Refactor Progress Summary

**Last updated:** 2026-04-24
**Branch:** `omniretarget-refactor`
**Scope:** Summary of the refactor work completed so far around `holosoma_retargeting/`

## Summary

So far, the refactor has moved the historical `holosoma_retargeting.src` layout
toward semantic module boundaries, established import and compatibility
guardrails, and recorded an explicit decision to keep the legacy `src/`
wrappers for one more phase.

The main result is that `solver/` and `utils/` now carry the intended ownership,
while `holosoma_retargeting.src.*` has been reduced to a compatibility bridge
instead of remaining the primary architectural boundary.

## Completed Changes

### 1. Introduced semantic module ownership

The previous `src/holosoma_retargeting/src/` implementation surface has been
reorganized into clearer semantic modules:

- `src/holosoma_retargeting/solver/`
  - `interaction_mesh_retargeter.py`
  - `collision.py`
  - `kinematics.py`
  - `visualization.py`
- `src/holosoma_retargeting/utils/`
  - `mujoco_utils.py`
  - `utils.py`
  - `viser_utils.py`
  - `motion_io.py`
  - `motion_preprocessing.py`
  - `object_mesh.py`
  - `scene_assets.py`
  - `transforms.py`
  - `contact.py`

This gives the project a clearer split between retargeting solver logic and
supporting utility functions.

### 2. Reduced production dependence on historical `src/`

Production-facing modules were moved away from directly depending on
`holosoma_retargeting.src.*`, including updates around:

- `src/holosoma_retargeting/pipelines/`
  - `motion_loading.py`
  - `object_setup.py`
  - `parallel.py`
  - `retarget.py`
- `src/holosoma_retargeting/evaluation/eval_retargeting.py`
- `src/holosoma_retargeting/viser_player.py`

The intended rule is now:

- production modules should import from semantic packages such as
  `holosoma_retargeting.solver.*` and `holosoma_retargeting.utils.*`
- historical `holosoma_retargeting.src.*` imports are compatibility-only

### 3. Retained historical `src/` as a thin compatibility bridge

The old package still exists under:

- `src/holosoma_retargeting/src/__init__.py`
- `src/holosoma_retargeting/src/interaction_mesh_retargeter.py`
- `src/holosoma_retargeting/src/mujoco_utils.py`
- `src/holosoma_retargeting/src/utils.py`
- `src/holosoma_retargeting/src/viser_utils.py`

These files are no longer treated as primary implementation ownership. They are
kept as wrappers that re-export from `solver/` or `utils/`.

### 4. Migrated tests toward semantic imports

Tests that previously imported from `holosoma_retargeting.src.utils` were moved
to the new semantic utility modules:

- `tests/test_optitrack_grounding_preprocess.py`
- `tests/test_package_paths.py`
- `tests/test_foot_sticking_contact_keys.py`

The import ownership now reflects the module split:

- preprocessing helpers from `holosoma_retargeting.utils.motion_preprocessing`
- contact extraction helpers from `holosoma_retargeting.utils.contact`

### 5. Added boundary and regression guardrails

New and updated tests now lock the refactor boundary into executable checks:

- `tests/test_pipeline_boundaries.py`
  - production modules must not import `holosoma_retargeting.src.*`
- `tests/test_module_entrypoints.py`
  - entrypoint imports must not mutate `sys.path`
  - one explicit legacy entrypoint coverage test is kept for the compatibility
    phase
- `tests/test_solver_module_boundaries.py`
  - verifies `solver/` importability and compatibility re-export behavior
- `tests/test_utils_module_boundaries.py`
  - verifies utility module import boundaries
- `tests/test_solver_visualization_helpers.py`
  - guards the split-out solver helper surface
- `tests/test_parallel_process_single_task_regression.py`
  - covers the parallel pipeline regression path
- `tests/test_src_compatibility_census.py`
  - scans configured source roots with AST and constrains remaining semantic
    `holosoma_retargeting.src.*` references to the temporary allowlist

### 6. Recorded design and phase-planning documents

The branch now includes refactor planning and design records for the completed
and upcoming phases, including:

- `docs/plans/2026-04-23-omniretarget-phase-roadmap-plan.md`
- `docs/plans/2026-04-24-solver-utils-boundary-design.md`
- `docs/plans/2026-04-24-solver-utils-boundary-plan.md`
- `docs/plans/2026-04-24-utils-first-internal-split-plan.md`
- `docs/plans/2026-04-24-solver-internal-split-design.md`
- `docs/plans/2026-04-24-solver-internal-split-plan.md`
- `docs/plans/2026-04-24-src-compat-removal-plan.md`

These docs explain the staged migration strategy rather than folding all
refactor goals into one unsafe step.

### 7. Made an explicit compatibility decision for legacy `src/`

Decision record:

- `docs/plans/2026-04-24-src-compat-removal-decision.md`

Decision:

- keep `src/holosoma_retargeting/src/` for one more phase
- do not delete the wrapper package yet

Reason:

- the wrapper layer is already thin, but it is still part of the package surface
- in-repo semantic uses are tightly bounded, but not yet intentionally retired
- active migration docs still treat legacy imports as a live compatibility bridge

## Verification Completed

The following verification has been run successfully during this phase:

1. Focused boundary verification
   - `PYTHONPATH=src uv run --with pytest pytest -q tests/test_pipeline_boundaries.py tests/test_module_entrypoints.py`
   - result: `28 passed`

2. Focused semantic utility-import migration verification
   - `PYTHONPATH=src uv run --with pytest pytest -q tests/test_optitrack_grounding_preprocess.py tests/test_package_paths.py tests/test_foot_sticking_contact_keys.py`
   - result: `9 passed`

3. Focused compatibility census verification
   - `PYTHONPATH=src uv run --with pytest pytest -q tests/test_src_compatibility_census.py`
   - result: `1 passed`

4. Focused phase suite
   - `PYTHONPATH=src uv run --with pytest pytest -q tests/test_parallel_process_single_task_regression.py tests/test_solver_visualization_helpers.py tests/test_solver_module_boundaries.py tests/test_module_entrypoints.py tests/test_pipeline_boundaries.py tests/test_src_compatibility_census.py`
   - result: `38 passed`

5. Smoke verification
   - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache bash scripts/test_smoke.sh`
   - result: passed

6. Build verification
   - `UV_CACHE_DIR=/tmp/uv-cache uv build`
   - result: passed

## Current Architecture Status

At the end of this stage:

- `solver/` owns the retargeting engine surface
- `utils/` owns the support utility surface
- `holosoma_retargeting.src.*` is a compatibility layer, not the preferred
  import boundary
- production code is guarded from reintroducing direct historical `src`
  dependencies
- remaining semantic `holosoma_retargeting.src.*` references are intentionally
  limited to compatibility tests

## Recommended Next Phase

The next safe phase is not deleting `src/` immediately. The safer sequence is:

1. continue internal decomposition inside `utils/`, especially
   `src/holosoma_retargeting/utils/utils.py`
2. stabilize ownership inside `solver/interaction_mesh_retargeter.py`
3. remove the remaining compatibility-test allowlist only after semantic usage
   truly reaches zero
4. revisit wrapper deletion as an explicit breaking-change decision, not as
   cleanup
