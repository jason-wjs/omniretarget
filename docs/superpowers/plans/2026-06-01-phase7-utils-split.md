# Phase 7 Utils Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split `src/omniretarget/src/utils.py` into focused modules under existing packages while preserving legacy imports and all current workflow behavior.

**Architecture:** Move implementation into four deeper modules under existing `retargeting` and `solver` packages, then keep `omniretarget.src.utils` as an explicit compatibility re-export layer. Internal production callers migrate to the deeper modules when the mapping is direct, while tests may keep legacy imports when they intentionally verify compatibility.

**Tech Stack:** Python, NumPy, SciPy, Trimesh, SMPL-X, Jinja2, pytest, uv, git worktrees.

---

## Safety Rules

- Work only in `/home/humanoid/Projects/Junsong_WU/learning/locomotion/RETARGET/omniretarget-arch-refactor` on branch `arch/phase7-utils-split`.
- Do not create a new worktree.
- Do not create new top-level packages under `src/omniretarget/`.
- Add only these modules:
  - `src/omniretarget/solver/laplacian.py`
  - `src/omniretarget/retargeting/spatial.py`
  - `src/omniretarget/retargeting/motion_data.py`
  - `src/omniretarget/retargeting/object_assets.py`
- Do not delete `src/omniretarget/src/utils.py`.
- Do not change CLI arguments, output schemas, asset paths, PARC height-origin behavior, object scaling behavior, or solver math.
- Stop and reassess if passing tests requires changing behavior outside import locations and moved implementations.

## Target File Structure

- Create `src/omniretarget/solver/laplacian.py`: owns interaction-mesh tetrahedral and Laplacian math.
- Create `src/omniretarget/retargeting/spatial.py`: owns shared world/local/human coordinate transforms.
- Create `src/omniretarget/retargeting/motion_data.py`: owns motion loading, scale factor, preprocessing, contact extraction, SMPL motion loading, and human orientation helpers.
- Create `src/omniretarget/retargeting/object_assets.py`: owns mesh sampling, surface weighting, scaled URDF/XML generation, and object asset helpers.
- Modify `src/omniretarget/src/utils.py`: explicit re-export compatibility layer only.
- Modify production import callers:
  - `src/omniretarget/solver/interaction_mesh.py`
  - `src/omniretarget/solver/optimizer.py`
  - `src/omniretarget/retargeting/initialization.py`
  - `src/omniretarget/retargeting/motion_source.py`
  - `src/omniretarget/retargeting/preprocessing.py`
  - `src/omniretarget/retargeting/object_setup.py`
  - `src/omniretarget/evaluation/eval_retargeting.py`
- Add `tests/test_utils_split_facades.py`: verifies new modules expose equivalent behavior through new and legacy import paths.
- Modify `tests/test_repo_doc_boundaries.py`: add a repository boundary test that prevents production modules from importing `omniretarget.src.utils`.

## Task 1: Baseline And Plan Commit

**Files:**
- Create: `docs/superpowers/plans/2026-06-01-phase7-utils-split.md`
- Read: `docs/superpowers/specs/2026-06-01-phase7-utils-split-design.md`

- [ ] **Step 1: Verify worktree branch**

Run:

```bash
git status --short --branch
git branch --show-current
```

Expected:

```text
## arch/phase7-utils-split...origin/arch/phase7-utils-split
arch/phase7-utils-split
```

- [ ] **Step 2: Run baseline checks**

Run:

```bash
git diff --check
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest
```

Expected: `git diff --check` exits 0 and pytest reports all existing tests passing.

- [ ] **Step 3: Commit the implementation plan**

Run:

```bash
git add docs/superpowers/plans/2026-06-01-phase7-utils-split.md
git commit -m "docs: add phase7 utils split implementation plan"
```

Expected: one documentation-only commit.

## Task 2: Laplacian Slice

**Files:**
- Create: `src/omniretarget/solver/laplacian.py`
- Modify: `src/omniretarget/src/utils.py`
- Modify: `src/omniretarget/solver/interaction_mesh.py`
- Modify: `src/omniretarget/solver/optimizer.py`
- Test: `tests/test_utils_split_facades.py`
- Existing focused tests: `tests/test_solver_facade.py`, `tests/test_mujoco_query_seam.py`

- [ ] **Step 1: Write the failing Laplacian compatibility tests**

Add this first slice to `tests/test_utils_split_facades.py`:

```python
from __future__ import annotations

import numpy as np


def test_laplacian_module_matches_legacy_utils():
    from omniretarget.solver import laplacian
    from omniretarget.src import utils as legacy_utils

    vertices = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    tetrahedra = np.array([[0, 1, 2, 3]])

    assert laplacian.create_interaction_mesh(vertices)[1].shape[1] == 4

    adj_list = laplacian.get_adjacency_list(tetrahedra, len(vertices))
    expected_adj_list = legacy_utils.get_adjacency_list(tetrahedra, len(vertices))
    assert [sorted(values) for values in adj_list] == [sorted(values) for values in expected_adj_list]

    np.testing.assert_allclose(
        laplacian.calculate_laplacian_coordinates(vertices, adj_list),
        legacy_utils.calculate_laplacian_coordinates(vertices, expected_adj_list),
    )
    np.testing.assert_allclose(
        laplacian.calculate_laplacian_matrix(vertices, adj_list),
        legacy_utils.calculate_laplacian_matrix(vertices, expected_adj_list),
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_utils_split_facades.py::test_laplacian_module_matches_legacy_utils -q
```

Expected: FAIL because `omniretarget.solver.laplacian` does not exist yet.

- [ ] **Step 3: Move Laplacian implementation**

Create `src/omniretarget/solver/laplacian.py` with the implementation currently in `utils.py` for:

```python
create_interaction_mesh
get_adjacency_list
calculate_laplacian_coordinates
calculate_laplacian_matrix
```

The module imports must be:

```python
from __future__ import annotations

import numpy as np
from scipy.spatial import Delaunay  # type: ignore[import-untyped]
```

- [ ] **Step 4: Update legacy re-exports and direct solver imports**

In `src/omniretarget/src/utils.py`, import these four functions from `omniretarget.solver.laplacian`.

In `src/omniretarget/solver/interaction_mesh.py`, replace Laplacian imports with:

```python
from omniretarget.solver.laplacian import (
    calculate_laplacian_coordinates,
    create_interaction_mesh,
    get_adjacency_list,
)
```

In `src/omniretarget/solver/optimizer.py`, replace the legacy import with:

```python
from omniretarget.solver.laplacian import calculate_laplacian_matrix
```

- [ ] **Step 5: Run focused verification**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_utils_split_facades.py::test_laplacian_module_matches_legacy_utils tests/test_solver_facade.py tests/test_mujoco_query_seam.py -q
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add src/omniretarget/solver/laplacian.py src/omniretarget/src/utils.py src/omniretarget/solver/interaction_mesh.py src/omniretarget/solver/optimizer.py tests/test_utils_split_facades.py
git commit -m "refactor: move laplacian utilities into solver module"
```

## Task 3: Spatial Slice

**Files:**
- Create: `src/omniretarget/retargeting/spatial.py`
- Modify: `src/omniretarget/src/utils.py`
- Modify: `src/omniretarget/solver/interaction_mesh.py`
- Modify: `src/omniretarget/retargeting/initialization.py`
- Test: `tests/test_utils_split_facades.py`
- Existing focused tests: `tests/test_retargeting_initialization.py`, `tests/test_solver_facade.py`, `tests/test_parc_process.py`

- [ ] **Step 1: Write the failing spatial compatibility tests**

Append this test to `tests/test_utils_split_facades.py`:

```python
def test_spatial_module_matches_legacy_utils_round_trip():
    from omniretarget.retargeting import spatial
    from omniretarget.src import utils as legacy_utils

    quat = np.array([1.0, 0.0, 0.0, 0.0])
    trans = np.array([0.25, -0.5, 1.5])
    points_local = np.array([[0.0, 0.0, 0.0], [1.0, 2.0, 3.0]])

    world_new = spatial.transform_points_local_to_world(quat, trans, points_local)
    world_legacy = legacy_utils.transform_points_local_to_world(quat, trans, points_local)
    np.testing.assert_allclose(world_new, world_legacy)

    local_new = spatial.transform_points_world_to_local(quat, trans, world_new)
    local_legacy = legacy_utils.transform_points_world_to_local(quat, trans, world_new)
    np.testing.assert_allclose(local_new, local_legacy)
    np.testing.assert_allclose(local_new, points_local)


def test_human_to_world_transform_matches_legacy_utils():
    from omniretarget.retargeting import spatial
    from omniretarget.src import utils as legacy_utils

    human_initial_root = np.array([0.0, 0.0, 0.0])
    object_initial_pose = np.array([0.0, 0.0, 0.0, 1.0, 2.0, 0.0, 0.5])
    local_translation = np.array([0.2, 0.1, 0.0])

    world_new, quat_new = spatial.transform_from_human_to_world(
        human_initial_root,
        object_initial_pose,
        local_translation,
    )
    world_legacy, quat_legacy = legacy_utils.transform_from_human_to_world(
        human_initial_root,
        object_initial_pose,
        local_translation,
    )

    np.testing.assert_allclose(world_new, world_legacy)
    np.testing.assert_allclose(quat_new, quat_legacy)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_utils_split_facades.py::test_spatial_module_matches_legacy_utils_round_trip tests/test_utils_split_facades.py::test_human_to_world_transform_matches_legacy_utils -q
```

Expected: FAIL because `omniretarget.retargeting.spatial` does not exist yet.

- [ ] **Step 3: Move spatial implementation**

Create `src/omniretarget/retargeting/spatial.py` with the implementation currently in `utils.py` for:

```python
augment_object_poses
transform_from_human_to_world
transform_points_world_to_local
transform_points_local_to_world
```

The module imports must be:

```python
from __future__ import annotations

import numpy as np
import trimesh
from scipy.spatial.transform import Rotation as R  # type: ignore[import-untyped]  # noqa: N817
```

- [ ] **Step 4: Update legacy re-exports and direct spatial imports**

In `src/omniretarget/src/utils.py`, import these four functions from `omniretarget.retargeting.spatial`.

In `src/omniretarget/solver/interaction_mesh.py`, import point transforms from:

```python
from omniretarget.retargeting.spatial import (
    transform_points_local_to_world,
    transform_points_world_to_local,
)
```

In `src/omniretarget/retargeting/initialization.py`, import spatial functions from:

```python
from omniretarget.retargeting.spatial import augment_object_poses, transform_from_human_to_world
```

- [ ] **Step 5: Run focused verification**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_utils_split_facades.py::test_spatial_module_matches_legacy_utils_round_trip tests/test_utils_split_facades.py::test_human_to_world_transform_matches_legacy_utils tests/test_retargeting_initialization.py tests/test_solver_facade.py tests/test_parc_process.py -q
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add src/omniretarget/retargeting/spatial.py src/omniretarget/src/utils.py src/omniretarget/solver/interaction_mesh.py src/omniretarget/retargeting/initialization.py tests/test_utils_split_facades.py
git commit -m "refactor: move spatial utilities into retargeting module"
```

## Task 4: Motion Data Slice

**Files:**
- Create: `src/omniretarget/retargeting/motion_data.py`
- Modify: `src/omniretarget/src/utils.py`
- Modify: `src/omniretarget/retargeting/motion_source.py`
- Modify: `src/omniretarget/retargeting/preprocessing.py`
- Modify: `src/omniretarget/retargeting/initialization.py`
- Modify: `src/omniretarget/evaluation/eval_retargeting.py`
- Test: `tests/test_utils_split_facades.py`
- Existing focused tests: `tests/test_retargeting_motion_source.py`, `tests/test_retargeting_preprocessing.py`, `tests/test_retargeting_initialization.py`, `tests/test_foot_sticking_contact_keys.py`, `tests/test_optitrack_grounding_preprocess.py`, `tests/test_package_paths.py`

- [ ] **Step 1: Write the failing motion-data compatibility tests**

Append these tests to `tests/test_utils_split_facades.py`:

```python
def test_motion_data_module_matches_legacy_y_up_transform():
    from omniretarget.retargeting import motion_data
    from omniretarget.src import utils as legacy_utils

    points = np.array(
        [
            [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
            [[-1.0, -2.0, -3.0], [7.0, 8.0, 9.0]],
        ]
    )

    np.testing.assert_allclose(
        motion_data.transform_y_up_to_z_up(points),
        legacy_utils.transform_y_up_to_z_up(points),
    )


def test_motion_data_module_matches_legacy_velocity_contacts():
    from omniretarget.retargeting import motion_data
    from omniretarget.src import utils as legacy_utils

    joints = np.array(
        [
            [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
            [[0.001, 0.0, 0.0], [1.5, 0.0, 0.0]],
            [[0.002, 0.0, 0.0], [2.0, 0.0, 0.0]],
        ]
    )
    demo_joints = ["left_toe", "right_toe"]
    foot_names = ["left_toe", "right_toe"]

    assert motion_data.extract_foot_sticking_sequence_velocity(joints, demo_joints, foot_names) == (
        legacy_utils.extract_foot_sticking_sequence_velocity(joints, demo_joints, foot_names)
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_utils_split_facades.py::test_motion_data_module_matches_legacy_y_up_transform tests/test_utils_split_facades.py::test_motion_data_module_matches_legacy_velocity_contacts -q
```

Expected: FAIL because `omniretarget.retargeting.motion_data` does not exist yet.

- [ ] **Step 3: Move motion-data implementation**

Create `src/omniretarget/retargeting/motion_data.py` with the implementation currently in `utils.py` for:

```python
load_intermimic_data
calculate_scale_factor
preprocess_motion_data
extract_object_first_moving_frame
extract_foot_sticking_sequence
extract_foot_sticking_sequence_velocity
transform_y_up_to_z_up
estimate_human_orientation
load_smpl_motion
find_standing_pose
```

The module imports must be:

```python
from __future__ import annotations

import pickle

import numpy as np
import smplx  # type: ignore[import-not-found]
import torch
from scipy.spatial.transform import Rotation as R  # type: ignore[import-untyped]  # noqa: N817

from omniretarget.path_utils import package_path
```

- [ ] **Step 4: Update legacy re-exports and direct motion-data imports**

In `src/omniretarget/src/utils.py`, import the ten moved functions from `omniretarget.retargeting.motion_data`.

In `src/omniretarget/retargeting/motion_source.py`, import:

```python
from omniretarget.retargeting.motion_data import (
    calculate_scale_factor,
    load_intermimic_data,
    transform_y_up_to_z_up,
)
```

In `src/omniretarget/retargeting/preprocessing.py`, import:

```python
from omniretarget.retargeting.motion_data import (
    extract_foot_sticking_sequence_velocity,
    preprocess_motion_data,
)
```

In `src/omniretarget/retargeting/initialization.py`, keep spatial imports separate and import motion helpers from:

```python
from omniretarget.retargeting.motion_data import estimate_human_orientation, extract_object_first_moving_frame
```

In `src/omniretarget/evaluation/eval_retargeting.py`, import motion helpers from `omniretarget.retargeting.motion_data` and leave object/spatial helpers for later slices if they have not moved yet.

- [ ] **Step 5: Run focused verification**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_utils_split_facades.py::test_motion_data_module_matches_legacy_y_up_transform tests/test_utils_split_facades.py::test_motion_data_module_matches_legacy_velocity_contacts tests/test_retargeting_motion_source.py tests/test_retargeting_preprocessing.py tests/test_retargeting_initialization.py tests/test_foot_sticking_contact_keys.py tests/test_optitrack_grounding_preprocess.py tests/test_package_paths.py -q
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add src/omniretarget/retargeting/motion_data.py src/omniretarget/src/utils.py src/omniretarget/retargeting/motion_source.py src/omniretarget/retargeting/preprocessing.py src/omniretarget/retargeting/initialization.py src/omniretarget/evaluation/eval_retargeting.py tests/test_utils_split_facades.py
git commit -m "refactor: move motion data utilities into retargeting module"
```

## Task 5: Object Assets Slice

**Files:**
- Create: `src/omniretarget/retargeting/object_assets.py`
- Modify: `src/omniretarget/src/utils.py`
- Modify: `src/omniretarget/retargeting/object_setup.py`
- Modify: `src/omniretarget/evaluation/eval_retargeting.py`
- Test: `tests/test_utils_split_facades.py`
- Existing focused tests: `tests/test_retargeting_object_setup.py`, `tests/test_parc_process.py`, `tests/test_convert_data_format_parc_mj.py`, `tests/test_mujoco_query_seam.py`

- [ ] **Step 1: Write the failing object-assets compatibility tests**

Append these tests to `tests/test_utils_split_facades.py`:

```python
def test_object_assets_module_matches_legacy_top_surface_weights():
    from omniretarget.retargeting import object_assets
    from omniretarget.src import utils as legacy_utils

    new_weight = object_assets.create_top_surface_weight_function(angle_threshold=30)
    legacy_weight = legacy_utils.create_top_surface_weight_function(angle_threshold=30)

    top_normal = np.array([0.0, 0.0, 1.0])
    side_normal = np.array([1.0, 0.0, 0.0])
    down_normal = np.array([0.0, 0.0, -1.0])
    high_center = np.array([0.0, 0.0, 1.0])
    low_center = np.array([0.0, 0.0, 0.1])

    assert new_weight(top_normal, high_center) == legacy_weight(top_normal, high_center)
    assert new_weight(top_normal, low_center) == legacy_weight(top_normal, low_center)
    assert new_weight(side_normal, low_center) == legacy_weight(side_normal, low_center)
    assert new_weight(down_normal, low_center) == legacy_weight(down_normal, low_center)


def test_object_assets_module_matches_legacy_axis_scaling():
    from omniretarget.retargeting import object_assets
    from omniretarget.src import utils as legacy_utils

    points = np.array([[1.0, 2.0, 3.0], [-1.0, -2.0, -3.0]])
    scale_factors = np.array([2.0, 0.5, 1.5])
    object_axes = np.eye(3)

    np.testing.assert_allclose(
        object_assets.scale_points_in_object_axes_frame(points, scale_factors, object_axes),
        legacy_utils.scale_points_in_object_axes_frame(points, scale_factors, object_axes),
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_utils_split_facades.py::test_object_assets_module_matches_legacy_top_surface_weights tests/test_utils_split_facades.py::test_object_assets_module_matches_legacy_axis_scaling -q
```

Expected: FAIL because `omniretarget.retargeting.object_assets` does not exist yet.

- [ ] **Step 3: Move object-assets implementation**

Create `src/omniretarget/retargeting/object_assets.py` with the implementation currently in `utils.py` for:

```python
load_object_data
weighted_surface_sampling
weighted_surface_sampling_by_face_normal
create_top_surface_weight_function
scale_points_in_object_axes_frame
create_scaled_object_mesh_and_urdf
create_scaled_multi_boxes_urdf
create_scaled_multi_boxes_xml
create_new_scene_xml_file
```

The module imports must be:

```python
from __future__ import annotations

import os
import re
from pathlib import Path

import numpy as np
import trimesh
from jinja2 import Template
```

- [ ] **Step 4: Update legacy re-exports and direct object-assets imports**

In `src/omniretarget/src/utils.py`, import the nine moved functions from `omniretarget.retargeting.object_assets`.

In `src/omniretarget/retargeting/object_setup.py`, import object helpers from:

```python
from omniretarget.retargeting.object_assets import (
    create_new_scene_xml_file,
    create_scaled_multi_boxes_urdf,
    create_scaled_multi_boxes_xml,
    load_object_data,
)
```

In `src/omniretarget/evaluation/eval_retargeting.py`, import object helpers from `omniretarget.retargeting.object_assets`.

- [ ] **Step 5: Run focused verification**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_utils_split_facades.py::test_object_assets_module_matches_legacy_top_surface_weights tests/test_utils_split_facades.py::test_object_assets_module_matches_legacy_axis_scaling tests/test_retargeting_object_setup.py tests/test_parc_process.py tests/test_convert_data_format_parc_mj.py tests/test_mujoco_query_seam.py -q
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add src/omniretarget/retargeting/object_assets.py src/omniretarget/src/utils.py src/omniretarget/retargeting/object_setup.py src/omniretarget/evaluation/eval_retargeting.py tests/test_utils_split_facades.py
git commit -m "refactor: move object asset utilities into retargeting module"
```

## Task 6: Compatibility Layer And Import Boundary Cleanup

**Files:**
- Modify: `src/omniretarget/src/utils.py`
- Modify: `tests/test_repo_doc_boundaries.py`
- Test: `tests/test_utils_split_facades.py`

- [ ] **Step 1: Make `src.utils` an explicit re-export layer**

Ensure `src/omniretarget/src/utils.py` contains no moved implementation and has this shape:

```python
"""Compatibility re-exports for legacy utility imports."""

from __future__ import annotations

from omniretarget.retargeting.motion_data import (...)
from omniretarget.retargeting.object_assets import (...)
from omniretarget.retargeting.spatial import (...)
from omniretarget.solver.laplacian import (...)

__all__ = [
    ...
]
```

The `__all__` list must include every migrated public function:

```python
[
    "augment_object_poses",
    "calculate_laplacian_coordinates",
    "calculate_laplacian_matrix",
    "calculate_scale_factor",
    "create_interaction_mesh",
    "create_new_scene_xml_file",
    "create_scaled_multi_boxes_urdf",
    "create_scaled_multi_boxes_xml",
    "create_scaled_object_mesh_and_urdf",
    "create_top_surface_weight_function",
    "estimate_human_orientation",
    "extract_foot_sticking_sequence",
    "extract_foot_sticking_sequence_velocity",
    "extract_object_first_moving_frame",
    "find_standing_pose",
    "get_adjacency_list",
    "load_intermimic_data",
    "load_object_data",
    "load_smpl_motion",
    "preprocess_motion_data",
    "scale_points_in_object_axes_frame",
    "transform_from_human_to_world",
    "transform_points_local_to_world",
    "transform_points_world_to_local",
    "transform_y_up_to_z_up",
    "weighted_surface_sampling",
    "weighted_surface_sampling_by_face_normal",
]
```

- [ ] **Step 2: Add legacy re-export coverage test**

Append this test to `tests/test_utils_split_facades.py`:

```python
def test_legacy_utils_reexports_all_migrated_functions():
    from omniretarget.src import utils

    expected_names = {
        "augment_object_poses",
        "calculate_laplacian_coordinates",
        "calculate_laplacian_matrix",
        "calculate_scale_factor",
        "create_interaction_mesh",
        "create_new_scene_xml_file",
        "create_scaled_multi_boxes_urdf",
        "create_scaled_multi_boxes_xml",
        "create_scaled_object_mesh_and_urdf",
        "create_top_surface_weight_function",
        "estimate_human_orientation",
        "extract_foot_sticking_sequence",
        "extract_foot_sticking_sequence_velocity",
        "extract_object_first_moving_frame",
        "find_standing_pose",
        "get_adjacency_list",
        "load_intermimic_data",
        "load_object_data",
        "load_smpl_motion",
        "preprocess_motion_data",
        "scale_points_in_object_axes_frame",
        "transform_from_human_to_world",
        "transform_points_local_to_world",
        "transform_points_world_to_local",
        "transform_y_up_to_z_up",
        "weighted_surface_sampling",
        "weighted_surface_sampling_by_face_normal",
    }

    assert set(utils.__all__) == expected_names
    for name in expected_names:
        assert callable(getattr(utils, name))
```

- [ ] **Step 3: Add production import boundary test**

Add a test to `tests/test_repo_doc_boundaries.py` that scans production files under `src/omniretarget` and fails if any file other than `src/omniretarget/src/utils.py` imports `omniretarget.src.utils`.

Use this allowlist:

```python
allowed_paths = {
    Path("src/omniretarget/src/utils.py"),
}
```

The test must not scan `tests/` because tests are allowed to verify legacy compatibility.

- [ ] **Step 4: Run boundary and compatibility verification**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_utils_split_facades.py tests/test_repo_doc_boundaries.py -q
rg "omniretarget\\.src\\.utils" src/omniretarget
```

Expected: pytest passes. The `rg` command should return only `src/omniretarget/src/utils.py` if it matches that file's docstring or comments, or no production legacy import matches.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/omniretarget/src/utils.py tests/test_utils_split_facades.py tests/test_repo_doc_boundaries.py
git commit -m "test: enforce utils split compatibility boundaries"
```

## Task 7: Full Verification And Branch Push

**Files:**
- No new source files expected.

- [ ] **Step 1: Run formatting diff check**

Run:

```bash
git diff --check
```

Expected: exits 0.

- [ ] **Step 2: Run full test suite**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest
```

Expected: all tests pass, with the same skip profile as baseline unless a newly added test changes only the pass count.

- [ ] **Step 3: Run CLI help smokes**

Run:

```bash
uv run python src/omniretarget/examples/robot_retarget.py --help
uv run python src/omniretarget/examples/parc_process.py --help
```

Expected: both commands exit 0 and print help text without import errors.

- [ ] **Step 4: Inspect import state and diff**

Run:

```bash
rg "omniretarget\\.src\\.utils" src/omniretarget
git diff --stat origin/main...HEAD
git status --short --branch
```

Expected: production code has no direct legacy utility imports outside `src/utils.py`; branch is clean after all commits.

- [ ] **Step 5: Push branch**

Run:

```bash
git push
```

Expected: `origin/arch/phase7-utils-split` contains all Phase 7 commits.

## Task 8: Safe Merge Back To Main

**Files:**
- Main worktree: `/home/humanoid/Projects/Junsong_WU/learning/locomotion/RETARGET/omniretarget`

- [ ] **Step 1: Verify main worktree state before merge**

Run from the main worktree:

```bash
git status --short --branch
git branch --show-current
```

Expected: on `main`. If unrelated untracked files exist, leave them untouched and report them.

- [ ] **Step 2: Update main**

Run from the main worktree:

```bash
git pull --ff-only origin main
```

Expected: main is up to date or fast-forwarded.

- [ ] **Step 3: Merge Phase 7 branch**

Run from the main worktree:

```bash
git merge --no-ff arch/phase7-utils-split
```

Expected: merge succeeds without conflicts.

- [ ] **Step 4: Verify merged main**

Run from the main worktree:

```bash
git diff --check
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest
uv run python src/omniretarget/examples/robot_retarget.py --help
uv run python src/omniretarget/examples/parc_process.py --help
```

Expected: diff check exits 0, full tests pass, and both CLI help smokes exit 0.

- [ ] **Step 5: Push main**

Run from the main worktree:

```bash
git push origin main
```

Expected: `origin/main` contains the Phase 7 merge commit.

- [ ] **Step 6: Stop and report**

Report:

- Phase 7 branch name and merge commit.
- New modules created.
- Compatibility status for `omniretarget.src.utils`.
- Verification commands and exact pass/smoke results.
- Any untouched unrelated files in the main worktree.

Do not start Phase 8 or any cleanup beyond the requested merge.
