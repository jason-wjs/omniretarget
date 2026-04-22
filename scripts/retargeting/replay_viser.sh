#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/../.." &>/dev/null && pwd)

source "${REPO_ROOT}/scripts/source_retargeting_setup.sh"
cd "${REPO_ROOT}/src/holosoma_retargeting/holosoma_retargeting"

python viser_player.py \
  --qpos-npz "/home/humanoid/Projects/Junsong_WU/adam_reference/holosoma/src/holosoma_retargeting/holosoma_retargeting/demo_results/adam_pro/robot_only/omomo/sub3_largebox_003.npz" \
  --robot-urdf models/adam_pro/adam_pro_29dof.urdf \
  --fps 30 \
  --no-assume-object-in-qpos \
  --no-loop \
  --show-meshes \
  --grid-width 8.0 \
  --grid-height 8.0 \
  --visual-fps-multiplier 2 \
  "$@"

