from __future__ import annotations

import tyro

from holosoma_retargeting.evaluation.eval_retargeting import Args, main as run_evaluation


def main() -> None:
    cfg = tyro.cli(Args)
    run_evaluation(cfg)


if __name__ == "__main__":
    main()
