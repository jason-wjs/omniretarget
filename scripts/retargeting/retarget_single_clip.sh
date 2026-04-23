#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/../.." &>/dev/null && pwd)

cd "${REPO_ROOT}/src/holosoma_retargeting"

## omomo_robot_only
# python -m holosoma_retargeting.cli.retarget \
#   --robot adam_pro \
#   --task-type robot_only \
#   --task-name sub3_largebox_003 \
#   --data-path demo_data/OMOMO_new \
#   --data-format smplh \
#   --save-dir "demo_results/adam_pro/robot_only/omomo" \
#   --retargeter.debug \
#   --retargeter.visualize \
#   "$@"

## omomo_object_interaction
# python -m holosoma_retargeting.cli.retarget \
#   --robot adam_pro \
#   --task-type object_interaction \
#   --task-name sub3_largebox_003 \
#   --data-path demo_data/OMOMO_new \
#   --data-format smplh \
#   --save-dir "demo_results/adam_pro/object_interaction/omomo" \
#   --retargeter.debug \
#   --retargeter.visualize \
#   "$@"

## lafan1
uv run python -m holosoma_retargeting.cli.retarget \
  --robot adam_pro \
  --task-type robot_only \
  --task-name dance1_subject1 \
  --data-path demo_data/lafan1_npy \
  --data-format lafan \
  --save-dir "demo_results/adam_pro/robot_only/lafan1" \
  --task-config.ground-range -15 15 \
  --retargeter.foot-sticking-tolerance 0.02 \
  --retargeter.debug \
  --retargeter.visualize \
  "$@"

## amass
# python -m holosoma_retargeting.cli.retarget \
#   --robot adam_pro \
#   --task-type robot_only \
#   --task-name demo_data_AMASS_E6_-_quick_retreat_stageii \
#   --data-path demo_data/amass_npz \
#   --data-format smplx \
#   --save-dir "demo_results/adam_pro/robot_only/amass" \
#   --retargeter.debug \
#   --retargeter.visualize \
#   "$@"

## optitrack
# python -m holosoma_retargeting.cli.retarget \
#   --robot adam_pro \
#   --task-type robot_only \
#   --task-name turn \
#   --data-path demo_data/custom_optitrack_npz \
#   --data-format optitrack \
#   --save-dir "demo_results/adam_pro/robot_only/optitrack" \
#   --retargeter.debug \
#   --retargeter.visualize \
#   "$@"
