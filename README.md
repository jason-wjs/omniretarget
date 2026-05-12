# OmniRetarget

OmniRetarget is a standalone motion-retargeting repository extracted from Holosoma.

The repository keeps the Python package name `omniretarget` to reduce migration risk during bootstrap. The supported focus is motion retargeting only.

## Supported Scope

- Robots: G1, T1, Adam Pro
- Tasks: `robot_only`, `object_interaction`, `climbing`
- Motion formats: LAFAN, SMPL-H, SMPL-X, OptiTrack, MOCAP, PARC humanoid
- Workflows: single-clip retargeting, batch retargeting, source-data conversion, MuJoCo export, Viser replay, quantitative evaluation
- PARC/G1 support: compile PARC `initial_aug` terrain-motion samples into G1 paired dataset artifacts

## Intentionally Not Migrated

- Policy training
- Real-robot deployment code
- Monorepo demo pipelines that depend on non-retargeting components
- `holosoma/` training and inference packages

## Setup

```bash
uv sync
```

If your environment has cache-permission issues, use:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv sync
```

To run the real PARC integration test, set:

```bash
export PARC_SAMPLE_PATH=/path/to/parc_sample.pkl
export PARC_HUMANOID_XML=/path/to/humanoid.xml
```

## Recommended Entry Points

The shell wrappers under `scripts/retargeting/` are the supported entry points from the repository root.

```bash
bash scripts/retargeting/retarget_single_clip.sh
bash scripts/retargeting/retarget_batch_clips.sh
bash scripts/retargeting/convert_lafan_bvh_to_npy.sh
bash scripts/retargeting/convert_optitrack_pkl_to_npz.sh
bash scripts/retargeting/convert_amass_smplx_to_npz.sh
bash scripts/retargeting/eval.sh
bash scripts/retargeting/replay_viser.sh
```

## Direct Python Entrypoints

Run these commands from the repository root with `uv run`.

### Adam Pro Retargeting

```bash
uv run python src/omniretarget/examples/robot_retarget.py \
  --robot adam_pro \
  --task-type robot_only \
  --task-name dance1_subject1 \
  --data-path src/omniretarget/demo_data/lafan1_npy \
  --data-format lafan \
  --save-dir demo_results/adam_pro/robot_only/lafan1 \
  --task-config.ground-range -15 15 \
  --retargeter.foot-sticking-tolerance 0.02
```

```bash
uv run python src/omniretarget/examples/robot_retarget.py \
  --robot adam_pro \
  --task-type object_interaction \
  --task-name sub3_largebox_003 \
  --data-path src/omniretarget/demo_data/OMOMO_new \
  --data-format smplh \
  --save-dir demo_results/adam_pro/object_interaction/omomo
```

### G1 Climbing

```bash
uv run python src/omniretarget/examples/robot_retarget.py \
  --robot g1 \
  --task-type climbing \
  --task-name mocap_climb_seq_0 \
  --data-path src/omniretarget/demo_data/climb \
  --data-format mocap \
  --robot-config.robot-urdf-file src/omniretarget/models/g1/g1_29dof_spherehand.urdf \
  --task-config.object-name multi_boxes \
  --save-dir demo_results/g1/climbing/mocap_climb
```

### PARC to G1 Paired Data

```bash
uv run python src/omniretarget/examples/parc_process.py \
  --sample /path/to/parc_initial_aug_sample.pkl \
  --source-xml /path/to/humanoid.xml \
  --output-root /tmp/parc_process_bootstrap \
  --retarget-save-dir /tmp/parc_process_workspace
```

Use `--dry-run` to generate the retargeting workspace without running the solver or emitting paired output.

### Batch Retargeting

```bash
uv run python src/omniretarget/examples/parallel_robot_retarget.py \
  --robot adam_pro \
  --task-type robot_only \
  --task-config.object-name ground \
  --data-format optitrack \
  --data-dir src/omniretarget/demo_data/optitrack_npz \
  --save-dir demo_results_parallel/adam_pro/robot_only/optitrack
```

### MuJoCo Export

```bash
uv run python src/omniretarget/data_conversion/convert_data_format_mj.py \
  --input_file demo_results/adam_pro/robot_only/lafan1/dance1_subject1.npz \
  --output_fps 50 \
  --output_name converted_res/robot_only/dance1_subject1_mj_fps50.npz \
  --data_format lafan \
  --object_name ground \
  --once
```

If the input clip already follows the OmniRetarget layout, add `--use_omniretarget_data`.

### Replay

```bash
uv run python src/omniretarget/viser_player.py \
  --qpos-npz demo_results_parallel/adam_pro/object_interaction/omomo/sub3_largebox_003_original.npz \
  --robot-urdf src/omniretarget/models/adam_pro/adam_pro_29dof.urdf \
  --object-urdf src/omniretarget/models/largebox/largebox.urdf
```

### Quantitative Evaluation

```bash
uv run python src/omniretarget/evaluation/eval_retargeting.py \
  --res-dir demo_results_parallel/adam_pro/robot_only/omomo \
  --data-dir src/omniretarget/demo_data/OMOMO_new \
  --data-type robot_only \
  --robot adam_pro \
  --data-format smplh \
  --max-workers 1
```

## Verification

```bash
uv sync
bash scripts/test_smoke.sh
```

During refactor work, this reduced test command avoids the two known external prerequisites:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run python -m pytest -q \
  --ignore=tests/test_prep_amass_smplx_gender_handling.py \
  --ignore=tests/test_adam_pro_cli_smoke.py \
  tests
```

Known external prerequisites:

- `tests/test_prep_amass_smplx_gender_handling.py` requires `human_body_prior`.
- `tests/test_adam_pro_cli_smoke.py` expects `/tmp/adam_pro_rt_smoke/sub3_largebox_003.npz` to be generated first.
- The real PARC integration check is skipped unless `PARC_SAMPLE_PATH` and `PARC_HUMANOID_XML` are set.

## Extension Docs

- `docs/add-motion-format.md`
- `docs/add-robot-type.md`
- `docs/adam-pro-robot-only-summary.md`
