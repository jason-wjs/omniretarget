# Phase 8 Src Retirement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Retire `omniretarget.src` as an implementation namespace while preserving legacy imports as compatibility wrappers.

**Architecture:** Move the remaining implementation-bearing legacy modules into existing domain packages, then make `src/omniretarget/src/*.py` explicit re-export wrappers. Production code must import from `retargeting`, `visualization`, `mujoco`, `solver`, or other domain packages, while tests may continue importing `omniretarget.src.*` to verify compatibility.

**Tech Stack:** Python, MuJoCo, NumPy, SciPy, Viser, pytest, uv, git worktrees.

---

## Safety Rules

- Work only in `/home/humanoid/Projects/Junsong_WU/learning/locomotion/RETARGET/omniretarget-phase8-src-retirement`.
- Branch is `arch/phase8-src-retirement`, based on `origin/main` commit `f6a7959`.
- Do not delete `src/omniretarget/src/` in Phase 8.
- Do not change CLI arguments, output schemas, solver behavior, visualization behavior, PARC behavior, or object asset behavior.
- Do not rename the public top-level facade `src/omniretarget/retargeter.py`.
- Do not create new top-level packages under `src/omniretarget/`.
- Add at most two implementation modules under existing packages:
  - `src/omniretarget/retargeting/interaction_mesh_retargeter.py`
  - `src/omniretarget/visualization/playback.py`
- Keep legacy imports working:
  - `omniretarget.src.interaction_mesh_retargeter.InteractionMeshRetargeter`
  - `omniretarget.src.viser_utils.create_motion_control_sliders`
  - `omniretarget.src.mujoco_utils._mesh_local_vf`
  - `omniretarget.src.mujoco_utils._to_world`
  - `omniretarget.src.mujoco_utils._world_mesh_from_geom`
  - all Phase 7 `omniretarget.src.utils` re-exports

## Current Legacy Surface

Tracked files under `src/omniretarget/src/`:

```text
src/omniretarget/src/__init__.py
src/omniretarget/src/interaction_mesh_retargeter.py  # 528 lines, implementation-bearing
src/omniretarget/src/mujoco_utils.py                 # 25 lines, thin wrapper
src/omniretarget/src/utils.py                        # 69 lines, Phase 7 compatibility wrapper
src/omniretarget/src/viser_utils.py                  # 236 lines, implementation-bearing
```

Production imports still using `omniretarget.src.*`:

```text
src/omniretarget/retargeter.py
src/omniretarget/viser_player.py
src/omniretarget/visualization/viser_adapter.py
```

Tests intentionally using legacy imports:

```text
tests/test_public_facades.py
tests/test_module_entrypoints.py
tests/test_utils_split_facades.py
tests/test_parc_process.py
tests/test_foot_sticking_contact_keys.py
tests/test_package_paths.py
tests/test_optitrack_grounding_preprocess.py
```

## Target File Structure

- Create `src/omniretarget/retargeting/interaction_mesh_retargeter.py`
  - Owns the `InteractionMeshRetargeter` implementation.
  - Imports existing `mujoco`, `solver`, and `visualization` modules.
- Modify `src/omniretarget/src/interaction_mesh_retargeter.py`
  - Re-export only `InteractionMeshRetargeter` from `omniretarget.retargeting.interaction_mesh_retargeter`.
- Modify `src/omniretarget/retargeter.py`
  - Re-export `InteractionMeshRetargeter` from the new retargeting module.
- Create `src/omniretarget/visualization/playback.py`
  - Owns `create_motion_control_sliders`.
- Modify `src/omniretarget/src/viser_utils.py`
  - Re-export only `create_motion_control_sliders` from `omniretarget.visualization.playback`.
- Modify `src/omniretarget/viser_player.py`
  - Import playback controls from `omniretarget.visualization.playback`.
- Modify `src/omniretarget/visualization/viser_adapter.py`
  - Import playback controls from `omniretarget.visualization.playback`.
- Modify `src/omniretarget/src/mujoco_utils.py`
  - Keep it as an explicit compatibility wrapper over `omniretarget.mujoco.assets`.
- Modify `tests/test_public_facades.py`
  - Verify new, public, and legacy class/helper identities.
- Modify `tests/test_module_entrypoints.py`
  - Include the new implementation modules in import-safety coverage.
- Modify `tests/test_repo_doc_boundaries.py`
  - Enforce that production code outside `src/omniretarget/src/` does not import `omniretarget.src.*`.

## Task 1: Baseline And Planning Checkpoint

**Files:**
- Create: `docs/superpowers/plans/2026-06-01-phase8-src-retirement.md`

- [ ] **Step 1: Verify branch and worktree**

Run:

```bash
git status --short --branch
git log --oneline --decorate -3
```

Expected:

```text
## arch/phase8-src-retirement...origin/main
f6a7959 ... merge: phase7 utils split
```

- [ ] **Step 2: Run baseline tests**

Run:

```bash
git diff --check
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest
```

Expected: `204 passed, 1 skipped`.

- [ ] **Step 3: Commit this implementation plan**

Run:

```bash
git add docs/superpowers/plans/2026-06-01-phase8-src-retirement.md
git commit -m "docs: add phase8 src retirement plan"
```

Expected: one documentation-only commit.

## Task 2: Move InteractionMeshRetargeter Implementation

**Files:**
- Create: `src/omniretarget/retargeting/interaction_mesh_retargeter.py`
- Modify: `src/omniretarget/src/interaction_mesh_retargeter.py`
- Modify: `src/omniretarget/retargeter.py`
- Modify: `tests/test_public_facades.py`
- Modify: `tests/test_module_entrypoints.py`

- [ ] **Step 1: Write the failing public facade test**

Update `tests/test_public_facades.py`:

```python
from __future__ import annotations


def test_public_retargeter_facade_preserves_legacy_class_identity() -> None:
    from omniretarget.retargeter import InteractionMeshRetargeter as PublicRetargeter
    from omniretarget.retargeting.interaction_mesh_retargeter import InteractionMeshRetargeter as DomainRetargeter
    from omniretarget.src.interaction_mesh_retargeter import InteractionMeshRetargeter as LegacyRetargeter

    assert PublicRetargeter is DomainRetargeter
    assert LegacyRetargeter is DomainRetargeter
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_public_facades.py::test_public_retargeter_facade_preserves_legacy_class_identity -q
```

Expected: FAIL because `omniretarget.retargeting.interaction_mesh_retargeter` does not exist yet.

- [ ] **Step 3: Move implementation**

Create `src/omniretarget/retargeting/interaction_mesh_retargeter.py` by moving the full current implementation from `src/omniretarget/src/interaction_mesh_retargeter.py`.

The new module must start with the same imports, except it must live under the retargeting package:

```python
from __future__ import annotations

import time
from types import ModuleType

import mujoco  # type: ignore[import-not-found]
import numpy as np
from scipy.spatial.transform import Rotation  # type: ignore[import-untyped]

from omniretarget.mujoco.collision import (...)
from omniretarget.mujoco.kinematics import (...)
from omniretarget.mujoco.model_state import load_model_state
from omniretarget.solver import optimizer as frame_optimizer
from omniretarget.solver.frame_problem import FrameProblem
from omniretarget.visualization import viser_adapter
```

Do not change method bodies while moving this file.

- [ ] **Step 4: Replace legacy and public facades**

Replace `src/omniretarget/src/interaction_mesh_retargeter.py` with:

```python
from __future__ import annotations

from omniretarget.retargeting.interaction_mesh_retargeter import InteractionMeshRetargeter

__all__ = ["InteractionMeshRetargeter"]
```

Replace `src/omniretarget/retargeter.py` with:

```python
from __future__ import annotations

from omniretarget.retargeting.interaction_mesh_retargeter import InteractionMeshRetargeter

__all__ = ["InteractionMeshRetargeter"]
```

- [ ] **Step 5: Update entrypoint import coverage**

In `tests/test_module_entrypoints.py`, add:

```python
(
    "omniretarget.retargeting.interaction_mesh_retargeter",
    ["omniretarget.retargeting.interaction_mesh_retargeter"],
),
```

Keep legacy reset entries for `omniretarget.src.interaction_mesh_retargeter` because legacy imports must still work.

- [ ] **Step 6: Run focused verification**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_public_facades.py tests/test_module_entrypoints.py tests/test_solver_facade.py tests/test_retargeting_initialization.py -q
```

Expected: all selected tests pass.

- [ ] **Step 7: Commit**

Run:

```bash
git add src/omniretarget/retargeting/interaction_mesh_retargeter.py src/omniretarget/src/interaction_mesh_retargeter.py src/omniretarget/retargeter.py tests/test_public_facades.py tests/test_module_entrypoints.py
git commit -m "refactor: move retargeter implementation into retargeting package"
```

## Task 3: Move Viser Playback Implementation

**Files:**
- Create: `src/omniretarget/visualization/playback.py`
- Modify: `src/omniretarget/src/viser_utils.py`
- Modify: `src/omniretarget/viser_player.py`
- Modify: `src/omniretarget/visualization/viser_adapter.py`
- Modify: `tests/test_public_facades.py`
- Modify: `tests/test_module_entrypoints.py`

- [ ] **Step 1: Write the failing playback facade test**

Append to `tests/test_public_facades.py`:

```python
def test_visualization_playback_facade_preserves_legacy_helper_identity() -> None:
    from omniretarget.src.viser_utils import create_motion_control_sliders as LegacyHelper
    from omniretarget.visualization.playback import create_motion_control_sliders as PlaybackHelper

    assert LegacyHelper is PlaybackHelper
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_public_facades.py::test_visualization_playback_facade_preserves_legacy_helper_identity -q
```

Expected: FAIL because `omniretarget.visualization.playback` does not exist yet.

- [ ] **Step 3: Move playback implementation**

Create `src/omniretarget/visualization/playback.py` by moving `create_motion_control_sliders` from `src/omniretarget/src/viser_utils.py`.

The new module must use the same imports:

```python
from __future__ import annotations

import threading
import time
from typing import List, Tuple

import numpy as np
import viser  # type: ignore[import-not-found]
from viser.extras import ViserUrdf  # type: ignore[import-not-found]
```

Do not change the function body while moving it.

- [ ] **Step 4: Replace legacy wrapper and production imports**

Replace `src/omniretarget/src/viser_utils.py` with:

```python
from __future__ import annotations

from omniretarget.visualization.playback import create_motion_control_sliders

__all__ = ["create_motion_control_sliders"]
```

In `src/omniretarget/viser_player.py`, replace:

```python
from omniretarget.src.viser_utils import create_motion_control_sliders  # noqa: E402
```

with:

```python
from omniretarget.visualization.playback import create_motion_control_sliders  # noqa: E402
```

In `src/omniretarget/visualization/viser_adapter.py`, replace:

```python
from omniretarget.src.viser_utils import create_motion_control_sliders
```

with:

```python
from omniretarget.visualization.playback import create_motion_control_sliders
```

- [ ] **Step 5: Update entrypoint import coverage**

In `tests/test_module_entrypoints.py`, add:

```python
(
    "omniretarget.visualization.playback",
    ["omniretarget.visualization.playback"],
),
```

- [ ] **Step 6: Run focused verification**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_public_facades.py tests/test_module_entrypoints.py -q
uv run python src/omniretarget/viser_player.py --help
```

Expected: pytest passes and `viser_player.py --help` exits 0.

- [ ] **Step 7: Commit**

Run:

```bash
git add src/omniretarget/visualization/playback.py src/omniretarget/src/viser_utils.py src/omniretarget/viser_player.py src/omniretarget/visualization/viser_adapter.py tests/test_public_facades.py tests/test_module_entrypoints.py
git commit -m "refactor: move viser playback helper into visualization package"
```

## Task 4: Harden Mujoco Utils Compatibility Wrapper

**Files:**
- Modify: `src/omniretarget/src/mujoco_utils.py`
- Modify: `tests/test_public_facades.py`

- [ ] **Step 1: Write the facade identity test**

Append to `tests/test_public_facades.py`:

```python
def test_legacy_mujoco_utils_reexports_asset_helpers() -> None:
    from omniretarget.mujoco import assets
    from omniretarget.src import mujoco_utils

    assert mujoco_utils._mesh_local_vf is assets.mesh_local_vertices_and_faces
    assert mujoco_utils._to_world is assets.transform_mesh_vertices_to_world
    assert mujoco_utils._world_mesh_from_geom is assets.world_mesh_from_geom
```

- [ ] **Step 2: Run the failing identity test**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_public_facades.py::test_legacy_mujoco_utils_reexports_asset_helpers -q
```

Expected: FAIL because current `mujoco_utils` wraps the functions rather than re-exporting the exact function objects.

- [ ] **Step 3: Replace wrapper functions with explicit aliases**

Replace `src/omniretarget/src/mujoco_utils.py` with:

```python
from __future__ import annotations

from typing import Tuple

from omniretarget.mujoco.assets import (
    mesh_local_vertices_and_faces as _mesh_local_vf,
    transform_mesh_vertices_to_world as _to_world,
    world_mesh_from_geom as _world_mesh_from_geom,
)

Pair = Tuple[str, str]

__all__ = ["Pair", "_mesh_local_vf", "_to_world", "_world_mesh_from_geom"]
```

- [ ] **Step 4: Run focused verification**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_public_facades.py tests/test_mujoco_query_seam.py -q
```

Expected: all selected tests pass.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/omniretarget/src/mujoco_utils.py tests/test_public_facades.py
git commit -m "refactor: make legacy mujoco utils explicit aliases"
```

## Task 5: Enforce Src Namespace Boundary

**Files:**
- Modify: `tests/test_repo_doc_boundaries.py`
- Test: `tests/test_repo_doc_boundaries.py`

- [ ] **Step 1: Add production boundary test for all `omniretarget.src.*` imports**

Append to `tests/test_repo_doc_boundaries.py`:

```python
def test_production_code_does_not_import_legacy_src_namespace() -> None:
    allowed_prefix = Path("src/omniretarget/src")
    offenders = []
    for path in PACKAGE_ROOT.rglob("*.py"):
        if path.is_relative_to(allowed_prefix):
            continue
        text = path.read_text()
        if "omniretarget.src." in text or "from omniretarget.src" in text:
            offenders.append(path)

    assert offenders == []
```

This test intentionally does not scan `tests/`, because tests verify legacy compatibility.

- [ ] **Step 2: Run the boundary test**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_repo_doc_boundaries.py::test_production_code_does_not_import_legacy_src_namespace -q
```

Expected: PASS after Tasks 2 and 3 remove production imports from `retargeter.py`, `viser_player.py`, and `visualization/viser_adapter.py`.

- [ ] **Step 3: Run legacy namespace grep**

Run:

```bash
rg "omniretarget\\.src\\." src/omniretarget
```

Expected: no output from production files outside `src/omniretarget/src/`.

- [ ] **Step 4: Commit**

Run:

```bash
git add tests/test_repo_doc_boundaries.py
git commit -m "test: enforce legacy src namespace boundary"
```

## Task 6: Final Verification And Handoff

**Files:**
- No new source files expected.

- [ ] **Step 1: Run static checks**

Run:

```bash
git diff --check
git status --short --branch
```

Expected: `git diff --check` exits 0. Status is clean except branch tracking information.

- [ ] **Step 2: Run full tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest
```

Expected: all tests pass with one skipped test unless the count changes only because new tests were added.

- [ ] **Step 3: Run CLI help smokes**

Run:

```bash
uv run python src/omniretarget/examples/robot_retarget.py --help
uv run python src/omniretarget/examples/parc_process.py --help
uv run python src/omniretarget/viser_player.py --help
```

Expected: all commands exit 0 and print help text without import errors.

- [ ] **Step 4: Inspect legacy namespace state**

Run:

```bash
git ls-files src/omniretarget/src
rg "omniretarget\\.src\\." src/omniretarget tests
```

Expected:

```text
src/omniretarget/src/__init__.py
src/omniretarget/src/interaction_mesh_retargeter.py
src/omniretarget/src/mujoco_utils.py
src/omniretarget/src/utils.py
src/omniretarget/src/viser_utils.py
```

Production matches should only be inside `src/omniretarget/src/`; tests may match legacy imports.

- [ ] **Step 5: Push the Phase 8 branch**

Run:

```bash
git push -u origin arch/phase8-src-retirement
```

Expected: branch pushed to `origin/arch/phase8-src-retirement`.

- [ ] **Step 6: Stop for review before merge**

Report:

- Worktree path.
- Branch name.
- New implementation modules created.
- Legacy wrappers retained.
- Test and smoke results.
- Confirmation that `main` has not been modified by Phase 8.

Do not merge Phase 8 into `main` until the user explicitly requests merge.
