#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/../.." &>/dev/null && pwd)

cd "${REPO_ROOT}/src/omniretarget"

QPOS_NPZ="${QPOS_NPZ:-demo_results/adam_pro/robot_only/omomo/sub3_largebox_003.npz}"

uv run python viser_player.py \
  --qpos-npz "${QPOS_NPZ}" \
  --robot-urdf models/adam_pro/adam_pro_29dof.urdf \
  --fps 30 \
  --no-assume-object-in-qpos \
  --no-loop \
  --show-meshes \
  --grid-width 8.0 \
  --grid-height 8.0 \
  --visual-fps-multiplier 2 \
  "$@"
