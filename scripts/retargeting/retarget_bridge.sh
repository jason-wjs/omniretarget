#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/../.." &>/dev/null && pwd)

cd "${REPO_ROOT}/src/omniretarget"

## omomo_robot_only
# python data_conversion/convert_data_format_mj.py \
#   --input_file ./demo_results/g1/robot_only/omomo/sub3_largebox_003.npz \
#   --output_fps 50 \
#   --output_name converted_res/robot_only/sub3_largebox_003_mj_fps50.npz \
#   --data_format smplh \
#   --object_name "ground" \
#   --once \
#   --no-viewer \
#   "$@"

## omomo_object_interaction
# python data_conversion/convert_data_format_mj.py \
#   --input_file ./demo_results/g1/object_interaction/omomo/sub3_largebox_003.npz \
#   --output_fps 50 \
#   --output_name converted_res/object_interaction/sub3_largebox_003_mj_fps50.npz \
#   --data_format smplh \
#   --object_name "largebox" \
#   --once \
#   --no-viewer \
#   "$@"

## lafan_robot_only
uv run python data_conversion/convert_data_format_mj.py \
  --input_file ./demo_results/adam_pro/robot_only/lafan1/dance1_subject1.npz \
  --output_fps 50 \
  --output_name converted_res/robot_only/lafan1/dance1_subject1_mj_fps50.npz \
  --data_format lafan \
  --object_name "ground" \
  --once \
  --no-viewer \
  "$@"
