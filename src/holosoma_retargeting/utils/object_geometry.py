from __future__ import annotations

import os
import re
from pathlib import Path

import numpy as np
import trimesh
from jinja2 import Template


def load_object_data(
    object_file,
    smpl_scale=0.714,
    bounding_box_oriented=False,
    sample_count=50,
    seed=42,
    surface_weights=None,
    use_face_normals=False,
):
    """Load an object mesh and sample points from its surface."""
    print("Loading and sampling object mesh...")
    obj_mesh = trimesh.load(object_file, force="mesh")

    if bounding_box_oriented:
        points = obj_mesh.bounding_box_oriented.vertices
    elif surface_weights is not None:
        if use_face_normals:
            points = weighted_surface_sampling_by_face_normal(obj_mesh, sample_count, surface_weights, seed)
        else:
            points = weighted_surface_sampling(obj_mesh, sample_count, surface_weights, seed)
    else:
        points, _ = trimesh.sample.sample_surface_even(obj_mesh, sample_count, seed=seed)

    points = np.array(points)
    points_scaled = points * smpl_scale
    return points, points_scaled


def weighted_surface_sampling(mesh, sample_count, weight_func, seed=42):
    """Sample points from mesh surface with custom center-based weighting."""
    np.random.seed(seed)

    faces = mesh.faces
    vertices = mesh.vertices

    face_areas = []
    face_centers = []

    for face in faces:
        v1, v2, v3 = vertices[face]
        area = 0.5 * np.linalg.norm(np.cross(v2 - v1, v3 - v1))
        face_areas.append(area)

        center = (v1 + v2 + v3) / 3.0
        face_centers.append(center)

    face_areas = np.array(face_areas)
    face_centers = np.array(face_centers)

    weights = np.array([weight_func(center) for center in face_centers])
    weighted_areas = face_areas * weights

    total_weighted_area = np.sum(weighted_areas)
    face_probs = weighted_areas / total_weighted_area

    sampled_face_indices = np.random.choice(len(faces), size=sample_count, p=face_probs)

    sampled_points = []
    for face_idx in sampled_face_indices:
        face = faces[face_idx]
        v1, v2, v3 = vertices[face]

        r1, r2 = np.random.random(2)
        if r1 + r2 > 1:
            r1, r2 = 1 - r1, 1 - r2

        point = v1 + r1 * (v2 - v1) + r2 * (v3 - v1)
        sampled_points.append(point)

    return np.array(sampled_points)


def weighted_surface_sampling_by_face_normal(mesh, sample_count, weight_func, seed=42):
    """Sample points from mesh surface with face-normal weighting."""
    np.random.seed(seed)

    faces = mesh.faces
    vertices = mesh.vertices

    face_areas = []
    face_centers = []
    face_normals = []

    for face in faces:
        v1, v2, v3 = vertices[face]
        area = 0.5 * np.linalg.norm(np.cross(v2 - v1, v3 - v1))
        face_areas.append(area)

        center = (v1 + v2 + v3) / 3.0
        face_centers.append(center)

        normal = np.cross(v2 - v1, v3 - v1)
        normal = normal / np.linalg.norm(normal)
        face_normals.append(normal)

    face_areas = np.array(face_areas)
    face_centers = np.array(face_centers)
    face_normals = np.array(face_normals)

    weights = np.array([weight_func(normal, center) for normal, center in zip(face_normals, face_centers)])
    weighted_areas = face_areas * weights

    total_weighted_area = np.sum(weighted_areas)
    face_probs = weighted_areas / total_weighted_area

    sampled_face_indices = np.random.choice(len(faces), size=sample_count, p=face_probs)

    sampled_points = []
    for face_idx in sampled_face_indices:
        face = faces[face_idx]
        v1, v2, v3 = vertices[face]

        r1, r2 = np.random.random(2)
        if r1 + r2 > 1:
            r1, r2 = 1 - r1, 1 - r2

        point = v1 + r1 * (v2 - v1) + r2 * (v3 - v1)
        sampled_points.append(point)

    return np.array(sampled_points)


def create_top_surface_weight_function(up_direction=None, angle_threshold=30):
    """Create a weight function that prioritizes top-facing surfaces."""
    if up_direction is None:
        up_direction = np.array([0, 0, 1])
    else:
        up_direction = up_direction / np.linalg.norm(up_direction)
    cos_threshold = np.cos(np.radians(angle_threshold))

    def top_surface_weight(face_normal, face_center):
        cos_angle = np.dot(face_normal, up_direction)

        if cos_angle >= cos_threshold:
            if face_center[2] >= 0.9:
                return 20.0
            return 1.0
        if cos_angle >= 0:
            return 1.0
        return 0.1

    return top_surface_weight


def scale_points_in_object_axes_frame(points, scale_factors, object_axes):
    """Scale points in the object axes frame."""
    return (points @ object_axes.T * scale_factors) @ object_axes


def create_scaled_object_mesh_and_urdf(
    scale_factors, object_vertices, object_faces, object_axes, object_urdf, save_dir="generated_objects/"
):
    """Create a scaled object mesh and URDF file."""
    object_file_name = f"largebox_scaled_{scale_factors[0]}_{scale_factors[1]}_{scale_factors[2]}"
    scaled_vertices = scale_points_in_object_axes_frame(object_vertices, scale_factors, object_axes)
    mesh = trimesh.Trimesh(vertices=scaled_vertices, faces=object_faces)

    mesh_subdir = f"{save_dir}/meshes"
    os.makedirs(mesh_subdir, exist_ok=True)

    mesh_file_name = f"{mesh_subdir}/{object_file_name}.obj"
    if not Path(mesh_file_name).exists():
        mesh.export(mesh_file_name)

    urdf_file_name = f"{save_dir}/{object_file_name}.urdf"
    if not Path(urdf_file_name).exists():
        with open(object_urdf) as f:
            template = Template(f.read(), autoescape=True)
        rendered_urdf = template.render(scale_x=scale_factors[0], scale_y=scale_factors[1], scale_z=scale_factors[2])
        with open(urdf_file_name, "w") as f:
            f.write(rendered_urdf)

    return urdf_file_name


def create_scaled_multi_boxes_urdf(
    urdf_path: str,
    new_scale: tuple,
    output_path: str | None = None,
):
    """Read multi_boxes.urdf and generate a scaled version."""
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
    """Read multi_boxes XML and generate a scaled version."""
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
