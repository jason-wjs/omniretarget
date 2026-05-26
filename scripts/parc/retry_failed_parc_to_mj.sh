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
ROBOT_TYPE="${ROBOT_TYPE:-g1}"
FAILED_LOG="${FAILED_LOG:-${OUTPUT_ROOT}/logs/failed.txt}"
LIMIT="${LIMIT:-}"

if [[ ! -f "${FAILED_LOG}" ]]; then
  echo "Failed log not found: ${FAILED_LOG}" >&2
  exit 1
fi

RETRY_LOG_DIR="${RETRY_LOG_DIR:-${OUTPUT_ROOT}/logs/retry_$(date +%Y%m%d_%H%M%S)}"
mkdir -p "${RETRY_LOG_DIR}"

SUCCEEDED_LOG="${RETRY_LOG_DIR}/succeeded.txt"
FAILED_RETRY_LOG="${RETRY_LOG_DIR}/failed.txt"
SKIPPED_LOG="${RETRY_LOG_DIR}/skipped.txt"
PLANNED_LOG="${RETRY_LOG_DIR}/planned.txt"

: >"${SUCCEEDED_LOG}"
: >"${FAILED_RETRY_LOG}"
: >"${SKIPPED_LOG}"
: >"${PLANNED_LOG}"

mapfile -t FAILED_SAMPLES < <(
  FAILED_LOG="${FAILED_LOG}" SOURCE_ROOT="${SOURCE_ROOT}" uv run python - <<'PY'
from __future__ import annotations

import os
from pathlib import Path

failed_log = Path(os.environ["FAILED_LOG"]).expanduser()
source_root = Path(os.environ["SOURCE_ROOT"]).expanduser().resolve()

seen: set[Path] = set()
for line in failed_log.read_text(encoding="utf-8", errors="replace").splitlines():
    if "\t" not in line:
        continue
    sample_text = line.split("\t", 1)[0].strip()
    if not sample_text.endswith(".pkl"):
        continue
    sample = Path(sample_text).expanduser().resolve()
    if not sample.is_file():
        continue
    try:
        sample.relative_to(source_root)
    except ValueError:
        continue
    if sample in seen:
        continue
    seen.add(sample)
    print(sample)
PY
)

if [[ -n "${LIMIT}" ]]; then
  FAILED_SAMPLES=("${FAILED_SAMPLES[@]:0:${LIMIT}}")
fi

TOTAL=${#FAILED_SAMPLES[@]}
echo "Retry samples: ${TOTAL}"
echo "Source root: ${SOURCE_ROOT}"
echo "Output root: ${OUTPUT_ROOT}"
echo "Retry logs: ${RETRY_LOG_DIR}"

converted=0
skipped=0
failed=0

for i in "${!FAILED_SAMPLES[@]}"; do
  sample="${FAILED_SAMPLES[$i]}"
  current=$((i + 1))
  echo "[${current}/${TOTAL}] ${sample}"
  printf '%s\n' "${sample}" >>"${PLANNED_LOG}"

  set +e
  output=$(
    SAMPLE_PATH="${sample}" \
    SOURCE_ROOT="${SOURCE_ROOT}" \
    SOURCE_XML="${SOURCE_XML}" \
    OUTPUT_ROOT="${OUTPUT_ROOT}" \
    ROBOT_XML="${ROBOT_XML}" \
    OUTPUT_FPS="${OUTPUT_FPS}" \
    ROBOT_TYPE="${ROBOT_TYPE}" \
    uv run python - <<'PY' 2>&1
from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

from omniretarget.examples.parc_batch_process_to_mj import (
    ParcBatchConfig,
    _process_one_sample,
    build_sample_plan,
)

sample = Path(os.environ["SAMPLE_PATH"]).expanduser().resolve()
source_root = Path(os.environ["SOURCE_ROOT"]).expanduser().resolve()
source_xml = Path(os.environ["SOURCE_XML"]).expanduser().resolve()
output_root = Path(os.environ["OUTPUT_ROOT"]).expanduser().resolve()
robot_xml = Path(os.environ["ROBOT_XML"]).expanduser().resolve()
output_fps = int(os.environ["OUTPUT_FPS"])
robot_type = os.environ["ROBOT_TYPE"]

plan = build_sample_plan(source_root=source_root, sample_path=sample, output_root=output_root)
if plan.mj_motion_file.exists():
    print(f"SKIPPED\t{sample}\t{plan.mj_motion_file}")
    sys.exit(0)

config = ParcBatchConfig(
    source_root=source_root,
    source_xml=source_xml,
    output_root=output_root,
    robot_xml=robot_xml,
    output_fps=output_fps,
    robot_type=robot_type,
    skip_existing=True,
    continue_on_error=True,
)

try:
    result = _process_one_sample(config, plan)
except Exception:
    print(f"FAILED\t{sample}\t{plan.mj_motion_file}")
    traceback.print_exc()
    sys.exit(1)

print(f"CONVERTED\t{sample}\t{result.mj_motion_file}")
PY
  )
  status=$?
  set -e

  result_line=$(printf '%s\n' "${output}" | awk -F '\t' '/^(CONVERTED|SKIPPED|FAILED)\t/ { line=$0 } END { print line }')
  if [[ ${status} -eq 0 && "${result_line}" == CONVERTED$'\t'* ]]; then
    printf '%s\n' "${result_line}" >>"${SUCCEEDED_LOG}"
    converted=$((converted + 1))
  elif [[ ${status} -eq 0 && "${result_line}" == SKIPPED$'\t'* ]]; then
    printf '%s\n' "${result_line}" >>"${SKIPPED_LOG}"
    skipped=$((skipped + 1))
  else
    {
      printf 'SAMPLE\t%s\n' "${sample}"
      printf 'EXIT_STATUS\t%s\n' "${status}"
      printf '%s\n' "${output}"
      printf '\n'
    } >>"${FAILED_RETRY_LOG}"
    failed=$((failed + 1))
  fi
done

echo "Retry complete."
echo "Converted: ${converted}"
echo "Skipped: ${skipped}"
echo "Failed: ${failed}"
echo "Logs: ${RETRY_LOG_DIR}"
