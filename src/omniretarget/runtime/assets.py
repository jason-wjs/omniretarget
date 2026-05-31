from __future__ import annotations

from pathlib import Path

from omniretarget.path_utils import package_path


def robot_urdf_path(robot_type: str, robot_dof: int) -> str:
    """Return the package path for a robot URDF."""
    return str(package_path(f"models/{robot_type}/{robot_type}_{robot_dof}dof.urdf"))


def robot_xml_path(robot_urdf_file: str) -> str:
    """Return the legacy robot XML path derived from a robot URDF path."""
    return robot_urdf_file.replace(".urdf", ".xml")


def object_urdf_path(object_name: str) -> str:
    """Return the package path for an object URDF."""
    return str(package_path(f"models/{object_name}/{object_name}.urdf"))


def object_mesh_path(object_name: str) -> str:
    """Return the package path for an object mesh."""
    return str(package_path(f"models/{object_name}/{object_name}.obj"))


def object_urdf_template_path(object_name: str) -> str:
    """Return the package path for an object URDF template."""
    return str(package_path(f"models/templates/{object_name}.urdf.jinja"))


def scene_xml_path(robot_type: str, robot_dof: int, object_name: str) -> str:
    """Return the package path for a robot/object scene XML."""
    return str(package_path(f"models/{robot_type}/{robot_type}_{robot_dof}dof_w_{object_name}.xml"))


def object_urdf_path_in_dir(object_dir: Path | str, object_name: str) -> str:
    """Return an object URDF path using the caller's legacy directory semantics."""
    if isinstance(object_dir, Path):
        return str(object_dir / f"{object_name}.urdf")
    return f"{object_dir}/{object_name}.urdf"


def object_mesh_path_in_dir(object_dir: Path | str, object_name: str) -> str:
    """Return an object mesh path using the caller's legacy directory semantics."""
    if isinstance(object_dir, Path):
        return str(object_dir / f"{object_name}.obj")
    return f"{object_dir}/{object_name}.obj"
