# OmniRetarget

OmniRetarget is a standalone motion-retargeting repository extracted from Holosoma.

The repository currently keeps the Python package name `holosoma_retargeting` to reduce migration risk during bootstrap. The supported focus is motion retargeting only.

## Supported Workflows

- Single-clip retargeting
- Batch retargeting
- Source-motion conversion for LAFAN, OptiTrack, and AMASS SMPL-X inputs
- MuJoCo-format export of retargeted trajectories
- Viser replay
- Quantitative evaluation

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

## Recommended Entry Points

The shell wrappers under `scripts/` are the supported entry points from the repository root. Data-processing wrappers live under `scripts/data_process/`.

### Single Clip Retargeting

```bash
bash scripts/retarget_single_clip.sh
```

### Batch Retargeting

```bash
bash scripts/retarget_batch_clips.sh
```

### Data Conversion

```bash
bash scripts/data_process/convert_lafan_bvh_to_npy.sh
bash scripts/data_process/convert_optitrack_pkl_to_npz.sh
bash scripts/data_process/convert_amass_smplx_to_npz.sh
```

For direct MuJoCo export of retargeted trajectories, see `docs/usage.md`.

### Evaluation

```bash
bash scripts/eval.sh
```

### Replay

```bash
bash scripts/viser_player.sh
```

## Verification

```bash
uv sync
bash scripts/test_smoke.sh
```

## More Detailed Usage

See `docs/usage.md` for direct Python entry points, example command lines, and detailed usage notes.

Additional repo docs:
- `docs/usage.md`
- `docs/add-motion-format.md`
- `docs/add-robot-type.md`
- `docs/adam-pro-robot-only-summary.md`
