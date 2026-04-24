from pathlib import Path

from tests.path_helpers import REPO_ROOT


def test_quantitative_eval_script_exists_with_adam_pro_robot_only_defaults() -> None:
    script = REPO_ROOT / "scripts" / "retargeting" / "quantitative_evaluation.sh"

    assert script.is_file()
    content = script.read_text(encoding="utf-8")

    assert "uv run omniretarget-eval" in content
    assert "--robot adam_pro" in content
    assert "--data-type robot_only" in content
    assert '--res-dir "demo_results_parallel/adam_pro/robot_only/omomo"' in content
    assert '--data-dir "demo_data/OMOMO_new"' in content
