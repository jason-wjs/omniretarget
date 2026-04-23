# holosoma_retargeting

This directory contains the extracted retargeting package used by OmniRetarget.

If you are working from the repository root, prefer the shell wrappers under `scripts/retargeting/`. The commands below are the direct Python entrypoints and assume you are running from this directory.

## Supported Tasks

- `robot_only`
- `object_interaction`
- `climbing`

## Motion Data Requirements

The retargeting pipeline expects world joint positions with shape `(T, J, 3)`. For custom data formats, update the joint definitions and mappings in `config_types/data_type.py`.

## Single Sequence Retargeting

```bash
uv run python examples/robot_retarget.py \
  --robot adam_pro \
  --task-type robot_only \
  --task-name dance1_subject1 \
  --data-path demo_data/lafan1_npy \
  --data-format lafan \
  --save-dir demo_results/adam_pro/robot_only/lafan1 \
  --task-config.ground-range -15 15 \
  --retargeter.foot-sticking-tolerance 0.02 \
  --retargeter.visualize
```

```bash
uv run python examples/robot_retarget.py \
  --robot adam_pro \
  --task-type object_interaction \
  --task-name sub3_largebox_003 \
  --data-path demo_data/OMOMO_new \
  --data-format smplh \
  --save-dir demo_results/adam_pro/object_interaction/omomo \
  --retargeter.visualize
```

```bash
uv run python examples/robot_retarget.py \
  --robot g1 \
  --task-type climbing \
  --task-name mocap_climb_seq_0 \
  --data-path demo_data/climb \
  --data-format mocap \
  --robot-config.robot-urdf-file models/g1/g1_29dof_spherehand.urdf \
  --task-config.object-name multi_boxes \
  --save-dir demo_results/g1/climbing/mocap_climb \
  --retargeter.visualize
```

## Batch Retargeting

```bash
uv run python examples/parallel_robot_retarget.py \
  --robot adam_pro \
  --task-type robot_only \
  --task-config.object-name ground \
  --data-format optitrack \
  --data-dir demo_data/optitrack_npz \
  --save-dir demo_results_parallel/adam_pro/robot_only/optitrack
```

```bash
uv run python examples/parallel_robot_retarget.py \
  --robot adam_pro \
  --task-type object_interaction \
  --task-config.object-name largebox \
  --data-format smplh \
  --data-dir demo_data/OMOMO_new \
  --save-dir demo_results_parallel/adam_pro/object_interaction/omomo
```

## Source Data Conversion

### LAFAN BVH to NPY

```bash
uv run python data_utils/extract_global_positions.py \
  --input-dir demo_data/lafan1_raw_bvh \
  --output-dir demo_data/lafan1
```

### OptiTrack PKL to NPZ

```bash
uv run python data_utils/prep_optitrack_for_rt.py \
  --input-dir demo_data/mocap_optitrack \
  --output-dir demo_data/optitrack_npz \
  --height 1.7
```

### AMASS SMPL-X to NPZ

```bash
PYTHONPATH="${PWD}/data_utils/human_body_prior:${PYTHONPATH:-}" \
uv run python -m data_utils.prep_amass_smplx_for_rt \
  --amass-root-folder /path/to/amass \
  --output-folder demo_data/amass_npz \
  --model-root-folder /path/to/models
```

## MuJoCo Export

```bash
uv run python data_conversion/convert_data_format_mj.py \
  --input_file demo_results/adam_pro/robot_only/lafan1/dance1_subject1.npz \
  --output_fps 50 \
  --output_name converted_res/robot_only/dance1_subject1_mj_fps50.npz \
  --data_format lafan \
  --object_name ground \
  --once
```

```bash
uv run python data_conversion/convert_data_format_mj.py \
  --input_file demo_results_parallel/adam_pro/object_interaction/omomo/sub3_largebox_003_original.npz \
  --output_fps 50 \
  --output_name converted_res/object_interaction/sub3_largebox_003_mj_w_obj.npz \
  --data_format smplh \
  --object_name largebox \
  --has_dynamic_object \
  --once
```

If your input clip already follows the OmniRetarget layout, add `--use_omniretarget_data`.

## Replay

```bash
uv run python viser_player.py \
  --qpos-npz demo_results_parallel/adam_pro/object_interaction/omomo/sub3_largebox_003_original.npz \
  --robot-urdf models/adam_pro/adam_pro_29dof.urdf \
  --object-urdf models/largebox/largebox.urdf
```

## Quantitative Evaluation

```bash
uv run python evaluation/eval_retargeting.py \
  --res-dir demo_results_parallel/adam_pro/robot_only/omomo \
  --data-dir demo_data/OMOMO_new \
  --data-type robot_only \
  --robot adam_pro \
  --data-format smplh \
  --max-workers 1
```

## Extension Notes

- Custom motion format instructions: [`../../docs/add-motion-format.md`](../../docs/add-motion-format.md)
- Custom robot instructions: [`../../docs/add-robot-type.md`](../../docs/add-robot-type.md)
