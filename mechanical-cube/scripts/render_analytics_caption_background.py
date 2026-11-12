"""Render the animated stripe background with only the Conclusion text hidden.

Run with Blender --background --python this_script -- --out OUTPUT_FOLDER.
The lossless strip is a small reusable asset; full dashboard pixels are retained.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out',type=Path,required=True)
a=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
a.out.mkdir(parents=True,exist_ok=True)
cfg=json.loads((ROOT/'config/analytics_caption_cleanup.json').read_text('utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/cfg['source_scene']))
s=bpy.context.scene
assert s.objects[cfg['object']].data.body==cfg['text']
s.objects[cfg['object']].hide_render=True
x,y,w,h=cfg['rectangle'];width,height=cfg['source_resolution']
s.render.use_border=True;s.render.use_crop_to_border=True
s.render.border_min_x=x/width;s.render.border_max_x=(x+w)/width
s.render.border_min_y=(height-y-h)/height;s.render.border_max_y=(height-y)/height
s.render.image_settings.file_format='PNG'
s.frame_start=cfg['start_frame'];s.frame_end=cfg['end_frame'];s.frame_step=1
s.render.filepath=str(a.out.resolve()/'frame_')
bpy.ops.render.render(animation=True)
target=ROOT/cfg['overlay_asset'];target.parent.mkdir(parents=True,exist_ok=True)
subprocess.run(['ffmpeg','-v','error','-y','-framerate',str(cfg['fps']),'-start_number',str(cfg['start_frame']),
    '-i',str(a.out.resolve()/'frame_%04d.png'),'-frames:v',str(cfg['end_frame']-cfg['start_frame']+1),
    '-c:v','ffv1','-level','3','-pix_fmt','bgr0',str(target)],check=True)
print('CLEAN_BACKGROUND_ASSET',target,flush=True)
