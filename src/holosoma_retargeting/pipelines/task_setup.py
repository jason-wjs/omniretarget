from __future__ import annotations

from types import SimpleNamespace
from typing import Literal

from holosoma_retargeting.config_types.data_type import DEMO_JOINTS_REGISTRY, MotionDataConfig
from holosoma_retargeting.config_types.retargeting import RetargetingConfig
from holosoma_retargeting.config_types.robot import RobotConfig
from holosoma_retargeting.config_types.task import TaskConfig
from holosoma_retargeting.path_utils import package_path


DEFAULT_DATA_FORMATS = {
    "robot_only": "smplh",
    "object_interaction": "smplh",
    "climbing": "mocap",
}

DEFAULT_SAVE_DIRS = {
    "robot_only": "demo_results/{robot}/robot_only/omomo",
    "object_interaction": "demo_results/{robot}/object_interaction/omomo",
    "climbing": "demo_results/{robot}/climbing/mocap_climb",
}


TaskType = Literal["robot_only", "object_interaction", "climbing"]


# Adam Pro robot-only hip constraint profile (moderate, asymmetry-preserving).
# Indices are qpos indices in the retargeting optimization state when q_a_init_idx == -7.
_ADAM_PRO_ROBOT_ONLY_HIP_LB = {
    "8": -0.499,  # left hip roll
    "9": -0.628,  # left hip yaw
    "14": -1.371,  # right hip roll
    "15": -0.628,  # right hip yaw
}
_ADAM_PRO_ROBOT_ONLY_HIP_UB = {
    "8": 1.371,  # left hip roll
    "9": 0.628,  # left hip yaw
    "14": 0.499,  # right hip roll
    "15": 0.628,  # right hip yaw
}


def create_task_constants(
    robot_config: RobotConfig,
    motion_data_config: MotionDataConfig,
    task_config: TaskConfig,
    task_type: str,
) -> SimpleNamespace:
    """Create combined task constants from robot and motion data configs."""
    task_constants = SimpleNamespace()

    # Copy all attributes from robot_config.
    for attr in dir(robot_config):
        if attr.isupper() and not attr.startswith("_"):
            setattr(task_constants, attr, getattr(robot_config, attr))

    # Copy legacy motion data constants (upper-case for compatibility).
    for attr, value in motion_data_config.legacy_constants().items():
        setattr(task_constants, attr, value)

    # Robot-only Adam Pro profile: apply hip roll/yaw manual bounds only.
    # Keep manual costs untouched (no hip zero-centering prior requested).
    if task_type == "robot_only" and robot_config.robot_type == "adam_pro":
        manual_lb = dict(task_constants.MANUAL_LB)
        manual_ub = dict(task_constants.MANUAL_UB)
        manual_lb.update(_ADAM_PRO_ROBOT_ONLY_HIP_LB)
        manual_ub.update(_ADAM_PRO_ROBOT_ONLY_HIP_UB)
        task_constants.MANUAL_LB = manual_lb
        task_constants.MANUAL_UB = manual_ub

    # Task-aware mapping override for Adam Pro object interaction:
    # use hand EE markers only in object mode, while keeping robot-only mappings unchanged.
    if task_type == "object_interaction" and robot_config.robot_type == "adam_pro":
        joint_mapping = dict(task_constants.JOINTS_MAPPING)
        for left_key in ("L_Wrist", "LeftHand"):
            if left_key in joint_mapping:
                joint_mapping[left_key] = "left_hand_ee_link"
        for right_key in ("R_Wrist", "RightHand"):
            if right_key in joint_mapping:
                joint_mapping[right_key] = "right_hand_ee_link"
        task_constants.JOINTS_MAPPING = joint_mapping

    # Task-specific object setup.
    if task_type == "robot_only":
        obj_name = task_config.object_name or "ground"
        task_constants.OBJECT_NAME = obj_name
        task_constants.OBJECT_URDF_FILE = None
        task_constants.OBJECT_MESH_FILE = None
    elif task_type == "object_interaction":
        obj_name = task_config.object_name or "largebox"
        task_constants.OBJECT_NAME = obj_name
        task_constants.OBJECT_URDF_FILE = str(package_path(f"models/{obj_name}/{obj_name}.urdf"))
        task_constants.OBJECT_MESH_FILE = str(package_path(f"models/{obj_name}/{obj_name}.obj"))
        task_constants.OBJECT_URDF_TEMPLATE = str(package_path(f"models/templates/{obj_name}.urdf.jinja"))
    elif task_type == "climbing":
        obj_name = task_config.object_name or "multi_boxes"
        task_constants.OBJECT_NAME = obj_name
        object_dir = task_config.object_dir
        task_constants.OBJECT_DIR = str(object_dir) if object_dir else ""
        task_constants.OBJECT_URDF_FILE = str(object_dir / f"{obj_name}.urdf") if object_dir else f"{obj_name}.urdf"
        task_constants.OBJECT_MESH_FILE = str(object_dir / f"{obj_name}.obj") if object_dir else f"{obj_name}.obj"
        task_constants.SCENE_XML_FILE = ""  # Will be set later.

    return task_constants


def validate_config(cfg: RetargetingConfig) -> None:
    """Validate configuration consistency."""
    if cfg.data_format is not None and cfg.data_format not in DEMO_JOINTS_REGISTRY:
        available = ", ".join(sorted(DEMO_JOINTS_REGISTRY.keys()))
        raise ValueError(
            f"Unknown data_format: '{cfg.data_format}'. "
            f"Available formats: {available}. "
            f"Add your format to DEMO_JOINTS_REGISTRY in config_types/data_type.py"
        )

    if cfg.task_type == "climbing" and cfg.data_format not in (None, "mocap"):
        raise ValueError("Climbing task requires 'mocap' data format")
    if cfg.task_type == "object_interaction" and cfg.data_format not in (None, "smplh"):
        raise ValueError("Object interaction requires 'smplh' data format")
    # robot_only accepts any format in the registry (already validated above).
