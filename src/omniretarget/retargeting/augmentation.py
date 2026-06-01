from __future__ import annotations

import numpy as np


def generate_augmentation_configs(task_type: str, augmentation: bool = True):
    """Generate augmentation configurations based on task type."""
    if task_type == "robot_only":
        return [{"name": "original"}]

    if task_type == "object_interaction":
        augmentations = []
        augmentations.append({"name": "original", "translation": np.array([0.0, 0.0, 0.0]), "rotation": 0.0})

        if augmentation:
            translations = [
                [0.2, 0.0, 0.0],
                [0.0, 0.2, 0.0],
                [0.0, -0.2, 0.0],
            ]
            for i, trans in enumerate(translations):
                augmentations.append({"name": f"trans_{i}", "translation": np.array(trans), "rotation": 0.0})

            rotations = [np.pi / 4, -np.pi / 4]
            for i, rot in enumerate(rotations):
                augmentations.append(
                    {
                        "name": f"rot_{i}",
                        "translation": np.array([0.0, 0.2 * (-1) ** i, 0.0]),
                        "rotation": rot,
                    }
                )

        return augmentations

    if task_type == "climbing":
        configs = [{"name": "original", "scale": np.array([1, 1, 1])}]
        if augmentation:
            configs.extend(
                {"name": f"z_scale_{z_scale}", "scale": np.array([1, 1, z_scale])} for z_scale in [0.8, 0.9, 1.1, 1.2]
            )
        return configs

    raise ValueError(f"Invalid task type: {task_type}")
