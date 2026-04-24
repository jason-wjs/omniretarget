#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/.." &>/dev/null && pwd)

cd "${REPO_ROOT}/src/holosoma_retargeting"

uv run omniretarget-eval \
  --res-dir "demo_results_parallel/adam_pro/robot_only/omomo" \
  --data-dir "demo_data/OMOMO_new" \
  --data-type robot_only \
  --robot adam_pro \
  --data-format smplh \
  --max-workers 1 \
  "$@"
