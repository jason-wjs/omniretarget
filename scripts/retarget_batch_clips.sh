#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/.." &>/dev/null && pwd)

cd "${REPO_ROOT}/src/holosoma_retargeting"

# Batch retargeting defaults (robot-only, OptiTrack)
# Override with env vars if needed:
#   ROBOT=g1 DATA_FORMAT=optitrack DATA_DIR=demo_data/optitrack_npz SAVE_DIR=demo_results_parallel/g1/robot_only/optitrack
ROBOT="${ROBOT:-adam_pro}"
DATA_FORMAT="${DATA_FORMAT:-optitrack}"
DATA_DIR="${DATA_DIR:-demo_data/optitrack_npz}"
SAVE_DIR="${SAVE_DIR:-demo_results_parallel/${ROBOT}/robot_only/optitrack}"

uv run omniretarget-batch \
  --robot "${ROBOT}" \
  --task-config.object-name ground \
  --task-type robot_only \
  --data-format "${DATA_FORMAT}" \
  --data-dir "${DATA_DIR}" \
  --augmentation false \
  --save-dir "${SAVE_DIR}" \
  "$@"
