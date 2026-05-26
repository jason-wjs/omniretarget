#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/../.." &>/dev/null && pwd)

cd "${REPO_ROOT}/src/omniretarget"

RETARGET_SAVE_DIR="${RETARGET_SAVE_DIR:-/tmp/parc_process_workspace}"
PARC_TASK="${PARC_TASK:-beyond_dash_vault_001_aug001_dm}"
ROBOT_URDF="${ROBOT_URDF:-models/g1/g1_29dof_spherehand.urdf}"
OBJECT_URDF="${OBJECT_URDF:-${RETARGET_SAVE_DIR}/workspace/${PARC_TASK}/multi_boxes.urdf}"
QPOS_NPZ="${QPOS_NPZ:-${RETARGET_SAVE_DIR}/retargeted/${PARC_TASK}_original.npz}"

## platform_001
# PARC_TASK=platform_001 bash scripts/parc/vis_parc_process.sh

## mid_blocks_004_dm
# PARC_TASK=mid_blocks_004_dm bash scripts/parc/vis_parc_process.sh

## climbing_up_down_terrain_001_aug001_dm
# PARC_TASK=climbing_up_down_terrain_001_aug001_dm bash scripts/parc/vis_parc_process.sh

## beyond_dash_vault_001_aug001_dm
uv run python viser_player.py \
  --qpos-npz "${QPOS_NPZ}" \
  --robot-urdf "${ROBOT_URDF}" \
  --object-urdf "${OBJECT_URDF}" \
  --no-assume-object-in-qpos \
  "$@"
