"""Volumetric robot: one physical click per screenshot, then page switch."""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve() if "--" in sys.argv else Path.cwd()
OUT = ROOT / "output" / "robot-arm" / "rig-v07-page-switch"
FRAMES = OUT / "frames"
OUT.mkdir(parents=True, exist_ok=True)
FRAMES.mkdir(parents=True, exist_ok=True)

spec = importlib.util.spec_from_file_location("v06", ROOT / "scripts" / "build_robot_four_clicks_v06_volumetric.py")
v06 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v06)
rig = v06.rig

PHONE_CENTER = Vector((2.50, 0.0, 0.0))
SCREEN_Z = 0.35
SCREEN_W, SCREEN_H = 2.72, 4.42
HOVER_FRAMES = (42, 90, 138, 186)
PRESS_FRAMES = (48, 96, 144, 192)
RELEASE_FRAMES = (54, 102, 150, 198)
TARGETS = (
    ("01 我", 0.90, 0.92),
    ("02 喜欢", 0.88, 0.555),
    ("03 视频", 0.125, 0.68),
    ("04 验证", 0.53, 0.52),
)
PAGES = (
    ROOT / "assets" / "screenshots" / "dashboard.jpg",
    ROOT / "assets" / "screenshots" / "myprofile1.png",
    ROOT / "assets" / "screenshots" / "myliketab.png",
    ROOT / "assets" / "screenshots" / "mylike.jpg",
    ROOT / "assets" / "screenshots" / "verification_success.png",
)


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
    if not -1.0 <= cosine <= 1.0:
        raise RuntimeError(f"Target outside robot workspace: {tuple(target)}")
    elbow = math.acos(cosine)
    shoulder = math.atan2(dx, dz) - math.atan2(rig.L2 * math.sin(elbow), rig.L1 + rig.L2 * math.cos(elbow))
    wrist = -(shoulder + elbow)
    return math.atan2(target.y, target.x), shoulder, elbow, wrist


def visibility(obj, keys):
    for frame, visible in keys:
        obj.hide_render = not visible
        obj.keyframe_insert("hide_render", frame=frame)


def image_material(name, path):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = bpy.data.images.load(str(path), check_existing=True)
    texture.interpolation = "Linear"
    mat.node_tree.links.new(texture.outputs["Color"], emission.inputs["Color"])
    mat.node_tree.links.new(texture.outputs["Alpha"], emission.inputs["Strength"])
    emission.inputs["Strength"].default_value = 0.88
    mat.node_tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return mat


def screen_plane(name, path, collection, z):
    x0, x1 = PHONE_CENTER.x - SCREEN_W / 2, PHONE_CENTER.x + SCREEN_W / 2
    y0, y1 = -SCREEN_H / 2, SCREEN_H / 2
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)), (), ((0, 1, 2, 3),))
    mesh.uv_layers.new(name="UVMap")
    uv = mesh.uv_layers.active.data
    for loop, coordinate in zip(uv, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop.uv = coordinate
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.data.materials.append(image_material(f"{name}_Material", path))
    obj["source_image"] = str(path)
    return obj


def add_ring(name, target, collection, mat):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.19, minor_radius=0.025, major_segments=48, minor_segments=12,
                                    location=(target.x, target.y, SCREEN_Z + 0.045))
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    rig.move_to(obj, collection)
    return obj


def add_lighting(scene):
    if scene.world is None:
        scene.world = bpy.data.worlds.new("V07_World")
    scene.world.color = (0.055, 0.065, 0.085)
    for name, location, energy, size in (
        ("Key", (7.0, -7.0, 12.0), 1500, 7.0),
        ("Fill", (-5.0, -2.0, 7.0), 900, 5.0),
        ("Rim", (1.0, 7.0, 9.0), 1100, 4.0),
    ):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        obj = bpy.data.objects.new(name, data)
        scene.collection.objects.link(obj)
        obj.location = location
        obj.rotation_euler = (Vector((2.0, 0.0, 1.6)) - obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = rig.setup_scene()
    scene.name = "RobotFourClicks_V07_PageSwitch"
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 1
    scene.eevee.use_raytracing = False
    scene.eevee.use_fast_gi = False
    scene.eevee.shadow_ray_count = 1
    scene.eevee.shadow_step_count = 1
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.frame_end = 240
    scene.render.filepath = str(FRAMES / "frame_")
    scene.camera.location = (13.2, -17.0, 9.6)
    scene.camera.data.lens = 47
    scene.camera.rotation_euler = (Vector((1.9, 0.0, 2.35)) - scene.camera.location).to_track_quat("-Z", "Y").to_euler()
    add_lighting(scene)

    robot = rig.new_collection("01_Volumetric_Robot_V07")
    phone = rig.new_collection("02_OneClick_Per_Page")
    lab = rig.new_collection("03_Lab_Set")

    white = rig.material("V07_PorcelainWhite", "#f3f4f6", 0.10, 0.23)
    graphite = rig.material("V07_Graphite", "#111419", 0.58, 0.18)
    metal = rig.material("V07_Aluminum", "#a9b0ba", 0.92, 0.13)
    rubber = rig.material("V07_Rubber", "#111317", 0.0, 0.68)
    dark = rig.material("V07_DarkMechanism", "#343a43", 0.82, 0.19)
    green = rig.material("V07_StatusGreen", "#18b778", 0.04, 0.24)
    amber = rig.material("V07_HydraulicAmber", "#d99a31", 0.20, 0.24)
    table = rig.material("V07_Table", "#d9dde3", 0.0, 0.74)

    root, j1, j2, j3, j4, j5, j6 = v06.build_volumetric_robot(
        robot, (white, graphite, metal, rubber, dark, green, amber)
    )
    rig.cube_local("Phone_Frame_V07", (SCREEN_W + 0.26, SCREEN_H + 0.28, 0.22), None,
                   (PHONE_CENTER.x, 0, 0.22), graphite, phone, 0.18)
    rig.cube_local("Phone_Dock_V07", (SCREEN_W + 0.54, SCREEN_H + 0.56, 0.12), None,
                   (PHONE_CENTER.x, 0, 0.07), white, lab, 0.14)
    rig.cube_local("Lab_Table_V07", (14, 12, 0.12), None, (1.8, 0, -0.06), table, lab, 0.02)

    pages = [screen_plane(f"Page_{i + 1}_{path.stem}", path, phone, SCREEN_Z + i * 0.001) for i, path in enumerate(PAGES)]
    page_ranges = ((1, 54), (55, 102), (103, 150), (151, 198), (199, 240))
    for index, (obj, (begin, end)) in enumerate(zip(pages, page_ranges)):
        keys = [(1, index == 0)]
        if index:
            keys.extend(((begin - 1, False), (begin, True)))
        keys.append((end, True))
        if end < 240:
            keys.extend(((end + 1, False), (240, False)))
        visibility(obj, keys)

    for index, target in enumerate(TARGET_WORLD):
        ring = add_ring(f"Tap_{index + 1}_Ring", target, phone, green)
        ring.scale = (0, 0, 0)
        ring.keyframe_insert("scale", frame=max(1, HOVER_FRAMES[index] - 12))
        ring.scale = (1, 1, 1)
        ring.keyframe_insert("scale", frame=HOVER_FRAMES[index])
        ring.scale = (0.58, 0.58, 0.58)
        ring.keyframe_insert("scale", frame=PRESS_FRAMES[index])
        ring.scale = (1.15, 1.15, 1.15)
        ring.keyframe_insert("scale", frame=RELEASE_FRAMES[index])
        ring.scale = (0, 0, 0)
        ring.keyframe_insert("scale", frame=RELEASE_FRAMES[index] + 1)

    # Required raised pose: base-to-middle is a straight 180 degrees; the
    # middle-to-tip included angle is 120 degrees (60-degree FK elbow bend).
    raised = (math.radians(-42), 0.0, math.radians(60), math.radians(-60))
    for frame in (1, 18):
        rig.key_rotation(j1, frame, z=raised[0])
        rig.key_rotation(j2, frame, y=raised[1])
        rig.key_rotation(j3, frame, y=raised[2])
        rig.key_rotation(j4, frame, y=raised[3])
        rig.key_location(j6, frame, (0, 0, 0))

    solutions, errors = [], []
    for index, (target, hover, press, release) in enumerate(zip(TARGET_WORLD, HOVER_FRAMES, PRESS_FRAMES, RELEASE_FRAMES)):
        solution = solve(target)
        solutions.append(solution)
        move_start = 18 if index == 0 else RELEASE_FRAMES[index - 1] + 1
        previous = raised if index == 0 else solutions[index - 1]
        for joint, angle in zip((j1, j2, j3, j4), previous):
            rig.key_rotation(joint, move_start, z=angle) if joint == j1 else rig.key_rotation(joint, move_start, y=angle)
        for joint, angle in zip((j1, j2, j3, j4), solution):
            rig.key_rotation(joint, hover, z=angle) if joint == j1 else rig.key_rotation(joint, hover, y=angle)
        rig.key_location(j6, hover, (0, 0, 0))
        rig.key_location(j6, press, (0, 0, -rig.HOVER))
        rig.key_location(j6, release, (0, 0, 0))
        scene.frame_set(press)
        bpy.context.view_layer.update()
        tip = bpy.data.objects["V06_TapTip"].matrix_world.translation
        errors.append(math.hypot(tip.x - target.x, tip.y - target.y))

    last = solutions[-1]
    for joint, angle in zip((j1, j2, j3, j4), last):
        rig.key_rotation(joint, 212, z=angle) if joint == j1 else rig.key_rotation(joint, 212, y=angle)
    for joint, angle in zip((j1, j2, j3, j4), raised):
        rig.key_rotation(joint, 240, z=angle) if joint == j1 else rig.key_rotation(joint, 240, y=angle)
    rig.key_location(j6, 240, (0, 0, 0))

    root["rig_version"] = "7.0-one-click-per-page"
    root["page_sequence"] = "dashboard -> profile -> liked grid -> video"
    root["raised_pose"] = "base-middle 180deg; middle-tip 120deg included angle"
    root["tap_xy_errors"] = ",".join(f"{value:.8f}" for value in errors)
    scene.frame_set(1)
    blend = OUT / "robot_four_clicks_v07_page_switch.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.render.render(animation=True)
    print(f"BLEND={blend}")
    print("TAP_ERRORS=" + ",".join(f"{value:.8f}" for value in errors))


if __name__ == "__main__":
    main()
