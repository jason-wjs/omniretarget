#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/../.." &>/dev/null && pwd)

cd "${REPO_ROOT}/src/omniretarget"

INPUT_FILE="${INPUT_FILE:-/tmp/parc_process_workspace/retargeted/platform_001_original.npz}"
OUTPUT_NAME="${OUTPUT_NAME:-/tmp/tt_converted/platform_001/motion.npz}"
ROBOT_XML="${ROBOT_XML:-/home/humanoid/Projects/Junsong_WU/learning/locomotion/controller/mjlab/src/mjlab/asset_zoo/robots/unitree_g1/xmls/g1.xml}"
OUTPUT_FPS="${OUTPUT_FPS:-50}"

uv run python -m omniretarget.data_conversion.convert_data_format_parc_mj \
  --input-file "${INPUT_FILE}" \
  --output-name "${OUTPUT_NAME}" \
  --robot-xml "${ROBOT_XML}" \
  --output-fps "${OUTPUT_FPS}" \
  "$@"
