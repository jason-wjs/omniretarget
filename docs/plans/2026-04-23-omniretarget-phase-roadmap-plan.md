# OmniRetarget Phase Roadmap Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor `holosoma_retargeting` into a cleaner standalone OmniRetarget package through small, independently verifiable phases.

**Architecture:** Keep the public package name `holosoma_retargeting` during the refactor, but progressively replace historical Holosoma layout with explicit CLI, pipeline, core, config, runtime, asset, and compatibility layers. Each phase must preserve existing shell wrappers and package imports until a later planned compatibility-removal phase.

**Tech Stack:** Python 3.11, setuptools/pyproject, tyro CLI, numpy/torch/scipy/mujoco/viser, pytest, ruff, uv.

---

## Execution Protocol

Work in `/home/humanoid/Projects/Junsong_WU/ADAM/omni/omniretarget-refactor` on branch `refactor` unless the user asks for a different branch strategy.

For every phase:

1. Start from a clean worktree.
2. Implement only that phase's scope.
3. Add or update tests before implementation where practical.
4. Run the phase-specific tests.
5. Run the smoke suite.
6. Commit with one focused commit message.
7. Push the `refactor` branch.

Standard verification commands:

```bash
uv run pytest -q tests
bash scripts/test_smoke.sh
uv build
```

If `uv build` is slow or blocked by environment state, record the exact failure and at least run the focused tests plus `bash scripts/test_smoke.sh`.

---

## Phase Overview

### Phase 1: Introduce Semantic Core Import Boundary

**Goal:** Stop new architecture layers from importing `holosoma_retargeting.src.*` directly without moving implementation files yet.

**Scope:**
- Create `src/holosoma_retargeting/core/` as semantic aliases over current `src/` modules.
- Update `pipelines/`, `evaluation/`, `data_conversion/`, and `viser_player.py` imports to prefer `holosoma_retargeting.core.*`.
- Keep `holosoma_retargeting.src.*` fully working.
- Add boundary tests that forbid direct `holosoma_retargeting.src` imports outside compatibility modules and tests.

**Why first:** It creates a stable migration boundary with low behavior risk.

**Commit:** `refactor: introduce semantic core import boundary`

**Push:** `git push origin refactor`

---

### Phase 2: Move Core Implementation Files

**Goal:** Make `core/` own the implementation and turn historical `src/` into compatibility wrappers.

**Scope:**
- Move implementation from:
  - `src/holosoma_retargeting/src/interaction_mesh_retargeter.py`
  - `src/holosoma_retargeting/src/mujoco_utils.py`
  - `src/holosoma_retargeting/src/utils.py`
  - `src/holosoma_retargeting/src/viser_utils.py`
- To:
  - `src/holosoma_retargeting/core/interaction_mesh_retargeter.py`
  - `src/holosoma_retargeting/core/mujoco_utils.py`
  - `src/holosoma_retargeting/core/utils.py`
  - `src/holosoma_retargeting/core/viser_utils.py`
- Replace old `src/*.py` files with thin re-export wrappers.
- Keep old import paths tested.

**Commit:** `refactor: move retargeting core out of historical src package`

**Push:** `git push origin refactor`

---

### Phase 3: Split Core Utilities by Responsibility

**Goal:** Reduce `core/utils.py` from a mixed utility bucket into domain modules while keeping a compatibility facade.

**Scope:**
- Create focused modules, likely:
  - `core/motion_io.py`
  - `core/motion_preprocessing.py`
  - `core/object_mesh.py`
  - `core/scene_assets.py`
  - `core/transforms.py`
  - `core/contact.py`
- Keep `core/utils.py` re-exporting moved functions during this phase.
- Update `pipelines/` to import focused modules, not the utility facade.

**Commit:** `refactor: split core utility modules`

**Push:** `git push origin refactor`

---

### Phase 4: Add Typed Runtime Specs

**Goal:** Replace ad hoc `SimpleNamespace` runtime constants with explicit typed objects.

**Scope:**
- Add `src/holosoma_retargeting/runtime/specs.py`.
- Introduce dataclasses such as `RobotRuntimeSpec`, `MotionRuntimeSpec`, `TaskRuntimeSpec`, and `RetargetingRuntimeSpec`.
- Add conversion functions from current config dataclasses.
- Keep compatibility adapter for core retargeter code that still expects legacy uppercase constants.
- Replace `create_task_constants()` internals without changing pipeline behavior.

**Commit:** `refactor: add typed runtime specs`

**Push:** `git push origin refactor`

---

### Phase 5: Unify Single and Parallel Retarget Jobs

**Goal:** Remove duplicate retargeting orchestration between single-clip and parallel pipelines.

**Scope:**
- Add a small job model, likely `RetargetJob` and `RetargetJobResult`.
- Extract shared single-job execution from `pipelines/retarget.py` and `pipelines/parallel.py`.
- Make single retarget create one job.
- Make parallel retarget discover many jobs and execute the same job function in a process pool.
- Keep output filenames unchanged.

**Commit:** `refactor: unify retarget job execution`

**Push:** `git push origin refactor`

---

### Phase 6: Formalize Asset Resolution

**Goal:** Make robot models, object assets, templates, and demo data explicit package resources instead of scattered string paths.

**Scope:**
- Add `src/holosoma_retargeting/assets.py` or `resources.py`.
- Move `package_path()` responsibility behind typed helpers:
  - `robot_model_path(robot, dof, kind)`
  - `object_asset_path(object_name, kind)`
  - `demo_data_path(relative)`
  - `template_path(name)`
- Keep `path_utils.package_path()` as compatibility.
- Add tests for current models and templates.

**Commit:** `refactor: centralize package asset resolution`

**Push:** `git push origin refactor`

---

### Phase 7: Improve CLI Packaging

**Goal:** Make OmniRetarget usable as a standalone installed tool, not only through shell wrappers and `python -m`.

**Scope:**
- Add `[project.scripts]` in `pyproject.toml`.
- Keep shell wrappers under `scripts/retargeting/`.
- Add import and help-output tests for console entrypoints where feasible.
- Update README with console script usage while keeping existing wrapper examples.

**Commit:** `refactor: add omniretarget console entrypoints`

**Push:** `git push origin refactor`

---

### Phase 8: Asset Packaging Policy

**Goal:** Decide what belongs in the Python package distribution and what should become external demo/example data.

**Scope:**
- Keep robot models packaged unless the team decides otherwise.
- Move or mark demo data as optional if package size becomes a problem.
- Update `MANIFEST.in` and tests to reflect the policy.
- Ensure examples still run with documented demo-data location.

**Commit:** `refactor: define package asset boundary`

**Push:** `git push origin refactor`

---

### Phase 9: Optional Package Rename Compatibility Layer

**Goal:** Decide whether to expose a future `omniretarget` Python package while preserving `holosoma_retargeting` imports.

**Scope:**
- Only do this after phases 1-8 are stable.
- If approved, add `omniretarget` package as primary import path.
- Keep `holosoma_retargeting` as compatibility wrappers for at least one migration window.
- Update docs and tests to cover both import paths.

**Commit:** `refactor: add omniretarget package compatibility layer`

**Push:** `git push origin refactor`

---

## Phase 1 Detailed Plan

### Task 1: Add Boundary Tests

**Files:**
- Modify: `tests/test_pipeline_boundaries.py`
- Test: `tests/test_pipeline_boundaries.py`

**Step 1: Write the failing test**

Add tests that inspect source text for direct historical imports:

```python
from pathlib import Path


PACKAGE_ROOT = Path("src/holosoma_retargeting")


def _python_sources_under(*parts: str) -> list[Path]:
    return sorted((PACKAGE_ROOT.joinpath(*parts)).glob("*.py"))


def test_pipeline_modules_do_not_import_historical_src_package() -> None:
    offenders = []
    for path in _python_sources_under("pipelines"):
        source = path.read_text()
        if "holosoma_retargeting.src" in source:
            offenders.append(str(path))
    assert offenders == []


def test_domain_entrypoints_do_not_import_historical_src_package() -> None:
    checked = [
        PACKAGE_ROOT / "viser_player.py",
        PACKAGE_ROOT / "data_conversion" / "convert_data_format_mj.py",
        PACKAGE_ROOT / "evaluation" / "eval_retargeting.py",
    ]
    offenders = [str(path) for path in checked if "holosoma_retargeting.src" in path.read_text()]
    assert offenders == []
```

**Step 2: Run test to verify it fails**

Run:

```bash
uv run pytest -q tests/test_pipeline_boundaries.py
```

Expected: FAIL listing files that still import `holosoma_retargeting.src`.

---

### Task 2: Create Core Alias Modules

**Files:**
- Create: `src/holosoma_retargeting/core/__init__.py`
- Create: `src/holosoma_retargeting/core/interaction_mesh_retargeter.py`
- Create: `src/holosoma_retargeting/core/mujoco_utils.py`
- Create: `src/holosoma_retargeting/core/utils.py`
- Create: `src/holosoma_retargeting/core/viser_utils.py`

**Step 1: Add alias modules**

Use this pattern for each module:

```python
from __future__ import annotations

from holosoma_retargeting.src.interaction_mesh_retargeter import *  # noqa: F401,F403
```

For `core/__init__.py`:

```python
"""Core retargeting implementation boundary for OmniRetarget."""
```

**Step 2: Run import test**

Run:

```bash
uv run pytest -q tests/test_module_entrypoints.py
```

Expected: PASS.

---

### Task 3: Update Imports to Core Boundary

**Files:**
- Modify: `src/holosoma_retargeting/pipelines/retarget.py`
- Modify: `src/holosoma_retargeting/pipelines/parallel.py`
- Modify: `src/holosoma_retargeting/pipelines/motion_loading.py`
- Modify: `src/holosoma_retargeting/pipelines/object_setup.py`
- Modify: `src/holosoma_retargeting/viser_player.py`
- Modify: `src/holosoma_retargeting/data_conversion/convert_data_format_mj.py`
- Modify: `src/holosoma_retargeting/evaluation/eval_retargeting.py`
- Modify tests only if they intentionally assert the old import path.

**Step 1: Replace imports**

Examples:

```python
from holosoma_retargeting.core.interaction_mesh_retargeter import InteractionMeshRetargeter
from holosoma_retargeting.core.utils import preprocess_motion_data
from holosoma_retargeting.core.viser_utils import create_motion_control_sliders
from holosoma_retargeting.core.mujoco_utils import _world_mesh_from_geom
```

**Step 2: Run boundary tests**

Run:

```bash
uv run pytest -q tests/test_pipeline_boundaries.py tests/test_module_entrypoints.py
```

Expected: PASS.

---

### Task 4: Add Compatibility Import Test

**Files:**
- Modify: `tests/test_module_entrypoints.py`

**Step 1: Add new module import cases**

Add import cases for:

```python
"holosoma_retargeting.core.interaction_mesh_retargeter"
"holosoma_retargeting.core.mujoco_utils"
"holosoma_retargeting.core.utils"
"holosoma_retargeting.core.viser_utils"
```

Keep old `holosoma_retargeting.src.*` imports where existing tests rely on compatibility.

**Step 2: Run test**

Run:

```bash
uv run pytest -q tests/test_module_entrypoints.py
```

Expected: PASS.

---

### Task 5: Update Documentation

**Files:**
- Modify: `docs/plans/2026-04-23-cli-pipelines-refactor-design.md` if needed
- Modify: `README.md` only if it mentions `holosoma_retargeting.src`

**Step 1: Search docs**

Run:

```bash
rg -n "holosoma_retargeting\\.src|src/" README.md docs src/holosoma_retargeting/README.md
```

**Step 2: Update only architecture references**

Do not churn user-facing usage examples unless they are stale.

---

### Task 6: Verify, Commit, Push

**Files:**
- All Phase 1 files.

**Step 1: Run focused tests**

```bash
uv run pytest -q tests/test_pipeline_boundaries.py tests/test_module_entrypoints.py tests/test_package_paths.py
```

Expected: PASS.

**Step 2: Run smoke suite**

```bash
bash scripts/test_smoke.sh
```

Expected: PASS.

**Step 3: Build package**

```bash
uv build
```

Expected: PASS.

**Step 4: Commit**

```bash
git add src/holosoma_retargeting tests docs README.md
git commit -m "refactor: introduce semantic core import boundary"
```

**Step 5: Push**

```bash
git push origin refactor
```

Expected: push succeeds.

---

## Stop Conditions

Stop and ask before proceeding if:

- A phase requires changing retargeting math or solver behavior.
- Tests show numeric output changes not covered by existing expectations.
- A package rename becomes necessary earlier than Phase 9.
- `uv build` reveals asset packaging changes outside the current phase.
- The reference branch `omniretarget` appears to need modification. It should remain untouched.

---

## Current Recommendation

Start with Phase 1 only. It gives us a new semantic architecture boundary while keeping implementation files in place, so it is low risk and easy to review. After Phase 1 is pushed, move to Phase 2.
