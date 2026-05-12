# OmniRetarget Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract `holosoma/src/omniretarget` into a standalone repository named `omniretarget` that runs independently of the training and inference components, while preserving current retargeting behavior before any cleanup or redesign.

**Architecture:** Start with a mechanical extraction instead of a redesign. Create a new repo with the same internal package layout, copy only the retargeting package, its scripts, and its required assets, then make the smallest set of path, packaging, and docs fixes required for the copied repo to install and run by itself. Defer API cleanup, CLI polish, and asset slimming to later follow-up changes.

**Tech Stack:** Python 3.11, uv, setuptools, pytest, tyro, mujoco, trimesh, yourdfpy, jinja2, shell entrypoint scripts

**Repository Root:** `/home/humanoid/Projects/Junsong_WU/ADAM/omni/omniretarget`

**Source Blueprint:** `/home/humanoid/Projects/Junsong_WU/ADAM/omni/holosoma`

**Constraint:** Treat `holosoma/` as read-only reference material. Do not modify files under `holosoma/`; copy required logic, scripts, assets, or tests into `omniretarget/` and edit only the copied versions.

**Environment Policy:** Use `uv` as the only supported Python environment workflow in `omniretarget`. Do not carry over conda-based `setup` / `source` environment scripts into the new repository except as reference material in the migration notes.

**Path Convention:** In file lists below, `omniretarget/...` means a path relative to this repository root. In commands, replace `/path/to/omniretarget` with `/home/humanoid/Projects/Junsong_WU/ADAM/omni/omniretarget`.

---

### Task 1: Freeze the extraction scope

**Files:**
- Review: `holosoma/src/omniretarget/`
- Review: `holosoma/scripts/setup_retargeting.sh`
- Review: `holosoma/scripts/source_retargeting_setup.sh`
- Review: `holosoma/scripts/retargeting/`
- Review: `holosoma/demo_scripts/demo_omomo_wb_tracking.sh`
- Review: `holosoma/demo_scripts/demo_lafan_wb_tracking.sh`
- Create: `omniretarget/MIGRATION_SCOPE.md`

**Step 1: Write the scope note**

```markdown
# OmniRetarget Migration Scope

Included:
- Python package from `src/omniretarget/`
- Retargeting shell entrypoints
- Required models and demo assets referenced by retargeting code/tests
- Retargeting tests
- uv-based project metadata and lockfile

Excluded:
- `src/holosoma/`
- `src/holosoma_inference/`
- conda-based `setup_retargeting.sh` / `source_retargeting_setup.sh`
- whole-body-tracking demo scripts that call training code
- monorepo Docker integration unless required to run retargeting itself
```

**Step 2: Verify the current dependency boundary**

Run:

```bash
cd /home/humanoid/Projects/Junsong_WU/ADAM/omni
rg -n "from omniretarget|import omniretarget" holosoma/src/holosoma holosoma/src/holosoma_inference
```

Expected: no output

**Step 3: Save the scope note**

Write `omniretarget/MIGRATION_SCOPE.md` with the exact included/excluded lists above.

**Step 4: Commit**

```bash
cd /path/to/omniretarget
git add MIGRATION_SCOPE.md
git commit -m "docs: define omniretarget migration scope"
```

### Task 2: Bootstrap the new repository skeleton

**Files:**
- Create: `omniretarget/.gitignore`
- Create: `omniretarget/.python-version`
- Create: `omniretarget/README.md`
- Create: `omniretarget/pyproject.toml`
- Create: `omniretarget/setup.py`
- Create: `omniretarget/scripts/retargeting/`
- Create: `omniretarget/src/omniretarget/`
- Create: `omniretarget/tests/`

**Step 1: Create the directory tree**

Run:

```bash
mkdir -p /path/to/omniretarget/{scripts/retargeting,src/omniretarget,tests}
```

Expected: directories created with no errors

**Step 2: Copy the package root files**

Run:

```bash
cp /home/humanoid/Projects/Junsong_WU/ADAM/omni/holosoma/src/omniretarget/pyproject.toml /path/to/omniretarget/pyproject.toml
cp /home/humanoid/Projects/Junsong_WU/ADAM/omni/holosoma/src/omniretarget/setup.py /path/to/omniretarget/setup.py
```

Expected: both files exist in the new repo

**Step 3: Copy the package source and tests**

Run:

```bash
cp -R /home/humanoid/Projects/Junsong_WU/ADAM/omni/holosoma/src/omniretarget/omniretarget /path/to/omniretarget/src/
cp -R /home/humanoid/Projects/Junsong_WU/ADAM/omni/holosoma/src/omniretarget/tests /path/to/omniretarget/
```

Expected: `src/omniretarget/` and `tests/` exist in the new repo

**Step 4: Copy only the retargeting entrypoint scripts**

Run:

```bash
cp -R /home/humanoid/Projects/Junsong_WU/ADAM/omni/holosoma/scripts/retargeting/* /path/to/omniretarget/scripts/retargeting/
```

Expected: the copied scripts are present under `omniretarget/scripts`

**Step 5: Pin the project Python version for uv**

Run:

```bash
cd /path/to/omniretarget
uv python pin 3.11
```

Expected: `.python-version` exists and contains `3.11`

**Step 6: Add a placeholder root README**

```markdown
# OmniRetarget

Standalone motion-retargeting repository extracted from Holosoma.

Current phase: bootstrap extraction preserving existing behavior.

Environment setup:

```bash
uv sync
```
```

**Step 7: Commit**

```bash
cd /path/to/omniretarget
git add .
git commit -m "chore: bootstrap omniretarget from omniretarget"
```

### Task 3: Adopt uv as the only environment workflow

**Files:**
- Modify: `omniretarget/pyproject.toml`
- Modify: `omniretarget/README.md`
- Create: `omniretarget/uv.lock`
- Modify: `omniretarget/scripts/retargeting/retarget_single_clip.sh`
- Modify: `omniretarget/scripts/retargeting/retarget_batch_clips.sh`
- Modify: `omniretarget/scripts/retargeting/retarget_bridge.sh`
- Modify: `omniretarget/scripts/retargeting/replay_viser.sh`
- Modify: `omniretarget/scripts/retargeting/eval.sh`
- Modify: `omniretarget/scripts/retargeting/convert_lafan_bvh_to_npy.sh`
- Modify: `omniretarget/scripts/retargeting/convert_amass_smplx_to_npz.sh`
- Modify: `omniretarget/scripts/retargeting/convert_optitrack_pkl_to_npz.sh`

**Step 1: Convert development dependencies to uv-friendly dependency groups**

Replace the old optional dev extra with a dependency group so plain `uv sync` installs test and lint tooling.

Preferred target:

```toml
[dependency-groups]
dev = ["mypy", "ruff", "pytest"]
```

**Step 2: Sync the environment with uv**

Run:

```bash
cd /path/to/omniretarget
uv sync
```

Expected: `.venv/` and `uv.lock` are created successfully

**Step 3: Verify the package imports through the uv-managed environment**

Run:

```bash
cd /path/to/omniretarget
uv run python -c "import omniretarget; print(omniretarget.__file__)"
```

Expected: prints a path under `/path/to/omniretarget/src/omniretarget`

**Step 4: Remove conda bootstrap assumptions from shell entrypoints**

Delete patterns like:

```bash
source "${REPO_ROOT}/scripts/source_retargeting_setup.sh"
```

and execute Python through `uv run`, for example:

```bash
uv run python examples/robot_retarget.py ...
```

**Step 5: Update shell entrypoints to the new source root**

Replace:

```bash
cd "${REPO_ROOT}/src/omniretarget/omniretarget"
```

With:

```bash
cd "${REPO_ROOT}/src/omniretarget"
```

**Step 6: Remove monorepo-specific absolute paths**

Search for hard-coded paths under `scripts/retargeting/` and replace them with repo-relative or argument-driven values.

Run:

```bash
cd /path/to/omniretarget
rg -n "/home/humanoid|adam_reference|src/omniretarget" scripts
```

Expected: no matches after edits

**Step 7: Verify there are no conda-era environment hooks left**

Run:

```bash
cd /path/to/omniretarget
rg -n "conda|mamba|source_retargeting|setup_retargeting|pip install -e" .
```

Expected: no matches, other than migration notes that explicitly describe the old approach

**Step 8: Run a smoke check on the scripts**

Run:

```bash
cd /path/to/omniretarget
for f in scripts/retargeting/*.sh; do bash -n "$f"; done
```

Expected: no syntax errors

**Step 9: Commit**

```bash
cd /path/to/omniretarget
git add pyproject.toml README.md uv.lock scripts
git commit -m "build: adopt uv workflow for omniretarget"
```

### Task 4: Fix packaging metadata so the repo installs cleanly

**Files:**
- Modify: `omniretarget/pyproject.toml`
- Modify: `omniretarget/setup.py`
- Create: `omniretarget/MANIFEST.in`
- Create: `omniretarget/src/omniretarget/README.md` if missing after copy

**Step 1: Make the readme path valid**

Ensure `pyproject.toml` points at a file that exists in the new repo root. Preferred change:

```toml
readme = "README.md"
```

with `/path/to/omniretarget/README.md` present.

**Step 2: Include non-Python package data**

Add one packaging mechanism, not both. Recommended `MANIFEST.in`:

```text
recursive-include src/omniretarget/models *
recursive-include src/omniretarget/demo_data *
recursive-include src/omniretarget *.md
recursive-include src/omniretarget *.jinja
```

**Step 3: Make setuptools discover the copied package correctly**

If needed, update `setup.py` to use:

```python
from setuptools import find_packages, setup

setup(
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
)
```

**Step 4: Verify the project installs and runs through uv**

Run:

```bash
cd /path/to/omniretarget
uv sync
uv run python -c "import omniretarget; print(omniretarget.__file__)"
```

Expected: install succeeds and prints a path under `/path/to/omniretarget/src/omniretarget`

**Step 5: Commit**

```bash
cd /path/to/omniretarget
git add pyproject.toml setup.py MANIFEST.in README.md src/omniretarget/README.md
git commit -m "build: package omniretarget as a standalone project"
```

### Task 5: Replace CWD-sensitive resource access with package-relative access

**Files:**
- Modify: `omniretarget/src/omniretarget/src/utils.py`
- Modify: `omniretarget/src/omniretarget/config_types/robot.py`
- Modify: `omniretarget/src/omniretarget/config_types/viser.py`
- Modify: `omniretarget/src/omniretarget/examples/robot_retarget.py`
- Modify: `omniretarget/src/omniretarget/examples/parallel_robot_retarget.py`
- Modify: `omniretarget/src/omniretarget/data_conversion/convert_data_format_mj.py`
- Modify: `omniretarget/src/omniretarget/evaluation/eval_retargeting.py`
- Create: `omniretarget/src/omniretarget/path_utils.py`
- Test: `omniretarget/tests/test_package_paths.py`

**Step 1: Write the failing path test**

```python
from omniretarget.path_utils import package_path


def test_package_path_resolves_height_dict() -> None:
    path = package_path("demo_data/height_dict.pkl")
    assert path.exists()


def test_package_path_resolves_robot_urdf() -> None:
    path = package_path("models/g1/g1_29dof.urdf")
    assert path.exists()
```

**Step 2: Run the new test**

Run:

```bash
cd /path/to/omniretarget
uv run pytest tests/test_package_paths.py -q
```

Expected: FAIL because `path_utils` does not exist yet

**Step 3: Write the minimal resolver**

```python
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent


def package_path(relative_path: str) -> Path:
    return PACKAGE_ROOT / relative_path
```

**Step 4: Replace raw string resource paths**

Use `package_path(...)` where code currently assumes the working directory contains `models/` or `demo_data/`.

Examples to replace:

```python
with open("demo_data/height_dict.pkl", "rb") as f:
```

becomes

```python
with package_path("demo_data/height_dict.pkl").open("rb") as f:
```

and

```python
return f"models/{self.robot_type}/{self.robot_type}_{self.ROBOT_DOF}dof.urdf"
```

becomes a path built from `package_path(...)` or a helper that returns a package-relative asset path.

**Step 5: Re-run the new test and a focused regression set**

Run:

```bash
cd /path/to/omniretarget
uv run pytest tests/test_package_paths.py tests/test_adam_pro_robot_config.py tests/test_adam_pro_xml_urdf_consistency.py -q
```

Expected: PASS

**Step 6: Commit**

```bash
cd /path/to/omniretarget
git add src/omniretarget tests/test_package_paths.py
git commit -m "fix: resolve omniretarget assets independent of cwd"
```

### Task 6: Remove repo-layout import hacks from executable modules

**Files:**
- Modify: `omniretarget/src/omniretarget/examples/robot_retarget.py`
- Modify: `omniretarget/src/omniretarget/examples/parallel_robot_retarget.py`
- Modify: `omniretarget/src/omniretarget/data_conversion/convert_data_format_mj.py`
- Modify: `omniretarget/src/omniretarget/evaluation/eval_retargeting.py`
- Modify: `omniretarget/src/omniretarget/viser_player.py`
- Test: `omniretarget/tests/test_module_entrypoints.py`

**Step 1: Write the failing import test**

```python
import importlib


def test_robot_retarget_module_imports() -> None:
    importlib.import_module("omniretarget.examples.robot_retarget")


def test_eval_module_imports() -> None:
    importlib.import_module("omniretarget.evaluation.eval_retargeting")
```

**Step 2: Run the test**

Run:

```bash
cd /path/to/omniretarget
uv run pytest tests/test_module_entrypoints.py -q
```

Expected: PASS or FAIL depending on remaining path assumptions; if FAIL, the failure must point at the import hack or cwd assumptions

**Step 3: Remove the `sys.path.insert(...)` blocks**

Delete the pattern:

```python
src_root = Path(__file__).resolve().parents[2]
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))
```

from each module once imports work through normal package installation.

**Step 4: Re-run the test**

Run:

```bash
cd /path/to/omniretarget
uv run pytest tests/test_module_entrypoints.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
cd /path/to/omniretarget
git add src/omniretarget tests/test_module_entrypoints.py
git commit -m "refactor: use normal package imports in omniretarget entrypoints"
```

### Task 7: Remove training and inference references from docs and demos

**Files:**
- Modify: `omniretarget/README.md`
- Modify: `omniretarget/src/omniretarget/README.md`
- Delete: `omniretarget/demo_scripts/demo_omomo_wb_tracking.sh` if copied
- Delete: `omniretarget/demo_scripts/demo_lafan_wb_tracking.sh` if copied
- Create: `omniretarget/docs/migration-notes.md`

**Step 1: Rewrite the root README**

Required sections:
- what OmniRetarget is
- supported workflows
- what was intentionally not migrated
- setup with `uv sync`
- single-clip retargeting
- batch retargeting
- data conversion
- evaluation

**Step 2: Remove training/deployment references**

Run:

```bash
cd /path/to/omniretarget
rg -n "whole-body tracking|train_agent|holosoma_inference|src/holosoma/" README.md src/omniretarget/README.md docs scripts
```

Expected: no references that describe training or deployment as in-repo features

**Step 3: Add migration notes**

```markdown
# Migration Notes

OmniRetarget was extracted from Holosoma's retargeting component.

Not included:
- policy training
- real-robot deployment
- shared monorepo demo pipelines that launch training jobs
```

**Step 4: Commit**

```bash
cd /path/to/omniretarget
git add README.md src/omniretarget/README.md docs/migration-notes.md
git commit -m "docs: scope omniretarget to retargeting only"
```

### Task 8: Establish a minimum standalone verification suite

**Files:**
- Modify: `omniretarget/README.md`
- Create: `omniretarget/Makefile` or `omniretarget/scripts/test_smoke.sh`
- Review: `omniretarget/tests/`

**Step 1: Define the minimum supported checks**

Use this exact smoke suite:

```bash
uv run pytest tests/test_adam_pro_robot_config.py -q
uv run pytest tests/test_adam_pro_motion_mappings.py -q
uv run pytest tests/test_adam_pro_data_conversion.py -q
uv run pytest tests/test_optitrack_motion_format.py -q
uv run pytest tests/test_package_paths.py -q
uv run pytest tests/test_module_entrypoints.py -q
```

**Step 2: Add a single test runner**

Example `scripts/test_smoke.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

uv run pytest tests/test_adam_pro_robot_config.py -q
uv run pytest tests/test_adam_pro_motion_mappings.py -q
uv run pytest tests/test_adam_pro_data_conversion.py -q
uv run pytest tests/test_optitrack_motion_format.py -q
uv run pytest tests/test_package_paths.py -q
uv run pytest tests/test_module_entrypoints.py -q
```

**Step 3: Run the smoke suite**

Run:

```bash
cd /path/to/omniretarget
bash scripts/test_smoke.sh
```

Expected: all commands pass

**Step 4: Document the verification command**

Add to `README.md`:

```bash
uv sync
bash scripts/test_smoke.sh
```

**Step 5: Commit**

```bash
cd /path/to/omniretarget
git add README.md scripts/test_smoke.sh
git commit -m "test: add standalone omniretarget smoke suite"
```

### Task 9: Optional size reduction after bootstrap stability

**Files:**
- Review: `omniretarget/src/omniretarget/models/`
- Review: `omniretarget/src/omniretarget/demo_data/`
- Create: `omniretarget/docs/asset-pruning.md`

**Step 1: Measure asset size by robot**

Run:

```bash
cd /path/to/omniretarget
du -sh src/omniretarget/models/*
du -sh src/omniretarget/demo_data/*
```

Expected: size report per robot and demo dataset

**Step 2: Decide retained robot assets**

Document one of these choices in `docs/asset-pruning.md`:
- keep all robots for compatibility
- keep only the robots actually used
- move unused robots to a separate asset repo or release archive

**Step 3: Only after the decision, prune unused assets**

Run only if approved:

```bash
rm -rf src/omniretarget/models/<unused_robot>
rm -rf src/omniretarget/demo_data/<unused_dataset>
```

Expected: repository size decreases with no missing assets for supported workflows

**Step 4: Re-run the smoke suite**

Run:

```bash
cd /path/to/omniretarget
bash scripts/test_smoke.sh
```

Expected: all supported workflows still pass

**Step 5: Commit**

```bash
cd /path/to/omniretarget
git add docs/asset-pruning.md src/omniretarget
git commit -m "chore: prune unused omniretarget assets"
```
