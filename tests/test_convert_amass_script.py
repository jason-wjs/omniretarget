from pathlib import Path

from tests.path_helpers import REPO_ROOT


def test_convert_amass_script_supports_human_body_prior_root() -> None:
    script = REPO_ROOT / "scripts" / "data_process" / "convert_amass_smplx_to_npz.sh"

    assert script.is_file()
    content = script.read_text(encoding="utf-8")

    assert "data_utils/human_body_prior" not in content
    assert "HUMAN_BODY_PRIOR_ROOT" in content
    assert "PYTHONPATH" in content
    assert "uv run omniretarget-prep-amass" in content
