"""Blender: render the editable 8-second page exploration scene at 30 fps."""
import argparse
import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', type=Path, required=True)
parser.add_argument('--save', type=Path)
parser.add_argument('--frames', help='Optional comma-separated preview frame numbers')
parser.add_argument('--resume', action='store_true', help='Reuse existing frames only when the scene/config is unchanged')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
cfg = json.loads((ROOT / 'config/page_exploration.json').read_text(encoding='utf-8'))
scene = bpy.data.scenes[cfg['scene']]
bpy.context.window.scene = scene
for obj in scene.objects:
    if obj.type != 'FONT':
        continue
    if obj.name.startswith('ShotTitle'):
        obj.data.body = cfg['title']
    elif obj.name.startswith('Caption'):
        obj.data.body = cfg['caption']
for name, text in zip(('Text', 'Text.001', 'Text.002'), cfg['labels']):
    scene.objects[name].data.body = text
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.fps = 30
scene.render.fps_base = 1
scene.frame_start = 1
scene.frame_end = 240
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.use_motion_blur = False
if args.save:
    # Keep this editable source focused on shot 02; the original master is untouched.
    for other in list(bpy.data.scenes):
        if other != scene:
            bpy.data.scenes.remove(other)
    bpy.data.orphans_purge(do_recursive=True)
    bpy.ops.file.pack_all()
    args.save.parent.mkdir(parents=True, exist_ok=True)
    scene.frame_set(235)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.save.resolve()), compress=True)
args.out.mkdir(parents=True, exist_ok=True)
frames = [int(n) for n in args.frames.split(',')] if args.frames else range(1, 241)
for frame in frames:
    target = args.out / f'frame_{frame:04d}.png'
    if args.resume and target.exists():
        continue
    scene.frame_set(frame)
    scene.render.filepath = str(target.resolve())
    bpy.ops.render.render(write_still=True)
print('PAGE_EXPLORATION_RENDER_COMPLETE', flush=True)
