# OmniRetarget

This repository is a re-implementation of the OmniRetarget algorithm for motion
retargeting. It converts human-only motions, human-object interaction (HOI) data,
and human-scene interaction (HSI) data into humanoid robot trajectories, with
support for single-clip and batch retargeting, PARC terrain-motion pairs, MuJoCo
export, Viser replay, and quantitative evaluation.

The method is described in
[arXiv:2509.26633](https://arxiv.org/abs/2509.26633). The original OmniRetarget
implementation and reference code are released in
[amazon-far/holosoma](https://github.com/amazon-far/holosoma).

## Highlights

- **Multi-robot retargeting:** Unitree G1, T1, and PND Adam Pro.
- **Multiple motion sources:** LAFAN, SMPL-H, SMPL-X/AMASS, OptiTrack, MOCAP,
  and PARC terrain-motion pairs.
- **Scene-aware tasks:** robot-only motion, object interaction, and climbing.
- **End-to-end tooling:** source-data conversion, retargeting, MuJoCo export,
  replay, batch processing, and evaluation.
- **Extension guides:** documented paths for adding new motion formats and robot
  types.

## Quick Start

[`uv`](https://docs.astral.sh/uv/) is the canonical package manager. The project
requires Python 3.11 or newer.

```bash
uv sync
```

Run a demo LAFAN clip on Adam Pro:

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

The retargeted clip is written to:

```text
demo_results/adam_pro/robot_only/lafan1/dance1_subject1.npz
```

Replay a generated result with Viser:

```bash
uv run python src/omniretarget/viser_player.py \
  --qpos-npz demo_results/adam_pro/robot_only/lafan1/dance1_subject1.npz \
  --robot-urdf src/omniretarget/models/adam_pro/adam_pro_29dof.urdf
```

If your environment has cache-permission issues, use:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv sync
```

## Pipeline

OmniRetarget follows a practical retargeting pipeline:

1. Load a source motion from a supported format.
2. Map source human joints to robot links or joints.
3. Scale and optimize the motion under robot, task, and contact constraints.
4. Save the retargeted robot trajectory as `.npz`.
5. Replay, export to MuJoCo-friendly data, or evaluate the result.

## Supported Scope

| Category | Supported items |
| --- | --- |
| Robots | G1, T1, PND Adam Pro |
| Tasks | `robot_only`, `object_interaction`, `climbing` |
| Motion formats | LAFAN, SMPL-H, SMPL-X/AMASS, OptiTrack, MOCAP, PARC terrain-motion pairs |
| Workflows | single-clip retargeting, batch retargeting, source-data conversion, MuJoCo export, Viser replay, quantitative evaluation |
| PARC/G1 | retarget PARC terrain-motion pairs to G1 paired data |

## Demo Data

Demo inputs live under `src/omniretarget/demo_data/` and cover the supported
source formats:

| Directory | Purpose |
| --- | --- |
| `lafan1_npy/` | LAFAN-style robot-only motion examples |
| `OMOMO_new/` | SMPL-H object-interaction examples |
| `amass_npz/` | SMPL-X/AMASS-style motion examples |
| `custom_optitrack_npz/` | OptiTrack-style motion examples |
| `climb/` | MOCAP climbing examples with terrain/object assets |
| `parc/` | PARC terrain-motion pair examples for G1 paired-data processing |

## Recommended Scripts

The shell wrappers under `scripts/` are the supported entry points from the
repository root:

```bash
bash scripts/retarget_single_clip.sh
bash scripts/retarget_batch_clips.sh
bash scripts/convert_lafan_bvh_to_npy.sh
bash scripts/convert_optitrack_pkl_to_npz.sh
bash scripts/convert_amass_smplx_to_npz.sh
bash scripts/convert_to_mj.sh
bash scripts/eval.sh
bash scripts/replay_viser.sh
```

PARC/G1 wrappers:

```bash
bash scripts/parc/run_parc_process.sh
bash scripts/parc/convert_parc_to_mj.sh
bash scripts/parc/batch_parc_initial_aug_to_mj.sh
bash scripts/parc/retry_failed_parc_to_mj.sh
bash scripts/parc/vis_parc_process.sh
```

## Recipes

Run commands from the repository root with `uv run` unless a shell wrapper is
shown.

### Adam Pro Robot-Only Retargeting

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

### Adam Pro Object Interaction

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

### Batch Retargeting

```bash
uv run python src/omniretarget/examples/parallel_robot_retarget.py \
  --robot adam_pro \
  --task-type robot_only \
  --task-config.object-name ground \
  --data-format optitrack \
  --data-dir src/omniretarget/demo_data/custom_optitrack_npz \
  --save-dir demo_results_parallel/adam_pro/robot_only/optitrack
```

### PARC to G1 Paired Data

```bash
uv run python src/omniretarget/examples/parc_process.py \
  --sample src/omniretarget/demo_data/parc/mid_blocks_001_dm_aug001_dm.pkl \
  --source-xml /path/to/humanoid.xml \
  --output-root /tmp/parc_process_bootstrap \
  --retarget-save-dir /tmp/parc_process_workspace
```

Use `--dry-run` to generate the retargeting workspace without running the solver
or emitting paired output.

To run the real PARC integration test, set:

```bash
export PARC_SAMPLE_PATH=/path/to/parc_sample.pkl
export PARC_HUMANOID_XML=/path/to/humanoid.xml
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

If the input clip already follows the OmniRetarget layout, add
`--use_omniretarget_data`.

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

## Extending OmniRetarget

OmniRetarget keeps format and robot customization paths documented in the repo:

- [Add a motion format](docs/add-motion-format.md)
- [Add a robot type](docs/add-robot-type.md)

## Verification

```bash
uv sync
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest
```

Known external prerequisites:

- `tests/test_prep_amass_smplx_gender_handling.py` requires `human_body_prior`.
- `tests/test_adam_pro_cli_smoke.py` expects
  `/tmp/adam_pro_rt_smoke/sub3_largebox_003.npz` to be generated first.
- The real PARC integration check is skipped unless `PARC_SAMPLE_PATH` and
  `PARC_HUMANOID_XML` are set.

## Citation and Acknowledgements

This repository re-implements OmniRetarget. If you use it, please cite the
original paper:

- **OmniRetarget** — [arXiv:2509.26633](https://arxiv.org/abs/2509.26633)

The original OmniRetarget implementation and reference code are:

- **holosoma** — <https://github.com/amazon-far/holosoma>

## License

This repository does not currently include a license file. Add a `LICENSE` file
before publishing the project as open source.
