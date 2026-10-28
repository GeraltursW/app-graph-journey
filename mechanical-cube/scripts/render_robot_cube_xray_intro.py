"""Render a short solid-to-X-ray component introduction for the mechanical CUBE."""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "robot-arm" / "cube-xray-intro"
OUT.mkdir(parents=True, exist_ok=True)
FRAMES = OUT / "frames"
FRAMES.mkdir(parents=True, exist_ok=True)


def load_base_scene():
    spec = importlib.util.spec_from_file_location("cube_base", ROOT / "scripts" / "build_robot_base_stage01.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()


def key_vec(obj, frame, value):
    obj.location = value
    obj.keyframe_insert(data_path="location", frame=frame)


def look_at(camera, frame, location, target=(0, 0, 2.15)):
    camera.location = location
    camera.rotation_euler = (Vector(target) - Vector(location)).to_track_quat("-Z", "Y").to_euler()
    camera.keyframe_insert(data_path="location", frame=frame)
    camera.keyframe_insert(data_path="rotation_euler", frame=frame)


def component_group(name):
    if name.startswith(("SideSupport_", "Gantry_YRail_", "Gantry_YSlider_")):
        return "Y"
    if name.startswith(("Gantry_Crossbeam", "Gantry_X_LinearRail")):
        return "X"
    if name.startswith("MovingHead_"):
        return "HEAD"
    if name.startswith("VisionCamera_"):
        return "CAMERA"
    if name.startswith("Stylus_"):
        return "STYLUS"
    if name.startswith("PhoneHolder_"):
        return "HOLDER"
    return "BODY"


def main():
    load_base_scene()
    scene = bpy.context.scene
    scene.name = "MechanicalCube_XRay_Intro"
    scene.frame_start = 1
    scene.frame_end = 360
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.filepath = str(FRAMES / "frame_")

    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.studio_light = "paint.sl"
    shading.color_type = "OBJECT"
    shading.show_shadows = True
    shading.show_cavity = True
    shading.cavity_type = "BOTH"
    shading.curvature_ridge_factor = 1.5
    shading.curvature_valley_factor = 1.0
    shading.background_type = "VIEWPORT"
    shading.background_color = (0.002, 0.006, 0.010)

    camera = scene.camera
    camera.data.lens = 54
    look_at(camera, 1, (7.0, -11.8, 5.2))
    look_at(camera, 72, (5.8, -12.4, 4.9))
    look_at(camera, 216, (5.2, -12.5, 4.8))
    look_at(camera, 360, (4.5, -12.6, 4.9))

    excluded = {"Ground"}
    render_meshes = [o for o in scene.objects if o.type == "MESH" and o.name not in excluded]
    for obj in render_meshes:
        obj["xray_group"] = component_group(obj.name)
        if obj.data.materials:
            obj.color = obj.data.materials[0].diffuse_color
        else:
            obj.color = (0.55, 0.58, 0.62, 1.0)

    # Fine edge layer. It is hidden during the opening solid-material view.
    wires = []
    for source in render_meshes:
        wire = source.copy()
        wire.data = source.data.copy()
        wire.animation_data_clear()
        wire.name = f"XRAY_Wire__{source.name}"
        wire["xray_group"] = source["xray_group"]
        scene.collection.objects.link(wire)
        modifier = wire.modifiers.new("TechnicalWire", "WIREFRAME")
        modifier.thickness = 0.008
        modifier.use_replace = True
        wire.color = (0.20, 0.88, 1.00, 1.0)
        wires.append(wire)

    # Engineering grid appears only after the X-ray transition.
    grid_objects = []
    grid_mat = bpy.data.materials.new("XRAY_Grid")
    grid_mat.diffuse_color = (0.02, 0.22, 0.32, 1.0)
    for index in range(-8, 9):
        for axis in ("X", "Y"):
            bpy.ops.mesh.primitive_cube_add(location=(0, index * 0.55, 1.015) if axis == "X" else (index * 0.55, 0, 1.015))
            line = bpy.context.object
            line.name = f"XRAY_Grid_{axis}_{index:+03d}"
            line.scale = (5.2, 0.006, 0.006) if axis == "X" else (0.006, 5.2, 0.006)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            line.data.materials.append(grid_mat)
            line.color = (0.02, 0.28, 0.40, 1.0)
            grid_objects.append(line)

    base_color = (0.055, 0.40, 0.52, 1.0)
    edge_color = (0.20, 0.88, 1.00, 1.0)
    highlight = (1.00, 0.42, 0.08, 1.0)
    highlight_edge = (1.00, 0.78, 0.22, 1.0)

    def active_group(frame):
        if 73 <= frame <= 112:
            return "Y"
        if 113 <= frame <= 152:
            return "X"
        if 153 <= frame <= 192:
            return "HEAD"
        if 193 <= frame <= 232:
            return "CAMERA"
        if 233 <= frame <= 272:
            return "STYLUS"
        if 273 <= frame <= 312:
            return "HOLDER"
        return None

    def update_visuals(scene_arg):
        frame = scene_arg.frame_current
        xray = frame >= 73
        shading.show_xray = xray
        shading.xray_alpha = 0.28
        scene_arg.world.color = (0.0, 0.0, 0.0) if xray else (0.018, 0.022, 0.030)
        bpy.data.objects.get("Ground").hide_render = xray
        group = active_group(frame)
        for obj in render_meshes:
            if xray:
                obj.color = highlight if obj["xray_group"] == group else base_color
            elif obj.data.materials:
                obj.color = obj.data.materials[0].diffuse_color
        for wire in wires:
            wire.hide_render = not xray
            wire.color = highlight_edge if wire["xray_group"] == group else edge_color
        for grid in grid_objects:
            grid.hide_render = not xray

    bpy.app.handlers.frame_change_pre.clear()
    bpy.app.handlers.frame_change_pre.append(update_visuals)

    y_axis = bpy.data.objects["AXIS_Y_GantryAssembly"]
    x_axis = bpy.data.objects["AXIS_X_MovingHead"]
    z_axis = bpy.data.objects["AXIS_Z_Stylus"]
    for frame in (1, 312):
        key_vec(y_axis, frame, (0, 0, 0))
        key_vec(x_axis, frame, (0, 0, 0))
        key_vec(z_axis, frame, (0, 0, 0))
    key_vec(y_axis, 328, (0, -0.42, 0))
    key_vec(y_axis, 344, (0, 0.16, 0))
    key_vec(y_axis, 360, (0, 0, 0))
    key_vec(x_axis, 328, (0.62, 0, 0))
    key_vec(x_axis, 344, (-0.38, 0, 0))
    key_vec(x_axis, 352, (0, 0, 0))
    key_vec(x_axis, 360, (0, 0, 0))
    key_vec(z_axis, 348, (0, 0, 0))
    key_vec(z_axis, 354, (0, 0, -0.11))
    key_vec(z_axis, 360, (0, 0, 0))

    scene.frame_set(1)
    update_visuals(scene)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "mechanical_cube_xray_intro.blend"))
    bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
