#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/../.." &>/dev/null && pwd)

source "${REPO_ROOT}/scripts/source_retargeting_setup.sh"
cd "${REPO_ROOT}/src/holosoma_retargeting/holosoma_retargeting"

# Convert LAFAN BVH clips to global-position NPY clips.
# Defaults (adjust or override via "$@"):
# - input-dir: demo_data/lafan1_raw_bvh
# - output-dir: demo_data/lafan1
python data_utils/extract_global_positions.py \
  --input-dir "demo_data/lafan_raw" \
  --output-dir "demo_data/lafan1" \
  "$@"
