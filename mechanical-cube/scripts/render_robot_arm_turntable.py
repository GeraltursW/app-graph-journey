"""Render a short 360-degree turntable preview of the robot-arm asset."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve() if "--" in sys.argv else Path.cwd()
OUT = ROOT / "output" / "robot-arm"
OUT.mkdir(parents=True, exist_ok=True)

scene = bpy.context.scene
root = bpy.data.objects.get("ARM_ROOT")
if root is None:
    raise RuntimeError("ARM_ROOT was not found in the robot-arm blend file")

# A turntable is a geometry check, so use Blender's studio workbench renderer:
# crisp, material-aware and fast enough to review motion immediately.
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "WORLD"
scene.display.shading.show_specular_highlight = True
scene.display.shading.background_type = "VIEWPORT"
scene.display.shading.background_color = (0.82, 0.84, 0.87)

scene.render.resolution_x = 960
scene.render.resolution_y = 540
scene.render.resolution_percentage = 100
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 72

root.rotation_mode = "XYZ"
root.rotation_euler[2] = 0.0
root.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
root.rotation_euler[2] = math.tau
root.keyframe_insert(data_path="rotation_euler", index=2, frame=73)

frames = OUT / "turntable-frames"
frames.mkdir(parents=True, exist_ok=True)
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.filepath = str(frames / "frame_")

# Save the animation setup as a separate reusable scene file.
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "robot_arm_turntable.blend"))
bpy.ops.render.render(animation=True)
print(f"FRAMES={frames}")

