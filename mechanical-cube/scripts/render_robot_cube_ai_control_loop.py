"""Render an 8-second AI closed-loop control shot from the saved X-ray CUBE scene."""

from __future__ import annotations

from pathlib import Path
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "robot-arm" / "cube-ai-control-loop"
FRAMES = OUT / "frames"
OUT.mkdir(parents=True, exist_ok=True)
FRAMES.mkdir(parents=True, exist_ok=True)


def cube(name, size, location, color, bevel=0.015, parent=None):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.color = color
    if bevel:
        mod = obj.modifiers.new("EdgeSoftening", "BEVEL")
        mod.width = bevel
        mod.segments = 3
    obj.parent = parent
    return obj


def cylinder(name, radius, depth, location, color, parent=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.color = color
    obj.parent = parent
    return obj


def sphere(name, radius, location, color, parent=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.color = color
    obj.parent = parent
    return obj


def cylinder_between(name, start, end, radius, color):
    start = Vector(start)
    end = Vector(end)
    direction = end - start
    obj = cylinder(name, radius, direction.length, (start + end) / 2, color)
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    return obj


def wire_copy(source, color=(0.20, 0.88, 1.00, 1.0)):
    wire = source.copy()
    wire.data = source.data.copy()
    wire.animation_data_clear()
    wire.name = f"XRAY_Wire__{source.name}"
    bpy.context.scene.collection.objects.link(wire)
    modifier = wire.modifiers.new("TechnicalWire", "WIREFRAME")
    modifier.thickness = 0.008
    modifier.use_replace = True
    wire.color = color
    return wire


def key_location(obj, frame, location):
    obj.location = location
    obj.keyframe_insert(data_path="location", frame=frame)


def key_scale(obj, frame, scale):
    obj.scale = scale
    obj.keyframe_insert(data_path="scale", frame=frame)


def look_at(camera, frame, location, target=(0, 0, 2.0)):
    camera.location = location
    camera.rotation_euler = (Vector(target) - Vector(location)).to_track_quat("-Z", "Y").to_euler()
    camera.keyframe_insert(data_path="location", frame=frame)
    camera.keyframe_insert(data_path="rotation_euler", frame=frame)


def group_for(obj):
    name = obj.name.replace("XRAY_Wire__", "")
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
    scene = bpy.context.scene
    scene.name = "MechanicalCube_AI_ControlLoop"
    scene.frame_start = 1
    scene.frame_end = 192
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
    shading.show_shadows = False
    shading.show_cavity = True
    shading.cavity_type = "BOTH"
    shading.show_xray = True
    shading.xray_alpha = 0.28
    shading.background_type = "VIEWPORT"
    shading.background_color = (0.002, 0.006, 0.010)

    for name in ("Ground",):
        obj = bpy.data.objects.get(name)
        if obj:
            obj.hide_render = True
    for obj in scene.objects:
        if obj.name.startswith("XRAY_Grid_") or obj.name.startswith("XRAY_Wire__"):
            obj.hide_render = False

    y_axis = bpy.data.objects["AXIS_Y_GantryAssembly"]
    x_axis = bpy.data.objects["AXIS_X_MovingHead"]
    z_axis = bpy.data.objects["AXIS_Z_Stylus"]
    render_camera = scene.camera
    for obj in (y_axis, x_axis, z_axis, render_camera):
        obj.animation_data_clear()
        obj.location = (0, 0, 0) if obj != render_camera else obj.location

    # Phone surface and UI target overlay.
    cyan = (0.10, 0.76, 0.94, 1.0)
    cyan_dark = (0.035, 0.25, 0.34, 1.0)
    orange = (1.00, 0.40, 0.06, 1.0)
    green = (0.10, 1.00, 0.52, 1.0)
    purple = (0.64, 0.30, 1.00, 1.0)
    white = (0.72, 0.94, 1.00, 1.0)
    phone_z = 1.315
    phone = cube("AI_PhoneScreen", (1.12, 1.82, 0.035), (0, -0.02, phone_z), cyan_dark, 0.055)
    target_x, target_y = 0.34, -0.30
    target_z = phone_z + 0.035

    # A real downward-facing camera module is rigidly mounted to the X-axis
    # head. It follows gantry X/Y motion but is deliberately not parented to
    # AXIS_Z_Stylus, so the click stroke cannot drag the camera downward.
    camera_parts = []
    if bpy.data.objects.get("VisionCamera_Housing") is None:
        camera_parts.extend([
            cube("VisionCamera_Bracket", (0.24, 0.28, 0.10), (-0.28, 0.10, 2.475), white, 0.015, x_axis),
            cube("VisionCamera_Housing", (0.34, 0.34, 0.25), (-0.42, 0.10, 2.255), cyan_dark, 0.030, x_axis),
            cylinder("VisionCamera_LensRing", 0.12, 0.08, (-0.42, 0.10, 2.090), white, x_axis),
            cylinder("VisionCamera_Lens", 0.082, 0.10, (-0.42, 0.10, 2.025), cyan, x_axis),
        ])
    else:
        camera_parts = [obj for obj in scene.objects if obj.name.startswith("VisionCamera_")]
    camera_wires = []
    for part in camera_parts:
        if bpy.data.objects.get(f"XRAY_Wire__{part.name}") is None:
            camera_wires.append(wire_copy(part))

    # The AI core is intentionally visible as an active participant rather
    # than just a label. Capture packets flow into it before and after tapping.
    ai_core_pos = Vector((-2.05, 0.48, 3.42))
    ai_core = sphere("AI_Core", 0.19, ai_core_pos, purple)
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.31, minor_radius=0.018, major_segments=48,
        minor_segments=12, location=ai_core_pos,
    )
    ai_ring = bpy.context.object
    ai_ring.name = "AI_CoreOrbit"
    ai_ring.color = purple
    ai_ring.rotation_euler = (0.55, 0.30, 0.0)
    key_scale(ai_core, 1, (1.0, 1.0, 1.0))
    key_scale(ai_core, 22, (1.18, 1.18, 1.18))
    key_scale(ai_core, 40, (1.0, 1.0, 1.0))
    key_scale(ai_core, 154, (1.0, 1.0, 1.0))
    key_scale(ai_core, 174, (1.22, 1.22, 1.22))
    key_scale(ai_core, 192, (1.0, 1.0, 1.0))

    lens_initial = Vector((-0.42, 0.10, 1.965))
    lens_final = lens_initial + Vector((target_x, target_y - 0.20, 0.0))
    phone_corners = [
        (-0.55, 0.82, target_z + 0.02), (0.55, 0.82, target_z + 0.02),
        (-0.55, -0.82, target_z + 0.02), (0.55, -0.82, target_z + 0.02),
    ]
    pre_fov = [
        cylinder_between(f"AI_CameraFOV_Pre_{index}", lens_initial, point, 0.008, cyan)
        for index, point in enumerate(phone_corners)
    ]
    final_corners = [
        (target_x - 0.30, target_y - 0.22, target_z + 0.025),
        (target_x + 0.30, target_y - 0.22, target_z + 0.025),
        (target_x - 0.30, target_y + 0.22, target_z + 0.025),
        (target_x + 0.30, target_y + 0.22, target_z + 0.025),
    ]
    post_fov = [
        cylinder_between(f"AI_CameraFOV_Post_{index}", lens_final, point, 0.009, green)
        for index, point in enumerate(final_corners)
    ]
    capture_path = cylinder_between("AI_CaptureReturnPath", lens_initial, ai_core_pos, 0.010, purple)
    verify_path = cylinder_between("AI_VerifyReturnPath", lens_final, ai_core_pos, 0.012, green)

    capture_packets = []
    for index in range(6):
        packet = sphere(f"AI_CapturePacket_{index}", 0.032, lens_initial, purple)
        start = 16 + index * 4
        key_location(packet, 1, lens_initial)
        key_location(packet, start, lens_initial)
        key_location(packet, start + 24, ai_core_pos)
        capture_packets.append(packet)
    verify_packets = []
    for index in range(6):
        packet = sphere(f"AI_VerifyPacket_{index}", 0.034, lens_final, green)
        start = 148 + index * 4
        key_location(packet, 1, lens_final)
        key_location(packet, start, lens_final)
        key_location(packet, start + 22, ai_core_pos)
        verify_packets.append(packet)

    # Four independent corner brackets make a machine-vision target box.
    corners = []
    half_w, half_h, seg, thick = 0.25, 0.18, 0.13, 0.018
    for sx in (-1, 1):
        for sy in (-1, 1):
            corners.append(cube(
                f"AI_TargetCornerX_{sx}_{sy}", (seg, thick, 0.018),
                (target_x + sx * (half_w - seg / 2), target_y + sy * half_h, target_z), orange, 0.004,
            ))
            corners.append(cube(
                f"AI_TargetCornerY_{sx}_{sy}", (thick, seg, 0.018),
                (target_x + sx * half_w, target_y + sy * (half_h - seg / 2), target_z), orange, 0.004,
            ))

    scan_line = cube("AI_ScanLine", (1.02, 0.025, 0.018), (0, 0.78, target_z + 0.006), cyan, 0.004)
    key_location(scan_line, 1, (0, 0.78, target_z + 0.006))
    key_location(scan_line, 28, (0, -0.84, target_z + 0.006))
    key_location(scan_line, 38, (0, -0.84, target_z + 0.006))

    x_guide = cube("AI_X_CoordinateGuide", (1.02, 0.016, 0.014), (0, target_y, target_z + 0.012), white, 0.003)
    y_guide = cube("AI_Y_CoordinateGuide", (0.016, 1.66, 0.014), (target_x, -0.02, target_z + 0.012), white, 0.003)
    crosshair = cylinder("AI_TargetCrosshair", 0.055, 0.020, (target_x, target_y, target_z + 0.018), orange)

    # Contact ripple at the moment of the click.
    bpy.ops.mesh.primitive_torus_add(major_radius=0.075, minor_radius=0.012, major_segments=48, minor_segments=12, location=(target_x, target_y, target_z + 0.03))
    ripple = bpy.context.object
    ripple.name = "AI_ClickRipple"
    ripple.color = green
    key_scale(ripple, 1, (0.01, 0.01, 0.01))
    key_scale(ripple, 128, (0.01, 0.01, 0.01))
    key_scale(ripple, 140, (2.8, 2.8, 1.0))
    key_scale(ripple, 148, (0.01, 0.01, 0.01))

    bpy.ops.mesh.primitive_torus_add(major_radius=0.18, minor_radius=0.018, major_segments=48, minor_segments=12, location=(target_x, target_y, target_z + 0.04))
    verify_ring = bpy.context.object
    verify_ring.name = "AI_VerificationRing"
    verify_ring.color = green
    key_scale(verify_ring, 1, (0.01, 0.01, 0.01))
    key_scale(verify_ring, 146, (0.01, 0.01, 0.01))
    key_scale(verify_ring, 160, (1.35, 1.35, 1.0))
    key_scale(verify_ring, 192, (1.35, 1.35, 1.0))

    # Final verification plate becomes visible by growing from zero.
    verify = cube("AI_VerificationMarker", (0.42, 0.14, 0.025), (target_x, target_y, target_z + 0.055), green, 0.025)
    key_scale(verify, 1, (0.01, 0.01, 0.01))
    key_scale(verify, 140, (0.01, 0.01, 0.01))
    key_scale(verify, 158, (1.0, 1.0, 1.0))
    key_scale(verify, 192, (1.0, 1.0, 1.0))

    # Coordinated mechanical movement: Y first, then X, then one Z tap.
    for frame in (1, 54):
        key_location(y_axis, frame, (0, 0, 0))
        key_location(x_axis, frame, (0, 0, 0))
        key_location(z_axis, frame, (0, 0, 0))
    key_location(y_axis, 90, (0, target_y - 0.20, 0))
    key_location(y_axis, 192, (0, target_y - 0.20, 0))
    key_location(x_axis, 62, (0, 0, 0))
    key_location(x_axis, 102, (target_x, 0, 0))
    key_location(x_axis, 192, (target_x, 0, 0))
    key_location(z_axis, 108, (0, 0, 0))
    key_location(z_axis, 126, (0, 0, -0.055))
    key_location(z_axis, 134, (0, 0, -0.055))
    key_location(z_axis, 146, (0, 0, 0))
    key_location(z_axis, 192, (0, 0, 0))

    look_at(render_camera, 1, (5.7, -11.7, 4.8), (0, 0, 2.0))
    look_at(render_camera, 192, (4.5, -12.2, 4.65), (0, -0.02, 1.95))

    original_meshes = [
        obj for obj in scene.objects
        if obj.type == "MESH" and not obj.name.startswith(("XRAY_Wire__", "XRAY_Grid_", "AI_"))
    ]
    wire_meshes = [obj for obj in scene.objects if obj.name.startswith("XRAY_Wire__")]

    def active_group(frame):
        if 1 <= frame <= 30:
            return "CAMERA"
        if 31 <= frame <= 60:
            return None
        if 61 <= frame <= 108:
            return "Y" if frame < 84 else "X"
        if 109 <= frame <= 146:
            return "STYLUS"
        if 147 <= frame <= 178:
            return "CAMERA"
        return None

    def update_visuals(scene_arg):
        frame = scene_arg.frame_current
        group = active_group(frame)
        for obj in original_meshes:
            obj.color = orange if group_for(obj) == group else (0.055, 0.40, 0.52, 1.0)
        for wire in wire_meshes:
            obj_group = group_for(wire)
            wire.color = (1.00, 0.78, 0.22, 1.0) if obj_group == group else (0.20, 0.88, 1.00, 1.0)
        detecting = frame <= 54
        phone.color = green if frame >= 148 else cyan_dark
        for obj in corners:
            obj.color = green if frame >= 148 else (orange if detecting else cyan)
        x_guide.hide_render = not (30 <= frame <= 66)
        y_guide.hide_render = not (30 <= frame <= 66)
        crosshair.hide_render = not (20 <= frame <= 140)
        scan_line.hide_render = frame > 38
        for ray in pre_fov:
            ray.hide_render = frame > 34
        for ray in post_fov:
            ray.hide_render = not (146 <= frame <= 180)
        capture_path.hide_render = not (14 <= frame <= 60)
        verify_path.hide_render = not (146 <= frame <= 184)
        for packet in capture_packets:
            packet.hide_render = not (14 <= frame <= 64)
        for packet in verify_packets:
            packet.hide_render = not (146 <= frame <= 190)
        ai_core.color = green if frame >= 172 else purple
        ai_ring.color = green if frame >= 172 else purple

    bpy.app.handlers.frame_change_pre.clear()
    bpy.app.handlers.frame_change_pre.append(update_visuals)
    scene.frame_set(1)
    update_visuals(scene)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "mechanical_cube_ai_control_loop.blend"))
    bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
