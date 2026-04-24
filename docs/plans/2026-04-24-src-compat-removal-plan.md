# Historical `src` Compatibility Removal Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Determine whether `src/holosoma_retargeting/src/` can be safely removed, and if so, remove it in a controlled phase with explicit compatibility decisions.

**Architecture:** Treat this as a compatibility-removal phase, not a mechanical cleanup. First eliminate all in-repo test dependencies on `holosoma_retargeting.src.*`, then decide whether the package should keep a deprecation bridge for one more phase or break imports and delete the wrappers. Do not mix this with optimization-core refactoring.

**Tech Stack:** Python 3.11, uv, pytest

---

### Task 1: Lock the current compatibility census into tests/docs

**Files:**
- Modify: `tests/test_pipeline_boundaries.py`
- Modify: `tests/test_module_entrypoints.py`
- Review: `src/holosoma_retargeting/src/__init__.py`
- Review: `src/holosoma_retargeting/src/interaction_mesh_retargeter.py`
- Review: `src/holosoma_retargeting/src/mujoco_utils.py`
- Review: `src/holosoma_retargeting/src/utils.py`
- Review: `src/holosoma_retargeting/src/viser_utils.py`

**Step 1: Confirm only compatibility wrappers remain**

Read the five files under `src/holosoma_retargeting/src/` and verify they are thin re-export wrappers only.

**Step 2: Tighten the boundary statement in tests**

Update `tests/test_pipeline_boundaries.py` comments or assertion messages so the contract is explicit:
- production modules must not import `holosoma_retargeting.src.*`
- tests may still do so temporarily during the compatibility-removal phase

**Step 3: Keep one explicit entrypoint coverage test for the legacy package**

Retain `holosoma_retargeting.src.interaction_mesh_retargeter` in `tests/test_module_entrypoints.py` for this phase only, so deletion later is a deliberate test change rather than an accidental fallout.

**Step 4: Run focused tests**

Run:

```bash
PYTHONPATH=src uv run --with pytest pytest -q \
  tests/test_pipeline_boundaries.py \
  tests/test_module_entrypoints.py
```

Expected: PASS

### Task 2: Migrate test imports off `holosoma_retargeting.src.utils`

**Files:**
- Modify: `tests/test_optitrack_grounding_preprocess.py`
- Modify: `tests/test_package_paths.py`
- Modify: `tests/test_foot_sticking_contact_keys.py`

**Step 1: Move each test to the semantic module it now belongs to**

Replace compatibility imports with direct imports:
- `preprocess_motion_data` -> `holosoma_retargeting.utils.motion_preprocessing`
- `calculate_scale_factor` -> `holosoma_retargeting.utils.motion_preprocessing`
- `extract_foot_sticking_sequence_velocity` -> `holosoma_retargeting.utils.contact`

**Step 2: Do not change asserted behavior**

Only change import locations. Keep the test bodies and behavioral expectations stable unless they rely on compatibility-specific semantics.

**Step 3: Run focused tests**

Run:

```bash
PYTHONPATH=src uv run --with pytest pytest -q \
  tests/test_optitrack_grounding_preprocess.py \
  tests/test_package_paths.py \
  tests/test_foot_sticking_contact_keys.py
```

Expected: PASS

### Task 3: Add a negative census for remaining in-repo `holosoma_retargeting.src.*` imports

**Files:**
- Create: `tests/test_src_compatibility_census.py`

**Step 1: Add a repo-local census test**

Write a test that scans:
- `src/holosoma_retargeting/`
- `tests/`

and reports remaining `holosoma_retargeting.src.*` references by category.

For this phase, the expected allowed set should be:
- `tests/test_module_entrypoints.py`
- `tests/test_solver_module_boundaries.py`

Everything else should fail.

**Step 2: Run the census test**

Run:

```bash
PYTHONPATH=src uv run --with pytest pytest -q tests/test_src_compatibility_census.py
```

Expected: PASS

### Task 4: Decide compatibility policy explicitly

**Files:**
- Create: `docs/plans/2026-04-24-src-compat-removal-decision.md`

**Step 1: Record the decision**

Write a short decision note with one of two outcomes:

1. **Keep wrappers for one more phase**
   - reason: external import compatibility still matters
   - effect: in-repo code/tests stop using them, but package keeps them

2. **Delete wrappers now**
   - reason: compatibility contract is no longer required
   - effect: remove package and update tests accordingly

This decision must be explicit before deletion work starts.

### Task 5: If deletion is approved, remove the legacy package

**Files:**
- Delete: `src/holosoma_retargeting/src/__init__.py`
- Delete: `src/holosoma_retargeting/src/interaction_mesh_retargeter.py`
- Delete: `src/holosoma_retargeting/src/mujoco_utils.py`
- Delete: `src/holosoma_retargeting/src/utils.py`
- Delete: `src/holosoma_retargeting/src/viser_utils.py`
- Modify: `tests/test_module_entrypoints.py`
- Modify: `tests/test_solver_module_boundaries.py`
- Modify: `tests/test_src_compatibility_census.py`

**Step 1: Remove the wrapper files**

Delete the historical compatibility package only after Task 4 says deletion is allowed.

**Step 2: Remove tests that still assert legacy importability**

Delete the explicit coverage for:
- `holosoma_retargeting.src.interaction_mesh_retargeter`

and replace it with a negative assertion that the legacy package no longer exists.

**Step 3: Make the census test strict**

Update `tests/test_src_compatibility_census.py` so the allowed set becomes empty.

**Step 4: Run focused tests**

Run:

```bash
PYTHONPATH=src uv run --with pytest pytest -q \
  tests/test_solver_module_boundaries.py \
  tests/test_module_entrypoints.py \
  tests/test_src_compatibility_census.py \
  tests/test_pipeline_boundaries.py
```

Expected: PASS

### Task 6: Phase verification

**Files:**
- Review only

**Step 1: Run focused phase suite**

Run:

```bash
PYTHONPATH=src uv run --with pytest pytest -q \
  tests/test_parallel_process_single_task_regression.py \
  tests/test_solver_visualization_helpers.py \
  tests/test_solver_module_boundaries.py \
  tests/test_module_entrypoints.py \
  tests/test_pipeline_boundaries.py \
  tests/test_src_compatibility_census.py
```

Expected: PASS

**Step 2: Run smoke tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache bash scripts/test_smoke.sh
```

Expected: PASS

**Step 3: Run build verification**

Run:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv build
```

Expected: PASS

### Task 7: Explicitly defer unrelated solver-core cleanup

**Files:**
- No code changes

**Step 1: Do not mix compatibility removal with solver-core logic fixes**

Do not fix pre-existing solver-core bugs in this phase unless they block deletion directly.

Examples to defer:
- foot Jacobian double-slicing inside `solve_single_iteration()`
- `point_offsets` position inconsistency in kinematics helpers
- any split of `retarget_motion`, `solve_single_iteration`, or `iterate`
