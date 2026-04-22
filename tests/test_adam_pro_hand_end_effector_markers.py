from pathlib import Path
import xml.etree.ElementTree as ET

from tests.path_helpers import PACKAGE_ROOT


def _model_xml() -> Path:
    return PACKAGE_ROOT / "models" / "adam_pro" / "adam_pro_29dof.xml"


def test_adam_pro_has_hand_end_effector_markers_in_xml() -> None:
    root = ET.parse(_model_xml()).getroot()
    body_names = {b.attrib["name"] for b in root.findall(".//body") if "name" in b.attrib}

    assert "left_hand_ee_link" in body_names
    assert "right_hand_ee_link" in body_names
