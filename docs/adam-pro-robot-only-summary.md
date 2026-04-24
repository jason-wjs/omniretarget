# Adam Pro Robot-Only Retargeting Summary

This note summarizes the current `robot_only` support added for Adam Pro in `holosoma_retargeting`, plus the bash entrypoints under `scripts/` and `scripts/data_process/`.

## Scope (Current)

- Scope covered: `robot_only` retargeting.
- In progress / next: object-interaction and climbing refinements.
- Hand end-effector markers are currently under refinement and should be ignored for robot-only tuning/evaluation.

## Features Added (Robot-Only)

### 1) Adam Pro as a first-class robot type

- Registered `adam_pro` in robot defaults (`29 DoF`, `robot_height=1.67`).
- Added Adam Pro `FOOT_STICKING_LINKS` using foot patch markers `left/right_foot_sphere_{1..4}_link`.
- Added Adam Pro nominal tracking indices for lower-body + waist (`np.arange(15)`).
- Added Adam Pro manual bounds/costs:
  - Waist/arm/wrist priors.
  - Elbow anti-hyperextension bounds.
  - Knee anti-hyperextension bounds and low knee prior costs.
  - Hip roll/yaw anti-twist bounds.

Main files:
- `src/holosoma_retargeting/config_types/robot.py`
- `src/holosoma_retargeting/cli/robot_retarget.py`

### 2) Adam Pro model refinements for retargeting XML/URDF flow

Model file:
- `src/holosoma_retargeting/models/adam_pro/adam_pro_29dof.xml`

Current retargeting-relevant details include:
- Retargeting-only `ground` plane in XML.
- Foot patch markers on each foot (5 points per foot).
- Named foot sphere geoms (`left/right_foot_sphere_{1..5}_link`) to align contact handling with G1 pattern.
- Hand end-effector marker links exist (`left_hand_ee_link`, `right_hand_ee_link`) but are not considered stable yet; for robot-only mode, continue to rely on wrist-based behavior and ignore these markers.

#### Foot marker logic (Adam Pro vs G1 baseline)

- Marker sphere radius is the same as G1 for foot markers: `0.005`.
- Adam Pro does **not** copy G1 marker positions; marker positions are adapted to Adam Pro toe/sole geometry.
  - G1 foot marker frame (`left_ankle_roll_sphere_*`) uses positions around:
    - rear: `x=-0.05`
    - front: `x=0.12/0.14`
    - lateral: `y=+/-0.025~0.03`
    - vertical: `z=-0.03`
  - Adam Pro foot marker frame (`left_foot_sphere_*`) uses:
    - rear: `x=-0.063633`
    - front: `x=0.158693` (left) / `0.158614` (right)
    - lateral: `y=+/-0.039~0.04`, with center lane near `+/-0.000351`
    - vertical: `z=-0.054562`
- Functional split of the 5 markers:
  - `sphere_1..4`: used in `FOOT_STICKING_LINKS` for XY sticking constraints.
  - `sphere_5`: kept as toe target in `JOINTS_MAPPING` (`Left/RightToeBase`, `L/R_Toe`, `L/R_Foot` by format), but excluded from sticking.
- Relationship to Adam Pro foot capsule collisions:
  - Adam Pro uses five parallel sole capsules (`left/right_foot{1..5}_collision`) with lane spacing about `0.019787`.
  - `foot_capsule` radius is `0.009894`, approximately half lane spacing (`0.019787 / 2 = 0.0098935`), so neighboring capsule strips just touch and form a continuous contact patch.
  - This `0.009894` is a collision approximation parameter, not a marker size parameter.

### 3) Motion format mappings for Adam Pro

Adam Pro joint/link mapping added for:
- `smplh`
- `lafan`
- `smplx`
- `optitrack`

Also added OptiTrack mapping for `g1`.

Main file:
- `src/holosoma_retargeting/profiles/mappings.py`

### 4) OptiTrack support (custom format path)

- Added `optitrack` format constants and joint registry entries.
- Added converter from OptiTrack `.pkl` to retargeting `.npz`:
  - output keys: `global_joint_positions`, `height`
  - default height used: `1.7`

Main files:
- `src/holosoma_retargeting/profiles/motions.py`
- `src/holosoma_retargeting/cli/data_process/prep_optitrack_for_rt.py`

### 5) Grounding behavior for OptiTrack robot-only

- In robot-only retargeting (`single` and `parallel`), OptiTrack preprocessing uses:
  - `ground_height_percentile=5.0`
  - `mat_height=0.0`
- This differs from non-OptiTrack defaults and improves floor grounding stability for OptiTrack data.

Main files:
- `src/holosoma_retargeting/cli/robot_retarget.py`
- `src/holosoma_retargeting/cli/parallel_robot_retarget.py`

## Bash Usage (`scripts/`)

All scripts assume you run from repo root:
- `/home/humanoid/Projects/Junsong_WU/ADAM/omni/omniretarget-refactor-next`

Retargeting/evaluation/replay wrappers live directly under `scripts/`; data conversion wrappers live under `scripts/data_process/`.

### 1) Single clip retargeting

Script:
- `scripts/retarget_single_clip.sh`

Default in script currently runs OptiTrack + Adam Pro:
```bash
bash scripts/retarget_single_clip.sh
```

The script contains commented templates for:
- OMOMO (`smplh`)
- LAFAN (`lafan`)
- AMASS (`smplx`)
- OptiTrack (`optitrack`)

### 2) Batch retargeting

Script:
- `scripts/retarget_batch_clips.sh`

Default:
- `ROBOT=adam_pro`
- `DATA_FORMAT=optitrack`
- `DATA_DIR=demo_data/optitrack_npz`
- `SAVE_DIR=demo_results_parallel/${ROBOT}/robot_only/optitrack`

Run:
```bash
bash scripts/retarget_batch_clips.sh
```

Override with env vars:
```bash
ROBOT=g1 DATA_FORMAT=optitrack DATA_DIR=demo_data/optitrack_npz \
SAVE_DIR=demo_results_parallel/g1/robot_only/optitrack \
bash scripts/retarget_batch_clips.sh
```

### 3) Replay retargeted result in Viser

Script:
- `scripts/replay_viser.sh`

Run:
```bash
bash scripts/replay_viser.sh
```

You can override any replay CLI arg by appending flags.

### 4) Quantitative evaluation

Script:
- `scripts/eval.sh`

Default target:
- Adam Pro
- `robot_only`
- OMOMO

Run:
```bash
bash scripts/eval.sh
```

### 5) LAFAN conversion (`.bvh` -> `.npy`)

Script:
- `scripts/data_process/convert_lafan_bvh_to_npy.sh`

Run:
```bash
bash scripts/data_process/convert_lafan_bvh_to_npy.sh
```

### 6) AMASS conversion (SMPL-X -> retargeting NPZ)

Script:
- `scripts/data_process/convert_amass_smplx_to_npz.sh`

Run:
```bash
bash scripts/data_process/convert_amass_smplx_to_npz.sh
```

### 7) OptiTrack conversion (`.pkl` -> retargeting NPZ)

Script:
- `scripts/data_process/convert_optitrack_pkl_to_npz.sh`

Run:
```bash
bash scripts/data_process/convert_optitrack_pkl_to_npz.sh
```
