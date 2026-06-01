from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from omniretarget.config_types.task import TaskConfig
from omniretarget.examples.robot_retarget import create_ground_points as legacy_create_ground_points
from omniretarget.examples.robot_retarget import setup_object_data as legacy_setup_object_data
from omniretarget.retargeting import object_setup as object_setup_module
from omniretarget.retargeting.object_setup import create_ground_points, setup_object_data


def test_create_ground_points_matches_legacy_meshgrid() -> None:
    actual = create_ground_points((-1.0, 1.0), (-2.0, 2.0), 3)
    expected = legacy_create_ground_points((-1.0, 1.0), (-2.0, 2.0), 3)

    np.testing.assert_array_equal(actual, expected)


def test_setup_object_data_matches_legacy_robot_only_ground() -> None:
    task_config = TaskConfig(ground_range=(-0.5, 0.5), ground_size=2)
    constants = SimpleNamespace()

    actual = setup_object_data(
        task_type="robot_only",
        constants=constants,
        object_dir=None,
        smpl_scale=1.0,
        task_config=task_config,
        augmentation=False,
    )
    expected = legacy_setup_object_data(
        task_type="robot_only",
        constants=constants,
        object_dir=None,
        smpl_scale=1.0,
        task_config=task_config,
        augmentation=False,
    )

    np.testing.assert_array_equal(actual[0], expected[0])
    np.testing.assert_array_equal(actual[1], expected[1])
    assert actual[2] == expected[2]


def test_setup_object_data_object_interaction_uses_mesh_loader(monkeypatch) -> None:
    object_local_pts = np.array([[1.0, 2.0, 3.0]])
    object_local_pts_demo = np.array([[4.0, 5.0, 6.0]])

    def fake_load_object_data(mesh_file, *, smpl_scale, sample_count):
        assert mesh_file == "mesh.obj"
        assert smpl_scale == 1.5
        assert sample_count == 100
        return object_local_pts, object_local_pts_demo

    monkeypatch.setattr(object_setup_module, "load_object_data", fake_load_object_data)
    constants = SimpleNamespace(OBJECT_MESH_FILE="mesh.obj", OBJECT_URDF_FILE="object.urdf")

    actual = setup_object_data(
        task_type="object_interaction",
        constants=constants,
        object_dir=None,
        smpl_scale=1.5,
        task_config=TaskConfig(),
        augmentation=False,
    )

    assert actual[0] is object_local_pts
    assert actual[1] is object_local_pts_demo
    assert actual[2] == "object.urdf"


def test_setup_object_data_climbing_updates_scene_and_scaled_assets(monkeypatch, tmp_path) -> None:
    object_local_pts = np.array([[1.0, 2.0, 3.0]])
    object_local_pts_demo = np.array([[4.0, 5.0, 6.0]])
    calls = {}

    def fake_load_object_data(mesh_file, *, smpl_scale, surface_weights, sample_count):
        assert mesh_file == "mesh.obj"
        assert smpl_scale == 2.0
        assert surface_weights(np.array([0.0, 0.0, 1.0])) == 20
        assert surface_weights(np.array([0.0, 0.0, 0.0])) == 1
        assert sample_count == 100
        return object_local_pts, object_local_pts_demo

    def fake_scaled_urdf(urdf_file, scale_factors):
        calls["urdf"] = (urdf_file, scale_factors)
        return "scaled.urdf"

    def fake_scaled_xml(box_asset_xml, scale_factors):
        calls["asset_xml"] = (box_asset_xml, scale_factors)
        return "asset.xml"

    def fake_scene_xml(scene_xml_file, scale_factors, object_asset_xml_path):
        calls["scene_xml"] = (scene_xml_file, scale_factors, object_asset_xml_path)
        return "scene.xml"

    monkeypatch.setattr(object_setup_module, "load_object_data", fake_load_object_data)
    monkeypatch.setattr(object_setup_module, "create_scaled_multi_boxes_urdf", fake_scaled_urdf)
    monkeypatch.setattr(object_setup_module, "create_scaled_multi_boxes_xml", fake_scaled_xml)
    monkeypatch.setattr(object_setup_module, "create_new_scene_xml_file", fake_scene_xml)
    constants = SimpleNamespace(
        ROBOT_URDF_FILE="/models/g1_29dof.urdf",
        OBJECT_NAME="multi_boxes",
        OBJECT_MESH_FILE="mesh.obj",
        OBJECT_URDF_FILE="multi_boxes.urdf",
    )

    actual = setup_object_data(
        task_type="climbing",
        constants=constants,
        object_dir=tmp_path,
        smpl_scale=2.0,
        task_config=TaskConfig(),
        augmentation=False,
    )

    assert actual[0] is object_local_pts_demo
    assert actual[1] is object_local_pts_demo
    assert actual[2] == "scaled.urdf"
    assert calls["urdf"] == ("multi_boxes.urdf", (2.0, 2.0, 2.0))
    assert calls["asset_xml"] == (str(tmp_path / "box_assets.xml"), (2.0, 2.0, 2.0))
    assert calls["scene_xml"] == (
        str(tmp_path / "g1_29dof_w_multi_boxes.xml"),
        (2.0, 2.0, 2.0),
        "asset.xml",
    )
    assert constants.SCENE_XML_FILE == "scene.xml"
