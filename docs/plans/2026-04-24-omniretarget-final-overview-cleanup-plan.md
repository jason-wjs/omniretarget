# OmniRetarget Final Overview Cleanup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove the remaining legacy package directories so `src/holosoma_retargeting/` matches the final overview layout exactly.

**Architecture:** Move typed dataclass configuration schemas from `config_types/` into `configs/`, collapse `config_values/`, and move the remaining package-internal `src/` code into responsibility-based modules. Keep algorithm-specific retargeting logic under `retargeter/`, keep algorithm-independent helpers under `utils/`, and remove legacy import paths after all first-party users migrate.

**Tech Stack:** Python 3.11, dataclasses, Tyro, setuptools, pytest, MuJoCo, Viser, NumPy

---

## Target End State

After this plan, `src/holosoma_retargeting/` should contain only:

```text
holosoma_retargeting/
  cli/
    data_process/
  configs/
  demo_data/
  models/
  profiles/
  retargeter/
  utils/
  __init__.py
  path_utils.py
```

The following directories must be removed:

```text
src/holosoma_retargeting/config_types/
src/holosoma_retargeting/config_values/
src/holosoma_retargeting/src/
```

## Final Internal Module Responsibilities

### `configs/`

`configs/` owns user-configurable typed dataclass schema, validation, and runtime resolution.

It should contain Tyro-facing config classes such as `RetargetingConfig`, `ParallelRetargetingConfig`, `RobotConfig`, `MotionDataConfig`, `TaskConfig`, `RetargeterConfig`, `DataConversionConfig`, and `ViserConfig`, plus runtime reconciliation helpers such as top-level `robot` / `data_format` selectors syncing into nested config objects.

It should not contain built-in robot or motion registries, retargeting algorithms, mesh processing, MuJoCo helpers, Viser playback, or command orchestration.

### `profiles/`

`profiles/` owns project-provided domain defaults and registries.

It should contain robot defaults, DOF, heights, manual limits, nominal tracking indices, foot sticking links, motion-format joint names, toe names, format metadata, and robot-motion joint mappings.

It should not contain Tyro dataclass schema, runtime config merging, package path resolution, CLI workflow code, or file conversion logic.

### `retargeter/`

`retargeter/` owns the interaction-mesh retargeting algorithm.

Its final module split should stay intentionally small:

```text
retargeter/
  __init__.py
  retargeter.py
  solver.py
  constraint.py
  interaction_mesh.py
```

- `retargeter.py`: canonical home of `InteractionMeshRetargeter`; owns retargeter state, MuJoCo model/data lifecycle, frame loop orchestration, iterative solve loop, result writing, and debug drawing methods that directly depend on retargeter state.
- `solver.py`: builds and solves the single-step SQP/CVXPY problem from prepared matrices and constraint data.
- `constraint.py`: extracts solver-ready constraint data from current retargeter/MuJoCo state, including qdot-to-qvel transforms, Jacobians, link positions, foot-sticking terms, and non-penetration contact terms.
- `interaction_mesh.py`: owns interaction-mesh and Laplacian helper functions such as Delaunay mesh creation, adjacency construction, Laplacian coordinates, and Laplacian matrices.

Do not add extra `retargeter/kinematics.py`, `retargeter/collision.py`, `retargeter/visualization.py`, or `retargeter/transform.py` modules during this phase unless a later code-size problem justifies it. The immediate goal is clearer algorithm semantics without over-abstracting.

### `utils/`

`utils/` owns reusable helpers that remain meaningful without knowing about the retargeter solver, task constants, or per-frame optimization state.

The final utility split for this cleanup should be:

```text
utils/
  __init__.py
  transform.py
  motion.py
  object_geometry.py
  mujoco_mesh.py
  viser_playback.py
```

- `transform.py`: generic coordinate and pose transforms, including local/world point transforms, y-up to z-up conversion, human orientation estimation, and human/object frame transforms when they do not depend on retargeter state.
- `motion.py`: motion IO, motion preprocessing, height normalization, scale handling, object pose preprocessing, first-moving-frame detection, and foot contact/sticking extraction from human motion.
- `object_geometry.py`: object mesh loading, surface sampling, weighted sampling, object-axis scaling, and generation of scaled object mesh/URDF/XML assets.
- `mujoco_mesh.py`: runtime MuJoCo geom-to-mesh extraction from `model`/`data` and current geom poses.
- `viser_playback.py`: generic Viser playback controls such as motion sliders and play/pause interpolation.

`utils/` should not contain CVXPY solver construction, retargeter constraints, interaction-mesh Laplacian algorithm helpers, CLI workflows, config schema, or profile registries.

### `models/` and `demo_data/`

`models/` and `demo_data/` remain stable package data and are intentionally not touched by this cleanup.

`models/` contains static robot/object URDF, XML, mesh, and template assets. `demo_data/` contains small packaged examples and fixtures. Large external datasets and generated experiment outputs should stay outside the package.

### `path_utils.py`

`path_utils.py` owns lightweight package-relative path resolution for package data. It should not become a registry, asset resolver class, dataset manager, plugin layer, or IO abstraction.

### `__init__.py`

The package root `__init__.py` should stay lightweight. It may expose a version or very small stable public surface, but it must not import heavy dependencies such as MuJoCo, Viser, CVXPY, or Torch as a side effect of `import holosoma_retargeting`.

## Execution Rules

- Work only in `/home/humanoid/Projects/Junsong_WU/ADAM/omni/omniretarget-refactor-next`.
- Keep `models/` and `demo_data/` unchanged.
- Do not introduce Hydra, `pipelines/`, top-level `io/`, plugin systems, or broad workflow base classes.
- Do not change public CLI command names in `pyproject.toml`.
- Use TDD for each deletion boundary: first add a test that describes the final desired absence, then migrate code, then delete the old module.
- Prefer small commits per phase.
- Use `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q ...` for tests.

## Final Verification

Run these commands before the final commit:

```bash
find src/holosoma_retargeting -maxdepth 1 -type d | sort
rg -n "holosoma_retargeting\.(config_types|config_values|src)" src tests README.md docs/*.md pyproject.toml
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests
git diff --check HEAD
git status --short
```

Expected:

- `find` shows no `config_types`, `config_values`, or `src` directories.
- `rg` returns no matches.
- Full test suite passes.
- `git diff --check HEAD` returns no output.
- `git status --short` only shows intended staged changes before commit, and is clean after commit.

---

### Task 1: Add Final Layout Boundary Tests

**Files:**
- Modify: `tests/test_repo_doc_boundaries.py`
- Create or modify: `tests/test_final_package_layout.py`

**Intent:** Make the final overview layout executable as a test before moving files.

**Step 1: Add failing package layout tests**

Create `tests/test_final_package_layout.py` with tests equivalent to:

```python
from __future__ import annotations

import importlib

import pytest

from tests.path_helpers import PACKAGE_ROOT


def test_final_overview_package_directories() -> None:
    expected = {
        "__pycache__",
        "cli",
        "configs",
        "demo_data",
        "models",
        "profiles",
        "retargeter",
        "utils",
    }
    actual = {path.name for path in PACKAGE_ROOT.iterdir() if path.is_dir()}
    assert actual <= expected


@pytest.mark.parametrize(
    "module_name",
    [
        "holosoma_retargeting.config_types",
        "holosoma_retargeting.config_values",
        "holosoma_retargeting.src",
        "holosoma_retargeting.src.utils",
        "holosoma_retargeting.src.mujoco_utils",
        "holosoma_retargeting.src.viser_utils",
        "holosoma_retargeting.src.interaction_mesh_retargeter",
    ],
)
def test_legacy_architecture_modules_are_removed(module_name: str) -> None:
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(module_name)
```

**Step 2: Run test and verify failure**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_final_package_layout.py
```

Expected: FAIL because `config_types/`, `config_values/`, and `src/` still exist.

**Step 3: Commit test baseline**

Do not commit yet if the test fails. Keep it as the guard for subsequent tasks.

---

### Task 2: Move Typed Config Schema from `config_types/` to `configs/`

**Files:**
- Move: `src/holosoma_retargeting/config_types/data_conversion.py` -> `src/holosoma_retargeting/configs/data_conversion.py`
- Move: `src/holosoma_retargeting/config_types/data_type.py` -> `src/holosoma_retargeting/configs/motion.py`
- Move: `src/holosoma_retargeting/config_types/retargeter.py` -> `src/holosoma_retargeting/configs/retargeter.py`
- Move: `src/holosoma_retargeting/config_types/retargeting.py` -> `src/holosoma_retargeting/configs/retargeting.py`
- Move: `src/holosoma_retargeting/config_types/robot.py` -> `src/holosoma_retargeting/configs/robot.py`
- Move: `src/holosoma_retargeting/config_types/task.py` -> `src/holosoma_retargeting/configs/task.py`
- Move: `src/holosoma_retargeting/config_types/viser.py` -> `src/holosoma_retargeting/configs/viser.py`
- Modify: `src/holosoma_retargeting/configs/__init__.py`
- Modify: all imports under `src/` and `tests/`

**Intent:** Make `configs/` the only configuration schema and runtime resolution package.

**Step 1: Move files**

Use `git mv`:

```bash
git mv src/holosoma_retargeting/config_types/data_conversion.py src/holosoma_retargeting/configs/data_conversion.py
git mv src/holosoma_retargeting/config_types/data_type.py src/holosoma_retargeting/configs/motion.py
git mv src/holosoma_retargeting/config_types/retargeter.py src/holosoma_retargeting/configs/retargeter.py
git mv src/holosoma_retargeting/config_types/retargeting.py src/holosoma_retargeting/configs/retargeting.py
git mv src/holosoma_retargeting/config_types/robot.py src/holosoma_retargeting/configs/robot.py
git mv src/holosoma_retargeting/config_types/task.py src/holosoma_retargeting/configs/task.py
git mv src/holosoma_retargeting/config_types/viser.py src/holosoma_retargeting/configs/viser.py
```

**Step 2: Update internal config imports**

Replace imports:

```text
holosoma_retargeting.config_types.data_conversion -> holosoma_retargeting.configs.data_conversion
holosoma_retargeting.config_types.data_type -> holosoma_retargeting.configs.motion
holosoma_retargeting.config_types.retargeter -> holosoma_retargeting.configs.retargeter
holosoma_retargeting.config_types.retargeting -> holosoma_retargeting.configs.retargeting
holosoma_retargeting.config_types.robot -> holosoma_retargeting.configs.robot
holosoma_retargeting.config_types.task -> holosoma_retargeting.configs.task
holosoma_retargeting.config_types.viser -> holosoma_retargeting.configs.viser
```

Also update the local import inside `MotionDataConfig.__post_init__` from `configs.robot`.

**Step 3: Update `configs/__init__.py`**

Export the public config classes:

```python
from holosoma_retargeting.configs.data_conversion import DataConversionConfig
from holosoma_retargeting.configs.motion import DataFormat, MotionDataConfig
from holosoma_retargeting.configs.retargeter import RetargeterConfig
from holosoma_retargeting.configs.retargeting import ParallelRetargetingConfig, RetargetingConfig
from holosoma_retargeting.configs.robot import RobotConfig
from holosoma_retargeting.configs.task import TaskConfig
from holosoma_retargeting.configs.viser import ViserConfig

__all__ = [
    "DataConversionConfig",
    "DataFormat",
    "MotionDataConfig",
    "ParallelRetargetingConfig",
    "RetargeterConfig",
    "RetargetingConfig",
    "RobotConfig",
    "TaskConfig",
    "ViserConfig",
]
```

**Step 4: Run focused config tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_config_runtime_resolution.py tests/test_profiles.py tests/test_adam_pro_robot_config.py tests/test_adam_pro_motion_mappings.py tests/test_optitrack_motion_format.py
```

Expected: PASS after all imports are updated.

**Step 5: Remove `config_types/__init__.py` and directory**

Run:

```bash
git rm src/holosoma_retargeting/config_types/__init__.py
rmdir src/holosoma_retargeting/config_types
```

If ignored `__pycache__` prevents removal, delete only that ignored cache directory, then `rmdir` the empty directory.

**Step 6: Commit**

Run:

```bash
git add src tests
git commit -m "refactor: move config schemas into configs"
```

---

### Task 3: Collapse and Remove `config_values/`

**Files:**
- Delete: `src/holosoma_retargeting/config_values/__init__.py`
- Delete: `src/holosoma_retargeting/config_values/data_conversion.py`
- Delete: `src/holosoma_retargeting/config_values/data_type.py`
- Delete: `src/holosoma_retargeting/config_values/robot.py`
- Delete: `src/holosoma_retargeting/config_values/viser.py`
- Modify or create: `src/holosoma_retargeting/configs/defaults.py` only if tests or first-party code still need factory helpers
- Modify: tests importing `config_values`

**Intent:** Remove the old thin factory layer unless a real responsibility remains.

**Step 1: Search for first-party usage**

Run:

```bash
rg -n "config_values|get_default_.*_config|get_.*_config_from_cli" src tests README.md docs/*.md
```

Expected: identify all uses before deleting.

**Step 2: Prefer direct dataclass construction**

Replace simple factory usage with direct construction:

```python
RobotConfig(robot_type="g1")
MotionDataConfig(data_format="smplh", robot_type="g1")
DataConversionConfig(...)
ViserConfig()
```

If a helper is still genuinely useful, move it to `configs/defaults.py` and import from there. Do not preserve the `config_values` package.

**Step 3: Delete old package**

Run:

```bash
git rm -r src/holosoma_retargeting/config_values
```

**Step 4: Add or update negative import tests**

Extend `tests/test_final_package_layout.py` if needed so `holosoma_retargeting.config_values` cannot import.

**Step 5: Run tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_final_package_layout.py tests/test_config_runtime_resolution.py tests/test_module_entrypoints.py
```

Expected: PASS.

**Step 6: Commit**

Run:

```bash
git add src tests
git commit -m "refactor: remove legacy config values package"
```

---

### Task 4: Move Generic Utility Code out of Package-Internal `src/`

**Files:**
- Move: `src/holosoma_retargeting/src/mujoco_utils.py` -> `src/holosoma_retargeting/utils/mujoco_mesh.py`
- Move: `src/holosoma_retargeting/src/viser_utils.py` -> `src/holosoma_retargeting/utils/viser_playback.py`
- Split: `src/holosoma_retargeting/src/utils.py` into focused modules under `src/holosoma_retargeting/utils/`
- Modify: `src/holosoma_retargeting/utils/__init__.py`
- Modify: all imports under `src/` and `tests/`

**Intent:** Remove broad package-internal `src/` utility imports and make reusable helpers discoverable under `utils/`.

**Recommended split for `src/utils.py`:**

```text
utils/motion.py
  load_intermimic_data
  calculate_scale_factor
  preprocess_motion_data
  extract_object_first_moving_frame
  extract_foot_sticking_sequence
  extract_foot_sticking_sequence_velocity

utils/object_geometry.py
  load_object_data
  weighted_surface_sampling
  weighted_surface_sampling_by_face_normal
  create_top_surface_weight_function
  scale_points_in_object_axes_frame
  create_scaled_object_mesh_and_urdf
  create_scaled_multi_boxes_urdf
  create_scaled_multi_boxes_xml
  create_new_scene_xml_file

utils/transform.py
  transform_from_human_to_world
  transform_points_world_to_local
  transform_points_local_to_world
  transform_y_up_to_z_up
  estimate_human_orientation

utils/mujoco_mesh.py
  _mesh_local_vf
  _to_world
  _world_mesh_from_geom

utils/viser_playback.py
  create_motion_control_sliders
```

**Step 1: Add import-focused tests for new utility modules**

Create or extend tests so first-party imports use:

```python
from holosoma_retargeting.utils.motion import preprocess_motion_data
from holosoma_retargeting.utils.motion import extract_foot_sticking_sequence_velocity
from holosoma_retargeting.utils.motion import calculate_scale_factor
from holosoma_retargeting.utils.transform import transform_points_world_to_local
from holosoma_retargeting.utils.mujoco_mesh import _world_mesh_from_geom
from holosoma_retargeting.utils.viser_playback import create_motion_control_sliders
```

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_package_paths.py tests/test_optitrack_grounding_preprocess.py tests/test_foot_sticking_contact_keys.py
```

Expected: FAIL until modules exist.

**Step 2: Move small modules first**

Run:

```bash
git mv src/holosoma_retargeting/src/mujoco_utils.py src/holosoma_retargeting/utils/mujoco_mesh.py
git mv src/holosoma_retargeting/src/viser_utils.py src/holosoma_retargeting/utils/viser_playback.py
```

Update imports:

```text
holosoma_retargeting.src.mujoco_utils -> holosoma_retargeting.utils.mujoco_mesh
holosoma_retargeting.src.viser_utils -> holosoma_retargeting.utils.viser_playback
```

**Step 3: Split `src/utils.py`**

Create `utils/motion.py`, `utils/object_geometry.py`, and `utils/transform.py`.

Move functions by responsibility using the recommended split above. Keep function names and behavior unchanged.

**Step 4: Update first-party imports**

Update CLI and retargeter modules:

- `cli/robot_retarget.py`
- `cli/parallel_robot_retarget.py`
- `cli/eval_retargeting.py`
- `cli/viser_player.py`
- `retargeter/interaction_mesh_retargeter.py`

Update tests to import from the new `utils.*` modules.

**Step 5: Delete old `src/utils.py`**

Run:

```bash
git rm src/holosoma_retargeting/src/utils.py
```

**Step 6: Run focused utility tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_package_paths.py tests/test_optitrack_grounding_preprocess.py tests/test_foot_sticking_contact_keys.py tests/test_utils_interaction_mesh.py tests/test_module_entrypoints.py
```

Expected: PASS.

**Step 7: Commit**

Run:

```bash
git add src tests
git commit -m "refactor: move shared helpers into utils modules"
```

---

### Task 5: Split the Interaction-Mesh Retargeter into Algorithm Modules

**Files:**
- Move: `src/holosoma_retargeting/retargeter/interaction_mesh_retargeter.py` -> `src/holosoma_retargeting/retargeter/retargeter.py`
- Create: `src/holosoma_retargeting/retargeter/solver.py`
- Create: `src/holosoma_retargeting/retargeter/constraint.py`
- Create: `src/holosoma_retargeting/retargeter/interaction_mesh.py`
- Delete: `src/holosoma_retargeting/utils/interaction_mesh.py`
- Modify: `src/holosoma_retargeting/retargeter/__init__.py`
- Modify: `src/holosoma_retargeting/utils/transform.py`
- Modify: `src/holosoma_retargeting/cli/robot_retarget.py`
- Modify: `src/holosoma_retargeting/cli/parallel_robot_retarget.py`
- Modify: `src/holosoma_retargeting/cli/eval_retargeting.py`
- Modify: `tests/test_utils_interaction_mesh.py` or replace it with retargeter/transform ownership tests
- Modify: `tests/test_retargeter_imports.py`
- Modify: `tests/test_module_entrypoints.py`

**Intent:** Align with the overview boundary: `retargeter/` owns interaction-mesh retargeting algorithms, while `utils/` owns only algorithm-independent helpers.

**Step 1: Rename the canonical retargeter module**

Run:

```bash
git mv src/holosoma_retargeting/retargeter/interaction_mesh_retargeter.py src/holosoma_retargeting/retargeter/retargeter.py
```

Update canonical imports from:

```python
from holosoma_retargeting.retargeter.interaction_mesh_retargeter import InteractionMeshRetargeter
```

to:

```python
from holosoma_retargeting.retargeter.retargeter import InteractionMeshRetargeter
```

Also update `retargeter/__init__.py` to re-export `InteractionMeshRetargeter` from `retargeter.py`.

**Step 2: Move generic transforms out of `utils/interaction_mesh.py`**

Move these functions to `utils/transform.py`:

```python
transform_points_world_to_local
transform_points_local_to_world
```

Use `utils/transform.py` for generic point and pose transforms. Do not create `retargeter/transform.py` in this phase.

**Step 3: Move interaction-mesh algorithms into `retargeter/interaction_mesh.py`**

Move these functions from `utils/interaction_mesh.py` to `retargeter/interaction_mesh.py`:

```python
create_interaction_mesh
get_adjacency_list
calculate_laplacian_coordinates
calculate_laplacian_matrix
```

Optionally add a small composition helper if it makes the frame loop clearer:

```python
def build_target_laplacian(vertices: np.ndarray) -> tuple[np.ndarray, np.ndarray, list[list[int]], np.ndarray]:
    ...
```

Delete `utils/interaction_mesh.py`; it should not remain as a legacy re-export or ambiguous utility module.

**Step 4: Extract solver construction into `retargeter/solver.py`**

Move the CVXPY problem construction and Clarabel solve from `InteractionMeshRetargeter.solve_single_iteration()` into a function such as:

```python
def solve_sqp_step(...):
    ...
    return q_star, cost
```

Keep this extraction conservative:

- preserve current objective terms;
- preserve current fallback that removes the SOC trust-region constraint on the first frame if needed;
- do not change solver tolerances or mathematical behavior;
- pass already-computed constraint data into the solver instead of making `solver.py` call MuJoCo.

**Step 5: Extract constraint data preparation into `retargeter/constraint.py`**

Move helper logic that prepares solver-ready constraints out of the main retargeter class:

```python
_build_transform_qdot_to_qvel_fast
_calc_contact_jacobian_from_point
_calc_manipulator_jacobians
_get_robot_link_positions
_world_to_body_frame
_compute_jacobian_for_contact_relative
_prefilter_pairs_with_mj_collision
_update_jacobians_and_phis_from_q
```

It is acceptable for `constraint.py` functions to receive the retargeter instance or an explicit state object during this phase. Prefer the minimal change that reduces `retargeter.py` size without introducing a new framework.

Do not split `constraint.py` into `kinematics.py` and `collision.py` during this phase.

**Step 6: Update imports**

In `retargeter/retargeter.py`, import mesh/Laplacian helpers from:

```python
from holosoma_retargeting.retargeter.interaction_mesh import ...
```

Import generic transforms from:

```python
from holosoma_retargeting.utils.transform import ...
```

In `cli/eval_retargeting.py`, import `transform_points_world_to_local` from `utils.transform`.

In first-party CLI modules, import `InteractionMeshRetargeter` from `holosoma_retargeting.retargeter` or `holosoma_retargeting.retargeter.retargeter`, not from the old `interaction_mesh_retargeter` module.

**Step 7: Update tests**

Replace legacy utility re-export tests with direct ownership tests:

```python
from holosoma_retargeting.retargeter import interaction_mesh
from holosoma_retargeting.utils.transform import transform_points_world_to_local
```

Keep the existing point roundtrip test under transform tests.

Update `tests/test_retargeter_imports.py` to assert the canonical import:

```python
from holosoma_retargeting.retargeter import InteractionMeshRetargeter
from holosoma_retargeting.retargeter.retargeter import InteractionMeshRetargeter as CanonicalRetargeter


def test_retargeter_imports_from_canonical_package() -> None:
    assert InteractionMeshRetargeter is CanonicalRetargeter
```

**Step 8: Run focused tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_utils_interaction_mesh.py tests/test_retargeter_imports.py tests/test_module_entrypoints.py
```

Expected: PASS after imports are updated.

**Step 9: Commit**

Run:

```bash
git add src tests
git commit -m "refactor: split interaction mesh retargeter modules"
```

---

### Task 6: Remove `holosoma_retargeting.src` Compatibility Package

**Files:**
- Delete: `src/holosoma_retargeting/src/__init__.py`
- Delete: `src/holosoma_retargeting/src/interaction_mesh_retargeter.py`
- Modify: `tests/test_retargeter_imports.py`
- Modify: `tests/test_module_entrypoints.py`
- Modify: `tests/test_final_package_layout.py`

**Intent:** Remove the last legacy package-internal `src/` namespace.

**Step 1: Remove compatibility shim**

Run:

```bash
git rm src/holosoma_retargeting/src/interaction_mesh_retargeter.py
git rm src/holosoma_retargeting/src/__init__.py
```

Remove ignored `__pycache__` if it prevents directory removal, then:

```bash
rmdir src/holosoma_retargeting/src
```

**Step 2: Update tests**

In `tests/test_retargeter_imports.py`, remove the legacy import assertion and assert the canonical import only:

```python
from holosoma_retargeting.retargeter.retargeter import InteractionMeshRetargeter


def test_retargeter_imports_from_canonical_package() -> None:
    assert InteractionMeshRetargeter.__name__ == "InteractionMeshRetargeter"
```

In `tests/test_module_entrypoints.py`, remove reset entries for `holosoma_retargeting.src.interaction_mesh_retargeter` and add it to the negative import list if not already covered by `tests/test_final_package_layout.py`.

**Step 3: Run tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_retargeter_imports.py tests/test_module_entrypoints.py tests/test_final_package_layout.py
```

Expected: PASS.

**Step 4: Commit**

Run:

```bash
git add src tests
git commit -m "refactor: remove legacy src namespace"
```

---

### Task 7: Update Documentation to Match Final Overview Layout

**Files:**
- Modify: `README.md`
- Modify: `docs/usage.md`
- Modify: `docs/add-robot-type.md`
- Modify: `docs/add-motion-format.md`
- Modify: `docs/adam-pro-robot-only-summary.md`
- Modify: `docs/plans/2026-04-24-omniretarget-refactor-overview.md`

**Intent:** Make docs describe the actual final package layout and import paths.

**Step 1: Search for stale architecture references**

Run:

```bash
rg -n "config_types|config_values|holosoma_retargeting/src|holosoma_retargeting\.src|utils/interaction_mesh|src/utils|src/mujoco_utils|src/viser_utils" README.md docs/*.md
```

Expected before edits: matches in user-facing docs that must be updated.

**Step 2: Update docs**

Use canonical paths:

```text
configs/
profiles/
retargeter/
utils/
```

Do not update historical `docs/plans/2026-04-22-*` files unless they are presented as current instructions.

**Step 3: Run doc grep**

Run:

```bash
rg -n "config_types|config_values|holosoma_retargeting/src|holosoma_retargeting\.src|utils/interaction_mesh|src/utils|src/mujoco_utils|src/viser_utils" README.md docs/*.md
```

Expected: no matches, except if a doc explicitly states that these paths were removed.

**Step 4: Commit**

Run:

```bash
git add README.md docs
git commit -m "docs: align documentation with final overview layout"
```

---

### Task 8: Final Verification and Push

**Files:**
- Review: entire repository

**Intent:** Prove that the final overview architecture is complete.

**Step 1: Verify final directory layout**

Run:

```bash
find src/holosoma_retargeting -maxdepth 1 -type d | sort
```

Expected directories:

```text
src/holosoma_retargeting
src/holosoma_retargeting/cli
src/holosoma_retargeting/configs
src/holosoma_retargeting/demo_data
src/holosoma_retargeting/models
src/holosoma_retargeting/profiles
src/holosoma_retargeting/retargeter
src/holosoma_retargeting/utils
```

`__pycache__` may appear locally but must be ignored and must not affect tests.

**Step 2: Verify no legacy imports remain**

Run:

```bash
rg -n "holosoma_retargeting\.(config_types|config_values|src)" src tests README.md docs/*.md pyproject.toml
```

Expected: no output.

**Step 3: Verify scripts and tests**

Run:

```bash
bash -n scripts/*.sh scripts/data_process/*.sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests
git diff --check HEAD
git status --short
```

Expected:

- shell syntax check passes;
- full test suite passes;
- no whitespace errors;
- working tree only contains intended staged changes before final commit.

**Step 4: Commit final verification cleanup if needed**

If final minor cleanup changes were required:

```bash
git add .
git commit -m "test: enforce final overview package layout"
```

**Step 5: Push**

Run:

```bash
git push
```

Expected: branch updates on `origin/refactor-next`.
