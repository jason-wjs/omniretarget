from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from omniretarget.config_types.data_type import MotionDataConfig
from omniretarget.config_types.robot import RobotConfig
from omniretarget.config_types.task import TaskConfig
from omniretarget.runtime.assets import (
    object_mesh_path,
    object_mesh_path_in_dir,
    object_urdf_path,
    object_urdf_path_in_dir,
    object_urdf_template_path,
    robot_xml_path,
    scene_xml_path,
)


_ADAM_PRO_ROBOT_ONLY_HIP_LB = {
    "8": -0.499,
    "9": -0.628,
    "14": -1.371,
    "15": -0.628,
}
_ADAM_PRO_ROBOT_ONLY_HIP_UB = {
    "8": 1.371,
    "9": 0.628,
    "14": 0.499,
    "15": 0.628,
}


@dataclass(frozen=True)
class RuntimeContext:
    """Resolved runtime facts shared by OmniRetarget workflows."""

    robot_config: RobotConfig
    motion_data_config: MotionDataConfig
    task_config: TaskConfig
    task_type: str
    object_name: str
    object_dir: Path | str | None
    robot_urdf_file: str
    object_urdf_file: str | None
    object_mesh_file: str | None
    object_urdf_template: str | None
    scene_xml_file: str | None

    def to_legacy_namespace(self) -> SimpleNamespace:
        """Return the uppercase constants namespace used by existing callers."""
        namespace = SimpleNamespace()

        for attr in dir(self.robot_config):
            if attr.isupper() and not attr.startswith("_"):
                setattr(namespace, attr, getattr(self.robot_config, attr))

        for attr, value in self.motion_data_config.legacy_constants().items():
            setattr(namespace, attr, value)

        if self.task_type == "robot_only" and self.robot_config.robot_type == "adam_pro":
            manual_lb = dict(namespace.MANUAL_LB)
            manual_ub = dict(namespace.MANUAL_UB)
            manual_lb.update(_ADAM_PRO_ROBOT_ONLY_HIP_LB)
            manual_ub.update(_ADAM_PRO_ROBOT_ONLY_HIP_UB)
            namespace.MANUAL_LB = manual_lb
            namespace.MANUAL_UB = manual_ub

        if self.task_type == "object_interaction" and self.robot_config.robot_type == "adam_pro":
            joint_mapping = dict(namespace.JOINTS_MAPPING)
            for left_key in ("L_Wrist", "LeftHand"):
                if left_key in joint_mapping:
                    joint_mapping[left_key] = "left_hand_ee_link"
            for right_key in ("R_Wrist", "RightHand"):
                if right_key in joint_mapping:
                    joint_mapping[right_key] = "right_hand_ee_link"
            namespace.JOINTS_MAPPING = joint_mapping

        namespace.OBJECT_NAME = self.object_name
        if self.task_type == "climbing":
            namespace.OBJECT_DIR = str(self.object_dir) if self.object_dir else ""
        elif self.task_type == "evaluation" and self.object_dir is not None:
            namespace.OBJECT_DIR = str(self.object_dir)
        if self.object_urdf_file is not None or self.task_type in {"robot_only", "object_interaction", "climbing"}:
            namespace.OBJECT_URDF_FILE = self.object_urdf_file
        if self.object_mesh_file is not None or self.task_type in {"robot_only", "object_interaction", "climbing"}:
            namespace.OBJECT_MESH_FILE = self.object_mesh_file
        if self.object_urdf_template is not None:
            namespace.OBJECT_URDF_TEMPLATE = self.object_urdf_template
        if self.scene_xml_file is not None:
            namespace.SCENE_XML_FILE = self.scene_xml_file

        return namespace


def build_runtime_context(
    *,
    robot_config: RobotConfig,
    motion_data_config: MotionDataConfig,
    task_config: TaskConfig,
    task_type: str,
) -> RuntimeContext:
    """Build runtime context using retargeting workflow object-resolution rules."""
    if task_type == "robot_only":
        object_name = task_config.object_name or "ground"
        object_dir = None
        object_urdf_file = None
        object_mesh_file = None
        object_urdf_template = None
        scene_xml_file = None
    elif task_type == "object_interaction":
        object_name = task_config.object_name or "largebox"
        object_dir = None
        object_urdf_file = object_urdf_path(object_name)
        object_mesh_file = object_mesh_path(object_name)
        object_urdf_template = object_urdf_template_path(object_name)
        scene_xml_file = None
    elif task_type == "climbing":
        object_name = task_config.object_name or "multi_boxes"
        object_dir = task_config.object_dir
        object_urdf_file = object_urdf_path_in_dir(object_dir, object_name) if object_dir else f"{object_name}.urdf"
        object_mesh_file = object_mesh_path_in_dir(object_dir, object_name) if object_dir else f"{object_name}.obj"
        object_urdf_template = None
        scene_xml_file = ""
    else:
        raise ValueError(f"Unknown task type: {task_type}")

    return RuntimeContext(
        robot_config=robot_config,
        motion_data_config=motion_data_config,
        task_config=task_config,
        task_type=task_type,
        object_name=object_name,
        object_dir=object_dir,
        robot_urdf_file=robot_config.ROBOT_URDF_FILE,
        object_urdf_file=object_urdf_file,
        object_mesh_file=object_mesh_file,
        object_urdf_template=object_urdf_template,
        scene_xml_file=scene_xml_file,
    )


def build_evaluation_runtime_context(
    *,
    robot_config: RobotConfig,
    motion_data_config: MotionDataConfig,
    object_name: str | None = None,
    object_dir: str | None = None,
) -> RuntimeContext:
    """Build runtime context using evaluation workflow object-resolution rules."""
    resolved_object_name = object_name or "ground"
    object_urdf_file = None
    object_mesh_file = None
    object_urdf_template = None

    if resolved_object_name != "ground":
        object_urdf_file = object_urdf_path(resolved_object_name)
        object_mesh_file = object_mesh_path(resolved_object_name)
        object_urdf_template = object_urdf_template_path(resolved_object_name)
        scene_xml_file = scene_xml_path(robot_config.robot_type, robot_config.ROBOT_DOF, resolved_object_name)
    else:
        scene_xml_file = robot_xml_path(robot_config.ROBOT_URDF_FILE)

    if object_dir is not None:
        object_urdf_file = object_urdf_path_in_dir(object_dir, resolved_object_name)
        object_mesh_file = object_mesh_path_in_dir(object_dir, resolved_object_name)

    return RuntimeContext(
        robot_config=robot_config,
        motion_data_config=motion_data_config,
        task_config=TaskConfig(object_name=resolved_object_name),
        task_type="evaluation",
        object_name=resolved_object_name,
        object_dir=object_dir,
        robot_urdf_file=robot_config.ROBOT_URDF_FILE,
        object_urdf_file=object_urdf_file,
        object_mesh_file=object_mesh_file,
        object_urdf_template=object_urdf_template,
        scene_xml_file=scene_xml_file,
    )


def build_mj_conversion_runtime_context(
    *,
    robot_config: RobotConfig,
    motion_data_config: MotionDataConfig,
    object_name: str | None = None,
) -> RuntimeContext:
    """Build runtime context using standard MJ conversion object-resolution rules."""
    resolved_object_name = object_name or "ground"

    if resolved_object_name != "ground":
        object_urdf_file = object_urdf_path(resolved_object_name)
        object_mesh_file = object_mesh_path(resolved_object_name)
        object_urdf_template = object_urdf_template_path(resolved_object_name)
        scene_xml_file = scene_xml_path(robot_config.robot_type, robot_config.ROBOT_DOF, resolved_object_name)
    else:
        object_urdf_file = robot_config.ROBOT_URDF_FILE
        object_mesh_file = ""
        object_urdf_template = None
        scene_xml_file = robot_xml_path(robot_config.ROBOT_URDF_FILE)

    return RuntimeContext(
        robot_config=robot_config,
        motion_data_config=motion_data_config,
        task_config=TaskConfig(object_name=resolved_object_name),
        task_type="mj_conversion",
        object_name=resolved_object_name,
        object_dir=None,
        robot_urdf_file=robot_config.ROBOT_URDF_FILE,
        object_urdf_file=object_urdf_file,
        object_mesh_file=object_mesh_file,
        object_urdf_template=object_urdf_template,
        scene_xml_file=scene_xml_file,
    )
