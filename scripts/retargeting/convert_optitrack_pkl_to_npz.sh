#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/../.." &>/dev/null && pwd)

cd "${REPO_ROOT}/src/holosoma_retargeting"

# Convert OptiTrack PKL clips to standard retargeting NPZ clips.
# Defaults:
# - input-dir: demo_data/mocap_optitrack
# - output-dir: demo_data/optitrack_npz
# - height: 1.7 (fixed operator height for this dataset)
uv run python data_utils/prep_optitrack_for_rt.py \
  --input-dir "demo_data/mocap_optitrack" \
  --output-dir "demo_data/optitrack_npz" \
  --height 1.7 \
  "$@"
