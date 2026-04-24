"""Object-mesh helpers for utility-layer decomposition."""

from __future__ import annotations

import os
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
    """
    Loads an object mesh and samples points from its surface.

    Args:
        object_file (str): Path to the object mesh file.
        smpl_scale (float): Scale factor for SMPL compatibility.
        bounding_box_oriented (bool): Whether to use oriented bounding box vertices.
        sample_count (int): Number of points to sample from the surface.
        seed (int): Random seed for sampling.
        surface_weights: Weight function for sampling. If use_face_normals=True,
                        should take (face_normal, face_center) as arguments.
        use_face_normals (bool): Whether to use face-normal-based sampling.

    Returns:
        tuple: (points, points_scaled) - original and scaled point arrays.
    """
    print("Loading and sampling object mesh...")
    obj_mesh = trimesh.load(object_file, force="mesh")

    if bounding_box_oriented:
        points = obj_mesh.bounding_box_oriented.vertices
    elif surface_weights is not None:
        if use_face_normals:
            # Use face-normal-based weighted sampling
            points = weighted_surface_sampling_by_face_normal(obj_mesh, sample_count, surface_weights, seed)
        else:
            # Use center-based weighted sampling
            points = weighted_surface_sampling(obj_mesh, sample_count, surface_weights, seed)
    else:
        points, _ = trimesh.sample.sample_surface_even(obj_mesh, sample_count, seed=seed)

    points = np.array(points)
    points_scaled = points * smpl_scale
    return points, points_scaled


def weighted_surface_sampling(mesh, sample_count, weight_func, seed=42):
    """
    Sample points from mesh surface with custom weighting.

    Args:
        mesh: Trimesh object
        sample_count: Number of points to sample
        weight_func: Function that takes (x,y,z) and returns weight
        seed: Random seed

    Returns:
        np.ndarray: Sampled points
    """
    rng = np.random.RandomState(seed)

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

    sampled_face_indices = rng.choice(len(faces), size=sample_count, p=face_probs)

    sampled_points = []
    for face_idx in sampled_face_indices:
        face = faces[face_idx]
        v1, v2, v3 = vertices[face]

        r1, r2 = rng.random_sample(2)
        if r1 + r2 > 1:
            r1, r2 = 1 - r1, 1 - r2

        point = v1 + r1 * (v2 - v1) + r2 * (v3 - v1)
        sampled_points.append(point)

    return np.array(sampled_points)


def weighted_surface_sampling_by_face_normal(mesh, sample_count, weight_func, seed=42):
    """
    Sample points from mesh surface with weighting based on face normals.

    Args:
        mesh: Trimesh object
        sample_count: Number of points to sample
        weight_func: Function that takes face_normal and face_center and returns weight
        seed: Random seed

    Returns:
        np.ndarray: Sampled points
    """
    rng = np.random.RandomState(seed)

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

    sampled_face_indices = rng.choice(len(faces), size=sample_count, p=face_probs)

    sampled_points = []
    for face_idx in sampled_face_indices:
        face = faces[face_idx]
        v1, v2, v3 = vertices[face]

        r1, r2 = rng.random_sample(2)
        if r1 + r2 > 1:
            r1, r2 = 1 - r1, 1 - r2

        point = v1 + r1 * (v2 - v1) + r2 * (v3 - v1)
        sampled_points.append(point)

    return np.array(sampled_points)


def create_top_surface_weight_function(up_direction=None, angle_threshold=30):
    """
    Create a weight function that prioritizes top-facing surfaces.

    Args:
        up_direction: Vector pointing upward (default: [0, 0, 1])
        angle_threshold: Maximum angle in degrees from up_direction to be considered "top"

    Returns:
        Function that takes (face_normal, face_center) and returns weight
    """
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
    """
    Create a scaled object mesh and URDF file.

    Args:
        scale_factors (tuple): Scale factors for x, y, z dimensions.
        save_dir (str): Directory to save the files.

    Returns:
        str: Path to the created URDF file.
    """
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
