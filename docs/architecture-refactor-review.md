# Architecture Refactor Review Package

Date: 2026-06-01

Branch: `arch/retargeting-runtime-refactor`

Worktree:

```text
/home/humanoid/Projects/Junsong_WU/learning/locomotion/RETARGET/omniretarget-arch-refactor
```

This branch is intentionally kept as a parallel branch. It has not been merged.

## Review Intent

This review package summarizes the refactor for human review before merge. The
goal of the refactor was to deepen the repository architecture while preserving
all workflows supported by the current `main` branch.

The refactor uses compatibility wrappers where public paths may still be used by
existing users, scripts, tests, or README commands. Wrapper retention is
intentional, not unfinished cleanup.

## Implementation Commit Sequence

```text
9b99752 docs: record architecture refactor safety contract
3084193 docs: add architecture refactor plan
48f1da8 refactor: add runtime context seam
fb1973b refactor: add retargeting pipeline seam
2d0fe09 refactor: add robot and motion spec registries
5720aa7 refactor: add mujoco query seam
3e0c8ca refactor: decompose interaction mesh solver
6b0d4ec refactor: migrate public facade imports
```

## Phase Summary

Phase 0 recorded the safety contract and domain vocabulary before runtime code
was changed.

Phase 1 added `omniretarget.runtime` so retargeting, evaluation, and MJ
conversion resolve robot, motion, task, object, and asset facts through a shared
Runtime Context seam.

Phase 2 moved single and parallel retargeting workflow behavior from CLI modules
into `omniretarget.retargeting`, while keeping the existing example script paths
as CLI adapters and compatibility wrappers.

Phase 3 moved robot defaults, motion-format constants, and joint mappings into
`omniretarget.specs`, reducing robot/data-format branches in config wrappers.

Phase 4 moved MuJoCo model state, kinematics, collision filtering, and asset
resolution into `omniretarget.mujoco`.

Phase 5 decomposed the interaction-mesh solver into `omniretarget.solver` and
`omniretarget.visualization`, while keeping `InteractionMeshRetargeter` as the
public workflow facade.

Phase 6 added `omniretarget.retargeter` as the public retargeter facade, moved
world-frame MuJoCo mesh extraction into `omniretarget.mujoco.assets`, and kept
legacy wrapper paths where removal would be unsafe.

## Primary Module Paths

New or deepened primary paths:

```text
src/omniretarget/runtime/
src/omniretarget/retargeting/
src/omniretarget/specs/
src/omniretarget/mujoco/
src/omniretarget/solver/
src/omniretarget/visualization/
src/omniretarget/retargeter.py
```

These are the preferred internal paths for new work.

## Compatibility Paths Kept

These paths remain intentionally supported:

```text
src/omniretarget/examples/robot_retarget.py
src/omniretarget/examples/parallel_robot_retarget.py
src/omniretarget/examples/parc_process.py
src/omniretarget/examples/parc_batch_process_to_mj.py
src/omniretarget/examples/parc_batch_vis.py
src/omniretarget/viser_player.py
src/omniretarget/src/interaction_mesh_retargeter.py
src/omniretarget/src/mujoco_utils.py
src/omniretarget/src/utils.py
src/omniretarget/src/viser_utils.py
```

The example scripts are protected CLI paths. `interaction_mesh_retargeter.py`
and `mujoco_utils.py` now mostly act as compatibility facades around deeper
modules. `utils.py` and `viser_utils.py` still have broad caller surfaces and
should not be removed without a separate, focused plan.

## Compatibility Matrix

| Area | Preferred path after refactor | Compatibility path kept | Notes |
| --- | --- | --- | --- |
| Retargeter construction | `omniretarget.retargeter.InteractionMeshRetargeter` | `omniretarget.src.interaction_mesh_retargeter.InteractionMeshRetargeter` | Class identity is tested. |
| Single retargeting workflow | `omniretarget.retargeting.pipeline.run_single_retargeting` | `src/omniretarget/examples/robot_retarget.py` | CLI path remains unchanged. |
| Parallel retargeting workflow | `omniretarget.retargeting.batch.run_parallel_retargeting` | `src/omniretarget/examples/parallel_robot_retarget.py` | CLI path remains unchanged. |
| Runtime constants | `omniretarget.runtime.context` | `create_task_constants()` wrappers in existing modules | Parity fields are tested. |
| Robot and motion specs | `omniretarget.specs` | `config_types` public wrappers | Extension docs now point to specs. |
| MuJoCo query behavior | `omniretarget.mujoco` | selected old helpers | Collision, kinematics, model-state behavior is tested. |
| MuJoCo mesh extraction | `omniretarget.mujoco.assets.world_mesh_from_geom` | `omniretarget.src.mujoco_utils._world_mesh_from_geom` | Old helper is a wrapper. |
| Solver internals | `omniretarget.solver` | `InteractionMeshRetargeter` methods | Public methods delegate to solver modules. |
| Retargeting visualization adapter | `omniretarget.visualization.viser_adapter` | methods on `InteractionMeshRetargeter` | Public methods remain available. |
| Generic replay | `src/omniretarget/viser_player.py` | same path | Protected README command path. |

## Verification Commands

Run these from the refactor worktree before merge review:

```bash
git status --short --branch
git diff --check
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest
```

Recommended focused checks:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_module_entrypoints.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_runtime_context.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_retargeting_pipeline.py tests/test_retargeting_batch.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_specs_registries.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_mujoco_query_seam.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_solver_facade.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_public_facades.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest tests/test_parc_process.py tests/test_parc_batch_process_to_mj.py tests/test_parc_batch_vis.py
```

## Current Review Verification

Latest review run on this branch:

```text
git status --short --branch
## arch/retargeting-runtime-refactor...origin/arch/retargeting-runtime-refactor

git diff --check
<no output>

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest
195 passed, 1 skipped
```

Lightweight CLI entrypoint smokes all returned exit code 0:

```bash
uv run python src/omniretarget/examples/robot_retarget.py --help
uv run python src/omniretarget/examples/parallel_robot_retarget.py --help
uv run python src/omniretarget/examples/parc_process.py --help
uv run python src/omniretarget/examples/parc_batch_process_to_mj.py --help
uv run python src/omniretarget/examples/parc_batch_vis.py --help
uv run python src/omniretarget/data_conversion/convert_data_format_mj.py --help
uv run python src/omniretarget/evaluation/eval_retargeting.py --help
uv run python src/omniretarget/viser_player.py --help
```

## Smoke Coverage

The branch has used short smoke inputs rather than full-length demonstration
motions when a full sequence would be too slow for a safety checkpoint. The
Phase 5 12-frame Adam Pro LAFAN smoke produced an `.npz` containing:

```text
qpos
human_joints
fps
cost
```

The full `dance1_subject1` LAFAN source has 3945 frames and was intentionally
stopped during Phase 5 after confirming it was not a short smoke input.

The review-stage 12-frame robot-only smoke used
`/tmp/omniretarget_lafan_short/dance1_subject1.npy` and produced:

```text
/tmp/omniretarget_review_smoke_robot_only/dance1_subject1.npz
fields: cost, fps, human_joints, qpos
qpos: (12, 36)
human_joints: (12, 22, 3)
```

The review-stage 12-frame object-interaction smoke truncated
`src/omniretarget/demo_data/OMOMO_new/sub3_largebox_003.pt` into
`/tmp/omniretarget_omomo_short/sub3_largebox_003.pt` and produced:

```text
/tmp/omniretarget_review_smoke_object_interaction/sub3_largebox_003_original.npz
fields: cost, fps, human_joints, qpos
qpos: (12, 43)
human_joints: (12, 52, 3)
```

The review-stage PARC dry-run smoke used:

```bash
uv run python src/omniretarget/examples/parc_process.py \
  --sample src/omniretarget/demo_data/parc/mid_blocks_001_dm_aug001_dm.pkl \
  --source-xml src/omniretarget/models/humanoid_parc/humanoid.xml \
  --output-root /tmp/omniretarget_review_smoke_parc_output \
  --retarget-save-dir /tmp/omniretarget_review_smoke_parc_retarget \
  --dry-run
```

It returned exit code 0 and planned the workspace:

```text
/tmp/omniretarget_review_smoke_parc_retarget/workspace/mid_blocks_001_dm_aug001_dm
```

## Known Residual Risk

The refactor intentionally does not remove all old modules. Remaining old paths
are compatibility surfaces or broad utility modules. The highest-value later
cleanup candidate is `src/omniretarget/src/utils.py`, but it should be split in
a separate phase with focused behavior tests because it is used by retargeting,
solver, evaluation, preprocessing, object setup, and tests.

Full GUI replay behavior is not deeply exercised by automated tests. Import
entrypoints and reusable visualization adapter paths are covered, but a manual
Viser run is still recommended before release if visualization behavior is
release-critical.

## Pre-Merge Checklist

Before merging, sync this branch with the latest `main` and rerun:

```bash
git fetch origin
git status --short --branch
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest
git diff --check
```

Then run one or more short CLI smokes for protected workflows that matter for the
merge decision:

```bash
uv run python src/omniretarget/examples/robot_retarget.py --help
uv run python src/omniretarget/examples/parallel_robot_retarget.py --help
uv run python src/omniretarget/examples/parc_process.py --help
uv run python src/omniretarget/data_conversion/convert_data_format_mj.py --help
uv run python src/omniretarget/evaluation/eval_retargeting.py --help
uv run python src/omniretarget/viser_player.py --help
```
