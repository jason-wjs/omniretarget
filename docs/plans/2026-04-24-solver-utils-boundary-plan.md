# Solver and Utils Boundary Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move the four historical implementation modules out of `holosoma_retargeting.src` into semantic `solver/` and `utils/` packages, while preserving behavior and legacy imports.

**Architecture:** First establish the new package boundaries and update imports to use them. Then leave thin compatibility wrappers in `holosoma_retargeting.src`. Do not split the moved files internally in this phase; treat file movement and internal decomposition as separate refactors.

**Tech Stack:** Python 3.11, uv, setuptools, pytest, tyro

---

### Task 1: Add failing boundary and import tests

**Files:**
- Modify: `tests/test_pipeline_boundaries.py`
- Modify: `tests/test_module_entrypoints.py`

**Step 1: Extend boundary tests**

Add tests that fail if production modules still import `holosoma_retargeting.src` directly:

- every file under `src/holosoma_retargeting/pipelines/*.py`
- `src/holosoma_retargeting/data_conversion/convert_data_format_mj.py`
- `src/holosoma_retargeting/evaluation/eval_retargeting.py`
- `src/holosoma_retargeting/viser_player.py`

**Step 2: Add import coverage for the new packages**

Add import cases for:

- `holosoma_retargeting.solver.interaction_mesh_retargeter`
- `holosoma_retargeting.utils.mujoco_utils`
- `holosoma_retargeting.utils.utils`
- `holosoma_retargeting.utils.viser_utils`

**Step 3: Run tests to confirm RED**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q \
  tests/test_pipeline_boundaries.py \
  tests/test_module_entrypoints.py
```

Expected:

- boundary tests fail because several modules still import `holosoma_retargeting.src`
- import tests fail because `solver/` and `utils/` do not exist yet

### Task 2: Create semantic packages and move implementation files

**Files:**
- Create: `src/holosoma_retargeting/solver/__init__.py`
- Create: `src/holosoma_retargeting/utils/__init__.py`
- Create: `src/holosoma_retargeting/solver/interaction_mesh_retargeter.py`
- Create: `src/holosoma_retargeting/utils/mujoco_utils.py`
- Create: `src/holosoma_retargeting/utils/utils.py`
- Create: `src/holosoma_retargeting/utils/viser_utils.py`
- Modify: `src/holosoma_retargeting/src/interaction_mesh_retargeter.py`
- Modify: `src/holosoma_retargeting/src/mujoco_utils.py`
- Modify: `src/holosoma_retargeting/src/utils.py`
- Modify: `src/holosoma_retargeting/src/viser_utils.py`

**Step 1: Create package markers**

Create:

```python
# src/holosoma_retargeting/solver/__init__.py
"""Retargeting solver implementations for OmniRetarget."""
```

```python
# src/holosoma_retargeting/utils/__init__.py
"""Runtime support utilities for OmniRetarget."""
```

**Step 2: Move the implementation files unchanged**

Move:

- `src/holosoma_retargeting/src/interaction_mesh_retargeter.py`
  -> `src/holosoma_retargeting/solver/interaction_mesh_retargeter.py`
- `src/holosoma_retargeting/src/mujoco_utils.py`
  -> `src/holosoma_retargeting/utils/mujoco_utils.py`
- `src/holosoma_retargeting/src/utils.py`
  -> `src/holosoma_retargeting/utils/utils.py`
- `src/holosoma_retargeting/src/viser_utils.py`
  -> `src/holosoma_retargeting/utils/viser_utils.py`

Do not do internal cleanup while moving.

**Step 3: Turn the old `src/` files into compatibility wrappers**

Each old file should re-export from the new location, for example:

```python
from __future__ import annotations

from holosoma_retargeting.solver.interaction_mesh_retargeter import *  # noqa: F401,F403
```

and similarly for the three utility modules.

### Task 3: Update imports to the new boundary

**Files:**
- Modify: `src/holosoma_retargeting/pipelines/motion_loading.py`
- Modify: `src/holosoma_retargeting/pipelines/object_setup.py`
- Modify: `src/holosoma_retargeting/pipelines/parallel.py`
- Modify: `src/holosoma_retargeting/pipelines/retarget.py`
- Modify: `src/holosoma_retargeting/data_conversion/convert_data_format_mj.py`
- Modify: `src/holosoma_retargeting/evaluation/eval_retargeting.py`
- Modify: `src/holosoma_retargeting/viser_player.py`

**Step 1: Replace direct historical imports**

Use the new semantic imports:

- `holosoma_retargeting.solver.interaction_mesh_retargeter`
- `holosoma_retargeting.utils.mujoco_utils`
- `holosoma_retargeting.utils.utils`
- `holosoma_retargeting.utils.viser_utils`

Do not touch compatibility modules under `src/holosoma_retargeting/src/` beyond the wrappers.

**Step 2: Keep behavior unchanged**

Do not rename functions, change call signatures, or alter file-local logic during this task.

### Task 4: Verify GREEN

**Files:**
- Review only

**Step 1: Run focused tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q \
  tests/test_pipeline_boundaries.py \
  tests/test_module_entrypoints.py
```

Expected: PASS

**Step 2: Run package boundary and path tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q \
  tests/test_package_paths.py \
  tests/test_cli_wrapper_scripts.py
```

Expected: PASS

**Step 3: Run the smoke suite**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache bash scripts/test_smoke.sh
```

Expected: PASS

**Step 4: Optional build verification**

Run:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv build
```

Expected: PASS

### Task 5: Follow-up phase boundary

**Files:**
- No changes in this phase

**Step 1: Explicitly defer internal decomposition**

After this migration lands, the next phase can safely split:

- `solver/interaction_mesh_retargeter.py`
- `utils/utils.py`

That follow-up should start with new failing tests and must not be mixed into this move-only phase.
