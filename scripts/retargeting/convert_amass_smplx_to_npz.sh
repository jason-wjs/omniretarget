#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
REPO_ROOT=$(cd -- "${SCRIPT_DIR}/../.." &>/dev/null && pwd)

source "${REPO_ROOT}/scripts/source_retargeting_setup.sh"
cd "${REPO_ROOT}/src/holosoma_retargeting/holosoma_retargeting"

# Use vendored human_body_prior package for SMPL-X body model loading.
export PYTHONPATH="${PWD}/data_utils/human_body_prior:${PYTHONPATH:-}"

# Convert AMASS SMPL-X clips to retargeting-ready NPZ files
# with keys: global_joint_positions and height.
#
# Update these placeholders to your local paths:
# - --amass-root-folder: AMASS SMPL-X root folder
# - --model-root-folder: SMPL/SMPL-X model root folder
#
# Optional:
# - --subdataset-folder: process one subset only (e.g. HumanEva)
python -m data_utils.prep_amass_smplx_for_rt \
  --amass-root-folder "/home/humanoid/Projects/Junsong_WU/adam_reference/holosoma/src/holosoma_retargeting/holosoma_retargeting/demo_data/AMASS" \
  --output-folder "demo_data/amass_npz" \
  --model-root-folder "/home/humanoid/Projects/Junsong_WU/adam_reference/holosoma/src/holosoma_retargeting/holosoma_retargeting/models" \
  "$@"
