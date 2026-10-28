"""Build a complete, correctly parented robot-phone reproduction scene.

V2 replaces the prototype's world-space parenting with a strict local-space
forward-kinematic chain.  Shoulder and elbow angles are solved from the phone
target using two-link inverse kinematics; the wrist cancels accumulated pitch
so the tap probe remains vertical.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve() if "--" in sys.argv else Path.cwd()
OUT = ROOT / "output" / "robot-arm" / "rig-v02"
FRAMES = OUT / "frames"
OUT.mkdir(parents=True, exist_ok=True)
FRAMES.mkdir(parents=True, exist_ok=True)

FPS = 24
W, H = 960, 540
PHONE_CENTER = Vector((3.40, 0.0, 0.0))
SCREEN_Z = 0.32
SCREEN_W, SCREEN_H = 2.17, 4.42
TARGET_U, TARGET_V = 0.90, 0.44
SOURCE_W, SOURCE_H = 1828, 2584
TARGET_PX = (round(TARGET_U * SOURCE_W), round(TARGET_V * SOURCE_H))
TARGET_LOCAL = Vector(((TARGET_U - 0.5) * SCREEN_W, (0.5 - TARGET_V) * SCREEN_H, 0.0))
TARGET_WORLD = Vector((PHONE_CENTER.x + TARGET_LOCAL.x, PHONE_CENTER.y + TARGET_LOCAL.y, SCREEN_Z))

SHOULDER_Z = 1.55
L1 = 2.35
L2 = 2.05
TOOL_REACH = 0.74
HOVER = 0.08


def rgba(value: str, alpha: float = 1.0):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255.0 for i in (0, 2, 4)) + (alpha,)


def material(name, color, metallic=0.0, roughness=0.40):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = rgba(color)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba(color)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def new_collection(name):
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def move_to(obj, collection):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    collection.objects.link(obj)


def smooth(obj):
    if hasattr(obj.data, "polygons"):
        for polygon in obj.data.polygons:
            polygon.use_smooth = True


def empty_local(name, parent, location, collection):
    obj = bpy.data.objects.new(name, None)
    collection.objects.link(obj)
    obj.parent = parent
    obj.location = location
    obj.rotation_mode = "XYZ"
    obj.empty_display_type = "ARROWS"
    obj.empty_display_size = 0.28
    return obj


def cube_local(name, dimensions, parent, location, mat, collection, bevel=0.08, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    move_to(obj, collection)
    obj.data.materials.append(mat)
    obj.parent = parent
    obj.location = location
    obj.rotation_euler = rotation
    if bevel:
        mod = obj.modifiers.new("Precision bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 5
    return obj


def cylinder_local(name, radius, depth, parent, location, mat, collection, rotation=(0, 0, 0), vertices=64, bevel=0.035):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth)
    obj = bpy.context.object
    obj.name = name
    move_to(obj, collection)
    obj.data.materials.append(mat)
    obj.parent = parent
    obj.location = location
    obj.rotation_euler = rotation
    smooth(obj)
    if bevel:
        mod = obj.modifiers.new("Edge catchlight", "BEVEL")
        mod.width = bevel
        mod.segments = 3
    return obj


def link_local(name, start, end, width, depth, parent, mat, dark_mat, collection):
    start, end = Vector(start), Vector(end)
    delta = end - start
    midpoint = (start + end) * 0.5
    outer = cube_local(name, (width, depth, delta.length), parent, midpoint, mat, collection, min(width, depth) * 0.22)
    outer.rotation_mode = "QUATERNION"
    outer.rotation_quaternion = delta.to_track_quat("Z", "Y")
    spine = cube_local(f"{name}_Spine", (width * 0.16, depth * 1.025, delta.length * 0.74), parent, midpoint, dark_mat, collection, min(width, depth) * 0.05)
    spine.rotation_mode = "QUATERNION"
    spine.rotation_quaternion = delta.to_track_quat("Z", "Y")
    return outer


def joint_shell(name, parent, location, radius, depth, white, graphite, metal, collection):
    rotation = (math.pi / 2, 0, 0)
    cylinder_local(f"{name}_Housing", radius, depth, parent, location, white, collection, rotation, bevel=0.055)
    cylinder_local(f"{name}_Cap", radius * 0.78, depth + 0.045, parent, (location[0], location[1] - 0.028, location[2]), graphite, collection, rotation, bevel=0.025)
    cylinder_local(f"{name}_Ring", radius * 0.48, depth + 0.068, parent, (location[0], location[1] - 0.041, location[2]), metal, collection, rotation, bevel=0.015)
    cylinder_local(f"{name}_Hub", radius * 0.38, depth + 0.082, parent, (location[0], location[1] - 0.050, location[2]), graphite, collection, rotation, bevel=0.012)
    for index in range(6):
        angle = index * math.tau / 6
        bolt_location = (
            location[0] + math.cos(angle) * radius * 0.61,
            location[1] - 0.058,
            location[2] + math.sin(angle) * radius * 0.61,
        )
        cylinder_local(f"{name}_Bolt_{index}", radius * 0.034, depth + 0.10, parent, bolt_location, metal, collection, rotation, vertices=20, bevel=0.006)


def text_world(name, body, location, size, mat, collection, align="CENTER"):
    curve = bpy.data.curves.new(f"{name}_Curve", "FONT")
    curve.body = body
    curve.align_x = align
    curve.align_y = "CENTER"
    curve.size = size
    curve.extrude = 0.003
    font_path = Path("C:/Windows/Fonts/msyh.ttc")
    if font_path.exists():
        curve.font = bpy.data.fonts.load(str(font_path), check_existing=True)
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    obj.location = location
    obj.data.materials.append(mat)
    return obj


def key_rotation(obj, frame, x=None, y=None, z=None):
    if x is not None:
        obj.rotation_euler[0] = x
    if y is not None:
        obj.rotation_euler[1] = y
    if z is not None:
        obj.rotation_euler[2] = z
    obj.keyframe_insert("rotation_euler", frame=frame)


def key_location(obj, frame, location):
    obj.location = location
    obj.keyframe_insert("location", frame=frame)


def solve_ik():
    radial = math.hypot(TARGET_WORLD.x, TARGET_WORLD.y)
    wrist_z = SCREEN_Z + TOOL_REACH + HOVER
    dx = radial
    dz = wrist_z - SHOULDER_Z
    cosine = (dx * dx + dz * dz - L1 * L1 - L2 * L2) / (2 * L1 * L2)
    cosine = max(-1.0, min(1.0, cosine))
    elbow = math.acos(cosine)
    shoulder = math.atan2(dx, dz) - math.atan2(L2 * math.sin(elbow), L1 + L2 * math.cos(elbow))
    wrist = -(shoulder + elbow)
    yaw = math.atan2(TARGET_WORLD.y, TARGET_WORLD.x)
    return yaw, shoulder, elbow, wrist, radial, wrist_z


def build_robot(robot_collection, mats):
    white, graphite, metal, rubber = mats
    root = empty_local("ARM_ROOT_V02", None, (0, 0, 0), robot_collection)
    j1 = empty_local("J01_BASE_YAW", root, (0, 0, 1.18), robot_collection)
    j2 = empty_local("J02_SHOULDER_PITCH", j1, (0, 0, SHOULDER_Z - 1.18), robot_collection)
    j3 = empty_local("J03_ELBOW_PITCH", j2, (0, 0, L1), robot_collection)
    j4 = empty_local("J04_WRIST_PITCH", j3, (0, 0, L2), robot_collection)
    j5 = empty_local("J05_WRIST_ROLL", j4, (0, 0, 0), robot_collection)
    j6 = empty_local("J06_TAP_SLIDE", j5, (0, 0, 0), robot_collection)

    # Root-mounted base never inherits arm pitch.
    cylinder_local("Base_Rubber", 1.08, 0.16, root, (0, 0, 0.08), rubber, robot_collection, bevel=0.05)
    cylinder_local("Base_Plate", 1.02, 0.22, root, (0, 0, 0.24), white, robot_collection, bevel=0.06)
    cylinder_local("Base_Column", 0.68, 0.74, root, (0, 0, 0.70), white, robot_collection, bevel=0.07)
    cylinder_local("Base_YawBand", 0.69, 0.10, root, (0, 0, 1.08), graphite, robot_collection, bevel=0.02)
    for index in range(8):
        angle = index * math.tau / 8
        cylinder_local(f"Base_Bolt_{index}", 0.032, 0.026, root, (math.cos(angle) * 0.81, math.sin(angle) * 0.81, 0.37), graphite, robot_collection, vertices=20, bevel=0.006)

    # Joint housings belong to the proximal joint; links and downstream pivots
    # share the exact same local coordinate system, preventing collapse.
    joint_shell("Shoulder", j1, (0, 0, SHOULDER_Z - 1.18), 0.67, 0.62, white, graphite, metal, robot_collection)
    link_local("UpperArm", (0, 0, 0.34), (0, 0, L1 - 0.32), 0.72, 0.66, j2, white, graphite, robot_collection)
    joint_shell("Elbow", j2, (0, 0, L1), 0.60, 0.58, white, graphite, metal, robot_collection)
    link_local("Forearm", (0, 0, 0.30), (0, 0, L2 - 0.28), 0.64, 0.59, j3, white, graphite, robot_collection)
    joint_shell("Wrist", j3, (0, 0, L2), 0.48, 0.52, white, graphite, metal, robot_collection)

    cylinder_local("Wrist_Collar", 0.34, 0.34, j4, (0, 0, -0.18), graphite, robot_collection, bevel=0.035)
    cylinder_local("Wrist_Ring", 0.35, 0.07, j4, (0, 0, -0.36), metal, robot_collection, bevel=0.014)
    cube_local("Gripper_Palm", (0.58, 0.52, 0.28), j6, (0, 0, -0.48), white, robot_collection, 0.08)
    for side in (-1, 1):
        cylinder_local(f"Finger_Knuckle_{side:+d}", 0.105, 0.12, j6, (0, side * 0.21, -0.57), metal, robot_collection, (math.pi / 2, 0, 0), vertices=40, bevel=0.016)
        cube_local(f"Finger_{side:+d}", (0.16, 0.14, 0.33), j6, (0, side * 0.21, -0.68), white, robot_collection, 0.045)
        cube_local(f"FingerPad_{side:+d}", (0.12, 0.17, 0.10), j6, (0, side * 0.21, -0.69), rubber, robot_collection, 0.025)

    root["rig_version"] = "2.0-local-fk"
    root["chain"] = "J01_BASE_YAW/J02_SHOULDER_PITCH/J03_ELBOW_PITCH/J04_WRIST_PITCH/J05_WRIST_ROLL/J06_TAP_SLIDE"
    return root, j1, j2, j3, j4, j5, j6


def build_phone(phone_collection, mats):
    white, graphite, green, blue, ink, muted, card, header = mats
    phone_w, phone_h = 2.40, 4.80
    cube_local("LabPhone_Frame", (phone_w, phone_h, 0.22), None, (PHONE_CENTER.x, PHONE_CENTER.y, 0.20), graphite, phone_collection, 0.18)
    cube_local("LabPhone_Glass", (SCREEN_W + 0.06, SCREEN_H + 0.06, 0.055), None, (PHONE_CENTER.x, PHONE_CENTER.y, SCREEN_Z - 0.025), graphite, phone_collection, 0.11)
    cube_local("UI_Background", (SCREEN_W, SCREEN_H, 0.025), None, (PHONE_CENTER.x, PHONE_CENTER.y, SCREEN_Z + 0.012), white, phone_collection, 0.07)
    cube_local("UI_Header", (SCREEN_W - 0.06, 0.92, 0.028), None, (PHONE_CENTER.x, PHONE_CENTER.y + SCREEN_H * 0.37, SCREEN_Z + 0.030), header, phone_collection, 0.06)
    text_world("UI_Title", "我的页面", (PHONE_CENTER.x, PHONE_CENTER.y + SCREEN_H * 0.38, SCREEN_Z + 0.055), 0.20, white, phone_collection)

    tab_y = PHONE_CENTER.y + TARGET_LOCAL.y
    tabs = (("作品", -0.86), ("日常", -0.43), ("推荐", 0.0), ("收藏", 0.43), ("喜欢", TARGET_LOCAL.x))
    for index, (label, offset_x) in enumerate(tabs):
        text_world(f"UI_Tab_{index}", label, (PHONE_CENTER.x + offset_x, tab_y, SCREEN_Z + 0.055), 0.145, ink if index in (0, 4) else muted, phone_collection)

    old_line = cube_local("UI_Active_作品", (0.31, 0.035, 0.027), None, (PHONE_CENTER.x - 0.86, tab_y - 0.22, SCREEN_Z + 0.052), ink, phone_collection, 0.010)
    new_line = cube_local("UI_Active_喜欢", (0.31, 0.035, 0.027), None, (PHONE_CENTER.x + TARGET_LOCAL.x, tab_y - 0.22, SCREEN_Z + 0.055), green, phone_collection, 0.010)
    for frame, after in ((1, False), (72, False), (73, True), (120, True)):
        old_line.hide_render = after
        old_line.keyframe_insert("hide_render", frame=frame)
        new_line.hide_render = not after
        new_line.keyframe_insert("hide_render", frame=frame)

    for index in range(6):
        col, row = index % 2, index // 2
        x = PHONE_CENTER.x + (-0.53 if col == 0 else 0.53)
        y = tab_y - 0.70 - row * 0.78
        obj = cube_local(f"UI_LikeCard_{index}", (0.88, 0.62, 0.026), None, (x, y, SCREEN_Z + 0.050), card if index % 2 == 0 else white, phone_collection, 0.075)
        for frame, visible in ((1, False), (72, False), (73, True), (120, True)):
            obj.hide_render = not visible
            obj.keyframe_insert("hide_render", frame=frame)

    origin = Vector((PHONE_CENTER.x - SCREEN_W * 0.5, PHONE_CENTER.y - SCREEN_H * 0.5, SCREEN_Z + 0.06))
    # Axis cylinders are authored in world coordinates because the phone stays fixed.
    for name, end, mat in (
        ("Screen_X_Axis", origin + Vector((0.78, 0, 0)), green),
        ("Screen_Y_Axis", origin + Vector((0, 0.78, 0)), blue),
    ):
        delta = end - origin
        bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=0.022, depth=delta.length, location=(origin + end) * 0.5)
        axis = bpy.context.object
        axis.name = name
        axis.rotation_mode = "QUATERNION"
        axis.rotation_quaternion = delta.to_track_quat("Z", "Y")
        axis.data.materials.append(mat)
        move_to(axis, phone_collection)

    for index, radius in enumerate((0.18, 0.29)):
        bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=0.024, major_segments=56, minor_segments=14, location=(TARGET_WORLD.x, TARGET_WORLD.y, SCREEN_Z + 0.07))
        ring = bpy.context.object
        ring.name = f"Coordinate_TargetRing_{index}"
        ring.data.materials.append(green if index else blue)
        move_to(ring, phone_collection)
        ring.scale = (0.35, 0.35, 0.35)
        ring.keyframe_insert("scale", frame=36)
        ring.scale = (1, 1, 1)
        ring.keyframe_insert("scale", frame=58)
        ring.scale = (0.62, 0.62, 0.62)
        ring.keyframe_insert("scale", frame=72)
        ring.scale = (1.18, 1.18, 1.18)
        ring.keyframe_insert("scale", frame=80)
        ring.scale = (0, 0, 0)
        ring.keyframe_insert("scale", frame=92)


def setup_scene():
    scene = bpy.context.scene
    scene.name = "RobotPhoneReproduction_V02"
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = W
    scene.render.resolution_y = H
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = 120
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.filepath = str(FRAMES / "frame_")
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "WORLD"
    scene.display.shading.show_specular_highlight = True
    scene.display.shading.background_type = "VIEWPORT"
    scene.display.shading.background_color = (0.94, 0.95, 0.97)

    camera_data = bpy.data.cameras.new("Main_Camera")
    camera = bpy.data.objects.new("Main_Camera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = (15.5, -20.0, 11.5)
    camera_data.lens = 57
    direction = Vector((2.10, 0.0, 2.80)) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera
    return scene


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = setup_scene()
    robot_collection = new_collection("01_RobotArm_Rig_V02")
    phone_collection = new_collection("02_LabPhone_UI")
    lab_collection = new_collection("03_Lab_Set")

    white = material("Robot_White", "#f5f6f7", 0.06, 0.25)
    graphite = material("Robot_Graphite", "#15181d", 0.48, 0.22)
    metal = material("Robot_Metal", "#aab0b8", 0.88, 0.16)
    rubber = material("Robot_Rubber", "#181a1e", 0.0, 0.62)
    green = material("UI_Green", "#16a36a", 0.02, 0.30)
    blue = material("UI_Blue", "#4f7cff", 0.02, 0.30)
    ink = material("UI_Ink", "#191b20", 0.0, 0.42)
    muted = material("UI_Muted", "#8a9099", 0.0, 0.48)
    card = material("UI_Card", "#e3e6ea", 0.0, 0.60)
    header = material("UI_Header", "#3d78ba", 0.0, 0.44)
    table_mat = material("Lab_Table", "#e6e8ec", 0.0, 0.76)

    root, j1, j2, j3, j4, j5, j6 = build_robot(robot_collection, (white, graphite, metal, rubber))
    build_phone(phone_collection, (white, graphite, green, blue, ink, muted, card, header))
    cube_local("Lab_Table", (14, 12, 0.12), None, (2.0, 0, -0.06), table_mat, lab_collection, 0.02)
    cube_local("Phone_Dock", (2.72, 5.12, 0.12), None, (PHONE_CENTER.x, PHONE_CENTER.y, 0.06), white, lab_collection, 0.14)

    yaw, shoulder, elbow, wrist, radial, wrist_z = solve_ik()
    start_shoulder = math.radians(12)
    start_elbow = math.radians(-18)
    start_wrist = -(start_shoulder + start_elbow)

    # Rotation, coordinated lowering, physical press, result verification, retreat.
    key_rotation(j1, 1, z=math.radians(-55))
    key_rotation(j1, 28, z=yaw)
    key_rotation(j1, 120, z=yaw)

    key_rotation(j2, 1, y=start_shoulder)
    key_rotation(j2, 24, y=start_shoulder)
    key_rotation(j2, 62, y=shoulder)
    key_rotation(j2, 88, y=shoulder)
    key_rotation(j2, 116, y=math.radians(24))

    key_rotation(j3, 1, y=start_elbow)
    key_rotation(j3, 24, y=start_elbow)
    key_rotation(j3, 62, y=elbow)
    key_rotation(j3, 88, y=elbow)
    key_rotation(j3, 116, y=math.radians(-10))

    key_rotation(j4, 1, y=start_wrist)
    key_rotation(j4, 24, y=start_wrist)
    key_rotation(j4, 62, y=wrist)
    key_rotation(j4, 88, y=wrist)
    key_rotation(j4, 116, y=-math.radians(14))

    key_location(j6, 1, (0, 0, 0))
    key_location(j6, 62, (0, 0, 0))
    key_location(j6, 72, (0, 0, -HOVER))
    key_location(j6, 80, (0, 0, 0))
    key_location(j6, 120, (0, 0, 0))

    # Validate the actual evaluated endpoint at maximum press.
    scene.frame_set(72)
    bpy.context.view_layer.update()
    pad_a = bpy.data.objects["FingerPad_-1"]
    pad_b = bpy.data.objects["FingerPad_+1"]
    contact = (pad_a.matrix_world.translation + pad_b.matrix_world.translation) * 0.5
    contact_error = (Vector((contact.x, contact.y, SCREEN_Z)) - TARGET_WORLD).length
    root["target_pixel"] = f"{TARGET_PX[0]},{TARGET_PX[1]}"
    root["target_uv"] = f"{TARGET_U:.4f},{TARGET_V:.4f}"
    root["target_world"] = f"{TARGET_WORLD.x:.4f},{TARGET_WORLD.y:.4f},{TARGET_WORLD.z:.4f}"
    root["ik_solution_degrees"] = f"yaw={math.degrees(yaw):.3f},shoulder={math.degrees(shoulder):.3f},elbow={math.degrees(elbow):.3f},wrist={math.degrees(wrist):.3f}"
    root["contact_xy_error"] = contact_error

    scene.frame_set(1)
    blend_path = OUT / "robot_phone_reproduction_v02.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.render.render(animation=True)
    print(f"BLEND={blend_path}")
    print(f"IK_DEG={math.degrees(yaw):.3f},{math.degrees(shoulder):.3f},{math.degrees(elbow):.3f},{math.degrees(wrist):.3f}")
    print(f"TARGET_WORLD={tuple(round(v, 4) for v in TARGET_WORLD)}")
    print(f"CONTACT_WORLD={tuple(round(v, 4) for v in contact)}")
    print(f"CONTACT_XY_ERROR={contact_error:.6f}")


if __name__ == "__main__":
    main()

