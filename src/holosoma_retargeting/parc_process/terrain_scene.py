from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from holosoma_retargeting.parc_process.source_io import ParcTerrainData


@dataclass(frozen=True)
class ParcSceneAssets:
    obj_path: Path
    asset_xml_path: Path
    scene_xml_path: Path
    urdf_path: Path


def _package_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _g1_scene_template() -> Path:
    return _package_root() / "models" / "g1" / "g1_29dof.xml"


def _heightfield_to_obj_mesh(
    hf: np.ndarray,
    min_x: float,
    min_y: float,
    dx: float,
    *,
    base_z: float,
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int]] = []

    def add_vertex(vertex: tuple[float, float, float]) -> int:
        vertices.append(vertex)
        return len(vertices)

    def add_quad(v0: int, v1: int, v2: int, v3: int) -> None:
        faces.append((v0, v1, v2))
        faces.append((v0, v2, v3))

    hf = np.asarray(hf, dtype=np.float64)
    for i in range(hf.shape[0]):
        for j in range(hf.shape[1]):
            z = float(hf[i, j])
            x0 = min_x + (i - 0.5) * dx
            x1 = min_x + (i + 0.5) * dx
            y0 = min_y + (j - 0.5) * dx
            y1 = min_y + (j + 0.5) * dx

            t00 = add_vertex((x0, y0, z))
            t01 = add_vertex((x0, y1, z))
            t11 = add_vertex((x1, y1, z))
            t10 = add_vertex((x1, y0, z))

            b00 = add_vertex((x0, y0, base_z))
            b01 = add_vertex((x0, y1, base_z))
            b11 = add_vertex((x1, y1, base_z))
            b10 = add_vertex((x1, y0, base_z))

            add_quad(t00, t10, t11, t01)
            add_quad(b00, b01, b11, b10)
            add_quad(t00, t01, b01, b00)
            add_quad(t01, t11, b11, b01)
            add_quad(t11, t10, b10, b11)
            add_quad(t10, t00, b00, b10)

    return vertices, faces


def _write_obj(
    hf: np.ndarray,
    min_x: float,
    min_y: float,
    dx: float,
    output_path: Path,
) -> Path:
    base_z = float(np.min(hf)) - max(float(dx), 0.1)
    vertices, faces = _heightfield_to_obj_mesh(hf, min_x, min_y, dx, base_z=base_z)
    with output_path.open("w") as f:
        for x, y, z in vertices:
            f.write(f"v {x:.8f} {y:.8f} {z:.8f}\n")
        for i, j, k in faces:
            f.write(f"f {i} {j} {k}\n")
    return output_path


def _write_asset_xml(obj_path: Path, asset_xml_path: Path, object_name: str) -> Path:
    asset_xml_path.write_text(
        "\n".join(
            [
                "<mujocoinclude>",
                f'    <mesh name="{object_name}_mesh" file="{obj_path}" scale="1 1 1"/>',
                "</mujocoinclude>",
                "",
            ]
        )
    )
    return asset_xml_path


def _write_scene_xml(
    template_xml_path: Path,
    asset_xml_path: Path,
    scene_xml_path: Path,
    object_name: str,
) -> Path:
    content = template_xml_path.read_text()
    meshdir = (_package_root() / "models" / "g1" / "assets").as_posix()
    content = content.replace('meshdir="assets/"', f'meshdir="{meshdir}"', 1)
    asset_block = f'  <include file="{asset_xml_path.name}"/>'
    geom_block = "\n".join(
        [
            f'    <body name="{object_name}" pos="0 0 0">',
            f'      <geom name="{object_name}" type="mesh" mesh="{object_name}_mesh" rgba="0.6 0.6 0.6 1" contype="1" conaffinity="1"/>',
            "    </body>",
        ]
    )
    content = content.replace("</asset>", f"{asset_block}\n</asset>", 1)
    content = content.replace("</worldbody>", f"{geom_block}\n  </worldbody>", 1)
    scene_xml_path.write_text(content)
    return scene_xml_path


def _write_object_urdf(obj_path: Path, urdf_path: Path, object_name: str) -> Path:
    urdf_path.write_text(
        "\n".join(
            [
                '<?xml version="1.0"?>',
                f'<robot name="{object_name}">',
                f'  <link name="{object_name}">',
                "    <visual>",
                "      <origin xyz=\"0 0 0\" rpy=\"0 0 0\"/>",
                "      <geometry>",
                f'        <mesh filename="{obj_path}" scale="1 1 1"/>',
                "      </geometry>",
                "    </visual>",
                "  </link>",
                "</robot>",
                "",
            ]
        )
    )
    return urdf_path


def export_parc_scene(
    terrain_data: ParcTerrainData,
    output_dir: str | Path,
    *,
    object_name: str = "multi_boxes",
) -> ParcSceneAssets:
    out_dir = Path(output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    obj_path = out_dir / f"{object_name}.obj"
    asset_xml_path = out_dir / "box_assets.xml"
    scene_xml_path = out_dir / "g1_29dof_w_multi_boxes.xml"
    urdf_path = out_dir / f"{object_name}.urdf"

    _write_obj(terrain_data.hf, float(terrain_data.min_point[0]), float(terrain_data.min_point[1]), float(terrain_data.dx), obj_path)
    _write_asset_xml(obj_path, asset_xml_path, object_name)
    _write_scene_xml(_g1_scene_template(), asset_xml_path, scene_xml_path, object_name)
    _write_object_urdf(obj_path, urdf_path, object_name)

    return ParcSceneAssets(
        obj_path=obj_path,
        asset_xml_path=asset_xml_path,
        scene_xml_path=scene_xml_path,
        urdf_path=urdf_path,
    )
