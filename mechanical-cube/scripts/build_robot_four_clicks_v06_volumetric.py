"""Volumetric workshop-assistant robot with a four-click IK sequence.

The structure is original but uses the spatial language requested by the user:
wide clevis joints, twin load-bearing beams, visible actuators and hoses, an
independent wrist gimbal, and a substantial tool head.  It retains the white,
black and silver surface language from the generated reference images.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve() if "--" in sys.argv else Path.cwd()
OUT = ROOT / "output" / "robot-arm" / "rig-v06-volumetric"
FRAMES = OUT / "frames"
OUT.mkdir(parents=True, exist_ok=True)
FRAMES.mkdir(parents=True, exist_ok=True)

spec = importlib.util.spec_from_file_location("four_click_v03", ROOT / "scripts" / "build_robot_four_clicks_v03.py")
v3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v3)
rig = v3.rig


def cylinder_between_local(name, start, end, radius, parent, mat, collection, vertices=48, bevel=0.02):
    start, end = Vector(start), Vector(end)
    delta = end - start
    obj = rig.cylinder_local(name, radius, delta.length, parent, (start + end) * 0.5, mat, collection, vertices=vertices, bevel=bevel)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    return obj


def tube_curve_local(name, points, parent, mat, collection, thickness=0.035):
    curve = bpy.data.curves.new(f"{name}_Curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = thickness
    curve.bevel_resolution = 3
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, coordinate in zip(spline.bezier_points, points):
        point.co = coordinate
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    obj.parent = parent
    obj.data.materials.append(mat)
    return obj


def side_bearing(prefix, parent, center_z, radius, y_offset, mats, collection):
    white, graphite, metal = mats
    for side in (-1, 1):
        y = side * y_offset
        rig.cylinder_local(f"{prefix}_Outer_{side:+d}", radius, 0.18, parent, (0, y, center_z), white, collection, (math.pi / 2, 0, 0), bevel=0.05)
        rig.cylinder_local(f"{prefix}_Cap_{side:+d}", radius * 0.78, 0.205, parent, (0, y - side * 0.015, center_z), graphite, collection, (math.pi / 2, 0, 0), bevel=0.025)
        rig.cylinder_local(f"{prefix}_Ring_{side:+d}", radius * 0.47, 0.225, parent, (0, y - side * 0.026, center_z), metal, collection, (math.pi / 2, 0, 0), bevel=0.012)
        rig.cylinder_local(f"{prefix}_Hub_{side:+d}", radius * 0.34, 0.238, parent, (0, y - side * 0.034, center_z), graphite, collection, (math.pi / 2, 0, 0), bevel=0.012)
        for index in range(6):
            angle = index * math.tau / 6
            rig.cylinder_local(
                f"{prefix}_Bolt_{side:+d}_{index}", radius * 0.035, 0.245, parent,
                (math.cos(angle) * radius * 0.61, y - side * 0.040, center_z + math.sin(angle) * radius * 0.61),
                metal, collection, (math.pi / 2, 0, 0), vertices=18, bevel=0.005,
            )


def hide_prototype_parts():
    prefixes = (
        "Shoulder_", "UpperArm", "Elbow_", "Forearm", "Wrist_",
        "Gripper_", "Finger", "Reference_", "TapProbe_",
    )
    for obj in list(bpy.data.objects):
        if obj.name.startswith(prefixes):
            obj.hide_render = True
            obj.hide_viewport = True


def build_volumetric_robot(collection, mats):
    white, graphite, metal, rubber, dark, accent, amber = mats
    root, j1, j2, j3, j4, j5, j6 = rig.build_robot(collection, (white, graphite, metal, rubber))
    hide_prototype_parts()

    shoulder_z = rig.SHOULDER_Z - 1.18

    # Heavy yaw turret and broad shoulder clevis.
    rig.cylinder_local("V06_ShoulderDeck", 0.88, 0.22, j1, (0, 0, 0.08), white, collection, bevel=0.07)
    rig.cylinder_local("V06_YawBearing", 0.79, 0.12, j1, (0, 0, 0.20), graphite, collection, bevel=0.025)
    for side in (-1, 1):
        rig.cube_local(
            f"V06_ShoulderFork_{side:+d}", (1.05, 0.22, 1.18), j1,
            (0, side * 0.45, shoulder_z), white, collection, 0.20,
        )
        rig.cube_local(
            f"V06_ShoulderForkInset_{side:+d}", (0.58, 0.235, 0.60), j1,
            (0.06, side * 0.46, shoulder_z + 0.02), dark, collection, 0.12,
        )
    side_bearing("V06_ShoulderBearing", j1, shoulder_z, 0.68, 0.56, (white, graphite, metal), collection)

    # Twin-beam upper arm leaves a visible mechanical cavity in the middle.
    upper_length = rig.L1 - 0.70
    upper_mid = rig.L1 * 0.50
    for side in (-1, 1):
        y = side * 0.34
        rig.cube_local(
            f"V06_UpperBeam_{side:+d}", (0.48, 0.22, upper_length), j2,
            (0, y, upper_mid), white, collection, 0.15,
        )
        rig.cube_local(
            f"V06_UpperBeamSpine_{side:+d}", (0.16, 0.235, upper_length * 0.70), j2,
            (0.20, y - side * 0.012, upper_mid), dark, collection, 0.055,
        )
    for z in (0.62, 1.18, 1.74):
        rig.cube_local(f"V06_UpperCrossbrace_{z:.2f}", (0.54, 0.78, 0.14), j2, (0, 0, z), metal, collection, 0.045)

    # Central hydraulic actuator and exposed polished piston.
    cylinder_between_local("V06_ShoulderActuatorBody", (-0.24, 0, 0.38), (-0.24, 0, 1.25), 0.16, j2, graphite, collection, bevel=0.035)
    cylinder_between_local("V06_ShoulderPiston", (-0.24, 0, 1.12), (-0.24, 0, rig.L1 - 0.26), 0.095, j2, metal, collection, bevel=0.018)
    tube_curve_local("V06_UpperHydraulicHose", ((0.30, -0.48, 0.34), (0.42, -0.50, 1.05), (0.34, -0.48, rig.L1 - 0.25)), j2, rubber, collection, 0.042)
    tube_curve_local("V06_UpperSignalCable", ((-0.28, -0.43, 0.40), (-0.40, -0.46, 1.10), (-0.30, -0.43, rig.L1 - 0.30)), j2, amber, collection, 0.022)

    # Wide, offset elbow bearing held by both beams.
    side_bearing("V06_ElbowBearing", j2, rig.L1, 0.61, 0.47, (white, graphite, metal), collection)
    rig.cube_local("V06_ElbowBridge", (0.82, 0.96, 0.30), j2, (0, 0, rig.L1), white, collection, 0.13)

    # Forearm uses a different spacing and diagonal bracing for a real 3D silhouette.
    fore_length = rig.L2 - 0.62
    fore_mid = rig.L2 * 0.50
    for side in (-1, 1):
        y = side * 0.29
        rig.cube_local(
            f"V06_ForeBeam_{side:+d}", (0.40, 0.19, fore_length), j3,
            (0, y, fore_mid), white, collection, 0.13,
        )
        rig.cube_local(
            f"V06_ForeBeamInset_{side:+d}", (0.13, 0.205, fore_length * 0.68), j3,
            (-0.16, y - side * 0.01, fore_mid), dark, collection, 0.045,
        )
    for z, angle in ((0.62, 0.30), (1.25, -0.30)):
        rig.cube_local(f"V06_ForeBrace_{z:.2f}", (0.46, 0.68, 0.13), j3, (0, 0, z), metal, collection, 0.040, rotation=(angle, 0, 0))
    cylinder_between_local("V06_ElbowActuatorBody", (0.22, 0, 0.28), (0.22, 0, 0.92), 0.135, j3, graphite, collection, bevel=0.030)
    cylinder_between_local("V06_ElbowPiston", (0.22, 0, 0.82), (0.22, 0, rig.L2 - 0.24), 0.078, j3, metal, collection, bevel=0.015)
    tube_curve_local("V06_ForeHydraulicHose", ((-0.24, -0.40, 0.25), (-0.36, -0.42, 0.95), (-0.28, -0.39, rig.L2 - 0.22)), j3, rubber, collection, 0.036)

    # Wrist clevis and three-axis gimbal provide volume separate from the arm.
    side_bearing("V06_WristBearing", j3, rig.L2, 0.50, 0.39, (white, graphite, metal), collection)
    for side in (-1, 1):
        rig.cube_local(f"V06_WristFork_{side:+d}", (0.65, 0.17, 0.62), j4, (0, side * 0.31, -0.22), white, collection, 0.14)
    rig.cylinder_local("V06_WristRollBody", 0.36, 0.54, j4, (0, 0, -0.34), graphite, collection, bevel=0.045)
    rig.cylinder_local("V06_WristRollRingA", 0.37, 0.055, j4, (0, 0, -0.46), metal, collection, bevel=0.012)
    rig.cylinder_local("V06_WristRollRingB", 0.37, 0.055, j4, (0, 0, -0.53), metal, collection, bevel=0.012)

    # Substantial palm and articulated two-finger tool head.
    rig.cube_local("V06_PalmHousing", (0.82, 0.78, 0.26), j6, (0, 0, -0.54), white, collection, 0.12)
    rig.cube_local("V06_PalmPlate", (0.58, 0.80, 0.09), j6, (0, 0, -0.62), dark, collection, 0.055)
    for side in (-1, 1):
        y = side * 0.28
        rig.cylinder_local(f"V06_FingerPivot_{side:+d}", 0.13, 0.16, j6, (0, y, -0.66), metal, collection, (math.pi / 2, 0, 0), bevel=0.020)
        rig.cube_local(f"V06_FingerLink_{side:+d}", (0.18, 0.20, 0.34), j6, (0.06, y, -0.79), white, collection, 0.055, rotation=(0, -0.16, 0))
        rig.cube_local(f"V06_FingerPad_{side:+d}", (0.16, 0.23, 0.10), j6, (0.10, y, -0.92), rubber, collection, 0.025)
    rig.cylinder_local("V06_TapProbeSpring", 0.080, 0.24, j6, (0, 0, -0.70), metal, collection, bevel=0.014)
    rig.cylinder_local("V06_TapProbe", 0.052, 0.18, j6, (0, 0, -0.82), graphite, collection, bevel=0.012)
    rig.cylinder_local("V06_TapTip", 0.045, 0.08, j6, (0, 0, -0.93), accent, collection, bevel=0.012)

    root["rig_version"] = "6.0-volumetric-workshop-assistant"
    root["structure"] = "wide clevis, twin beams, offset bearings, hydraulic actuators, hoses, wrist gimbal, articulated gripper"
    return root, j1, j2, j3, j4, j5, j6


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = rig.setup_scene()
    scene.name = "RobotFourClicks_V06_Volumetric"
    scene.frame_end = 240
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.filepath = str(FRAMES / "frame_")
    scene.camera.location = (13.2, -17.0, 9.6)
    # Keep the complete arm visible in both the upright establishing pose and
    # the low four-tap poses. A slightly wider lens also reveals the fork depth.
    scene.camera.data.lens = 45
    scene.camera.rotation_euler = (Vector((1.9, 0.0, 2.35)) - scene.camera.location).to_track_quat("-Z", "Y").to_euler()

    references = rig.new_collection("00_Reference_Images")
    robot = rig.new_collection("01_Volumetric_Robot_V06")
    phone = rig.new_collection("02_FourClick_UI")
    lab = rig.new_collection("03_Lab_Set")
    v3.add_reference_planes(references)

    white = rig.material("V06_PorcelainWhite", "#f3f4f6", 0.10, 0.23)
    graphite = rig.material("V06_Graphite", "#111419", 0.58, 0.18)
    metal = rig.material("V06_Aluminum", "#a9b0ba", 0.92, 0.13)
    rubber = rig.material("V06_Rubber", "#111317", 0.0, 0.68)
    dark = rig.material("V06_DarkMechanism", "#343a43", 0.82, 0.19)
    green = rig.material("V06_StatusGreen", "#18b778", 0.04, 0.24)
    amber = rig.material("V06_HydraulicAmber", "#d99a31", 0.20, 0.24)
    blue = rig.material("V06_StatusBlue", "#4f7cff", 0.06, 0.23)
    ink = rig.material("V06_UIInk", "#191b20", 0.0, 0.42)
    muted = rig.material("V06_UIMuted", "#8a9099", 0.0, 0.48)
    card = rig.material("V06_UICard", "#e3e6ea", 0.0, 0.60)
    header = rig.material("V06_UIHeader", "#3d78ba", 0.0, 0.44)
    table = rig.material("V06_Table", "#e4e7eb", 0.0, 0.78)

    root, j1, j2, j3, j4, j5, j6 = build_volumetric_robot(robot, (white, graphite, metal, rubber, dark, green, amber))
    v3.build_phone_ui(phone, (white, graphite, green, blue, ink, muted, card, header))
    rig.cube_local("Lab_Table_V06", (14, 12, 0.12), None, (1.8, 0, -0.06), table, lab, 0.02)
    rig.cube_local("Phone_Dock_V06", (2.72, 5.12, 0.12), None, (v3.PHONE_CENTER.x, 0, 0.06), white, lab, 0.14)

    start = (math.radians(-48), math.radians(14), math.radians(-18), math.radians(4))
    rig.key_rotation(j1, 1, z=start[0])
    rig.key_rotation(j2, 1, y=start[1])
    rig.key_rotation(j3, 1, y=start[2])
    rig.key_rotation(j4, 1, y=start[3])
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
        tip = bpy.data.objects["V06_TapTip"].matrix_world.translation
        errors.append(math.hypot(tip.x - target.x, tip.y - target.y))

    last = solutions[-1]
    hold = v3.RELEASE_FRAMES[-1] + 12
    rig.key_rotation(j1, hold, z=last[0])
    rig.key_rotation(j2, hold, y=last[1])
    rig.key_rotation(j3, hold, y=last[2])
    rig.key_rotation(j4, hold, y=last[3])
    rig.key_rotation(j1, 236, z=math.radians(8))
    rig.key_rotation(j2, 236, y=math.radians(30))
    rig.key_rotation(j3, 236, y=math.radians(-12))
    rig.key_rotation(j4, 236, y=math.radians(-18))
    rig.key_location(j6, 240, (0, 0, 0))

    root["click_sequence"] = "我 -> 喜欢 -> 视频 -> 验证"
    root["tap_xy_errors"] = ",".join(f"{value:.8f}" for value in errors)

    scene.frame_set(1)
    blend = OUT / "robot_four_clicks_v06_volumetric.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.render.render(animation=True)
    print(f"BLEND={blend}")
    print("TAP_ERRORS=" + ",".join(f"{value:.8f}" for value in errors))


if __name__ == "__main__":
    main()

