# Solver and Utils Boundary Design

## Goal

Replace the historical `holosoma_retargeting.src` package boundary with explicit `solver/` and `utils/` modules, while keeping behavior and legacy imports working during the migration.

## Context

The current standalone refactor already introduced `cli/` and `pipelines/`, but the lower layers still import `holosoma_retargeting.src.*` directly. That package name is a historical artifact inherited from Holosoma. It is not a meaningful architectural boundary for an independent project.

The four files under `src/holosoma_retargeting/src/` currently have two different roles:

- `interaction_mesh_retargeter.py` is the retargeting solver and should be treated as the engine layer.
- `mujoco_utils.py`, `utils.py`, and `viser_utils.py` are supporting utility modules and should be grouped under a utility boundary.

## Selected Approach

Use a two-stage migration:

1. Move the four implementation files into semantic destinations:
   - `solver/interaction_mesh_retargeter.py`
   - `utils/mujoco_utils.py`
   - `utils/utils.py`
   - `utils/viser_utils.py`
2. Leave thin compatibility wrappers in `holosoma_retargeting.src.*` that re-export from the new locations.

This phase only moves files and updates imports. It does not split `interaction_mesh_retargeter.py` internally, and it does not decompose `utils/utils.py` yet. Internal splitting comes later once the semantic package boundaries are stable.

## Target Structure

```text
src/holosoma_retargeting/
  solver/
    __init__.py
    interaction_mesh_retargeter.py

  utils/
    __init__.py
    mujoco_utils.py
    utils.py
    viser_utils.py

  src/
    __init__.py
    interaction_mesh_retargeter.py   # compatibility wrapper
    mujoco_utils.py                  # compatibility wrapper
    utils.py                         # compatibility wrapper
    viser_utils.py                   # compatibility wrapper
```

## Responsibilities

### `solver/`

`solver/` owns the retargeting engine layer.

It should contain:

- optimization and solving logic
- retargeting state progression
- constraint/objective orchestration
- the main retargeting class entrypoint

It should not contain:

- CLI parsing
- task discovery
- batch orchestration
- shell wrapper behavior

### `utils/`

`utils/` owns supporting runtime helpers that are shared by solver, pipelines, conversion, evaluation, and replay.

It currently includes:

- MuJoCo bridge helpers
- Viser playback helpers
- geometry/object/scene helpers
- motion preprocessing helpers
- transform/contact helpers

This phase keeps `utils/utils.py` as-is to minimize behavior risk. Later phases can split it into smaller modules such as motion preprocessing, transforms, object mesh, contact, or scene assets.

### `src/`

`src/` becomes a compatibility-only namespace.

It remains importable for existing code and tests, but new architecture layers should stop importing from it. Its sole job is migration compatibility.

## Import Rules After This Phase

Preferred imports:

```python
from holosoma_retargeting.solver.interaction_mesh_retargeter import InteractionMeshRetargeter
from holosoma_retargeting.utils.utils import preprocess_motion_data
from holosoma_retargeting.utils.mujoco_utils import _world_mesh_from_geom
from holosoma_retargeting.utils.viser_utils import create_motion_control_sliders
```

Compatibility imports that remain valid:

```python
from holosoma_retargeting.src.interaction_mesh_retargeter import InteractionMeshRetargeter
```

## Non-Goals

- No internal split of `interaction_mesh_retargeter.py` in this phase
- No internal split of `utils/utils.py` in this phase
- No package rename to `omniretarget`
- No asset layout changes
- No CLI surface changes
- No algorithm changes

## Risks

- Import cycles could appear if wrappers point the wrong direction.
- Tests may still encode assumptions about the historical `src` namespace.
- A broad search-and-replace could accidentally touch compatibility modules that are supposed to remain as wrappers.

## Verification Strategy

- Add boundary tests that forbid new direct `holosoma_retargeting.src` imports from `pipelines/`, `evaluation/`, `data_conversion/`, and `viser_player.py`.
- Add import tests for the new `solver.*` and `utils.*` modules.
- Keep existing compatibility imports tested indirectly through the old `examples.*` and `src.*` paths.
- Run focused pytest coverage and the smoke suite.

## Success Criteria

- The four historical implementation files live under `solver/` and `utils/`.
- `holosoma_retargeting.src.*` still imports cleanly through wrappers.
- New architecture layers no longer import `holosoma_retargeting.src.*` directly.
- Existing smoke checks still pass.
