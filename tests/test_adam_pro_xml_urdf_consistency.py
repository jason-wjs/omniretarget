from pathlib import Path
import xml.etree.ElementTree as ET

from tests.path_helpers import PACKAGE_ROOT

XML = PACKAGE_ROOT / "models" / "adam_pro" / "adam_pro_29dof.xml"
URDF = PACKAGE_ROOT / "models" / "adam_pro" / "adam_pro_29dof.urdf"
FOOT_MARKERS = [
    "left_foot_sphere_1_link",
    "left_foot_sphere_2_link",
    "left_foot_sphere_3_link",
    "left_foot_sphere_4_link",
    "left_foot_sphere_5_link",
    "right_foot_sphere_1_link",
    "right_foot_sphere_2_link",
    "right_foot_sphere_3_link",
    "right_foot_sphere_4_link",
    "right_foot_sphere_5_link",
]


def _xml_joint_names() -> list[str]:
    root = ET.parse(XML).getroot()
    return [j.attrib["name"] for j in root.findall(".//joint") if j.attrib.get("name") != "floating_base"]


def _urdf_revolute_joint_names() -> list[str]:
    root = ET.parse(URDF).getroot()
    return [j.attrib["name"] for j in root.findall("joint") if j.attrib.get("type") == "revolute"]


def _xml_body_names() -> set[str]:
    root = ET.parse(XML).getroot()
    return {b.attrib["name"] for b in root.findall(".//body") if "name" in b.attrib}


def _urdf_link_names() -> set[str]:
    root = ET.parse(URDF).getroot()
    return {l.attrib["name"] for l in root.findall("link") if "name" in l.attrib}


def test_urdf_exists() -> None:
    assert URDF.is_file()


def test_xml_urdf_joint_order_match_exactly() -> None:
    assert _urdf_revolute_joint_names() == _xml_joint_names()


def test_foot_patch_markers_exist_in_xml_and_urdf() -> None:
    xml_bodies = _xml_body_names()
    urdf_links = _urdf_link_names()
    for marker in FOOT_MARKERS:
        assert marker in xml_bodies
        assert marker in urdf_links
