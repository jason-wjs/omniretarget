from __future__ import annotations

from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent


def package_path(relative_path: str | Path) -> Path:
    path = Path(relative_path)
    if path.is_absolute():
        return path
    return PACKAGE_ROOT / path


def model_path(relative_path: str | Path = Path()) -> Path:
    path = Path(relative_path)
    if path.is_absolute():
        return path
    return package_path(Path("models") / path)


def demo_data_path(relative_path: str | Path = Path()) -> Path:
    path = Path(relative_path)
    if path.is_absolute():
        return path
    return package_path(Path("demo_data") / path)
