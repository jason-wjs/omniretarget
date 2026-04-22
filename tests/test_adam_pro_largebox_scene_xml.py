from pathlib import Path
import xml.etree.ElementTree as ET


def _scene_xml() -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    return (
        repo_root
        / "src"
        / "holosoma_retargeting"
        / "holosoma_retargeting"
        / "models"
        / "adam_pro"
        / "adam_pro_29dof_w_largebox.xml"
    )


def test_adam_pro_largebox_scene_xml_exists() -> None:
    assert _scene_xml().exists()


def test_adam_pro_largebox_scene_has_dynamic_object_body() -> None:
    root = ET.parse(_scene_xml()).getroot()
    mesh_names = {m.attrib["name"] for m in root.findall(".//asset/mesh") if "name" in m.attrib}
    assert "largebox_mesh" in mesh_names

    bodies = {b.attrib.get("name", ""): b for b in root.findall(".//worldbody//body")}
    assert "largebox_link" in bodies
    largebox_body = bodies["largebox_link"]

    assert largebox_body.find("freejoint") is not None
    geom_names = {g.attrib.get("name", "") for g in largebox_body.findall("geom")}
    assert "largebox" in geom_names
