from tests.path_helpers import REPO_ROOT


def test_single_retarget_script_uses_cli_entrypoint() -> None:
    script = REPO_ROOT / "scripts" / "retargeting" / "retarget_single_clip.sh"

    assert script.is_file()
    content = script.read_text(encoding="utf-8")

    assert "uv run python -m holosoma_retargeting.cli.retarget" in content


def test_replay_script_uses_cli_entrypoint() -> None:
    script = REPO_ROOT / "scripts" / "retargeting" / "replay_viser.sh"

    assert script.is_file()
    content = script.read_text(encoding="utf-8")

    assert "uv run python -m holosoma_retargeting.cli.replay" in content


def test_bridge_conversion_script_uses_cli_entrypoint() -> None:
    script = REPO_ROOT / "scripts" / "retargeting" / "retarget_bridge.sh"

    assert script.is_file()
    content = script.read_text(encoding="utf-8")

    assert "uv run python -m holosoma_retargeting.cli.convert_mj" in content
