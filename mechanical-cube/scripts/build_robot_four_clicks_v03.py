"""Reference-restored Blender robot performing four coordinate-driven taps."""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve() if "--" in sys.argv else Path.cwd()
OUT = ROOT / "output" / "robot-arm" / "rig-v03-four-clicks"
FRAMES = OUT / "frames"
OUT.mkdir(parents=True, exist_ok=True)
FRAMES.mkdir(parents=True, exist_ok=True)

spec = importlib.util.spec_from_file_location("rig_v02", ROOT / "scripts" / "build_robot_phone_reproduction_v02.py")
rig = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rig)

PHONE_CENTER = Vector((2.90, 0.0, 0.0))
SCREEN_Z = 0.32
SCREEN_W, SCREEN_H = 2.17, 4.42
TARGETS = (
    ("我", 0.90, 0.90),
    ("喜欢", 0.90, 0.44),
    ("视频", 0.25, 0.64),
    ("验证", 0.50, 0.52),
)
HOVER_FRAMES = (40, 88, 136, 184)
PRESS_FRAMES = (46, 94, 142, 190)
RELEASE_FRAMES = (52, 100, 148, 196)


def target_world(u, v):
    return Vector((
        PHONE_CENTER.x + (u - 0.5) * SCREEN_W,
        PHONE_CENTER.y + (0.5 - v) * SCREEN_H,
        SCREEN_Z,
    ))


TARGET_WORLD = tuple(target_world(u, v) for _, u, v in TARGETS)


def solve(target):
    radial = math.hypot(target.x, target.y)
    wrist_z = SCREEN_Z + rig.TOOL_REACH + rig.HOVER
    dx = radial
    dz = wrist_z - rig.SHOULDER_Z
    cosine = (dx * dx + dz * dz - rig.L1 * rig.L1 - rig.L2 * rig.L2) / (2 * rig.L1 * rig.L2)
    if cosine < -1.0 or cosine > 1.0:
        raise RuntimeError(f"Target outside robot workspace: {tuple(target)}")
    elbow = math.acos(cosine)
    shoulder = math.atan2(dx, dz) - math.atan2(rig.L2 * math.sin(elbow), rig.L1 + rig.L2 * math.cos(elbow))
    wrist = -(shoulder + elbow)
    yaw = math.atan2(target.y, target.x)
    return yaw, shoulder, elbow, wrist


def add_reference_planes(collection):
    paths = (
        ROOT / "assets" / "robot-arm" / "robot-arm-front.png",
        ROOT / "assets" / "robot-arm" / "robot-arm-back.png",
        ROOT / "assets" / "robot-arm" / "robot-arm-left.png",
        ROOT / "assets" / "robot-arm" / "robot-arm-right.png",
    )
    for index, path in enumerate(paths):
        image = bpy.data.images.load(str(path), check_existing=True)
        obj = bpy.data.objects.new(f"REF_{path.stem}", None)
        collection.objects.link(obj)
        obj.empty_display_type = "IMAGE"
        obj.data = image
        obj.empty_display_size = 5.4
        obj.location = (index * 6.0, 8.0, 2.8)
        obj.hide_render = True
        obj["reference_path"] = str(path)


def set_visibility(obj, switches):
    for frame, visible in switches:
        obj.hide_render = not visible
        obj.keyframe_insert("hide_render", frame=frame)


def build_phone_ui(collection, mats):
    white, graphite, green, blue, ink, muted, card, header = mats
    rig.cube_local("Phone_Frame_V03", (2.40, 4.80, 0.22), None, (PHONE_CENTER.x, 0, 0.20), graphite, collection, 0.18)
    rig.cube_local("Phone_Glass_V03", (SCREEN_W + 0.06, SCREEN_H + 0.06, 0.055), None, (PHONE_CENTER.x, 0, SCREEN_Z - 0.025), graphite, collection, 0.11)
    rig.cube_local("Screen_Surface_V03", (SCREEN_W, SCREEN_H, 0.025), None, (PHONE_CENTER.x, 0, SCREEN_Z + 0.012), white, collection, 0.07)
    rig.cube_local("Screen_Header_V03", (SCREEN_W - 0.06, 0.74, 0.028), None, (PHONE_CENTER.x, SCREEN_H * 0.40, SCREEN_Z + 0.030), header, collection, 0.06)
    rig.text_world("Screen_Title_V03", "实验室用例复现", (PHONE_CENTER.x, SCREEN_H * 0.40, SCREEN_Z + 0.055), 0.19, white, collection)

    # Four explicit shadcn-style action cards placed at the actual test coordinates.
    for index, ((label, u, v), world) in enumerate(zip(TARGETS, TARGET_WORLD)):
        rig.cube_local(f"ActionCard_{index}", (0.66, 0.42, 0.025), None, (world.x, world.y, SCREEN_Z + 0.045), card, collection, 0.08)
        rig.text_world(f"ActionLabel_{index}", label, (world.x, world.y, SCREEN_Z + 0.064), 0.145, ink, collection)

        # Target rings appear only while the corresponding IK move is active.
        for ring_index, radius in enumerate((0.19, 0.29)):
            bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=0.024, major_segments=56, minor_segments=14, location=(world.x, world.y, SCREEN_Z + 0.075))
            ring_obj = bpy.context.object
            ring_obj.name = f"Tap{index + 1}_Ring_{ring_index}"
            ring_obj.data.materials.append(blue if ring_index == 0 else green)
            rig.move_to(ring_obj, collection)
            appear = 22 if index == 0 else RELEASE_FRAMES[index - 1] + 6
            disappear = RELEASE_FRAMES[index] + 12
            ring_obj.scale = (0, 0, 0)
            ring_obj.keyframe_insert("scale", frame=max(1, appear - 1))
            ring_obj.scale = (1, 1, 1)
            ring_obj.keyframe_insert("scale", frame=HOVER_FRAMES[index])
            ring_obj.scale = (0.60, 0.60, 0.60)
            ring_obj.keyframe_insert("scale", frame=PRESS_FRAMES[index])
            ring_obj.scale = (1.20, 1.20, 1.20)
            ring_obj.keyframe_insert("scale", frame=RELEASE_FRAMES[index] + 4)
            ring_obj.scale = (0, 0, 0)
            ring_obj.keyframe_insert("scale", frame=disappear)

        # A green completion marker remains after each physical click.
        done = rig.cube_local(f"Tap{index + 1}_Done", (0.16, 0.16, 0.040), None, (world.x + 0.24, world.y - 0.13, SCREEN_Z + 0.075), green, collection, 0.05)
        set_visibility(done, ((1, False), (RELEASE_FRAMES[index], False), (RELEASE_FRAMES[index] + 1, True), (240, True)))

    # Screen-local coordinate axes.
    origin = Vector((PHONE_CENTER.x - SCREEN_W * 0.5, -SCREEN_H * 0.5, SCREEN_Z + 0.06))
    for name, end, mat in (
        ("Screen_X_Axis_V03", origin + Vector((0.72, 0, 0)), green),
        ("Screen_Y_Axis_V03", origin + Vector((0, 0.72, 0)), blue),
    ):
        delta = end - origin
        bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=0.022, depth=delta.length, location=(origin + end) * 0.5)
        axis = bpy.context.object
        axis.name = name
        axis.rotation_mode = "QUATERNION"
        axis.rotation_quaternion = delta.to_track_quat("Z", "Y")
        axis.data.materials.append(mat)
        rig.move_to(axis, collection)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = rig.setup_scene()
    scene.name = "RobotFourClicks_V03"
    scene.frame_end = 240
    scene.render.filepath = str(FRAMES / "frame_")
    scene.camera.location = (15.5, -20.0, 11.5)
    direction = Vector((2.0, 0.0, 2.75)) - scene.camera.location
    scene.camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    reference_collection = rig.new_collection("00_Orthographic_References")
    robot_collection = rig.new_collection("01_RobotArm_ReferenceRestored_V03")
    phone_collection = rig.new_collection("02_FourClick_UI")
    lab_collection = rig.new_collection("03_Lab_Set")
    add_reference_planes(reference_collection)

    white = rig.material("V03_White", "#f5f6f7", 0.06, 0.25)
    graphite = rig.material("V03_Graphite", "#13161b", 0.48, 0.22)
    metal = rig.material("V03_Metal", "#aab0b8", 0.88, 0.16)
    rubber = rig.material("V03_Rubber", "#181a1e", 0.0, 0.62)
    green = rig.material("V03_Green", "#16a36a", 0.02, 0.30)
    blue = rig.material("V03_Blue", "#4f7cff", 0.02, 0.30)
    ink = rig.material("V03_Ink", "#191b20", 0.0, 0.42)
    muted = rig.material("V03_Muted", "#8a9099", 0.0, 0.48)
    card = rig.material("V03_Card", "#e3e6ea", 0.0, 0.60)
    header = rig.material("V03_Header", "#3d78ba", 0.0, 0.44)
    table = rig.material("V03_Table", "#e6e8ec", 0.0, 0.76)

    root, j1, j2, j3, j4, j5, j6 = rig.build_robot(robot_collection, (white, graphite, metal, rubber))
    build_phone_ui(phone_collection, (white, graphite, green, blue, ink, muted, card, header))
    rig.cube_local("Lab_Table_V03", (14, 12, 0.12), None, (1.8, 0, -0.06), table, lab_collection, 0.02)
    rig.cube_local("Phone_Dock_V03", (2.72, 5.12, 0.12), None, (PHONE_CENTER.x, 0, 0.06), white, lab_collection, 0.14)

    start_q = (math.radians(-48), math.radians(14), math.radians(-18), math.radians(4))
    rig.key_rotation(j1, 1, z=start_q[0])
    rig.key_rotation(j2, 1, y=start_q[1])
    rig.key_rotation(j3, 1, y=start_q[2])
    rig.key_rotation(j4, 1, y=start_q[3])
    rig.key_location(j6, 1, (0, 0, 0))

    solutions = []
    errors = []
    for index, (target, hover_frame, press_frame, release_frame) in enumerate(zip(TARGET_WORLD, HOVER_FRAMES, PRESS_FRAMES, RELEASE_FRAMES)):
        yaw, shoulder, elbow, wrist = solve(target)
        solutions.append((yaw, shoulder, elbow, wrist))
        move_start = 18 if index == 0 else RELEASE_FRAMES[index - 1] + 6
        # Hold the previous pose briefly, then move all four FK joints together.
        if index > 0:
            prev = solutions[index - 1]
            rig.key_rotation(j1, move_start, z=prev[0])
            rig.key_rotation(j2, move_start, y=prev[1])
            rig.key_rotation(j3, move_start, y=prev[2])
            rig.key_rotation(j4, move_start, y=prev[3])
        rig.key_rotation(j1, hover_frame, z=yaw)
        rig.key_rotation(j2, hover_frame, y=shoulder)
        rig.key_rotation(j3, hover_frame, y=elbow)
        rig.key_rotation(j4, hover_frame, y=wrist)
        rig.key_location(j6, hover_frame, (0, 0, 0))
        rig.key_location(j6, press_frame, (0, 0, -rig.HOVER))
        rig.key_location(j6, release_frame, (0, 0, 0))

        scene.frame_set(press_frame)
        bpy.context.view_layer.update()
        pad_a = bpy.data.objects["FingerPad_-1"]
        pad_b = bpy.data.objects["FingerPad_+1"]
        contact = (pad_a.matrix_world.translation + pad_b.matrix_world.translation) * 0.5
        error = math.hypot(contact.x - target.x, contact.y - target.y)
        errors.append(error)

    # Return to a presentation pose after the fourth validation click.
    final_hold = RELEASE_FRAMES[-1] + 12
    last = solutions[-1]
    rig.key_rotation(j1, final_hold, z=last[0])
    rig.key_rotation(j2, final_hold, y=last[1])
    rig.key_rotation(j3, final_hold, y=last[2])
    rig.key_rotation(j4, final_hold, y=last[3])
    rig.key_rotation(j1, 236, z=math.radians(8))
    rig.key_rotation(j2, 236, y=math.radians(28))
    rig.key_rotation(j3, 236, y=math.radians(-8))
    rig.key_rotation(j4, 236, y=math.radians(-20))
    rig.key_location(j6, 240, (0, 0, 0))

    root["reference_images"] = "front,back,left,right"
    root["click_sequence"] = "我 -> 喜欢 -> 视频 -> 验证"
    root["click_xy_errors"] = ",".join(f"{value:.8f}" for value in errors)
    root["rig_version"] = "3.0-reference-restored-four-click"

    scene.frame_set(1)
    blend = OUT / "robot_four_clicks_v03.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.render.render(animation=True)
    print(f"BLEND={blend}")
    print("ERRORS=" + ",".join(f"{value:.8f}" for value in errors))


if __name__ == "__main__":
    main()

