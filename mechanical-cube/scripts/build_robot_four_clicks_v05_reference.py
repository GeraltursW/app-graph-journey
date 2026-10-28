"""Faithful four-click robot based on the generated four-view reference set."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import bpy


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve() if "--" in sys.argv else Path.cwd()
OUT = ROOT / "output" / "robot-arm" / "rig-v05-reference"
FRAMES = OUT / "frames"
OUT.mkdir(parents=True, exist_ok=True)
FRAMES.mkdir(parents=True, exist_ok=True)

spec = importlib.util.spec_from_file_location("four_click_v03", ROOT / "scripts" / "build_robot_four_clicks_v03.py")
v3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v3)
rig = v3.rig
original_build_robot = rig.build_robot


def tapered_shell(name, parent, z_start, z_end, width_start, width_end, depth, mat, collection, bevel=0.14):
    hs = width_start * 0.5
    he = width_end * 0.5
    hd = depth * 0.5
    vertices = (
        (-hs, -hd, z_start), (hs, -hd, z_start), (hs, hd, z_start), (-hs, hd, z_start),
        (-he, -hd, z_end), (he, -hd, z_end), (he, hd, z_end), (-he, hd, z_end),
    )
    faces = (
        (0, 1, 2, 3), (4, 7, 6, 5),
        (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7),
    )
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.parent = parent
    obj.data.materials.append(mat)
    modifier = obj.modifiers.new("Sculpted shell bevel", "BEVEL")
    modifier.width = bevel
    modifier.segments = 8
    return obj


def build_reference_robot(collection, mats):
    result = original_build_robot(collection, mats)
    root, j1, j2, j3, j4, j5, j6 = result
    white, graphite, metal, rubber = mats

    # Replace rectangular prototype links with clean tapered shells matching the
    # generated side references. Hidden originals remain only as non-rendering
    # construction guides inside the project.
    for name in ("UpperArm", "UpperArm_Spine", "Forearm", "Forearm_Spine"):
        obj = bpy.data.objects.get(name)
        if obj:
            obj.hide_render = True
            obj.hide_viewport = True

    tapered_shell("UpperArm_ReferenceShell", j2, 0.32, rig.L1 - 0.31, 0.76, 0.63, 0.66, white, collection, 0.16)
    tapered_shell("Forearm_ReferenceShell", j3, 0.29, rig.L2 - 0.27, 0.66, 0.54, 0.59, white, collection, 0.145)

    # Restrained seam lines give the shells manufacturing definition without
    # departing from the smooth black-and-white reference language.
    rig.cube_local("UpperArm_Seam", (0.045, 0.025, rig.L1 * 0.48), j2, (0.27, -0.34, rig.L1 * 0.50), graphite, collection, 0.012)
    rig.cube_local("Forearm_Seam", (0.040, 0.025, rig.L2 * 0.46), j3, (-0.23, -0.305, rig.L2 * 0.50), graphite, collection, 0.010)

    # Reference wrist: black rotating cylinder, two silver bands and compact
    # two-finger gripper with replaceable black pads.
    rig.cylinder_local("Wrist_BlackBarrel", 0.345, 0.31, j4, (0, 0, -0.22), graphite, collection, bevel=0.040)
    rig.cylinder_local("Wrist_SilverBand_A", 0.352, 0.055, j4, (0, 0, -0.34), metal, collection, bevel=0.012)
    rig.cylinder_local("Wrist_SilverBand_B", 0.352, 0.055, j4, (0, 0, -0.405), metal, collection, bevel=0.012)
    rig.cylinder_local("Wrist_ToolFlange", 0.31, 0.12, j4, (0, 0, -0.47), graphite, collection, bevel=0.025)
    for side in (-1, 1):
        rig.cube_local(f"Reference_GripperPad_{side:+d}", (0.16, 0.18, 0.18), j6, (0, side * 0.21, -0.735), rubber, collection, 0.035)

    root["rig_version"] = "5.0-generated-reference-faithful"
    root["master_reference"] = str(ROOT / "assets" / "robot-arm" / "robot-arm-front.png")
    root["design_language"] = "smooth white shells, black circular joints, twin silver wrist bands, dual-finger gripper"
    return result


def main():
    # Reuse the already validated V3 four-click timeline and IK, replacing only
    # the robot builder and all output locations.
    v3.OUT = OUT
    v3.FRAMES = FRAMES
    rig.build_robot = build_reference_robot
    v3.main()
    bpy.context.scene.name = "RobotFourClicks_V05_ReferenceFaithful"
    bpy.context.scene.frame_set(1)
    final_blend = OUT / "robot_four_clicks_v05_reference.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(final_blend))
    print(f"FINAL_BLEND={final_blend}")


if __name__ == "__main__":
    main()

