"""Scene asset generation helpers for utility-layer decomposition."""

from __future__ import annotations

import re
from pathlib import Path


def create_scaled_multi_boxes_urdf(
    urdf_path: str,
    new_scale: tuple,
    output_path: str | None = None,
):
    """Read multi_boxes.urdf and generate scaled version."""
    if output_path is None:
        sx, sy, sz = new_scale
        output_path = urdf_path.replace(".urdf", f"_scaled_{sx:.2f}_{sy:.2f}_{sz:.2f}.urdf")

    if Path(output_path).exists():
        return output_path

    with open(urdf_path) as f:
        content = f.read()

    pattern = r'scale="[^"]*"'
    replacement = f'scale="{new_scale[0]} {new_scale[1]} {new_scale[2]}"'
    content = re.sub(pattern, replacement, content)

    with open(output_path, "w") as f:
        f.write(content)

    return output_path


def create_scaled_multi_boxes_xml(
    xml_path: str,
    new_scale: tuple,
    output_path: str | None = None,
):
    """Read `box_assets.xml` and generate a scaled copy."""
    if output_path is None:
        sx, sy, sz = new_scale
        output_path = xml_path.replace(".xml", f"_scaled_{sx:.2f}_{sy:.2f}_{sz:.2f}.xml")

    with open(xml_path) as f:
        content = f.read()

    pattern = r'scale="[^"]*"'
    replacement = f'scale="{new_scale[0]} {new_scale[1]} {new_scale[2]}"'
    content = re.sub(pattern, replacement, content)

    with open(output_path, "w") as f:
        f.write(content)

    return output_path


def create_new_scene_xml_file(
    ori_scene_xml_path: str,
    new_scale: tuple,
    new_object_asset_xml_path: str,
    output_path: str | None = None,
):
    """Generate a scene XML that points at the scaled object asset XML."""
    if output_path is None:
        sx, sy, sz = new_scale
        output_path = ori_scene_xml_path.replace(".xml", f"_scaled_{sx:.2f}_{sy:.2f}_{sz:.2f}.xml")

    with open(ori_scene_xml_path) as f:
        content = f.read()

    new_asset = new_object_asset_xml_path.split("/")[-1]
    pattern = r'file="box_assets\.xml"'
    replacement = f'file="{new_asset}"'
    content = re.sub(pattern, replacement, content)

    with open(output_path, "w") as f:
        f.write(content)

    return output_path
