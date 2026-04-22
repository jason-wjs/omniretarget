from pathlib import Path
import xml.etree.ElementTree as ET

MODEL_XML = Path("holosoma_retargeting/models/adam_pro/adam_pro_29dof.xml")

EXPECTED_29 = [
    "hipPitch_Left",
    "hipRoll_Left",
    "hipYaw_Left",
    "kneePitch_Left",
    "anklePitch_Left",
    "ankleRoll_Left",
    "hipPitch_Right",
    "hipRoll_Right",
    "hipYaw_Right",
    "kneePitch_Right",
    "anklePitch_Right",
    "ankleRoll_Right",
    "waistRoll",
    "waistPitch",
    "waistYaw",
    "shoulderPitch_Left",
    "shoulderRoll_Left",
    "shoulderYaw_Left",
    "elbow_Left",
    "wristYaw_Left",
    "wristPitch_Left",
    "wristRoll_Left",
    "shoulderPitch_Right",
    "shoulderRoll_Right",
    "shoulderYaw_Right",
    "elbow_Right",
    "wristYaw_Right",
    "wristPitch_Right",
    "wristRoll_Right",
]


def test_refined_xml_exists() -> None:
    assert MODEL_XML.is_file()


def test_refined_xml_has_expected_joint_set_and_order() -> None:
    root = ET.parse(MODEL_XML).getroot()
    names = [
        j.attrib["name"]
        for j in root.findall(".//joint")
        if "name" in j.attrib and j.attrib["name"] != "floating_base"
    ]
    assert names == EXPECTED_29


def test_refined_xml_drops_retargeting_irrelevant_sections() -> None:
    root = ET.parse(MODEL_XML).getroot()
    assert root.find("actuator") is None
    assert root.find("sensor") is None
