"""Stage 01: rectangular robot base with an open, hollow mechanism housing."""

from pathlib import Path
import math
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "robot-arm" / "rebuild-stage01-professional"
OUT.mkdir(parents=True, exist_ok=True)


def mat(name, color, metallic=0.0, roughness=0.4):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return material


def cube(name, size, location, material, bevel=0.04):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new("EdgeSoftening", "BEVEL")
        mod.width = bevel
        mod.segments = 4
    return obj


def cylinder(name, radius, depth, location, material, vertices=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    bevel = obj.modifiers.new("EdgeSoftening", "BEVEL")
    bevel.width = 0.025
    bevel.segments = 3
    return obj


def bolt(name, location, material):
    obj = cylinder(name, 0.035, 0.022, location, material, 32)
    obj.rotation_euler.x = math.radians(90)
    return obj


def empty(name):
    obj = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(obj)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = 0.22
    return obj


def parent_to(obj, parent):
    obj.parent = parent
    return obj


def cone(name, radius1, radius2, depth, location, material, vertices=48):
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices, radius1=radius1, radius2=radius2,
        depth=depth, location=location,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    bevel = obj.modifiers.new("EdgeSoftening", "BEVEL")
    bevel.width = 0.012
    bevel.segments = 3
    return obj


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    print("STAGE01 factory", flush=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.studio_light = "paint.sl"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "BOTH"
    scene.display.shading.curvature_ridge_factor = 1.25
    scene.display.shading.curvature_valley_factor = 0.85
    scene.display.shading.background_type = "VIEWPORT"
    scene.display.shading.background_color = (0.025, 0.030, 0.038)
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(OUT / "robot_base_stage01_professional.png")
    scene.render.film_transparent = False
    scene.world = bpy.data.worlds.new("Workshop_World")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.025, 0.030, 0.038, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.22

    white = mat("PowderCoated_Aluminum", (0.57, 0.60, 0.64), 0.74, 0.24)
    edge = mat("Black_Anodized_Frame", (0.018, 0.023, 0.030), 0.82, 0.17)
    inner = mat("Internal_Structural_Graphite", (0.055, 0.064, 0.078), 0.84, 0.20)
    steel = mat("Machined_Steel", (0.42, 0.48, 0.55), 0.96, 0.10)
    motor_black = mat("Servo_Black", (0.025, 0.030, 0.038), 0.68, 0.20)
    warning = mat("Industrial_Orange", (0.55, 0.16, 0.025), 0.42, 0.30)
    rubber = mat("PhoneHolder_Rubber", (0.012, 0.015, 0.020), 0.05, 0.72)
    vision_glass = mat("VisionCamera_Glass", (0.025, 0.16, 0.22), 0.72, 0.10)
    floor_mat = mat("Floor", (0.035, 0.042, 0.052), 0.12, 0.48)
    print("STAGE01 materials", flush=True)

    # Rectangular load-bearing base: deliberately not a circular robot pedestal.
    cube("Base_LowerPlinth", (4.80, 3.50, 0.20), (0, 0, 0.10), edge, 0.025)
    cube("Base_MainBlock", (4.62, 3.32, 0.72), (0, 0, 0.56), white, 0.035)
    cube("Base_TopPlate", (4.72, 3.42, 0.14), (0, 0, 0.99), edge, 0.018)

    # Recessed front service panel and four visible fasteners.
    cube("Base_ServicePanel", (2.95, 0.035, 0.40), (0, -1.677, 0.56), inner, 0.012)
    for x in (-1.37, 1.37):
        for z in (0.42, 0.70):
            bolt(f"Base_Bolt_{x}_{z}", (x, -1.704, z), steel)
    print("STAGE01 base", flush=True)

    # Hollow upper shell. It is constructed from real wall panels, leaving the
    # front open instead of faking the cavity with a black rectangle.
    shell_z0 = 1.08
    shell_h = 2.85
    shell_w = 3.82
    shell_d = 2.66
    wall = 0.105
    cube("Housing_BackWall", (shell_w, wall, shell_h), (0, shell_d / 2 - wall / 2, shell_z0 + shell_h / 2), white, 0.018)
    cube("Housing_LeftWall", (wall, shell_d, shell_h), (-shell_w / 2 + wall / 2, 0, shell_z0 + shell_h / 2), white, 0.018)
    cube("Housing_RightWall", (wall, shell_d, shell_h), (shell_w / 2 - wall / 2, 0, shell_z0 + shell_h / 2), white, 0.018)
    cube("Housing_Roof", (shell_w, shell_d, 0.11), (0, 0, shell_z0 + shell_h - 0.055), white, 0.018)
    cube("Housing_Floor", (shell_w, shell_d, 0.11), (0, 0, shell_z0 + 0.055), edge, 0.018)

    # Strong rim around the open front makes wall thickness and volume legible.
    front_y = -shell_d / 2 - 0.012
    cube("Opening_LeftRim", (0.105, 0.10, shell_h - 0.10), (-shell_w / 2 + 0.052, front_y, shell_z0 + shell_h / 2), edge, 0.012)
    cube("Opening_RightRim", (0.105, 0.10, shell_h - 0.10), (shell_w / 2 - 0.052, front_y, shell_z0 + shell_h / 2), edge, 0.012)
    cube("Opening_TopRim", (shell_w - 0.10, 0.10, 0.105), (0, front_y, shell_z0 + shell_h - 0.052), edge, 0.012)
    for x in (-1.72, 1.72):
        for z in (1.30, 2.50, 3.70):
            bolt(f"Housing_Fastener_{x}_{z}", (x, front_y - 0.057, z), steel)
    print("STAGE01 shell", flush=True)

    # Low-profile phone fixture, mounted horizontally on the cavity floor.
    # No phone or other mechanism is added at this stage.
    holder_z = shell_z0 + 0.145
    cube("PhoneHolder_BasePlate", (1.38, 2.12, 0.075), (0, -0.02, holder_z), inner, 0.025)
    cube("PhoneHolder_RubberPad", (1.16, 1.84, 0.025), (0, -0.02, holder_z + 0.050), rubber, 0.015)
    cube("PhoneHolder_LeftGuide", (0.105, 1.96, 0.16), (-0.665, -0.02, holder_z + 0.105), edge, 0.022)
    cube("PhoneHolder_RightGuide", (0.105, 1.96, 0.16), (0.665, -0.02, holder_z + 0.105), edge, 0.022)
    cube("PhoneHolder_EndStop", (1.36, 0.105, 0.16), (0, 0.985, holder_z + 0.105), edge, 0.022)
    for x in (-0.54, 0.54):
        for y in (-0.84, 0.84):
            cylinder(f"PhoneHolder_Bolt_{x}_{y}", 0.032, 0.018, (x, y, holder_z + 0.093), steel, 24)

    # Gantry axis: structural uprights, crossbeam, one linear guide and its
    # mounting slider only. Motors, cabling and end tooling are intentionally
    # omitted until explicitly requested.
    gantry_y = 0.20
    y_rail_z = shell_z0 + shell_h * 0.50
    y_motion = empty("AXIS_Y_GantryAssembly")
    x_motion = empty("AXIS_X_MovingHead")
    z_motion = empty("AXIS_Z_Stylus")
    x_motion.parent = y_motion
    z_motion.parent = x_motion
    # The two side supports sit halfway up the box walls. Their Y rails are
    # fixed; the crossbeam bridges the two moving sliders without floor posts.
    for x in (-1.72, 1.72):
        cube(f"SideSupport_{x}", (0.20, 2.34, 0.28), (x, 0.00, y_rail_z), edge, 0.018)
        cube(f"Gantry_YRail_{x}", (0.115, 2.18, 0.105), (x - (0.075 if x > 0 else -0.075), 0.00, y_rail_z), steel, 0.010)
        parent_to(cube(f"Gantry_YSlider_{x}", (0.25, 0.38, 0.24), (x, gantry_y, y_rail_z), inner, 0.015), y_motion)
    crossbeam_z = y_rail_z + 0.17
    parent_to(cube("Gantry_Crossbeam", (3.48, 0.34, 0.30), (0, gantry_y, crossbeam_z), edge, 0.020), y_motion)
    parent_to(cube("Gantry_X_LinearRail", (3.02, 0.075, 0.105), (0, gantry_y - 0.205, crossbeam_z), steel, 0.010), y_motion)

    # X-axis moving head carried by the horizontal gantry rail.
    parent_to(cube("MovingHead_X_Slider", (0.42, 0.14, 0.30), (0, gantry_y - 0.235, crossbeam_z), inner, 0.018), x_motion)
    parent_to(cube("MovingHead_Housing", (0.48, 0.38, 0.65), (0, gantry_y - 0.12, crossbeam_z - 0.40), edge, 0.030), x_motion)
    parent_to(cube("MovingHead_Z_Rail", (0.13, 0.075, 0.50), (0, gantry_y - 0.35, crossbeam_z - 0.40), steel, 0.010), x_motion)

    # Downward-facing vision camera fixed to the moving head. It follows X/Y
    # positioning but remains independent from the Z-axis stylus stroke.
    parent_to(cube("VisionCamera_Bracket", (0.24, 0.28, 0.10), (-0.28, gantry_y - 0.10, crossbeam_z - 0.20), steel, 0.015), x_motion)
    parent_to(cube("VisionCamera_Housing", (0.34, 0.34, 0.25), (-0.42, gantry_y - 0.10, crossbeam_z - 0.42), edge, 0.030), x_motion)
    parent_to(cylinder("VisionCamera_LensRing", 0.12, 0.08, (-0.42, gantry_y - 0.10, crossbeam_z - 0.585), steel, 40), x_motion)
    parent_to(cylinder("VisionCamera_Lens", 0.082, 0.10, (-0.42, gantry_y - 0.10, crossbeam_z - 0.65), vision_glass, 40), x_motion)

    # Z-axis slider and stylus. The tip is held just above the empty phone
    # fixture; translating AXIS_Z_Stylus downward produces the tap.
    parent_to(cube("Stylus_Z_Slider", (0.28, 0.15, 0.24), (0, gantry_y - 0.39, crossbeam_z - 0.48), inner, 0.018), z_motion)
    parent_to(cylinder("Stylus_Collet", 0.105, 0.18, (0, gantry_y - 0.39, 1.98), steel, 40), z_motion)
    parent_to(cylinder("Stylus_Body", 0.052, 0.42, (0, gantry_y - 0.39, 1.68), edge, 40), z_motion)
    parent_to(cone("Stylus_Tip", 0.047, 0.014, 0.14, (0, gantry_y - 0.39, 1.40), rubber, 40), z_motion)
    print("STAGE01 internals", flush=True)

    # Ground and studio backdrop.
    cube("Ground", (16, 16, 0.12), (0, 0, -0.08), floor_mat, 0.02)

    bpy.ops.object.light_add(type="AREA", location=(-4.5, -5.0, 7.0))
    key = bpy.context.object
    key.name = "Key_Light"
    key.data.energy = 900
    key.data.shape = "DISK"
    key.data.size = 4.5
    aim(key, (0, 0, 2.4))
    bpy.ops.object.light_add(type="AREA", location=(4.5, -1.0, 5.5))
    fill = bpy.context.object
    fill.name = "Fill_Light"
    fill.data.energy = 800
    fill.data.size = 3.5
    aim(fill, (0, 0, 2.7))
    bpy.ops.object.light_add(type="AREA", location=(0, 4.0, 6.0))
    rim = bpy.context.object
    rim.name = "Rim_Light"
    rim.data.energy = 1000
    rim.data.size = 3.0
    aim(rim, (0, 0.5, 2.8))

    bpy.ops.object.camera_add(location=(0, -12.6, 4.8))
    camera = bpy.context.object
    camera.name = "Camera"
    camera.data.lens = 64
    aim(camera, (0, 0.05, 2.05))
    scene.camera = camera
    print("STAGE01 lights-camera", flush=True)

    scene.view_settings.look = "AgX - Medium High Contrast"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "robot_base_stage01_professional.blend"))
    print("STAGE01 saved", flush=True)
    bpy.ops.render.render(write_still=True)

    # Secondary inspection view makes the front-to-back Y rails unambiguous.
    camera.location = (6.8, -10.8, 5.9)
    aim(camera, (0, 0.05, 2.05))
    scene.render.filepath = str(OUT / "robot_base_stage01_professional_perspective.png")
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "robot_base_stage01_professional.blend"))


if __name__ == "__main__":
    main()
