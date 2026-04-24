#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/../.." &>/dev/null && pwd)

cd "${REPO_ROOT}/src/holosoma_retargeting"

# Use vendored human_body_prior package for SMPL-X body model loading.
export PYTHONPATH="${PWD}/data_utils/human_body_prior:${PYTHONPATH:-}"

AMASS_ROOT="${AMASS_ROOT:-demo_data/AMASS}"
OUTPUT_DIR="${OUTPUT_DIR:-demo_data/amass_npz}"
MODEL_ROOT="${MODEL_ROOT:-models}"

# Convert AMASS SMPL-X clips to retargeting-ready NPZ files
# with keys: global_joint_positions and height.
#
# Update these placeholders to your local paths:
# - --amass-root-folder: AMASS SMPL-X root folder
# - --model-root-folder: SMPL/SMPL-X model root folder
#
# Optional:
# - --subdataset-folder: process one subset only (e.g. HumanEva)
uv run omniretarget-prep-amass \
  --amass-root-folder "${AMASS_ROOT}" \
  --output-folder "${OUTPUT_DIR}" \
  --model-root-folder "${MODEL_ROOT}" \
  "$@"
