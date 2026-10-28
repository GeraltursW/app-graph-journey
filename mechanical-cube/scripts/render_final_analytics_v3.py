"""Repair panel animation in the editable v2 scene and render native 30 fps frames."""
from pathlib import Path
import argparse
import sys
import bpy

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('--source', type=Path, default=ROOT / 'blender/final_analytics_v2.blend')
p.add_argument('--out', type=Path, default=ROOT / 'output/final-analytics-v3')
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
a.out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(a.source.resolve()))
s = bpy.context.scene
s.frame_set(180)
for name in ['MetricCard0', 'MetricCard1', 'MetricCard2', 'Tooltip']:
    border = s.objects[name + '_Border']
    inner = s.objects[name + '_Inner']
    base_border = border.scale.copy()
    base_inner = inner.scale.copy()
    for frame in range(1, 181):
        s.frame_set(frame)
        border.scale = tuple(base_border[i] * inner.scale[i] / base_inner[i] for i in range(3))
        border.keyframe_insert('scale', frame=frame)
    s.frame_set(180)
s.render.fps = 30
s.render.frame_map_old = s.render.frame_map_new = 100
s.frame_step = 1
s.render.filepath = str(a.out.resolve() / 'frames/frame_')
(a.out / 'frames').mkdir(exist_ok=True)
s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve() / 'final_analytics_v3.blend'))
bpy.ops.render.render(animation=True)
