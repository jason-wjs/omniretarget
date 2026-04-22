from pathlib import Path

from tests.path_helpers import REPO_ROOT


def test_convert_amass_script_sets_human_body_prior_pythonpath() -> None:
    script = REPO_ROOT / "scripts" / "retargeting" / "convert_amass_smplx_to_npz.sh"

    assert script.is_file()
    content = script.read_text(encoding="utf-8")

    assert "data_utils/human_body_prior" in content
    assert "PYTHONPATH" in content
    assert "python -m data_utils.prep_amass_smplx_for_rt" in content
