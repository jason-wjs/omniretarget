from pathlib import Path


def test_optitrack_converter_script_exists_with_expected_defaults() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    script = repo_root / "scripts" / "retargeting" / "convert_optitrack_pkl_to_npz.sh"

    assert script.is_file()
    content = script.read_text(encoding="utf-8")

    assert "data_utils/prep_optitrack_for_rt.py" in content
    assert '--input-dir "demo_data/mocap_optitrack"' in content
    assert '--output-dir "demo_data/optitrack_npz"' in content
