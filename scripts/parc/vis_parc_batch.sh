#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/../.." &>/dev/null && pwd)

cd "${REPO_ROOT}"

OUTPUT_ROOT="${OUTPUT_ROOT:-/home/humanoid/Downloads/Data/parc_initial_aug_g1_v2_height_fixed_mid_climbing_full_20260531}"
PARC_DATASET="${PARC_DATASET:-mid_climbing}"
ROBOT_URDF="${ROBOT_URDF:-src/omniretarget/models/g1/g1_29dof_spherehand.urdf}"

args=(
  python -m omniretarget.examples.parc_batch_vis
  --output-root "${OUTPUT_ROOT}"
  --dataset "${PARC_DATASET}"
  --robot-urdf "${ROBOT_URDF}"
)

if [[ -n "${TASK_LIST:-}" ]]; then
  args+=(--task-list "${TASK_LIST}")
fi

if [[ -n "${REVIEW_FILE:-}" ]]; then
  args+=(--review-file "${REVIEW_FILE}")
fi

uv run "${args[@]}" "$@"
