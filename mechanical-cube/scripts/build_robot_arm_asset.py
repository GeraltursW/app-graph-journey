"""Build a reusable, articulated black-and-white industrial robot arm.

Run with Blender:
    blender --background --factory-startup --python scripts/build_robot_arm_asset.py -- PROJECT_ROOT

The asset is intentionally stylized for the application-knowledge-graph film:
clean shadcn-like black/white surfaces, readable joints, and a hierarchy that
can be animated later without rebuilding the model.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve() if "--" in sys.argv else Path.cwd()
OUT = ROOT / "output" / "robot-arm"
OUT.mkdir(parents=True, exist_ok=True)


def rgba(hex_color: str, alpha: float = 1.0):
    value = hex_color.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255.0 for i in (0, 2, 4)) + (alpha,)


def material(name: str, color: str, metallic=0.0, roughness=0.35):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = rgba(color)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba(color)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def set_collection(obj, collection):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    collection.objects.link(obj)


def parent_keep_world(obj, parent):
    """Attach an object without changing its authored world transform."""
    if parent is None:
        return
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world


def smooth(obj):
    if hasattr(obj.data, "polygons"):
        for poly in obj.data.polygons:
            poly.use_smooth = True


def empty(name, location, collection, parent=None):
    obj = bpy.data.objects.new(name, None)
    collection.objects.link(obj)
    obj.location = location
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = 0.34
    parent_keep_world(obj, parent)
    return obj


def cylinder(name, radius, depth, location, mat, collection, rotation=(0, 0, 0), parent=None, vertices=96, bevel=0.04):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    set_collection(obj, collection)
    obj.data.materials.append(mat)
    parent_keep_world(obj, parent)
    smooth(obj)
    if bevel:
        mod = obj.modifiers.new("Edge catchlight", "BEVEL")
        mod.width = bevel
        mod.segments = 3
    return obj


def uv_sphere(name, radius, location, mat, collection, scale=(1, 1, 1), parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    set_collection(obj, collection)
    obj.data.materials.append(mat)
    parent_keep_world(obj, parent)
    smooth(obj)
    return obj


def bevel_cube(name, dimensions, location, mat, collection, bevel=0.12, rotation=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    set_collection(obj, collection)
    obj.data.materials.append(mat)
    parent_keep_world(obj, parent)
    mod = obj.modifiers.new("Precision bevel", "BEVEL")
    mod.width = bevel
    mod.segments = 6
    return obj


def link_between(name, start, end, width, depth, mat, collection, parent=None, inset_mat=None):
    a, b = Vector(start), Vector(end)
    delta = b - a
    midpoint = (a + b) * 0.5
    obj = bevel_cube(name, (width, depth, delta.length), midpoint, mat, collection, min(width, depth) * 0.24, parent=parent)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = delta.to_track_quat("Z", "Y")
    if inset_mat:
        inset = bevel_cube(f"{name}_GraphiteSpine", (width * 0.20, depth * 1.025, delta.length * 0.76), midpoint, inset_mat, collection, min(width, depth) * 0.08, parent=parent)
        inset.rotation_mode = "QUATERNION"
        inset.rotation_quaternion = delta.to_track_quat("Z", "Y")
    return obj


def joint(name, center, radius, depth, collection, white, graphite, metal, parent=None):
    # Pitch joints use the Y axis so the black circular caps remain legible in side and 3/4 views.
    rot = (math.pi / 2, 0, 0)
    cylinder(f"{name}_WhiteHousing", radius, depth, center, white, collection, rot, parent, bevel=0.065)
    cylinder(f"{name}_BlackCapNear", radius * 0.78, depth + 0.055, (center[0], center[1] - 0.03, center[2]), graphite, collection, rot, parent, bevel=0.035)
    cylinder(f"{name}_MetalRing", radius * 0.48, depth + 0.075, (center[0], center[1] - 0.042, center[2]), metal, collection, rot, parent, bevel=0.018)
    cylinder(f"{name}_InnerCap", radius * 0.39, depth + 0.088, (center[0], center[1] - 0.050, center[2]), graphite, collection, rot, parent, bevel=0.015)
    # Six understated fasteners sell the industrial scale without making the model noisy.
    for idx in range(6):
        angle = idx * math.tau / 6
        x = center[0] + math.cos(angle) * radius * 0.61
        z = center[2] + math.sin(angle) * radius * 0.61
        cylinder(f"{name}_Bolt_{idx:02d}", radius * 0.035, depth + 0.11, (x, center[1] - 0.06, z), metal, collection, rot, parent, vertices=24, bevel=0.008)


def build_robot():
    collection = bpy.data.collections.new("RobotArm_Asset")
    bpy.context.scene.collection.children.link(collection)

    white = material("Robot_PorcelainWhite", "#f4f5f7", metallic=0.08, roughness=0.24)
    graphite = material("Robot_Graphite", "#111318", metallic=0.44, roughness=0.22)
    black = material("Robot_DeepBlack", "#050607", metallic=0.16, roughness=0.19)
    metal = material("Robot_AnodizedMetal", "#aeb4bc", metallic=0.88, roughness=0.16)
    rubber = material("Robot_BaseRubber", "#17191c", metallic=0.0, roughness=0.64)

    root = empty("ARM_ROOT", (0, 0, 0), collection)
    base_yaw = empty("J01_BaseYaw", (0, 0, 0.65), collection, root)
    shoulder = empty("J02_ShoulderPitch", (0, 0, 1.55), collection, base_yaw)
    elbow = empty("J03_ElbowPitch", (0.55, 0, 3.72), collection, shoulder)
    wrist_pitch = empty("J04_WristPitch", (1.68, 0, 5.12), collection, elbow)
    wrist_roll = empty("J05_WristRoll", (2.23, 0, 5.34), collection, wrist_pitch)
    tool_yaw = empty("J06_ToolYaw", (2.61, 0, 5.08), collection, wrist_roll)

    # Base and first yaw stage.
    cylinder("Base_RubberFoot", 1.18, 0.18, (0, 0, 0.09), rubber, collection, parent=root, bevel=0.06)
    cylinder("Base_MountPlate", 1.10, 0.23, (0, 0, 0.25), white, collection, parent=root, bevel=0.07)
    cylinder("Base_Pedestal", 0.72, 0.78, (0, 0, 0.68), white, collection, parent=root, bevel=0.08)
    cylinder("Base_YawGap", 0.73, 0.10, (0, 0, 1.08), graphite, collection, parent=root, bevel=0.025)
    cylinder("Base_ShoulderDeck", 0.77, 0.22, (0, 0, 1.20), white, collection, parent=base_yaw, bevel=0.07)
    for idx in range(8):
        a = idx * math.tau / 8
        cylinder(f"Base_Bolt_{idx:02d}", 0.035, 0.025, (math.cos(a) * 0.87, math.sin(a) * 0.87, 0.375), graphite, collection, parent=root, vertices=24, bevel=0.008)

    joint("Shoulder", (0, 0, 1.58), 0.72, 0.66, collection, white, graphite, metal, base_yaw)
    link_between("UpperArm", (0.08, 0, 1.92), (0.49, 0, 3.42), 0.78, 0.72, white, collection, shoulder, graphite)
    joint("Elbow", (0.55, 0, 3.72), 0.63, 0.62, collection, white, graphite, metal, shoulder)
    link_between("Forearm", (0.78, 0, 4.02), (1.51, 0, 4.88), 0.67, 0.63, white, collection, elbow, graphite)
    joint("WristPitch", (1.68, 0, 5.12), 0.50, 0.54, collection, white, graphite, metal, elbow)

    # Wrist roll stack follows the last arm segment and ends in a compact gripper.
    link_between("WristNeck", (1.93, 0, 5.24), (2.26, 0, 5.34), 0.46, 0.46, white, collection, wrist_pitch)
    neck_dir = Vector((0.53, 0, -0.25)).normalized()
    wrist_angle = math.atan2(neck_dir.x, neck_dir.z)
    cylinder("WristRoll_Black", 0.34, 0.48, (2.35, 0, 5.28), graphite, collection, (0, wrist_angle, 0), wrist_pitch, bevel=0.045)
    cylinder("WristRoll_Silver", 0.35, 0.085, (2.50, 0, 5.17), metal, collection, (0, wrist_angle, 0), wrist_roll, bevel=0.018)
    cylinder("ToolFlange", 0.31, 0.22, (2.61, 0, 5.08), black, collection, (0, wrist_angle, 0), wrist_roll, bevel=0.035)
    bevel_cube("GripperPalm", (0.54, 0.46, 0.38), (2.77, 0, 4.90), white, collection, 0.09, rotation=(0, -0.62, 0), parent=tool_yaw)

    # Two fingers with metal knuckles and replaceable graphite pads.
    for side in (-1, 1):
        y = side * 0.25
        cylinder(f"FingerKnuckle_{side:+d}", 0.115, 0.13, (2.84, y, 4.78), metal, collection, (math.pi / 2, 0, 0), tool_yaw, vertices=48, bevel=0.02)
        finger = bevel_cube(f"Finger_{side:+d}", (0.18, 0.15, 0.62), (2.93, y, 4.48), white, collection, 0.055, rotation=(0, -0.15, 0), parent=tool_yaw)
        pad = bevel_cube(f"FingerPad_{side:+d}", (0.12, 0.18, 0.24), (2.98, y - side * 0.02, 4.22), rubber, collection, 0.035, rotation=(0, -0.15, 0), parent=tool_yaw)

    # Small status indicator; neutral white so it remains compatible with the film palette.
    indicator = material("Robot_StatusLight", "#dffaf1", metallic=0.0, roughness=0.22)
    bsdf = indicator.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Emission Color"].default_value = rgba("#dffaf1")
    bsdf.inputs["Emission Strength"].default_value = 2.0
    cylinder("Status_Indicator", 0.055, 0.03, (0.0, -0.405, 0.78), indicator, collection, (math.pi / 2, 0, 0), root, vertices=32, bevel=0.01)

    # Preserve useful names for later animation tooling.
    root["asset_type"] = "articulated_industrial_robot"
    root["joint_order"] = "J01_BaseYaw,J02_ShoulderPitch,J03_ElbowPitch,J04_WristPitch,J05_WristRoll,J06_ToolYaw"
    return root


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_scene():
    scene = bpy.context.scene
    scene.name = "RobotArm_Lookdev"
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(OUT / "robot_arm_preview.png")
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.fps = 30
    scene.frame_start = 1
    scene.frame_end = 180
    scene.view_settings.look = "AgX - Medium High Contrast"

    world = bpy.data.worlds.new("RobotArm_StudioWorld")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = rgba("#eef1f4")
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.38
    scene.world = world

    floor_mat = material("Studio_Floor", "#e7eaee", metallic=0.0, roughness=0.78)
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
    floor = bpy.context.object
    floor.name = "Studio_Floor"
    floor.data.materials.append(floor_mat)

    # Large softboxes produce broad highlights on the white shells and readable black caps.
    for name, location, energy, size, color in (
        ("Key_Softbox", (-4.5, -5.8, 8.5), 1250, 5.0, "#ffffff"),
        ("Fill_Softbox", (5.0, -2.0, 6.0), 820, 4.0, "#dfeaff"),
        ("Rim_Softbox", (1.5, 5.5, 7.2), 1050, 3.5, "#ffffff"),
    ):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        data.color = rgba(color)[:3]
        light = bpy.data.objects.new(name, data)
        scene.collection.objects.link(light)
        light.location = location
        look_at(light, (0.8, 0, 2.8))

    camera_data = bpy.data.cameras.new("RobotArm_Camera")
    camera = bpy.data.objects.new("RobotArm_Camera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = (11.0, -17.5, 8.1)
    camera_data.lens = 60
    camera_data.sensor_width = 36
    look_at(camera, (0.9, 0, 2.70))
    scene.camera = camera

    # Mild depth of field keeps the product-shot feeling without softening the model.
    focus = bpy.data.objects.new("Camera_Focus", None)
    scene.collection.objects.link(focus)
    focus.location = (0.8, 0, 2.8)
    camera_data.dof.use_dof = True
    camera_data.dof.focus_object = focus
    camera_data.dof.aperture_fstop = 7.5

    scene.render.image_settings.color_mode = "RGB"
    return scene


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = setup_scene()
    build_robot()
    blend_path = OUT / "robot_arm_v01.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    scene.render.filepath = str(OUT / "robot_arm_preview.png")
    bpy.ops.render.render(write_still=True)
    print(f"BLEND={blend_path}")
    print(f"PREVIEW={scene.render.filepath}")


if __name__ == "__main__":
    main()
