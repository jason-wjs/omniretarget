# Solver Internal Split Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Decompose `src/holosoma_retargeting/solver/interaction_mesh_retargeter.py` into solver-local helper modules while preserving the public solver facade and current pipeline behavior.

**Architecture:** Keep `InteractionMeshRetargeter` as the stable public entrypoint. Extract visualization, kinematics, and collision helper groups into dedicated modules. Defer splitting the optimization core itself until those helper boundaries are stable.

**Tech Stack:** Python 3.11, uv, pytest, numpy, scipy, mujoco, trimesh, viser, cvxpy

---

### Task 1: Add a regression test for the multi-augmentation parallel path

**Files:**
- Create: `tests/test_parallel_process_single_task_regression.py`

**Step 1: Write the failing regression**

Add a lightweight unit test around `holosoma_retargeting.pipelines.parallel.process_single_task`.

The test should:

- monkeypatch heavy collaborators so it stays unit-level
- run a multi-augmentation path
- assert that every call to `build_retargeter_kwargs_from_config(...)` receives the original config object

This test is specifically guarding the recent fix where later augmentations accidentally reused the live solver instance instead of the config input.

**Step 2: Run focused tests and confirm RED before implementation if practical**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q \
  tests/test_parallel_process_single_task_regression.py \
  tests/test_pipeline_boundaries.py
```

Expected:

- the new regression fails against the old buggy behavior
- current branch should pass once the fix is preserved

### Task 2: Add failing solver module-boundary tests

**Files:**
- Create: `tests/test_solver_module_boundaries.py`
- Modify: `tests/test_module_entrypoints.py`

**Step 1: Add import coverage for new solver helper modules**

Add import cases for:

- `holosoma_retargeting.solver.visualization`
- `holosoma_retargeting.solver.kinematics`
- `holosoma_retargeting.solver.collision`

**Step 2: Add boundary assertions**

Create tests that assert:

- `InteractionMeshRetargeter` is still importable from `holosoma_retargeting.solver.interaction_mesh_retargeter`
- the new helper modules import cleanly
- the historical compatibility wrapper `holosoma_retargeting.src.interaction_mesh_retargeter` still imports cleanly

### Task 3: Extract visualization helpers first

**Files:**
- Create: `src/holosoma_retargeting/solver/visualization.py`
- Modify: `src/holosoma_retargeting/solver/interaction_mesh_retargeter.py`

**Step 1: Move visualization functions**

Extract the behavior behind:

- `_setup_visualization`
- `draw_mesh_from_geom`
- `draw_mesh_pair_with_contact`
- `draw_q`
- `draw_keypoints`
- `visualize_motion`
- `visualize_tetrahedra`

The main class should keep the same method names but delegate to helper functions in `solver/visualization.py`.

**Step 2: Keep import behavior stable**

Do not change public class construction or pipeline call sites.

### Task 4: Extract kinematics helpers

**Files:**
- Create: `src/holosoma_retargeting/solver/kinematics.py`
- Modify: `src/holosoma_retargeting/solver/interaction_mesh_retargeter.py`

**Step 1: Move Jacobian and position helpers**

Extract helper logic behind:

- `_world_to_body_frame`
- `_build_transform_qdot_to_qvel_fast`
- `_calc_contact_jacobian_from_point`
- `_calc_manipulator_jacobians`
- `_get_robot_link_positions`

As with visualization, preserve the current class method names as delegating wrappers in this phase.

### Task 5: Extract collision helpers

**Files:**
- Create: `src/holosoma_retargeting/solver/collision.py`
- Modify: `src/holosoma_retargeting/solver/interaction_mesh_retargeter.py`

**Step 1: Move collision/contact helpers**

Extract helper logic behind:

- `_compute_jacobian_for_contact_relative`
- `_prefilter_pairs_with_mj_collision`
- `_update_jacobians_and_phis_from_q`
- `_get_geometry_name`

Keep the sequence driver and optimization methods in the main solver file.

### Task 6: Verify the reduced solver facade stays green

**Files:**
- Review only

**Step 1: Run focused tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q \
  tests/test_parallel_process_single_task_regression.py \
  tests/test_solver_module_boundaries.py \
  tests/test_module_entrypoints.py \
  tests/test_pipeline_boundaries.py
```

Expected: PASS

**Step 2: Run compatibility and smoke checks**

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

### Task 7: Explicitly defer the optimization-core split

**Files:**
- No code changes

**Step 1: Defer splitting the two highest-risk methods**

Do not split these methods in this phase:

- `retarget_motion`
- `solve_single_iteration`
- `iterate`

These three methods form the behavioral core of the solver. They should be reconsidered only after the helper extractions are stable and separately tested.
