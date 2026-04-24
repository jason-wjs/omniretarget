# OmniRetarget Refactor Phase Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Execute the OmniRetarget architecture refactor in small behavior-preserving phases based on `docs/plans/2026-04-24-omniretarget-refactor-overview.md`.

**Architecture:** Refactor from the outside inward. First lock down repository and documentation boundaries, then formalize CLI command locations, then centralize typed config/runtime resolution, then split profiles, retargeter code, and reusable utilities. Avoid `pipelines/`, Hydra, top-level `io/`, and broad rewrites.

**Tech Stack:** Python 3.11, uv, setuptools, pytest, Tyro, dataclasses, MuJoCo, Viser, Markdown docs

---

## Execution Rules

- Work only in `/home/humanoid/Projects/Junsong_WU/ADAM/omni/omniretarget-refactor-next`.
- Treat `/home/humanoid/Projects/Junsong_WU/ADAM/omni/holosoma` as read-only reference material.
- Keep `models/` and `demo_data/` stable unless a phase explicitly says otherwise.
- Preserve old import paths with compatibility wrappers until a phase explicitly removes them.
- Do not introduce Hydra, `pipelines/`, top-level `io/`, plugin systems, or base pipeline classes.
- Do not move algorithm internals before CLI/config/profile boundaries are stable.
- Prefer one commit per task or per tightly related group of files.
- Use `.venv/bin/python -m pytest` after `uv sync` so `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` does not need to wrap the snap-provided `uv` command.

## Phase Gates

Every phase must finish with:

```bash
git status --short
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q <phase-specific tests>
```

If `.venv/` does not exist yet, run:

```bash
uv sync
```

Expected: environment sync completes and `.venv/bin/python` exists.

Do not proceed to the next phase until the current phase-specific tests pass or the failure is documented as unrelated infrastructure breakage.

### Task 1: Phase 0 - Commit Architecture Planning Baseline

**Files:**
- Review: `docs/plans/2026-04-24-omniretarget-refactor-overview.md`
- Create: `docs/plans/2026-04-24-omniretarget-refactor-phase-plan.md`

**Intent:** Freeze the agreed architecture direction before moving code.

**Allowed changes:**
- Documentation only.

**Forbidden changes:**
- No source moves.
- No import changes.
- No test rewrites except typo fixes in the plan itself.

**Step 1: Review the overview for the agreed architecture decisions**

Check that the overview states:

- `dataclass` + Tyro stays as the config mechanism.
- `configs/` and `profiles/` replace the long-term `config_types/` / `config_values/` split.
- `cli/` owns formal command modules.
- `cli/data_process/` owns data preprocessing and conversion command modules.
- `pipelines/`, Hydra, top-level `io/`, and heavyweight asset resolver abstractions are deferred or avoided.
- The repository has one root README.

**Step 2: Review this phase plan**

Check that every phase has:

- files or file groups to touch;
- allowed and forbidden changes;
- test commands;
- a commit point.

**Step 3: Run documentation-only sanity checks**

Run:

```bash
grep -n 'Hydra should\|cfg/\|Keep workflow orchestration in `pipelines`\|Configuration is composed through Hydra' docs/plans/2026-04-24-omniretarget-refactor-overview.md
```

Expected: no output.

Run:

```bash
grep -n 'cli/data_process/\|A separate `pipelines/` package is intentionally avoided\|Hydra is intentionally not part' docs/plans/2026-04-24-omniretarget-refactor-overview.md
```

Expected: output showing those agreed decisions.

**Step 4: Commit the planning baseline**

Run:

```bash
git add docs/plans/2026-04-24-omniretarget-refactor-overview.md docs/plans/2026-04-24-omniretarget-refactor-phase-plan.md
git commit -m "docs: define omniretarget refactor phases"
```

### Task 2: Phase 1 - Repository and Documentation Boundaries

**Files:**
- Modify: `README.md`
- Modify: `docs/`
- Modify: `tests/test_repo_doc_boundaries.py`
- Delete or migrate: `src/holosoma_retargeting/README.md`

**Intent:** Make repository documentation ownership match the target architecture before moving Python modules.

**Allowed changes:**
- Move useful package README content to root `README.md` or focused docs under `docs/`.
- Delete `src/holosoma_retargeting/README.md` after content is migrated or confirmed obsolete.
- Strengthen repository-boundary tests.

**Forbidden changes:**
- No Python source moves.
- No CLI entrypoint changes.
- No package data layout changes.

**Step 1: Write or extend the failing boundary test**

Modify `tests/test_repo_doc_boundaries.py` to add:

```python

def test_package_root_does_not_keep_readme() -> None:
    assert not (PACKAGE_ROOT / "README.md").exists()
```

**Step 2: Run the focused test to verify it fails**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_repo_doc_boundaries.py::test_package_root_does_not_keep_readme
```

Expected: FAIL because `src/holosoma_retargeting/README.md` exists.

**Step 3: Migrate or delete package README content**

Move still-useful command examples and usage notes from `src/holosoma_retargeting/README.md` into one of:

- `README.md`
- `docs/usage.md`
- an existing focused doc under `docs/`

Delete `src/holosoma_retargeting/README.md`.

**Step 4: Re-run documentation boundary tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_repo_doc_boundaries.py
```

Expected: PASS.

**Step 5: Commit**

Run:

```bash
git add README.md docs tests/test_repo_doc_boundaries.py
git rm src/holosoma_retargeting/README.md
git commit -m "docs: keep project readme at repository root"
```

### Task 3: Phase 2 - Formal CLI Command Modules with Compatibility Wrappers

**Files:**
- Create: `src/holosoma_retargeting/cli/__init__.py`
- Create: `src/holosoma_retargeting/cli/robot_retarget.py`
- Create: `src/holosoma_retargeting/cli/parallel_robot_retarget.py`
- Create: `src/holosoma_retargeting/cli/eval_retargeting.py`
- Create: `src/holosoma_retargeting/cli/viser_player.py`
- Modify: `src/holosoma_retargeting/examples/robot_retarget.py`
- Modify: `src/holosoma_retargeting/examples/parallel_robot_retarget.py`
- Modify: `src/holosoma_retargeting/evaluation/eval_retargeting.py`
- Modify: `src/holosoma_retargeting/viser_player.py`
- Modify: `tests/test_module_entrypoints.py`

**Intent:** Introduce the target `cli/` command surface without breaking old import paths.

**Allowed changes:**
- Move command implementation modules into `cli/`.
- Leave old modules as thin compatibility wrappers that re-export from `cli/`.
- Update tests to import both new and old module paths.

**Forbidden changes:**
- No behavior changes inside command workflows.
- No retargeter algorithm moves.
- No config/profile restructuring.
- No shell script rewrites except import-path-only updates if required by tests.

**Step 1: Add failing import tests for new CLI modules**

Modify `tests/test_module_entrypoints.py` to include:

```python
        (
            "holosoma_retargeting.cli.robot_retarget",
            [
                "holosoma_retargeting.cli.robot_retarget",
                "holosoma_retargeting.src.interaction_mesh_retargeter",
            ],
        ),
        (
            "holosoma_retargeting.cli.parallel_robot_retarget",
            [
                "holosoma_retargeting.cli.parallel_robot_retarget",
                "holosoma_retargeting.cli.robot_retarget",
                "holosoma_retargeting.src.interaction_mesh_retargeter",
            ],
        ),
        (
            "holosoma_retargeting.cli.eval_retargeting",
            ["holosoma_retargeting.cli.eval_retargeting"],
        ),
        (
            "holosoma_retargeting.cli.viser_player",
            ["holosoma_retargeting.cli.viser_player"],
        ),
```

**Step 2: Run the import test to verify it fails**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_module_entrypoints.py
```

Expected: FAIL because `holosoma_retargeting.cli.*` modules do not exist.

**Step 3: Move command modules into `cli/`**

Move implementations:

- `src/holosoma_retargeting/examples/robot_retarget.py` -> `src/holosoma_retargeting/cli/robot_retarget.py`
- `src/holosoma_retargeting/examples/parallel_robot_retarget.py` -> `src/holosoma_retargeting/cli/parallel_robot_retarget.py`
- `src/holosoma_retargeting/evaluation/eval_retargeting.py` -> `src/holosoma_retargeting/cli/eval_retargeting.py`
- `src/holosoma_retargeting/viser_player.py` -> `src/holosoma_retargeting/cli/viser_player.py`

Update imports inside moved files from old command paths to new command paths. For example:

```python
from holosoma_retargeting.cli.robot_retarget import (
    DEFAULT_DATA_FORMATS,
    build_retargeter_kwargs_from_config,
    create_task_constants,
    initialize_robot_pose,
    load_motion_data,
    setup_object_data,
)
```

**Step 4: Replace old files with compatibility wrappers**

`src/holosoma_retargeting/examples/robot_retarget.py`:

```python
from holosoma_retargeting.cli.robot_retarget import *  # noqa: F401,F403


if __name__ == "__main__":
    import tyro

    from holosoma_retargeting.config_types.retargeting import RetargetingConfig
    from holosoma_retargeting.cli.robot_retarget import main

    main(tyro.cli(RetargetingConfig))
```

Use the same wrapper pattern for:

- `src/holosoma_retargeting/examples/parallel_robot_retarget.py`
- `src/holosoma_retargeting/evaluation/eval_retargeting.py`
- `src/holosoma_retargeting/viser_player.py`

Use each command's existing config class in its wrapper:

- `ParallelRetargetingConfig` for `parallel_robot_retarget.py`
- `Args` for `eval_retargeting.py`
- `ViserConfig` for `viser_player.py`

**Step 5: Re-run import tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_module_entrypoints.py
```

Expected: PASS.

**Step 6: Run focused command smoke tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_adam_pro_cli_smoke.py tests/test_batch_retarget_script_optitrack.py tests/test_quantitative_eval_script.py
```

Expected: PASS or only known environment-related skips.

**Step 7: Commit**

Run:

```bash
git add src/holosoma_retargeting/cli src/holosoma_retargeting/examples src/holosoma_retargeting/evaluation src/holosoma_retargeting/viser_player.py tests/test_module_entrypoints.py
git commit -m "refactor: move executable workflows into cli modules"
```

### Task 4: Phase 3 - Data Processing CLI Modules

**Files:**
- Create: `src/holosoma_retargeting/cli/data_process/__init__.py`
- Create: `src/holosoma_retargeting/cli/data_process/convert_data_format_mj.py`
- Create: `src/holosoma_retargeting/cli/data_process/prep_amass_smplx_for_rt.py`
- Create: `src/holosoma_retargeting/cli/data_process/prep_optitrack_for_rt.py`
- Create: `src/holosoma_retargeting/cli/data_process/extract_global_positions.py`
- Modify: `src/holosoma_retargeting/data_conversion/convert_data_format_mj.py`
- Modify: `src/holosoma_retargeting/data_utils/prep_amass_smplx_for_rt.py`
- Modify: `src/holosoma_retargeting/data_utils/prep_optitrack_for_rt.py`
- Modify: `src/holosoma_retargeting/data_utils/extract_global_positions.py`
- Modify: `tests/test_module_entrypoints.py`

**Intent:** Group executable data preparation and conversion commands under `cli/data_process/` while preserving legacy imports.

**Allowed changes:**
- Move command implementation modules into `cli/data_process/`.
- Leave old modules as compatibility wrappers.
- Update shell scripts only if needed to point to new module paths.

**Forbidden changes:**
- No changes to conversion algorithms.
- No format adapter package.
- No broad utility extraction yet.

**Step 1: Add failing import tests for new data-process modules**

Modify `tests/test_module_entrypoints.py` to include:

```python
        (
            "holosoma_retargeting.cli.data_process.convert_data_format_mj",
            ["holosoma_retargeting.cli.data_process.convert_data_format_mj"],
        ),
        (
            "holosoma_retargeting.cli.data_process.prep_amass_smplx_for_rt",
            ["holosoma_retargeting.cli.data_process.prep_amass_smplx_for_rt"],
        ),
        (
            "holosoma_retargeting.cli.data_process.prep_optitrack_for_rt",
            ["holosoma_retargeting.cli.data_process.prep_optitrack_for_rt"],
        ),
        (
            "holosoma_retargeting.cli.data_process.extract_global_positions",
            ["holosoma_retargeting.cli.data_process.extract_global_positions"],
        ),
```

**Step 2: Run the import test to verify it fails**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_module_entrypoints.py
```

Expected: FAIL because the new data-process modules do not exist.

**Step 3: Move implementations and add wrappers**

Move:

- `src/holosoma_retargeting/data_conversion/convert_data_format_mj.py` -> `src/holosoma_retargeting/cli/data_process/convert_data_format_mj.py`
- `src/holosoma_retargeting/data_utils/prep_amass_smplx_for_rt.py` -> `src/holosoma_retargeting/cli/data_process/prep_amass_smplx_for_rt.py`
- `src/holosoma_retargeting/data_utils/prep_optitrack_for_rt.py` -> `src/holosoma_retargeting/cli/data_process/prep_optitrack_for_rt.py`
- `src/holosoma_retargeting/data_utils/extract_global_positions.py` -> `src/holosoma_retargeting/cli/data_process/extract_global_positions.py`

Replace old files with wrappers using the same pattern as Phase 2.

**Step 4: Re-run import tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_module_entrypoints.py
```

Expected: PASS.

**Step 5: Run data-processing focused tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_adam_pro_data_conversion.py tests/test_optitrack_converter_script.py tests/test_convert_amass_script.py tests/test_lafan_bvh_to_npy_script.py tests/test_prep_amass_smplx_gender_handling.py tests/test_optitrack_pkl_to_npz_converter.py tests/test_optitrack_grounding_preprocess.py
```

Expected: PASS.

**Step 6: Commit**

Run:

```bash
git add src/holosoma_retargeting/cli src/holosoma_retargeting/data_conversion src/holosoma_retargeting/data_utils tests/test_module_entrypoints.py
git commit -m "refactor: move data processing commands under cli"
```

### Task 5: Phase 4 - Centralize Config Runtime Resolution

**Files:**
- Create: `src/holosoma_retargeting/configs/__init__.py`
- Create: `src/holosoma_retargeting/configs/runtime.py`
- Create or move later: `src/holosoma_retargeting/configs/retargeting.py`
- Modify: `src/holosoma_retargeting/cli/robot_retarget.py`
- Modify: `src/holosoma_retargeting/cli/parallel_robot_retarget.py`
- Modify: `src/holosoma_retargeting/cli/eval_retargeting.py`
- Modify: `src/holosoma_retargeting/cli/data_process/convert_data_format_mj.py`
- Test: `tests/test_adam_pro_robot_config.py`
- Test: `tests/test_adam_pro_motion_mappings.py`
- Test: `tests/test_optitrack_motion_format.py`
- Test: `tests/test_eval_contact_joint_defaults.py`

**Intent:** Remove repeated config synchronization from command modules without changing the public Tyro config model.

**Allowed changes:**
- Add `configs/runtime.py`.
- Centralize repeated logic such as `robot` vs `robot_config.robot_type` and `data_format` vs `motion_data_config.data_format`.
- Keep existing `config_types/` import paths alive.

**Forbidden changes:**
- No Hydra.
- No YAML config root.
- No wholesale rename of `config_types/` in this phase.
- No robot/motion profile extraction yet unless needed for a small helper.

**Step 1: Add focused tests for runtime resolution**

Create `tests/test_config_runtime_resolution.py`:

```python
from holosoma_retargeting.config_types.retargeting import RetargetingConfig
from holosoma_retargeting.configs.runtime import resolve_retargeting_config


def test_resolve_retargeting_config_syncs_robot_and_motion_format() -> None:
    cfg = RetargetingConfig(robot="adam_pro", data_format="optitrack", task_type="robot_only")

    resolved = resolve_retargeting_config(cfg)

    assert resolved.robot_config.robot_type == "adam_pro"
    assert resolved.motion_data_config.robot_type == "adam_pro"
    assert resolved.motion_data_config.data_format == "optitrack"
```

**Step 2: Run the new test to verify it fails**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_config_runtime_resolution.py
```

Expected: FAIL because `holosoma_retargeting.configs.runtime` does not exist.

**Step 3: Implement minimal runtime resolution**

Create `src/holosoma_retargeting/configs/runtime.py` with helpers that return resolved config objects without changing behavior.

Minimum expected API:

```python
from __future__ import annotations

from dataclasses import replace

from holosoma_retargeting.config_types.data_type import MotionDataConfig
from holosoma_retargeting.config_types.retargeting import RetargetingConfig
from holosoma_retargeting.config_types.robot import RobotConfig


def resolve_retargeting_config(cfg: RetargetingConfig) -> RetargetingConfig:
    data_format = cfg.data_format
    if data_format is None:
        return cfg

    robot_config = cfg.robot_config
    if robot_config.robot_type != cfg.robot:
        robot_config = RobotConfig(robot_type=cfg.robot)

    motion_data_config = cfg.motion_data_config
    if motion_data_config.robot_type != cfg.robot or motion_data_config.data_format != data_format:
        motion_data_config = MotionDataConfig(data_format=data_format, robot_type=cfg.robot)

    return replace(cfg, robot_config=robot_config, motion_data_config=motion_data_config)
```

Adjust implementation if existing behavior needs task-specific default data format before resolution.

**Step 4: Use the helper in command modules**

Replace repeated config synchronization blocks in command modules with calls to runtime helpers.

**Step 5: Run config-focused tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_config_runtime_resolution.py tests/test_adam_pro_robot_config.py tests/test_adam_pro_motion_mappings.py tests/test_optitrack_motion_format.py tests/test_eval_contact_joint_defaults.py
```

Expected: PASS.

**Step 6: Commit**

Run:

```bash
git add src/holosoma_retargeting/configs src/holosoma_retargeting/cli tests/test_config_runtime_resolution.py
git commit -m "refactor: centralize runtime config resolution"
```

### Task 6: Phase 5 - Split Built-in Profiles from Config Schema

**Files:**
- Create: `src/holosoma_retargeting/profiles/__init__.py`
- Create: `src/holosoma_retargeting/profiles/robots.py`
- Create: `src/holosoma_retargeting/profiles/motions.py`
- Create: `src/holosoma_retargeting/profiles/mappings.py`
- Modify: `src/holosoma_retargeting/config_types/robot.py`
- Modify: `src/holosoma_retargeting/config_types/data_type.py`
- Test: `tests/test_adam_pro_robot_config.py`
- Test: `tests/test_adam_pro_motion_mappings.py`
- Test: `tests/test_optitrack_motion_format.py`

**Intent:** Move built-in robot and motion defaults out of config schema modules while preserving public config classes.

**Allowed changes:**
- Move dictionaries and lists, not behavior.
- Leave `RobotConfig` and `MotionDataConfig` in `config_types/` for compatibility.
- Re-export profile constants if tests or docs still refer to old names.

**Forbidden changes:**
- No config class rename.
- No CLI behavior changes.
- No motion adapter package.

**Step 1: Add profile import tests**

Create `tests/test_profiles.py`:

```python
from holosoma_retargeting.profiles.mappings import JOINTS_MAPPINGS
from holosoma_retargeting.profiles.motions import DEMO_JOINTS_REGISTRY
from holosoma_retargeting.profiles.robots import ROBOT_DEFAULTS


def test_profiles_expose_existing_robot_and_motion_defaults() -> None:
    assert "adam_pro" in ROBOT_DEFAULTS
    assert "optitrack" in DEMO_JOINTS_REGISTRY
    assert ("optitrack", "adam_pro") in JOINTS_MAPPINGS
```

**Step 2: Run the test to verify it fails**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_profiles.py
```

Expected: FAIL because `profiles/` does not exist.

**Step 3: Move constants into profile modules**

Move:

- `_ROBOT_DEFAULTS` from `config_types/robot.py` to `profiles/robots.py` as `ROBOT_DEFAULTS`
- demo joint lists and `DEMO_JOINTS_REGISTRY` from `config_types/data_type.py` to `profiles/motions.py`
- `JOINTS_MAPPINGS` from `config_types/data_type.py` to `profiles/mappings.py`

Keep compatibility aliases in old modules where needed:

```python
from holosoma_retargeting.profiles.robots import ROBOT_DEFAULTS as _ROBOT_DEFAULTS
```

**Step 4: Re-run profile and config tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_profiles.py tests/test_adam_pro_robot_config.py tests/test_adam_pro_motion_mappings.py tests/test_optitrack_motion_format.py
```

Expected: PASS.

**Step 5: Commit**

Run:

```bash
git add src/holosoma_retargeting/profiles src/holosoma_retargeting/config_types tests/test_profiles.py
git commit -m "refactor: move built-in defaults into profiles"
```

### Task 7: Phase 6 - Move Retargeter Module with Legacy Shim

**Files:**
- Create: `src/holosoma_retargeting/retargeter/__init__.py`
- Create: `src/holosoma_retargeting/retargeter/interaction_mesh_retargeter.py`
- Modify: `src/holosoma_retargeting/src/interaction_mesh_retargeter.py`
- Modify: imports in `src/holosoma_retargeting/cli/`
- Modify: `tests/test_module_entrypoints.py`

**Intent:** Remove the most important algorithm module from the package-internal `src/` namespace without changing its interface.

**Allowed changes:**
- Move `InteractionMeshRetargeter` implementation into `retargeter/`.
- Leave `holosoma_retargeting.src.interaction_mesh_retargeter` as a wrapper.
- Update command imports to new path.

**Forbidden changes:**
- No algorithm decomposition.
- No solver behavior changes.
- No utility splitting in the same commit.

**Step 1: Add new retargeter import test**

Create `tests/test_retargeter_imports.py`:

```python
from holosoma_retargeting.retargeter.interaction_mesh_retargeter import InteractionMeshRetargeter
from holosoma_retargeting.src.interaction_mesh_retargeter import InteractionMeshRetargeter as LegacyRetargeter


def test_retargeter_new_and_legacy_imports_resolve_same_class() -> None:
    assert InteractionMeshRetargeter is LegacyRetargeter
```

**Step 2: Run the test to verify it fails**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_retargeter_imports.py
```

Expected: FAIL because `holosoma_retargeting.retargeter` does not exist.

**Step 3: Move implementation and add legacy wrapper**

Move:

- `src/holosoma_retargeting/src/interaction_mesh_retargeter.py` -> `src/holosoma_retargeting/retargeter/interaction_mesh_retargeter.py`

Replace old file with:

```python
from holosoma_retargeting.retargeter.interaction_mesh_retargeter import *  # noqa: F401,F403
```

**Step 4: Update command imports**

Change command modules to import:

```python
from holosoma_retargeting.retargeter.interaction_mesh_retargeter import InteractionMeshRetargeter
```

**Step 5: Run retargeter-focused tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_retargeter_imports.py tests/test_module_entrypoints.py tests/test_adam_pro_cli_smoke.py
```

Expected: PASS.

**Step 6: Commit**

Run:

```bash
git add src/holosoma_retargeting/retargeter src/holosoma_retargeting/src/interaction_mesh_retargeter.py src/holosoma_retargeting/cli tests/test_retargeter_imports.py tests/test_module_entrypoints.py
git commit -m "refactor: move interaction mesh retargeter into retargeter package"
```

### Task 8: Phase 7 - Split Utilities Only Where Readability Improves

**Files:**
- Create as needed: `src/holosoma_retargeting/utils/*.py`
- Modify as needed: `src/holosoma_retargeting/src/utils.py`
- Modify as needed: `src/holosoma_retargeting/src/mujoco_utils.py`
- Modify as needed: `src/holosoma_retargeting/src/viser_utils.py`
- Modify imports in `src/holosoma_retargeting/cli/`
- Modify imports in `src/holosoma_retargeting/retargeter/`

**Intent:** Split broad support code into cohesive utility modules after command/config/retargeter boundaries are stable.

**Allowed changes:**
- Create utility modules named by responsibility.
- Move functions in small groups with tests.
- Leave wrappers or re-exports in old `src/*_utils.py` modules during migration.

**Forbidden changes:**
- No `misc.py`, `common.py`, or broad catch-all files.
- No behavior changes.
- No large all-at-once move of every utility function.

**Step 1: Choose one cohesive utility slice**

Pick exactly one slice per commit, such as:

- pose transforms;
- motion IO;
- MuJoCo model helpers;
- mesh sampling;
- visualization helpers;
- retarget output helpers.

**Step 2: Add or identify focused tests for the slice**

Use existing focused tests when available. Examples:

- path and package data: `tests/test_package_paths.py`
- MuJoCo model contracts: `tests/test_adam_pro_largebox_scene_xml.py`, `tests/test_adam_pro_xml_urdf_consistency.py`
- motion mappings: `tests/test_adam_pro_motion_mappings.py`
- data conversion: `tests/test_adam_pro_data_conversion.py`

Add a new import-compatibility test only if the moved helpers are public or imported by multiple modules.

**Step 3: Move the smallest coherent function group**

Example for pose transforms:

- Create: `src/holosoma_retargeting/utils/pose_transforms.py`
- Move only transform-related functions from `src/holosoma_retargeting/src/utils.py`
- Re-export moved functions from `src/holosoma_retargeting/src/utils.py`
- Update imports in modules that use the moved functions.

**Step 4: Run focused tests for that slice**

Run the smallest relevant test set first. Example:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests/test_package_paths.py tests/test_adam_pro_motion_mappings.py
```

Expected: PASS.

**Step 5: Commit each utility slice separately**

Run:

```bash
git add src/holosoma_retargeting/utils src/holosoma_retargeting/src tests
git commit -m "refactor: move <utility responsibility> helpers into utils"
```

Repeat Task 8 for each utility slice. Stop when the remaining old utility files are either compatibility wrappers or still too coupled to move safely.

### Task 9: Phase 8 - Console Scripts, Shell Wrappers, and Compatibility Cleanup

**Files:**
- Modify: `pyproject.toml`
- Modify: `scripts/retargeting/*.sh`
- Modify: `tests/test_module_entrypoints.py`
- Modify or delete: compatibility wrappers under `examples/`, `data_utils/`, `data_conversion/`, `evaluation/`, and `src/`

**Intent:** Make official command entrypoints explicit and remove compatibility shims only after users and tests have migrated.

**Allowed changes:**
- Add `[project.scripts]` console entrypoints.
- Update shell scripts to call console commands.
- Remove legacy wrappers only when no tests, docs, or scripts import them.

**Forbidden changes:**
- No user-facing command removal without a documented replacement.
- No compatibility cleanup before new imports and scripts are stable.

**Step 1: Add console script entries**

Add to `pyproject.toml`:

```toml
[project.scripts]
omniretarget-retarget = "holosoma_retargeting.cli.robot_retarget:entrypoint"
omniretarget-batch = "holosoma_retargeting.cli.parallel_robot_retarget:entrypoint"
omniretarget-eval = "holosoma_retargeting.cli.eval_retargeting:entrypoint"
omniretarget-replay = "holosoma_retargeting.cli.viser_player:entrypoint"
omniretarget-convert = "holosoma_retargeting.cli.data_process.convert_data_format_mj:entrypoint"
omniretarget-prep-amass = "holosoma_retargeting.cli.data_process.prep_amass_smplx_for_rt:entrypoint"
omniretarget-prep-optitrack = "holosoma_retargeting.cli.data_process.prep_optitrack_for_rt:entrypoint"
omniretarget-extract-global-positions = "holosoma_retargeting.cli.data_process.extract_global_positions:entrypoint"
```

If command modules do not yet expose zero-argument `entrypoint()` functions, add them as thin Tyro wrappers that call existing `main(cfg)` functions.

**Step 2: Verify scripts are installed**

Run:

```bash
uv sync
.venv/bin/omniretarget-retarget --help
.venv/bin/omniretarget-eval --help
.venv/bin/omniretarget-convert --help
```

Expected: each command prints help and exits successfully.

**Step 3: Update shell wrappers**

Update files under `scripts/retargeting/` to call `.venv/bin/omniretarget-*` or `uv run omniretarget-*` consistently.

**Step 4: Search for legacy imports**

Run:

```bash
grep -R -n "holosoma_retargeting.examples\|holosoma_retargeting.data_utils\|holosoma_retargeting.data_conversion\|holosoma_retargeting.evaluation\|holosoma_retargeting.src.interaction_mesh_retargeter" README.md docs scripts src tests
```

Expected: either no output or only intentional compatibility tests/docs.

**Step 5: Remove legacy wrappers only if safe**

If Step 4 shows no active users, remove wrappers in a separate commit. If active users remain, keep wrappers and document them as deprecated.

**Step 6: Run broad tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests
```

Expected: PASS or known environment-related skips only.

**Step 7: Commit**

Run:

```bash
git add pyproject.toml scripts tests src README.md docs
git commit -m "refactor: expose official omniretarget console commands"
```

## Final Verification

After all phases:

```bash
git status --short
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -q tests
grep -R -n "Hydra\|pipelines/" src tests README.md
grep -n 'Hydra is intentionally not part\|A separate `pipelines/` package is intentionally avoided' docs/plans/2026-04-24-omniretarget-refactor-overview.md
find src/holosoma_retargeting -maxdepth 2 -name "README.md" -print
```

Expected:

- `pytest` passes or only known environment-related skips remain.
- No source/test/root README code path depends on Hydra or `pipelines/`.
- The overview still records Hydra and `pipelines/` as avoided or deferred decisions.
- `find` prints no package-level README.
- Any remaining legacy wrappers are intentionally documented.
