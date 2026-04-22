# OmniRetarget

Standalone motion-retargeting repository bootstrapped from `holosoma_retargeting`.

Current rule: `holosoma/` is the read-only blueprint. All new work happens in this repository.

## Setup

```bash
UV_CACHE_DIR=/tmp/uv-cache uv sync
```

## Run

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python src/holosoma_retargeting/examples/robot_retarget.py --help
```
