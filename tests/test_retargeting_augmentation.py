from __future__ import annotations

import numpy as np

from omniretarget.examples.parallel_robot_retarget import generate_augmentation_configs as legacy_generate_configs
from omniretarget.retargeting.augmentation import generate_augmentation_configs


def _assert_configs_equal(actual, expected) -> None:
    assert len(actual) == len(expected)
    for actual_config, expected_config in zip(actual, expected):
        assert actual_config.keys() == expected_config.keys()
        for key, expected_value in expected_config.items():
            actual_value = actual_config[key]
            if isinstance(expected_value, np.ndarray):
                np.testing.assert_array_equal(actual_value, expected_value)
            else:
                assert actual_value == expected_value


def test_generate_augmentation_configs_matches_legacy_object_interaction() -> None:
    actual = generate_augmentation_configs("object_interaction", augmentation=True)
    expected = legacy_generate_configs("object_interaction", augmentation=True)

    _assert_configs_equal(actual, expected)


def test_generate_augmentation_configs_matches_legacy_climbing_without_augmentation() -> None:
    actual = generate_augmentation_configs("climbing", augmentation=False)
    expected = legacy_generate_configs("climbing", augmentation=False)

    _assert_configs_equal(actual, expected)
