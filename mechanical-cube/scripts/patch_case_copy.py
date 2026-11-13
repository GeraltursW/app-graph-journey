"""Replace STEP 07's baked page copy while retaining its existing animation."""
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from video_fonts import chinese_font

SIZE=(1920,1080)
# Only the three text areas; leave cards, connectors and borders intact.
AREAS=[('heading',(700,112,1220,172),(960,127),31,(600,140),True),
       ('status',(755,670,1170,720),(960,680),28,(735,695),True),
       ('footer',(500,930,1420,994),(960,948),28,(440,960),False)]


def rewrite_frame(frame,copy):
    original=np.asarray(frame)
    edited=frame.copy();draw=ImageDraw.Draw(edited)
    for key,box,position,size,sample,green in AREAS:
        x,y=sample
        background=tuple(np.median(original[y-2:y+3,x-2:x+3],axis=(0,1)).astype(int))
        crop=original[box[1]:box[3],box[0]:box[2]].astype(float)
        # Retain the source label's fade level instead of introducing a flash.
        signal=crop[:,:,1]-(crop[:,:,0]+crop[:,:,2])/2 if green else crop.mean(axis=2)
        ink=crop[signal>=np.percentile(signal,99.3)]
        color=tuple(np.median(ink,axis=0).astype(int))
        draw.rectangle((box[0],box[1],box[2]-1,box[3]-1),fill=background)
        font_path=chinese_font()
        # macOS Heiti's first TTC face is Traditional Chinese; use its SC face.
        face=1 if Path(font_path).name.startswith('STHeiti') else 0
        draw.text(position,copy[key],font=ImageFont.truetype(font_path,size,index=face),fill=color,anchor='mt')
    return edited


def transform_video(source,target,transform):
    decoder=subprocess.Popen(['ffmpeg','-v','error','-i',str(source),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
    encoder=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','60','-i','-','-an','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(target)],stdin=subprocess.PIPE)
    size=SIZE[0]*SIZE[1]*3;index=0
    try:
        while True:
            data=decoder.stdout.read(size)
            if not data:break
            if len(data)!=size:raise ValueError('Incomplete decoded frame')
            frame=Image.frombytes('RGB',SIZE,data)
            encoder.stdin.write(transform(frame,index).tobytes());index+=1
    finally:
        decoder.stdout.close();encoder.stdin.close()
    if decoder.wait()!=0 or encoder.wait()!=0:raise RuntimeError('Case copy patch failed')


def patch_case_copy(path,copy):
    path=Path(path);target=path.with_name(path.stem+'-page-copy.mp4')
    transform_video(path,target,lambda frame,index:rewrite_frame(frame,copy))
    target.replace(path)
