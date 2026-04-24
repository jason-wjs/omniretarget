# OmniRetarget Final Overview Cleanup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove the remaining legacy package directories so `src/holosoma_retargeting/` matches the final overview layout exactly.

**Architecture:** Move typed dataclass configuration schemas from `config_types/` into `configs/`, collapse `config_values/`, and move the remaining package-internal `src/` utilities into responsibility-based modules. Keep retargeting-specific interaction-mesh helpers under `retargeter/`, keep generic support under `utils/`, and remove legacy import paths after all first-party users migrate.

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
- Move: `src/holosoma_retargeting/src/mujoco_utils.py` -> `src/holosoma_retargeting/utils/mujoco.py`
- Move: `src/holosoma_retargeting/src/viser_utils.py` -> `src/holosoma_retargeting/utils/visualization.py`
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
  transform_y_up_to_z_up
  estimate_human_orientation

utils/mesh.py
  load_object_data
  weighted_surface_sampling
  weighted_surface_sampling_by_face_normal
  create_top_surface_weight_function
  scale_points_in_object_axes_frame

utils/object_assets.py
  create_scaled_object_mesh_and_urdf
  create_scaled_multi_boxes_urdf
  create_scaled_multi_boxes_xml
  create_new_scene_xml_file

utils/geometry.py
  transform_from_human_to_world
  transform_points_world_to_local
  transform_points_local_to_world

utils/mujoco.py
  _mesh_local_vf
  _to_world
  _world_mesh_from_geom

utils/visualization.py
  create_motion_control_sliders
```

**Step 1: Add import-focused tests for new utility modules**

Create or extend tests so first-party imports use:

```python
from holosoma_retargeting.utils.motion import preprocess_motion_data
from holosoma_retargeting.utils.motion import extract_foot_sticking_sequence_velocity
from holosoma_retargeting.utils.motion import calculate_scale_factor
from holosoma_retargeting.utils.geometry import transform_points_world_to_local
from holosoma_retargeting.utils.mujoco import _world_mesh_from_geom
from holosoma_retargeting.utils.visualization import create_motion_control_sliders
```

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_package_paths.py tests/test_optitrack_grounding_preprocess.py tests/test_foot_sticking_contact_keys.py
```

Expected: FAIL until modules exist.

**Step 2: Move small modules first**

Run:

```bash
git mv src/holosoma_retargeting/src/mujoco_utils.py src/holosoma_retargeting/utils/mujoco.py
git mv src/holosoma_retargeting/src/viser_utils.py src/holosoma_retargeting/utils/visualization.py
```

Update imports:

```text
holosoma_retargeting.src.mujoco_utils -> holosoma_retargeting.utils.mujoco
holosoma_retargeting.src.viser_utils -> holosoma_retargeting.utils.visualization
```

**Step 3: Split `src/utils.py`**

Create `utils/motion.py`, `utils/mesh.py`, `utils/object_assets.py`, and `utils/geometry.py`.

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

### Task 5: Put Interaction-Mesh Algorithm Helpers under `retargeter/`

**Files:**
- Move or split: `src/holosoma_retargeting/utils/interaction_mesh.py`
- Create: `src/holosoma_retargeting/retargeter/interaction_mesh.py`
- Modify: `src/holosoma_retargeting/retargeter/interaction_mesh_retargeter.py`
- Modify: `src/holosoma_retargeting/utils/geometry.py`
- Modify: `tests/test_utils_interaction_mesh.py` or replace it with retargeter-specific tests

**Intent:** Align with the overview boundary: interaction-mesh retargeting internals belong to `retargeter/`, while generic geometry belongs in `utils/`.

**Step 1: Split generic transforms from algorithm helpers**

Move these functions to `utils/geometry.py`:

```python
transform_points_world_to_local
transform_points_local_to_world
```

Move these functions to `retargeter/interaction_mesh.py`:

```python
create_interaction_mesh
get_adjacency_list
calculate_laplacian_coordinates
calculate_laplacian_matrix
```

Delete `utils/interaction_mesh.py` unless it still has a genuine generic responsibility. Prefer deleting it to avoid ambiguous ownership.

**Step 2: Update imports**

In `retargeter/interaction_mesh_retargeter.py`, import mesh/Laplacian helpers from:

```python
from holosoma_retargeting.retargeter.interaction_mesh import ...
```

Import transforms from:

```python
from holosoma_retargeting.utils.geometry import ...
```

In `cli/eval_retargeting.py`, import `transform_points_world_to_local` from `utils.geometry`.

**Step 3: Update tests**

Replace legacy utility reexport tests with direct ownership tests:

```python
from holosoma_retargeting.retargeter import interaction_mesh
from holosoma_retargeting.utils.geometry import transform_points_world_to_local
```

Keep the existing roundtrip transform test under geometry tests.

**Step 4: Run focused tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_utils_interaction_mesh.py tests/test_retargeter_imports.py tests/test_module_entrypoints.py
```

Expected: PASS after imports are updated.

**Step 5: Commit**

Run:

```bash
git add src tests
git commit -m "refactor: keep interaction mesh helpers in retargeter"
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
from holosoma_retargeting.retargeter.interaction_mesh_retargeter import InteractionMeshRetargeter


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

