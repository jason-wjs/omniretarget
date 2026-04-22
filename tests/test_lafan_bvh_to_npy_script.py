from pathlib import Path


def test_lafan_bvh_to_npy_script_exists_with_expected_converter_call() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    script = repo_root / "scripts" / "retargeting" / "convert_lafan_bvh_to_npy.sh"

    assert script.is_file()
    content = script.read_text(encoding="utf-8")

    assert "data_utils/extract_global_positions.py" in content
    assert '--input-dir "demo_data/lafan1_raw_bvh"' in content
    assert '--output-dir "demo_data/lafan1"' in content
