# PARC Retargeting Error Record

This record summarizes the PARC mid-climbing retargeting issues found before full dataset regeneration.

## 1. Terrain Exported Below the Ground Plane

- Typical sample: `mid_blocks_001_dm_aug004_dm_aug0`
- Related sample: `mid_blocks_001_dm_aug007_dm_aug0`
- Symptom: the whole terrain rendered below `z=0`, making the robot appear initialized in the air.
- Root cause: the original PARC heightfield can use a negative vertical origin. The old workspace export shifted human joints but did not normalize the terrain and human joints together with the terrain height origin.
- Fix: compute `z_origin = nanmin(terrain_data.hf)` and subtract it from both `human_joints[:, :, 2]` and `terrain_data.hf` during PARC workspace construction.

## 2. Terrain Payload and Visual URDF Used the Wrong Scale

- Typical sample: `mid_blocks_001_dm_aug004_dm_aug0`
- Symptom: after height-origin normalization, the terrain appeared above the ground plane, but the robot motion was still far below the terrain and severely penetrated it.
- Root cause: retargeting scales the human motion and robot trajectory to G1 scale, while the visualization script selected the unscaled `multi_boxes.urdf`; the paired `.pkl` terrain payload was also still written in unscaled workspace units.
- Fix: write scaled terrain payload fields (`hf`, `hf_maxmin`, `min_point`, `dx`) to paired output, and make `scripts/parc/vis_parc_process.sh` prefer `multi_boxes_scaled_*.urdf` when present.

## 3. PARC Climbing Motion Was Height-Normalized a Second Time

- Typical sample: `mid_blocks_004_dm_aug002_dm_aug1`
- Related sample: `mid_blocks_004_dm_aug003_dm_aug0`
- Symptom: the intended semantic start platform was the second-height platform, but the G1 robot started around the wrong vertical level and penetrated the platform.
- Root cause: `preprocess_motion_data()` normalized all climbing motions by the sequence toe-height minimum. That behavior is valid for flat mocap-style data, but PARC terrain already encodes absolute platform height after workspace normalization. The second normalization destroyed the terrain-relative height semantics.
- Fix: keep `preprocess_motion_data(..., normalize_height=True)` as the default, but pass `normalize_height=False` for `task_type == "climbing"` and `data_format == "parc_humanoid"` in both single and parallel retargeting paths.

## Remaining Watch Item

- Sample to watch: `mid_blocks_004_dm_aug003_dm_aug0`
- Observation: before the third fix, this sample also showed a possible heightfield axis-order ambiguity around one foot contact cell. After disabling the second height normalization, manual visualization confirmed the two checked `mid_blocks_004` canaries are correct, but non-symmetric terrains should still be included in canary validation before full conversion.
