from pathlib import Path
import xml.etree.ElementTree as ET


def _model_xml() -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / "src" / "holosoma_retargeting" / "holosoma_retargeting" / "models" / "adam_pro" / "adam_pro_29dof.xml"


def test_adam_pro_has_collidable_foot_patch_sphere_geoms() -> None:
    root = ET.parse(_model_xml()).getroot()
    geom_names = {g.attrib["name"] for g in root.findall(".//geom") if "name" in g.attrib}

    for side in ("left", "right"):
        for idx in (1, 2, 3, 4, 5):
            assert f"{side}_foot_sphere_{idx}_link" in geom_names
