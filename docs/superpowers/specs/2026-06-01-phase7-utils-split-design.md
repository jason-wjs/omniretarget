# Phase 7 Utils Split Design

Date: 2026-06-01

Branch: `arch/phase7-utils-split`

Worktree:

```text
/home/humanoid/Projects/Junsong_WU/learning/locomotion/RETARGET/omniretarget-arch-refactor
```

## Intent

Phase 7 splits `src/omniretarget/src/utils.py` without expanding the top-level
package structure. The goal is to reduce the remaining legacy implementation
surface while preserving all public and workflow-facing imports.

This is a compatibility-first refactor. It must not change CLI arguments,
output schemas, asset paths, PARC height-origin behavior, object scaling
behavior, or solver behavior.

## Scope Constraints

- Do not create a new worktree.
- Do not create new top-level packages under `src/omniretarget/`.
- Add at most four modules under existing packages.
- Do not delete `omniretarget.src.utils`.
- Do not rename public CLI files.
- Do not mix this refactor with solver, PARC, runtime, evaluation, or CLI
  behavior changes.
- Treat `src/omniretarget/src/utils.py` as a compatibility interface after the
  split.

## Current State

`src/omniretarget/src/utils.py` is 839 lines and exposes 25 top-level functions.
Its callers are concentrated in these areas:

```text
src/omniretarget/retargeting/preprocessing.py
src/omniretarget/retargeting/motion_source.py
src/omniretarget/retargeting/object_setup.py
src/omniretarget/retargeting/initialization.py
src/omniretarget/evaluation/eval_retargeting.py
src/omniretarget/solver/interaction_mesh.py
src/omniretarget/solver/optimizer.py
tests/
```

The caller surface is broad enough that deleting the legacy module in Phase 7
would be unsafe. The right target is to move implementation into deeper modules
and keep `omniretarget.src.utils` as a re-export compatibility layer.

## Target Modules

Phase 7 may add these modules only:

```text
src/omniretarget/retargeting/motion_data.py
src/omniretarget/retargeting/object_assets.py
src/omniretarget/retargeting/spatial.py
src/omniretarget/solver/laplacian.py
```

These modules live under existing packages. This avoids the package-count
inflation risk from creating new `geometry/`, `motion/`, `objects/`, `terrain/`,
or `data/` top-level packages.

## Function Placement

### `retargeting/motion_data.py`

Owns human-motion loading and motion-frame preparation helpers:

```text
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

Rationale: these functions are about source motion data, contact extraction,
motion preprocessing, or human pose interpretation. Current callers are mostly
`retargeting.motion_source`, `retargeting.preprocessing`, tests, and evaluation.

### `retargeting/object_assets.py`

Owns object sampling, surface weighting, object scaling, and generated asset
files:

```text
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

Rationale: these functions are about object/terrain assets and generated URDF/XML
files. Current callers are mostly `retargeting.object_setup` and evaluation.

### `retargeting/spatial.py`

Owns coordinate transforms that are not solver-specific:

```text
augment_object_poses
transform_from_human_to_world
transform_points_world_to_local
transform_points_local_to_world
```

Rationale: these functions bridge human, object, local, and world coordinate
frames. They are shared by retargeting initialization, solver interaction-mesh
frame construction, and PARC tests.

### `solver/laplacian.py`

Owns interaction-mesh and Laplacian math used by the Trajectory Solver:

```text
create_interaction_mesh
get_adjacency_list
calculate_laplacian_coordinates
calculate_laplacian_matrix
```

Rationale: these functions are solver math, not general retargeting utilities.
Current callers are `solver.interaction_mesh` and `solver.optimizer`.

## Compatibility Layer

After implementation, `src/omniretarget/src/utils.py` remains import-compatible.
It should re-export the migrated functions from their new modules.

Example shape:

```python
from omniretarget.retargeting.motion_data import (
    calculate_scale_factor,
    extract_foot_sticking_sequence_velocity,
    load_intermimic_data,
    preprocess_motion_data,
)
from omniretarget.retargeting.object_assets import load_object_data
from omniretarget.retargeting.spatial import transform_points_world_to_local
from omniretarget.solver.laplacian import calculate_laplacian_matrix
```

The exact import list should be explicit. Do not use `import *`.

## Import Migration Policy

Internal callers should move to the new modules when the mapping is direct and
low-risk:

```text
retargeting.motion_source -> retargeting.motion_data
retargeting.preprocessing -> retargeting.motion_data
retargeting.object_setup -> retargeting.object_assets
retargeting.initialization -> retargeting.spatial / motion_data
solver.interaction_mesh -> solver.laplacian / retargeting.spatial
solver.optimizer -> solver.laplacian
evaluation.eval_retargeting -> only direct, low-risk imports
```

Tests that intentionally verify legacy compatibility may keep importing from
`omniretarget.src.utils`.

## Implementation Strategy

Use small vertical slices:

1. Add focused characterization tests for the function family being moved.
2. Add the new module with moved implementation.
3. Update `src.utils` to re-export that family.
4. Migrate direct internal imports for that family.
5. Run focused tests and the full suite.
6. Commit that family before moving to the next family.

Recommended order:

1. `solver/laplacian.py`
2. `retargeting/spatial.py`
3. `retargeting/motion_data.py`
4. `retargeting/object_assets.py`
5. Final compatibility and docs pass

This order starts with relatively pure math and ends with file/asset-generating
functions, which are higher risk.

## Tests

Baseline:

```bash
git diff --check
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest
```

Focused tests during implementation:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_mujoco_query_seam.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_solver_facade.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_retargeting_motion_source.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_retargeting_preprocessing.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_retargeting_object_setup.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_retargeting_initialization.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_foot_sticking_contact_keys.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_optitrack_grounding_preprocess.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_parc_process.py
```

Final gate:

```bash
git diff --check
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest
```

Short smoke checks:

```bash
uv run python src/omniretarget/examples/robot_retarget.py --help
uv run python src/omniretarget/examples/parc_process.py --help
```

If temporary short datasets are available, also rerun:

```text
12-frame robot-only smoke
12-frame object-interaction smoke
PARC dry-run smoke
```

## Stop Conditions

Stop and reassess if any of these happen:

- A new top-level package appears necessary.
- More than four modules are needed for a clean split.
- `src.utils` wrapper becomes complex or starts adding behavior.
- Any CLI argument changes.
- Any output `.npz` schema changes.
- PARC height-origin behavior becomes ambiguous.
- Object scaling or generated XML/URDF behavior changes without explicit tests.
- Solver tests pass only after changing solver behavior.
- Evaluation or conversion requires broad rewrites to keep passing.

## Non-Goals

- Delete `omniretarget.src.utils`.
- Delete `omniretarget.src`.
- Refactor `src/omniretarget/src/viser_utils.py`.
- Move `viser_player.py`.
- Split `config_types`, `config_values`, `data_conversion`, or `evaluation`.
- Rename CLI adapters.

## Success Criteria

- No new top-level packages are added.
- `src.utils` is a compatibility layer with explicit re-exports.
- Internal direct callers use deeper modules where safe.
- Existing public imports from `omniretarget.src.utils` still work.
- Full tests pass.
- Short workflow smokes pass or are explicitly documented if unavailable.
