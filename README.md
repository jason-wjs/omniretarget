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

The shell wrappers under `scripts/retargeting/` are the supported entry points from the repository root. They call the package `holosoma_retargeting.cli.*` modules while preserving the current package-relative working directory assumptions for demo assets.

### Single Clip Retargeting

```bash
bash scripts/retargeting/retarget_single_clip.sh
```

### Batch Retargeting

```bash
bash scripts/retargeting/retarget_batch_clips.sh
```

### Data Conversion

```bash
bash scripts/retargeting/convert_lafan_bvh_to_npy.sh
bash scripts/retargeting/convert_optitrack_pkl_to_npz.sh
bash scripts/retargeting/convert_amass_smplx_to_npz.sh
```

For direct MuJoCo export of retargeted trajectories, use the package-level command examples in `src/holosoma_retargeting/README.md`.

### Evaluation

```bash
bash scripts/retargeting/eval.sh
```

### Replay

```bash
bash scripts/retargeting/replay_viser.sh
```

## Verification

```bash
uv sync
bash scripts/test_smoke.sh
```

## More Detailed Usage

See `src/holosoma_retargeting/README.md` for direct Python entrypoints, example command lines, and package-level workflow notes.

Additional repo docs:
- `docs/add-motion-format.md`
- `docs/add-robot-type.md`
- `docs/adam-pro-robot-only-summary.md`
