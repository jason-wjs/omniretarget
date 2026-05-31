#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pickle
from pathlib import Path

import numpy as np


def load_payload(path: Path, key: str):
    with path.open("rb") as f:
        container = pickle.load(f)
    return pickle.loads(container[key])


def audit_source(root: Path) -> int:
    count = 0
    risky = 0
    for sample_path in sorted(root.rglob("*.pkl")):
        terrain = load_payload(sample_path, "terrain_data")
        hf = np.asarray(terrain["hf"], dtype=np.float64)
        if hf.size == 0:
            continue
        count += 1
        hf_min = float(np.nanmin(hf))
        hf_max = float(np.nanmax(hf))
        if hf_max <= 1e-6 and hf_min < -0.2:
            risky += 1
            print(f"RISKY_SOURCE\t{sample_path}\thf_min={hf_min:.6f}\thf_max={hf_max:.6f}")
    print(f"SUMMARY_SOURCE\tcount={count}\trisky={risky}")
    return risky


def audit_workspace(root: Path) -> int:
    count = 0
    bad = 0
    for hf_path in sorted(root.rglob("terrain_hf.npy")):
        hf = np.load(hf_path)
        count += 1
        hf_min = float(np.nanmin(hf))
        if hf_min < -1e-5:
            bad += 1
            print(f"BAD_WORKSPACE\t{hf_path}\thf_min={hf_min:.6f}")
    print(f"SUMMARY_WORKSPACE\tcount={count}\tbad={bad}")
    return bad


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit PARC terrain height origins.")
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--workspace-root", type=Path)
    args = parser.parse_args()

    exit_code = 0
    if args.source_root is not None:
        audit_source(args.source_root.expanduser().resolve())
    if args.workspace_root is not None:
        exit_code = max(exit_code, audit_workspace(args.workspace_root.expanduser().resolve()))
    raise SystemExit(1 if exit_code else 0)


if __name__ == "__main__":
    main()
