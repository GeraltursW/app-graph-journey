"""Replace only the lab shot's heading and subheading, preserving animation."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from video_fonts import chinese_font
from patch_case_copy import transform_video
from render_lab_replay_monochrome import decoded
from render_page_nodes_monochrome import ease

HEADING='实验室手机执行'
SUBHEADING='沿用例路径执行 · 定位控件 · 进入并验证页面'

def patch_lab_copy(path,previous):
    path=Path(path);area=(115,125,1805,250)
    old=decoded(previous,path.with_name('lab-copy-prior.png'),last=True).crop(area)
    reference=decoded(path,path.with_name('lab-copy-background.png'),time=1)
    background=reference.getpixel((1800,200))
    patch=Image.new('RGB',((area[2]-area[0])*2,(area[3]-area[1])*2),background);d=ImageDraw.Draw(patch)
    font=chinese_font();face=1 if Path(font).name.startswith('STHeiti') else 0
    for text,y,size,color in [(HEADING,139,42,(244,244,245)),(SUBHEADING,209,26,(163,163,173))]:
        d.text(((120-area[0])*2,(y-area[1])*2),text,font=ImageFont.truetype(font,size*2,index=face),fill=color)
    patch=patch.resize(old.size,Image.Resampling.LANCZOS)
    def frame(im,n):
        replacement=Image.blend(old,patch,ease(n/60,0,.34)) if n/60<.34 else patch
        im.paste(replacement,area[:2]);return im
    target=path.with_name(path.stem+'-copy.mp4');transform_video(path,target,frame);target.replace(path)
