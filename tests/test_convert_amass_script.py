from pathlib import Path


def test_convert_amass_script_sets_human_body_prior_pythonpath() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    script = repo_root / "scripts" / "retargeting" / "convert_amass_smplx_to_npz.sh"

    assert script.is_file()
    content = script.read_text(encoding="utf-8")

    assert "data_utils/human_body_prior" in content
    assert "PYTHONPATH" in content
    assert "python -m data_utils.prep_amass_smplx_for_rt" in content
