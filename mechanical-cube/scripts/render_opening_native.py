"""Render the original opening typography crisply, preserving its 3-second hold."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from video_fonts import chinese_font
from integrate_scenario_main import write_bridge


def render_opening_native(out,name='01-01',duration=3):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    scale=2
    font_path=chinese_font();face=1 if Path(font_path).name.startswith('STHeiti') else 0
    title=ImageFont.truetype(font_path,72*scale,index=face)
    subtitle=ImageFont.truetype(font_path,26*scale,index=face)
    canvas=Image.new('RGB',(1920*scale,1080*scale),(4,4,6))
    pen=ImageDraw.Draw(canvas)
    pen.text((960*scale,430*scale),'应用知识图谱',font=title,fill=(244,244,245),anchor='mt')
    pen.line((807*scale,512*scale,1113*scale,512*scale),fill=(95,95,105),width=2*scale)
    pen.text((960*scale,558*scale),'从应用探索到测试验证与数据分析',font=subtitle,fill=(180,180,192),anchor='mt')
    pen.rectangle((0,1008*scale,1920*scale,1080*scale),fill=(9,9,11))
    pen.line((0,1008*scale,1920*scale,1008*scale),fill=(51,51,59),width=scale)
    frame=canvas.resize((1920,1080),Image.Resampling.LANCZOS)
    frame.save(out/'opening-native-preview.png')
    write_bridge(out,name,duration,lambda t:frame)
