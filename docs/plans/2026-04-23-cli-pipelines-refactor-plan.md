# CLI and Pipelines Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move production Python entrypoints into `holosoma_retargeting.cli` and move shared single/parallel retargeting orchestration into `holosoma_retargeting.pipelines`.

**Architecture:** Add `cli/` as the thin executable layer and `pipelines/` as the minimal internal orchestration layer. Keep `examples/` as compatibility wrappers for this phase, and leave `evaluation/`, `data_conversion/`, `data_utils/`, `models/`, `demo_data/`, and `holosoma_retargeting/src/` structurally intact.

**Tech Stack:** Python 3.11, uv, setuptools, pytest, tyro, shell scripts

---

### Task 1: Add CLI import boundary tests

**Files:**
- Modify: `tests/test_module_entrypoints.py`

**Step 1: Write the failing test**

Extend the parametrized `test_entrypoint_import_does_not_mutate_sys_path` cases with the new modules:

```python
        (
            "holosoma_retargeting.cli.retarget",
            [
                "holosoma_retargeting.cli.retarget",
                "holosoma_retargeting.pipelines.retarget",
                "holosoma_retargeting.pipelines.task_setup",
                "holosoma_retargeting.pipelines.motion_loading",
                "holosoma_retargeting.pipelines.object_setup",
                "holosoma_retargeting.src.interaction_mesh_retargeter",
            ],
        ),
        (
            "holosoma_retargeting.cli.parallel_retarget",
            [
                "holosoma_retargeting.cli.parallel_retarget",
                "holosoma_retargeting.pipelines.parallel",
                "holosoma_retargeting.pipelines.retarget",
                "holosoma_retargeting.src.interaction_mesh_retargeter",
            ],
        ),
        (
            "holosoma_retargeting.cli.evaluate",
            ["holosoma_retargeting.cli.evaluate"],
        ),
        (
            "holosoma_retargeting.cli.convert_mj",
            ["holosoma_retargeting.cli.convert_mj"],
        ),
        (
            "holosoma_retargeting.cli.replay",
            ["holosoma_retargeting.cli.replay"],
        ),
```

**Step 2: Run test to verify it fails**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_module_entrypoints.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'holosoma_retargeting.cli'`.

**Step 3: Commit only the failing test if desired**

Do not commit failing tests alone unless pausing. Continue to Task 2 in the same TDD cycle.

### Task 2: Create thin CLI entrypoint modules

**Files:**
- Create: `src/holosoma_retargeting/cli/__init__.py`
- Create: `src/holosoma_retargeting/cli/retarget.py`
- Create: `src/holosoma_retargeting/cli/parallel_retarget.py`
- Create: `src/holosoma_retargeting/cli/evaluate.py`
- Create: `src/holosoma_retargeting/cli/convert_mj.py`
- Create: `src/holosoma_retargeting/cli/replay.py`

**Step 1: Add the package marker**

Create `src/holosoma_retargeting/cli/__init__.py`:

```python
"""Command-line entrypoints for OmniRetarget."""
```

**Step 2: Add temporary thin wrappers**

Create `src/holosoma_retargeting/cli/retarget.py`:

```python
from __future__ import annotations

import tyro

from holosoma_retargeting.config_types.retargeting import RetargetingConfig
from holosoma_retargeting.examples.robot_retarget import main as run_retarget


def main() -> None:
    cfg = tyro.cli(RetargetingConfig)
    run_retarget(cfg)


if __name__ == "__main__":
    main()
```

Create `src/holosoma_retargeting/cli/parallel_retarget.py`:

```python
from __future__ import annotations

import tyro

from holosoma_retargeting.config_types.retargeting import ParallelRetargetingConfig
from holosoma_retargeting.examples.parallel_robot_retarget import main as run_parallel_retarget


def main() -> None:
    cfg = tyro.cli(ParallelRetargetingConfig)
    run_parallel_retarget(cfg)


if __name__ == "__main__":
    main()
```

Create `src/holosoma_retargeting/cli/evaluate.py`:

```python
from __future__ import annotations

import tyro

from holosoma_retargeting.evaluation.eval_retargeting import Args, main as run_evaluation


def main() -> None:
    cfg = tyro.cli(Args)
    run_evaluation(cfg)


if __name__ == "__main__":
    main()
```

Create `src/holosoma_retargeting/cli/convert_mj.py`:

```python
from __future__ import annotations

import tyro

from holosoma_retargeting.config_types.data_conversion import DataConversionConfig
from holosoma_retargeting.data_conversion.convert_data_format_mj import main as run_conversion


def main() -> None:
    cfg = tyro.cli(DataConversionConfig)
    run_conversion(cfg)


if __name__ == "__main__":
    main()
```

Create `src/holosoma_retargeting/cli/replay.py`:

```python
from __future__ import annotations

import tyro

from holosoma_retargeting.config_types.viser import ViserConfig
from holosoma_retargeting.viser_player import main as run_replay


def main() -> None:
    cfg = tyro.cli(ViserConfig)
    run_replay(cfg)


if __name__ == "__main__":
    main()
```

**Step 3: Re-run import tests**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_module_entrypoints.py -q
```

Expected: PASS for the new `cli.*` import cases and existing cases.

**Step 4: Commit**

```bash
git add tests/test_module_entrypoints.py src/holosoma_retargeting/cli
git commit -m "refactor: add cli entrypoint package"
```

### Task 3: Extract task setup helpers into `pipelines/task_setup.py`

**Files:**
- Create: `src/holosoma_retargeting/pipelines/__init__.py`
- Create: `src/holosoma_retargeting/pipelines/task_setup.py`
- Modify: `src/holosoma_retargeting/examples/robot_retarget.py`
- Modify: `src/holosoma_retargeting/examples/parallel_robot_retarget.py`
- Test: `tests/test_module_entrypoints.py`

**Step 1: Write a failing import test**

Add `holosoma_retargeting.pipelines.task_setup` to `tests/test_module_entrypoints.py` as a separate import case:

```python
        (
            "holosoma_retargeting.pipelines.task_setup",
            ["holosoma_retargeting.pipelines.task_setup"],
        ),
```

**Step 2: Run test to verify it fails**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_module_entrypoints.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'holosoma_retargeting.pipelines'`.

**Step 3: Create the package and move helper definitions unchanged**

Create `src/holosoma_retargeting/pipelines/__init__.py`:

```python
"""Internal orchestration pipelines for OmniRetarget."""
```

Create `src/holosoma_retargeting/pipelines/task_setup.py`.

Move these definitions from `examples/robot_retarget.py` into `pipelines/task_setup.py` without behavior changes:

- `DEFAULT_DATA_FORMATS`
- `DEFAULT_SAVE_DIRS`
- `_ADAM_PRO_ROBOT_ONLY_HIP_LB`
- `_ADAM_PRO_ROBOT_ONLY_HIP_UB`
- `TaskType`
- `create_task_constants`
- `validate_config`

Required imports in `task_setup.py`:

```python
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Literal

from holosoma_retargeting.config_types.data_type import DEMO_JOINTS_REGISTRY, MotionDataConfig
from holosoma_retargeting.config_types.retargeting import RetargetingConfig
from holosoma_retargeting.config_types.robot import RobotConfig
from holosoma_retargeting.config_types.task import TaskConfig
from holosoma_retargeting.path_utils import package_path
```

**Step 4: Update old modules to import moved helpers**

In `examples/robot_retarget.py`, remove the moved definitions and import them:

```python
from holosoma_retargeting.pipelines.task_setup import (
    DEFAULT_DATA_FORMATS,
    DEFAULT_SAVE_DIRS,
    TaskType,
    create_task_constants,
    validate_config,
)
```

In `examples/parallel_robot_retarget.py`, replace `DEFAULT_DATA_FORMATS` and `create_task_constants` imports from `examples.robot_retarget` with imports from `pipelines.task_setup`.

**Step 5: Re-run focused tests**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_module_entrypoints.py tests/test_adam_pro_robot_config.py tests/test_adam_pro_motion_mappings.py -q
```

Expected: PASS.

**Step 6: Commit**

```bash
git add src/holosoma_retargeting/pipelines src/holosoma_retargeting/examples tests/test_module_entrypoints.py
git commit -m "refactor: extract retargeting task setup pipeline"
```

### Task 4: Extract motion loading into `pipelines/motion_loading.py`

**Files:**
- Create: `src/holosoma_retargeting/pipelines/motion_loading.py`
- Modify: `src/holosoma_retargeting/examples/robot_retarget.py`
- Modify: `src/holosoma_retargeting/examples/parallel_robot_retarget.py`
- Test: `tests/test_module_entrypoints.py`

**Step 1: Write a failing import test**

Add:

```python
        (
            "holosoma_retargeting.pipelines.motion_loading",
            ["holosoma_retargeting.pipelines.motion_loading"],
        ),
```

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_module_entrypoints.py -q
```

Expected: FAIL with `ModuleNotFoundError`.

**Step 2: Move motion loading helpers unchanged**

Create `src/holosoma_retargeting/pipelines/motion_loading.py`.

Move these definitions from `examples/robot_retarget.py`:

- `create_ground_points`
- `load_motion_data`

Required imports include the imports currently used by those functions:

```python
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import numpy as np

from holosoma_retargeting.config_types.data_type import MotionDataConfig
from holosoma_retargeting.pipelines.task_setup import TaskType
from holosoma_retargeting.src.utils import (
    calculate_scale_factor,
    load_intermimic_data,
    load_object_data,
    transform_from_human_to_world,
    transform_y_up_to_z_up,
)
```

Use the actual import set needed after moving the function body; remove unused imports.

**Step 3: Update imports**

In `examples/robot_retarget.py`, import:

```python
from holosoma_retargeting.pipelines.motion_loading import create_ground_points, load_motion_data
```

In `examples/parallel_robot_retarget.py`, import `load_motion_data` from `pipelines.motion_loading`.

**Step 4: Re-run focused tests**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_module_entrypoints.py tests/test_optitrack_motion_format.py tests/test_optitrack_grounding_preprocess.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/holosoma_retargeting/pipelines/motion_loading.py src/holosoma_retargeting/examples tests/test_module_entrypoints.py
git commit -m "refactor: extract motion loading pipeline helpers"
```

### Task 5: Extract object setup and retarget support helpers

**Files:**
- Create: `src/holosoma_retargeting/pipelines/object_setup.py`
- Create: `src/holosoma_retargeting/pipelines/retarget.py`
- Modify: `src/holosoma_retargeting/examples/robot_retarget.py`
- Modify: `src/holosoma_retargeting/examples/parallel_robot_retarget.py`
- Modify: `src/holosoma_retargeting/cli/retarget.py`
- Test: `tests/test_module_entrypoints.py`

**Step 1: Write failing import tests**

Add:

```python
        (
            "holosoma_retargeting.pipelines.object_setup",
            ["holosoma_retargeting.pipelines.object_setup"],
        ),
        (
            "holosoma_retargeting.pipelines.retarget",
            ["holosoma_retargeting.pipelines.retarget"],
        ),
```

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_module_entrypoints.py -q
```

Expected: FAIL with missing modules.

**Step 2: Move object setup definitions unchanged**

Create `src/holosoma_retargeting/pipelines/object_setup.py`.

Move these definitions from `examples/robot_retarget.py`:

- `_OBJECT_SCALE_AUGMENTED`
- `_OBJECT_SCALE_NORMAL`
- `_AUGMENTATION_TRANSLATION`
- `setup_object_data`
- `initialize_robot_pose`
- `determine_output_path`
- `build_retargeter_kwargs_from_config`

Use imports from `examples/robot_retarget.py` that these functions already require, including:

```python
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import numpy as np

from holosoma_retargeting.config_types.retargeter import RetargeterConfig
from holosoma_retargeting.config_types.task import TaskConfig
from holosoma_retargeting.pipelines.task_setup import TaskType
from holosoma_retargeting.src.utils import (
    augment_object_poses,
    create_new_scene_xml_file,
    create_scaled_multi_boxes_urdf,
    create_scaled_multi_boxes_xml,
    estimate_human_orientation,
    extract_object_first_moving_frame,
    load_object_data,
    transform_points_world_to_local,
)
```

Adjust the import list to the exact function bodies after moving.

**Step 3: Create `pipelines/retarget.py`**

Create `src/holosoma_retargeting/pipelines/retarget.py` with `run_retarget(cfg: RetargetingConfig) -> None`.

Move the full body of `examples/robot_retarget.py::main` into `run_retarget` and update imports to use:

- `pipelines.task_setup`
- `pipelines.motion_loading`
- `pipelines.object_setup`

Keep behavior unchanged.

**Step 4: Make CLI use the pipeline**

Update `src/holosoma_retargeting/cli/retarget.py`:

```python
from holosoma_retargeting.pipelines.retarget import run_retarget
```

**Step 5: Make the old example a compatibility wrapper**

Replace `examples/robot_retarget.py::main` with:

```python
from holosoma_retargeting.pipelines.retarget import run_retarget


def main(cfg: RetargetingConfig) -> None:
    run_retarget(cfg)
```

Keep any helper re-exports needed by old imports during the transition, but prefer importing them from `pipelines.*`.

**Step 6: Re-run focused tests**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_module_entrypoints.py tests/test_adam_pro_cli_smoke.py tests/test_package_paths.py -q
```

Expected: PASS.

**Step 7: Commit**

```bash
git add src/holosoma_retargeting/pipelines src/holosoma_retargeting/examples/robot_retarget.py src/holosoma_retargeting/cli/retarget.py tests/test_module_entrypoints.py
git commit -m "refactor: extract single retarget pipeline"
```

### Task 6: Extract parallel retargeting into `pipelines/parallel.py`

**Files:**
- Create: `src/holosoma_retargeting/pipelines/parallel.py`
- Modify: `src/holosoma_retargeting/examples/parallel_robot_retarget.py`
- Modify: `src/holosoma_retargeting/cli/parallel_retarget.py`
- Test: `tests/test_module_entrypoints.py`

**Step 1: Add a structural test that parallel no longer imports examples**

Create or extend a structural test:

```python
from pathlib import Path


def test_parallel_pipeline_does_not_import_examples_modules() -> None:
    source = Path("src/holosoma_retargeting/pipelines/parallel.py").read_text()
    assert "holosoma_retargeting.examples" not in source
```

Run before creating the file:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_module_entrypoints.py tests/test_repo_doc_boundaries.py -q
```

Expected: FAIL because `pipelines/parallel.py` does not exist.

**Step 2: Move parallel-specific definitions**

Create `src/holosoma_retargeting/pipelines/parallel.py`.

Move these definitions from `examples/parallel_robot_retarget.py`:

- `PARALLEL_SAVE_DIRS`
- `find_files`
- `generate_augmentation_configs`
- `extract_task_name`
- `process_single_task`
- `run_parallel_retarget(cfg: ParallelRetargetingConfig) -> None`

Move the body of `examples/parallel_robot_retarget.py::main` into `run_parallel_retarget`.

Update imports so `pipelines/parallel.py` imports shared helpers from:

- `pipelines.task_setup`
- `pipelines.motion_loading`
- `pipelines.object_setup`

It must not import from `holosoma_retargeting.examples.*`.

**Step 3: Update CLI**

Update `src/holosoma_retargeting/cli/parallel_retarget.py`:

```python
from holosoma_retargeting.pipelines.parallel import run_parallel_retarget
```

**Step 4: Make old example a compatibility wrapper**

Replace `examples/parallel_robot_retarget.py::main` with:

```python
from holosoma_retargeting.pipelines.parallel import run_parallel_retarget


def main(cfg: ParallelRetargetingConfig) -> None:
    run_parallel_retarget(cfg)
```

Keep compatibility re-exports only if existing tests or old imports need them.

**Step 5: Re-run focused tests**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_module_entrypoints.py tests/test_batch_retarget_script_optitrack.py tests/test_quantitative_eval_script.py -q
```

Expected: PASS.

**Step 6: Commit**

```bash
git add src/holosoma_retargeting/pipelines/parallel.py src/holosoma_retargeting/examples/parallel_robot_retarget.py src/holosoma_retargeting/cli/parallel_retarget.py tests
git commit -m "refactor: extract parallel retarget pipeline"
```

### Task 7: Move shell wrappers to the new CLI modules

**Files:**
- Modify: `scripts/retargeting/retarget_single_clip.sh`
- Modify: `scripts/retargeting/retarget_batch_clips.sh`
- Modify: `scripts/retargeting/eval.sh`
- Modify: `scripts/retargeting/replay_viser.sh`
- Modify: any conversion wrapper that directly calls `data_conversion/convert_data_format_mj.py`
- Modify: `README.md`
- Modify: `src/holosoma_retargeting/README.md`

**Step 1: Write or update script tests**

Update existing script tests so they assert wrappers call module entrypoints:

Expected patterns:

- `uv run python -m holosoma_retargeting.cli.retarget`
- `uv run python -m holosoma_retargeting.cli.parallel_retarget`
- `uv run python -m holosoma_retargeting.cli.evaluate`
- `uv run python -m holosoma_retargeting.cli.replay`

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_adam_pro_cli_smoke.py tests/test_batch_retarget_script_optitrack.py tests/test_quantitative_eval_script.py -q
```

Expected: FAIL until scripts are updated.

**Step 2: Update shell wrappers**

Change Python invocations from file paths to module invocations.

Examples:

```bash
uv run python -m holosoma_retargeting.cli.retarget \
```

```bash
uv run python -m holosoma_retargeting.cli.parallel_retarget \
```

```bash
uv run python -m holosoma_retargeting.cli.evaluate \
```

```bash
uv run python -m holosoma_retargeting.cli.replay \
```

Do not change script names or their user-facing flags.

If a wrapper still needs package-relative asset paths, keep the existing `cd "${REPO_ROOT}/src/holosoma_retargeting"` behavior for this phase. Removing CWD assumptions is a later phase.

**Step 3: Update README references**

Replace direct examples path references with the new module paths:

- `examples/robot_retarget.py` -> `python -m holosoma_retargeting.cli.retarget`
- `examples/parallel_robot_retarget.py` -> `python -m holosoma_retargeting.cli.parallel_retarget`
- `evaluation/eval_retargeting.py` -> `python -m holosoma_retargeting.cli.evaluate`
- `data_conversion/convert_data_format_mj.py` -> `python -m holosoma_retargeting.cli.convert_mj`
- `viser_player.py` -> `python -m holosoma_retargeting.cli.replay`

**Step 4: Re-run script tests**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_adam_pro_cli_smoke.py tests/test_batch_retarget_script_optitrack.py tests/test_quantitative_eval_script.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add scripts README.md src/holosoma_retargeting/README.md tests
git commit -m "refactor: route shell wrappers through cli modules"
```

### Task 8: Final verification and push

**Files:**
- Review: `src/holosoma_retargeting/cli/`
- Review: `src/holosoma_retargeting/pipelines/`
- Review: `src/holosoma_retargeting/examples/`
- Review: `README.md`
- Review: `scripts/retargeting/`

**Step 1: Check stale import patterns**

```bash
rg -n "holosoma_retargeting\\.examples|examples/robot_retarget|examples/parallel_robot_retarget" src tests scripts README.md docs
```

Expected:

- `examples/` compatibility wrappers may remain.
- Tests may intentionally mention compatibility imports.
- Scripts and README should prefer `holosoma_retargeting.cli.*`.

**Step 2: Run focused import and boundary tests**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_module_entrypoints.py tests/test_repo_doc_boundaries.py -q
```

Expected: PASS.

**Step 3: Run smoke suite**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 UV_CACHE_DIR=/tmp/uv-cache bash scripts/test_smoke.sh
```

Expected: PASS.

**Step 4: Run build verification**

```bash
UV_CACHE_DIR=/tmp/uv-cache uv build
```

Expected: PASS.

**Step 5: Commit final doc or test cleanup if needed**

Only commit if Step 1-4 required cleanup:

```bash
git add <changed-files>
git commit -m "test: verify cli pipelines refactor"
```

**Step 6: Push the `refactor` branch**

```bash
git push origin refactor
```

Expected: remote `refactor` branch updated.
