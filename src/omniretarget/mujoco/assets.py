from __future__ import annotations


def resolve_robot_xml_path(
    robot_model_path: str,
    object_name: str,
    *,
    scene_xml_file: str | None = None,
) -> str:
    """Resolve the MuJoCo XML path using the legacy task object rules."""
    if object_name == "ground":
        return robot_model_path.replace(".urdf", ".xml")
    if object_name == "multi_boxes":
        if scene_xml_file is None:
            raise ValueError("scene_xml_file is required when object_name='multi_boxes'")
        return scene_xml_file
    return robot_model_path.replace(".urdf", f"_w_{object_name}.xml")
