#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/../.." &>/dev/null && pwd)

cd "${REPO_ROOT}"

SOURCE_ROOT="${SOURCE_ROOT:-/home/humanoid/Projects/Junsong_WU/learning/locomotion/PARC/data/releases_parc/dec_release/initial_aug}"
SOURCE_XML="${SOURCE_XML:-/home/humanoid/Projects/Junsong_WU/learning/locomotion/PARC/data/assets/humanoid.xml}"
OUTPUT_ROOT="${OUTPUT_ROOT:-/tmp/parc_initial_aug_g1}"
ROBOT_XML="${ROBOT_XML:-/home/humanoid/Projects/Junsong_WU/learning/locomotion/controller/mjlab/src/mjlab/asset_zoo/robots/unitree_g1/xmls/g1.xml}"
OUTPUT_FPS="${OUTPUT_FPS:-50}"

uv run python -m omniretarget.examples.parc_batch_process_to_mj \
  --source-root "${SOURCE_ROOT}" \
  --source-xml "${SOURCE_XML}" \
  --output-root "${OUTPUT_ROOT}" \
  --robot-xml "${ROBOT_XML}" \
  --output-fps "${OUTPUT_FPS}" \
  --skip-existing \
  --continue-on-error \
  "$@"
