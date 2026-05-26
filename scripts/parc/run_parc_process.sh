#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/../.." &>/dev/null && pwd)

cd "${REPO_ROOT}/src/omniretarget"

PARC_SAMPLE="${PARC_SAMPLE:-}"
PARC_MANIFEST="${PARC_MANIFEST:-}"
PARC_SOURCE_XML="${PARC_SOURCE_XML:-/home/humanoid/Projects/Junsong_WU/learning/locomotion/PARC/data/assets/humanoid.xml}"
OUTPUT_ROOT="${OUTPUT_ROOT:-/tmp/parc_process_bootstrap}"
RETARGET_SAVE_DIR="${RETARGET_SAVE_DIR:-/tmp/parc_process_workspace}"

if [[ -n "${PARC_SAMPLE}" ]]; then
  INPUT_ARGS=(--sample "${PARC_SAMPLE}")
elif [[ -n "${PARC_MANIFEST}" ]]; then
  INPUT_ARGS=(--manifest "${PARC_MANIFEST}")
else
  INPUT_ARGS=(
    --sample
    /home/humanoid/Projects/Junsong_WU/learning/locomotion/PARC/data/releases_parc/dec_release/initial_aug/platform/platform_001.pkl
  )
fi

uv run python examples/parc_process.py \
  "${INPUT_ARGS[@]}" \
  --source-xml "${PARC_SOURCE_XML}" \
  --output-root "${OUTPUT_ROOT}" \
  --retarget-save-dir "${RETARGET_SAVE_DIR}" \
  "$@"
