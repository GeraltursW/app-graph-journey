"""Animate the robot arm reproducing a UI tap on a lab phone.

The tap target is authored in phone-screen coordinates, then converted into
world space.  This keeps the animation tied to the same (x, y) control point
used by the automated test case rather than eyeballing the contact location.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve() if "--" in sys.argv else Path.cwd()
OUT = ROOT / "output" / "robot-arm" / "phone-click"
FRAMES = OUT / "frames"
OUT.mkdir(parents=True, exist_ok=True)
FRAMES.mkdir(parents=True, exist_ok=True)

ROBOT_BLEND = ROOT / "output" / "robot-arm" / "robot_arm_v01.blend"
PROFILE_SCREEN = ROOT / "assets" / "screenshots" / "myprofile1.png"
LIKES_SCREEN = ROOT / "assets" / "screenshots" / "myliketab.png"

# The "喜欢" tab in myprofile1.png, expressed in source pixels and normalized UV.
SOURCE_W, SOURCE_H = 1828, 2584
TARGET_U, TARGET_V = 0.90, 0.44
TARGET_PX = (round(TARGET_U * SOURCE_W), round(TARGET_V * SOURCE_H))


def rgba(value: str, alpha: float = 1.0):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255.0 for i in (0, 2, 4)) + (alpha,)


def mat(name, color, metallic=0.0, roughness=0.42):
    material = bpy.data.materials.new(name)
    material.diffuse_color = rgba(color)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba(color)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return material


def image_mat(name, image_path):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = (1, 1, 1, 1)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(image_path), check_existing=True)
    tex.interpolation = "Linear"
    bsdf.inputs["Roughness"].default_value = 0.32
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return material


def smooth(obj):
    if hasattr(obj.data, "polygons"):
        for polygon in obj.data.polygons:
            polygon.use_smooth = True


def cube(name, dimensions, location, material, bevel=0.06, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new("Soft bevel", "BEVEL")
        modifier.width = bevel
        modifier.segments = 5
    return obj


def cylinder_between(name, start, end, radius, material, vertices=32):
    start, end = Vector(start), Vector(end)
    delta = end - start
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=delta.length, location=(start + end) * 0.5)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    obj.data.materials.append(material)
    smooth(obj)
    return obj


def plane_with_image(name, size_xy, location, image_path):
    bpy.ops.mesh.primitive_plane_add(size=2, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = (size_xy[0], size_xy[1], 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(image_mat(f"{name}_Material", image_path))
    return obj


def text_flat(name, body, location, size, material, align="CENTER"):
    curve = bpy.data.curves.new(f"{name}_Curve", "FONT")
    curve.body = body
    curve.align_x = align
    curve.align_y = "CENTER"
    curve.size = size
    curve.extrude = 0.004
    font = Path("C:/Windows/Fonts/msyh.ttc")
    if font.exists():
        curve.font = bpy.data.fonts.load(str(font), check_existing=True)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.data.materials.append(material)
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def key_rotation(obj, frame, x=None, y=None, z=None):
    if x is not None:
        obj.rotation_euler[0] = math.radians(x)
    if y is not None:
        obj.rotation_euler[1] = math.radians(y)
    if z is not None:
        obj.rotation_euler[2] = math.radians(z)
    obj.keyframe_insert("rotation_euler", frame=frame)


def append_robot():
    with bpy.data.libraries.load(str(ROBOT_BLEND), link=False) as (source, target):
        if "RobotArm_Asset" not in source.collections:
            raise RuntimeError("RobotArm_Asset collection is missing")
        target.collections = ["RobotArm_Asset"]
    collection = target.collections[0]
    bpy.context.scene.collection.children.link(collection)
    return bpy.data.objects["ARM_ROOT"]


def setup_scene():
    scene = bpy.context.scene
    scene.name = "RobotPhoneClick"
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.frame_start = 1
    scene.frame_end = 108
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
    scene.display.shading.background_color = (0.93, 0.94, 0.96)

    camera_data = bpy.data.cameras.new("UseCase_Camera")
    camera = bpy.data.objects.new("UseCase_Camera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = (10.8, -13.8, 9.4)
    camera_data.lens = 55
    look_at(camera, (1.9, 0.0, 2.15))
    scene.camera = camera
    return scene


def build_phone(phone_center, screen_z, target_world):
    white = mat("Lab_White", "#f7f7f8", metallic=0.02, roughness=0.32)
    frame = mat("Phone_Frame", "#202328", metallic=0.60, roughness=0.20)
    black = mat("Phone_Black", "#07080a", metallic=0.10, roughness=0.20)
    green = mat("Coordinate_Green", "#16a36a", metallic=0.05, roughness=0.28)
    blue = mat("Coordinate_Blue", "#4f7cff", metallic=0.05, roughness=0.28)
    red = mat("Target_Red", "#ff3b4d", metallic=0.02, roughness=0.28)

    phone_w, phone_h = 2.40, 4.80
    screen_w, screen_h = 2.17, 4.42
    target_local_x = (TARGET_U - 0.5) * screen_w
    target_local_y = (0.5 - TARGET_V) * screen_h
    chassis_z = screen_z - 0.10
    cube("LabPhone_Frame", (phone_w, phone_h, 0.22), (phone_center.x, phone_center.y, chassis_z), frame, 0.18)
    cube("LabPhone_Glass", (screen_w + 0.06, screen_h + 0.06, 0.055), (phone_center.x, phone_center.y, screen_z - 0.025), black, 0.12)
    # Build the UI as simple shadcn-like geometry so it remains crisp in the
    # fast turntable renderer. The layout mirrors the profile -> likes action.
    screen_bg = mat("UI_Background", "#fbfbfc", metallic=0.0, roughness=0.55)
    ui_ink = mat("UI_Ink", "#191b20", metallic=0.0, roughness=0.45)
    ui_muted = mat("UI_Muted", "#8a9099", metallic=0.0, roughness=0.50)
    ui_card = mat("UI_Card", "#e7e9ed", metallic=0.0, roughness=0.62)
    ui_blue = mat("UI_Header", "#3d78ba", metallic=0.0, roughness=0.45)
    cube("UI_ScreenBackground", (screen_w, screen_h, 0.028), (phone_center.x, phone_center.y, screen_z + 0.014), screen_bg, 0.08)
    cube("UI_ProfileHeader", (screen_w - 0.06, 0.92, 0.035), (phone_center.x, phone_center.y + screen_h * 0.37, screen_z + 0.035), ui_blue, 0.07)
    text_flat("UI_ProfileTitle", "我的页面", (phone_center.x, phone_center.y + screen_h * 0.38, screen_z + 0.060), 0.20, white)

    tab_y = phone_center.y + target_local_y
    tabs = (("作品", -0.86), ("日常", -0.43), ("推荐", 0.0), ("收藏", 0.43), ("喜欢", target_local_x))
    for index, (label, offset_x) in enumerate(tabs):
        text_flat(f"UI_Tab_{index}", label, (phone_center.x + offset_x, tab_y, screen_z + 0.060), 0.145, ui_ink if index in (0, 4) else ui_muted)

    # Active-tab underline moves from 作品 to 喜欢 when the press completes.
    old_line = cube("UI_ActiveBefore", (0.31, 0.035, 0.027), (phone_center.x - 0.86, tab_y - 0.22, screen_z + 0.055), ui_ink, 0.012)
    new_line = cube("UI_ActiveAfter", (0.31, 0.035, 0.027), (phone_center.x + target_local_x, tab_y - 0.22, screen_z + 0.058), green, 0.012)
    for frame_no, after_click in ((1, False), (62, False), (63, True), (108, True)):
        old_line.hide_render = after_click
        old_line.keyframe_insert("hide_render", frame=frame_no)
        new_line.hide_render = not after_click
        new_line.keyframe_insert("hide_render", frame=frame_no)

    # Content cards become visible only after the 喜欢 tab is selected.
    card_colors = (ui_card, white, ui_card, white, ui_card, white)
    for index in range(6):
        col, row = index % 2, index // 2
        x = phone_center.x + (-0.53 if col == 0 else 0.53)
        y = tab_y - 0.70 - row * 0.78
        card = cube(f"UI_LikeCard_{index}", (0.88, 0.62, 0.026), (x, y, screen_z + 0.050), card_colors[index], 0.08)
        for frame_no, visible in ((1, False), (62, False), (63, True), (108, True)):
            card.hide_render = not visible
            card.keyframe_insert("hide_render", frame=frame_no)

    # Local phone coordinate axes start at the lower-left corner of the screen.
    origin = Vector((phone_center.x - screen_w * 0.5, phone_center.y - screen_h * 0.5, screen_z + 0.06))
    cylinder_between("Screen_X_Axis", origin, origin + Vector((0.82, 0, 0)), 0.025, green)
    cylinder_between("Screen_Y_Axis", origin, origin + Vector((0, 0.82, 0)), 0.025, blue)
    text_flat("Axis_X", "x", origin + Vector((0.94, 0, 0.015)), 0.18, green)
    text_flat("Axis_Y", "y", origin + Vector((0, 0.96, 0.015)), 0.18, blue)

    # Target rings pulse during coordinate lock and collapse under the finger.
    rings = []
    for index, radius in enumerate((0.20, 0.31)):
        bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=0.025, major_segments=64, minor_segments=16, location=(target_world.x, target_world.y, screen_z + 0.075))
        ring = bpy.context.object
        ring.name = f"TargetRing_{index}"
        ring.data.materials.append(red if index == 0 else green)
        rings.append(ring)
        ring.scale = (0.45, 0.45, 0.45)
        ring.keyframe_insert("scale", frame=42)
        ring.scale = (1, 1, 1)
        ring.keyframe_insert("scale", frame=54)
        ring.scale = (0.62, 0.62, 0.62)
        ring.keyframe_insert("scale", frame=61)
        ring.scale = (1.18, 1.18, 1.18)
        ring.keyframe_insert("scale", frame=67)
        ring.scale = (0.0, 0.0, 0.0)
        ring.keyframe_insert("scale", frame=77)

    # A thin lab platform supports the phone if the solved contact plane is above the table.
    platform_height = max(0.04, chassis_z - 0.11)
    cube("Phone_LabPlatform", (phone_w + 0.44, phone_h + 0.44, platform_height), (phone_center.x, phone_center.y, platform_height * 0.5), white, 0.14)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = setup_scene()
    append_robot()

    root = bpy.data.objects["ARM_ROOT"]
    base = bpy.data.objects["J01_BaseYaw"]
    shoulder = bpy.data.objects["J02_ShoulderPitch"]
    elbow = bpy.data.objects["J03_ElbowPitch"]
    wrist = bpy.data.objects["J04_WristPitch"]

    for obj in (root, base, shoulder, elbow, wrist):
        obj.rotation_mode = "XYZ"

    # 1) rotate toward the lab phone; 2) lower the arm; 3) press; 4) retract.
    key_rotation(base, 1, z=-58)
    key_rotation(base, 24, z=0)
    key_rotation(base, 108, z=0)

    key_rotation(shoulder, 1, y=0)
    key_rotation(shoulder, 22, y=0)
    key_rotation(shoulder, 54, y=35)
    key_rotation(shoulder, 76, y=35)
    key_rotation(shoulder, 104, y=8)

    key_rotation(elbow, 1, y=0)
    key_rotation(elbow, 26, y=0)
    key_rotation(elbow, 54, y=50)
    key_rotation(elbow, 76, y=50)
    key_rotation(elbow, 104, y=10)

    key_rotation(wrist, 1, y=0)
    key_rotation(wrist, 30, y=0)
    key_rotation(wrist, 54, y=-50)
    key_rotation(wrist, 60, y=-54)
    key_rotation(wrist, 67, y=-50)
    key_rotation(wrist, 76, y=-50)
    key_rotation(wrist, 104, y=-8)

    # Solve the phone placement from the evaluated fingertip at maximum press.
    scene.frame_set(60)
    bpy.context.view_layer.update()
    pad_a = bpy.data.objects.get("FingerPad_-1")
    pad_b = bpy.data.objects.get("FingerPad_+1")
    if pad_a is None or pad_b is None:
        raise RuntimeError("Robot gripper pads were not found")
    tip_world = (pad_a.matrix_world.translation + pad_b.matrix_world.translation) * 0.5

    screen_w, screen_h = 2.17, 4.42
    target_local_x = (TARGET_U - 0.5) * screen_w
    target_local_y = (0.5 - TARGET_V) * screen_h
    phone_center = Vector((tip_world.x - target_local_x, tip_world.y - target_local_y, 0))
    screen_z = max(0.16, tip_world.z - 0.10)
    target_world = Vector((phone_center.x + target_local_x, phone_center.y + target_local_y, screen_z))
    build_phone(phone_center, screen_z, target_world)

    # Table surface. Coordinate math is added later as a fixed 2D HUD so the
    # formula remains readable while the camera watches the physical action.
    table = mat("Lab_Table", "#e7e9ed", metallic=0.0, roughness=0.76)
    cube("Lab_Table", (14, 12, 0.12), (2.1, 0, -0.06), table, 0.03)
    scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "robot_phone_click.blend"))
    bpy.ops.render.render(animation=True)
    print(f"TARGET_PIXEL={TARGET_PX}")
    print(f"TARGET_WORLD=({target_world.x:.3f}, {target_world.y:.3f}, {target_world.z:.3f})")
    print(f"FRAMES={FRAMES}")


if __name__ == "__main__":
    main()

