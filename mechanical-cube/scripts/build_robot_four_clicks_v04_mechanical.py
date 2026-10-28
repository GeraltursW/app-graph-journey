"""Create the refined mechanical V4 robot and preserve four-click IK motion."""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve() if "--" in sys.argv else Path.cwd()
OUT = ROOT / "output" / "robot-arm" / "rig-v04-mechanical"
FRAMES = OUT / "frames"
OUT.mkdir(parents=True, exist_ok=True)
FRAMES.mkdir(parents=True, exist_ok=True)

spec = importlib.util.spec_from_file_location("four_click_v03", ROOT / "scripts" / "build_robot_four_clicks_v03.py")
v3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v3)
rig = v3.rig


def torus_local(name, major_radius, minor_radius, parent, location, mat, collection, rotation=(math.pi / 2, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major_radius, minor_radius=minor_radius, major_segments=64, minor_segments=16)
    obj = bpy.context.object
    obj.name = name
    rig.move_to(obj, collection)
    obj.data.materials.append(mat)
    obj.parent = parent
    obj.location = location
    obj.rotation_euler = rotation
    return obj


def add_panel_fasteners(prefix, parent, z_values, x_values, y, mat, collection):
    for zi, z in enumerate(z_values):
        for xi, x in enumerate(x_values):
            rig.cylinder_local(
                f"{prefix}_Fastener_{zi}_{xi}", 0.028, 0.025, parent,
                (x, y, z), mat, collection, (math.pi / 2, 0, 0), vertices=18, bevel=0.005,
            )


def add_mechanical_details(root, j1, j2, j3, j4, j5, j6, mats, collection):
    white, graphite, metal, rubber, dark_metal, accent, warning = mats

    # Base drivetrain: knurled circumference, service port and status cluster.
    for index in range(20):
        angle = index * math.tau / 20
        radius = 1.075
        rig.cube_local(
            f"Base_Knurl_{index:02d}", (0.055, 0.12, 0.13), root,
            (math.cos(angle) * radius, math.sin(angle) * radius, 0.13),
            dark_metal, collection, 0.014, rotation=(0, 0, angle),
        )
    rig.cube_local("Base_ServiceHatch", (0.50, 0.045, 0.28), root, (0, -0.685, 0.70), graphite, collection, 0.055)
    for index, color in enumerate((accent, metal, warning)):
        rig.cylinder_local(
            f"Base_Status_{index}", 0.040, 0.035, root,
            (-0.13 + index * 0.13, -0.716, 0.82), color, collection,
            (math.pi / 2, 0, 0), vertices=28, bevel=0.008,
        )
    torus_local("Base_BearingRing", 0.70, 0.035, root, (0, 0, 1.12), metal, collection, rotation=(0, 0, 0))

    # Shoulder fork and reinforced bearing stack.
    shoulder_local_z = rig.SHOULDER_Z - 1.18
    rig.cube_local("Shoulder_ForkNear", (0.82, 0.09, 0.92), j1, (0, -0.34, shoulder_local_z), white, collection, 0.16)
    rig.cube_local("Shoulder_ForkFar", (0.82, 0.09, 0.92), j1, (0, 0.34, shoulder_local_z), white, collection, 0.16)
    torus_local("Shoulder_OuterBearing", 0.54, 0.055, j1, (0, -0.385, shoulder_local_z), dark_metal, collection)
    torus_local("Shoulder_InnerBearing", 0.38, 0.028, j1, (0, -0.425, shoulder_local_z), metal, collection)

    # Upper arm: dual aluminum rails, near-side removable panel and cable duct.
    upper_mid = rig.L1 * 0.50
    for x in (-0.245, 0.245):
        rig.cube_local(f"UpperArm_Rail_{x:+.3f}", (0.055, 0.050, rig.L1 * 0.58), j2, (x, -0.342, upper_mid), metal, collection, 0.018)
    rig.cube_local("UpperArm_ServicePanel", (0.44, 0.035, rig.L1 * 0.43), j2, (0, -0.372, upper_mid), dark_metal, collection, 0.055)
    rig.cube_local("UpperArm_CableDuct", (0.11, 0.075, rig.L1 * 0.58), j2, (0.31, 0.20, upper_mid), rubber, collection, 0.035)
    add_panel_fasteners("UpperArm", j2, (0.73, 1.18, 1.63), (-0.18, 0.18), -0.397, metal, collection)

    # Elbow bearing, encoder cover and strain-relief collar.
    torus_local("Elbow_OuterBearing", 0.48, 0.050, j2, (0, -0.365, rig.L1), dark_metal, collection)
    torus_local("Elbow_EncoderRing", 0.33, 0.025, j2, (0, -0.405, rig.L1), metal, collection)
    rig.cube_local("Elbow_EncoderBlock", (0.23, 0.07, 0.16), j2, (0.42, -0.30, rig.L1 + 0.06), graphite, collection, 0.035)

    # Forearm: tapered-looking armor through layered rails and a visible conduit.
    fore_mid = rig.L2 * 0.50
    for x in (-0.215, 0.215):
        rig.cube_local(f"Forearm_Rail_{x:+.3f}", (0.050, 0.045, rig.L2 * 0.55), j3, (x, -0.307, fore_mid), metal, collection, 0.016)
    rig.cube_local("Forearm_ServicePanel", (0.38, 0.035, rig.L2 * 0.40), j3, (0, -0.334, fore_mid), dark_metal, collection, 0.050)
    rig.cube_local("Forearm_CableDuct", (0.10, 0.070, rig.L2 * 0.55), j3, (-0.27, 0.18, fore_mid), rubber, collection, 0.032)
    add_panel_fasteners("Forearm", j3, (0.65, 1.02, 1.39), (-0.15, 0.15), -0.357, metal, collection)

    # Wrist gearbox: multiple concentric rotating stages and vent slots.
    torus_local("Wrist_OuterBearing", 0.385, 0.045, j3, (0, -0.335, rig.L2), dark_metal, collection)
    torus_local("Wrist_EncoderRing", 0.265, 0.024, j3, (0, -0.375, rig.L2), metal, collection)
    for index in range(8):
        angle = index * math.tau / 8
        rig.cube_local(
            f"Wrist_Vent_{index}", (0.035, 0.055, 0.12), j4,
            (math.cos(angle) * 0.285, math.sin(angle) * 0.285, -0.15),
            dark_metal, collection, 0.010, rotation=(0, angle, 0),
        )
    rig.cylinder_local("Wrist_GearboxA", 0.37, 0.18, j4, (0, 0, -0.16), graphite, collection, bevel=0.035)
    rig.cylinder_local("Wrist_GearboxB", 0.34, 0.10, j4, (0, 0, -0.31), metal, collection, bevel=0.020)
    rig.cylinder_local("Wrist_GearboxC", 0.31, 0.13, j4, (0, 0, -0.42), graphite, collection, bevel=0.025)

    # Gripper carriage with jaw rails, hinge links, pads, and central spring probe.
    rig.cube_local("Gripper_Backplate", (0.62, 0.56, 0.09), j6, (0, 0, -0.46), dark_metal, collection, 0.07)
    for side in (-1, 1):
        y = side * 0.21
        rig.cube_local(f"Jaw_Rail_{side:+d}", (0.08, 0.10, 0.30), j6, (0.16, y, -0.63), metal, collection, 0.025, rotation=(0, -0.20, 0))
        rig.cube_local(f"Jaw_Link_{side:+d}", (0.09, 0.12, 0.22), j6, (-0.10, y, -0.58), graphite, collection, 0.028, rotation=(0, 0.36, 0))
        rig.cube_local(f"Jaw_PadDetail_{side:+d}", (0.16, 0.19, 0.055), j6, (0, y, -0.735), rubber, collection, 0.020)
    rig.cylinder_local("TapProbe_Spring", 0.082, 0.26, j6, (0, 0, -0.61), metal, collection, bevel=0.016)
    rig.cylinder_local("TapProbe_Body", 0.060, 0.21, j6, (0, 0, -0.71), graphite, collection, bevel=0.014)
    rig.cylinder_local("TapProbe_Tip", 0.044, 0.10, j6, (0, 0, -0.79), accent, collection, bevel=0.014)

    # Technical identity plates keep the product look restrained.
    rig.cube_local("UpperArm_IdentityPlate", (0.30, 0.028, 0.13), j2, (-0.18, -0.405, 1.02), metal, collection, 0.025)
    rig.cube_local("Forearm_IdentityPlate", (0.26, 0.028, 0.12), j3, (0.16, -0.366, 0.88), metal, collection, 0.022)


def set_camera(scene):
    scene.camera.location = (14.2, -18.3, 10.4)
    scene.camera.data.lens = 60
    direction = Vector((1.95, 0.0, 2.45)) - scene.camera.location
    scene.camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = rig.setup_scene()
    scene.name = "RobotFourClicks_V04_Mechanical"
    scene.frame_end = 240
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.filepath = str(FRAMES / "frame_")
    set_camera(scene)

    references = rig.new_collection("00_Orthographic_References")
    robot = rig.new_collection("01_RobotArm_V04_Mechanical")
    phone = rig.new_collection("02_FourClick_UI")
    lab = rig.new_collection("03_Lab_Set")
    v3.add_reference_planes(references)

    white = rig.material("V04_CeramicWhite", "#f3f4f6", 0.10, 0.22)
    graphite = rig.material("V04_Graphite", "#111419", 0.55, 0.18)
    metal = rig.material("V04_AnodizedAluminum", "#a7adb6", 0.92, 0.13)
    rubber = rig.material("V04_IndustrialRubber", "#111317", 0.0, 0.66)
    dark_metal = rig.material("V04_DarkSteel", "#343a43", 0.82, 0.19)
    green = rig.material("V04_StatusGreen", "#18b778", 0.04, 0.24)
    blue = rig.material("V04_StatusBlue", "#4f7cff", 0.06, 0.23)
    warning = rig.material("V04_StatusAmber", "#f2b84b", 0.02, 0.25)
    ink = rig.material("V04_UIInk", "#191b20", 0.0, 0.42)
    muted = rig.material("V04_UIMuted", "#8a9099", 0.0, 0.48)
    card = rig.material("V04_UICard", "#e3e6ea", 0.0, 0.60)
    header = rig.material("V04_UIHeader", "#3d78ba", 0.0, 0.44)
    table_mat = rig.material("V04_Table", "#e3e6ea", 0.0, 0.78)

    root, j1, j2, j3, j4, j5, j6 = rig.build_robot(robot, (white, graphite, metal, rubber))
    add_mechanical_details(root, j1, j2, j3, j4, j5, j6, (white, graphite, metal, rubber, dark_metal, green, warning), robot)
    v3.build_phone_ui(phone, (white, graphite, green, blue, ink, muted, card, header))
    rig.cube_local("Lab_Table_V04", (14, 12, 0.12), None, (1.8, 0, -0.06), table_mat, lab, 0.02)
    rig.cube_local("Phone_Dock_V04", (2.72, 5.12, 0.12), None, (v3.PHONE_CENTER.x, 0, 0.06), white, lab, 0.14)

    start_q = (math.radians(-48), math.radians(14), math.radians(-18), math.radians(4))
    rig.key_rotation(j1, 1, z=start_q[0])
    rig.key_rotation(j2, 1, y=start_q[1])
    rig.key_rotation(j3, 1, y=start_q[2])
    rig.key_rotation(j4, 1, y=start_q[3])
    rig.key_location(j6, 1, (0, 0, 0))

    solutions = []
    errors = []
    for index, (target, hover, press, release) in enumerate(zip(v3.TARGET_WORLD, v3.HOVER_FRAMES, v3.PRESS_FRAMES, v3.RELEASE_FRAMES)):
        solution = v3.solve(target)
        solutions.append(solution)
        if index:
            move_start = v3.RELEASE_FRAMES[index - 1] + 6
            previous = solutions[index - 1]
            rig.key_rotation(j1, move_start, z=previous[0])
            rig.key_rotation(j2, move_start, y=previous[1])
            rig.key_rotation(j3, move_start, y=previous[2])
            rig.key_rotation(j4, move_start, y=previous[3])
        rig.key_rotation(j1, hover, z=solution[0])
        rig.key_rotation(j2, hover, y=solution[1])
        rig.key_rotation(j3, hover, y=solution[2])
        rig.key_rotation(j4, hover, y=solution[3])
        rig.key_location(j6, hover, (0, 0, 0))
        rig.key_location(j6, press, (0, 0, -rig.HOVER))
        rig.key_location(j6, release, (0, 0, 0))
        scene.frame_set(press)
        bpy.context.view_layer.update()
        # Central probe is the actual click effector in V4.
        tip = bpy.data.objects["TapProbe_Tip"]
        # The cylinder center sits 0.05 above the glass at full press; compare XY only.
        position = tip.matrix_world.translation
        errors.append(math.hypot(position.x - target.x, position.y - target.y))

    last = solutions[-1]
    hold = v3.RELEASE_FRAMES[-1] + 12
    for obj, value in ((j1, last[0]), (j2, last[1]), (j3, last[2]), (j4, last[3])):
        rig.key_rotation(obj, hold, z=value if obj == j1 else None, y=value if obj != j1 else None)
    rig.key_rotation(j1, 236, z=math.radians(8))
    rig.key_rotation(j2, 236, y=math.radians(28))
    rig.key_rotation(j3, 236, y=math.radians(-8))
    rig.key_rotation(j4, 236, y=math.radians(-20))
    rig.key_location(j6, 240, (0, 0, 0))

    root["rig_version"] = "4.0-mechanical-reference-restored"
    root["click_sequence"] = "我 -> 喜欢 -> 视频 -> 验证"
    root["probe_xy_errors"] = ",".join(f"{value:.8f}" for value in errors)
    root["mechanical_details"] = "bearing rings, rails, fasteners, cable ducts, gearbox, jaw linkage, spring probe"

    scene.frame_set(1)
    blend = OUT / "robot_four_clicks_v04_mechanical.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.render.render(animation=True)
    print(f"BLEND={blend}")
    print("PROBE_ERRORS=" + ",".join(f"{value:.8f}" for value in errors))


if __name__ == "__main__":
    main()

