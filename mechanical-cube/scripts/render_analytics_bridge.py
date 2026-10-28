"""Render a continuous mechanical completion -> telemetry bridge at 60 fps.

Requires Pillow and FFmpeg. Starts on the exact last decoded mechanical frame.
The following dashboard overlaps the final second using an ordinary dissolve.
"""
from pathlib import Path
import argparse
import math
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
W, H, SCALE, FPS, SECONDS = 1280, 720, 2, 60, 5
COLORS = [(34, 211, 238), (250, 204, 21), (251, 113, 133)]

def smooth(t, a, b):
    v = min(1.0, max(0.0, (t-a)/(b-a)))
    return v*v*(3-2*v)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, default=ROOT/'releases/latest/c159cc4d19a03485a4677970789f6f1a.mp4')
    p.add_argument('--out', type=Path, default=ROOT/'output/final-analytics-v3')
    p.add_argument('--font', default='C:/Windows/Fonts/msyh.ttc')
    p.add_argument('--preview', action='store_true')
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    still = a.out/'mechanical-last.png'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-sseof','-0.05','-i',str(a.source),'-frames:v','1',str(still)],check=True)
    original = Image.open(still).convert('RGB').resize((W*SCALE,H*SCALE),Image.Resampling.LANCZOS)
    robot = original.crop((0,0,780*SCALE,H*SCALE))
    old_text = original.crop((780*SCALE,0,W*SCALE,H*SCALE))
    fonts = {s:ImageFont.truetype(a.font,s*SCALE) for s in (16,19,22,24,30,44)}
    bg = Image.new('RGB',(W*SCALE,H*SCALE),(2,5,9))
    d = ImageDraw.Draw(bg)
    for x in range(-450,1550,40):
        d.line([(x*SCALE,H*SCALE),((x+360)*SCALE,0)],fill=(23,29,34),width=SCALE)

    def frame(t):
        move = smooth(t,.15,1.65)
        im = bg.copy()
        # Original text fades while the real device image glides into its card.
        old = Image.blend(Image.new('RGB',old_text.size,(2,5,9)),old_text,1-smooth(t,.05,.85))
        im.paste(old,(780*SCALE,0))
        x,y = round(50*move*SCALE),round(148*move*SCALE)
        rw = round((780-246*move)*SCALE)
        rh = round(H*rw/(780*SCALE)) * SCALE
        im.paste(robot.resize((rw,rh),Image.Resampling.LANCZOS),(x,y))
        if t == 0:
            return original.resize((W,H),Image.Resampling.LANCZOS)

        layer = Image.new('RGBA',im.size)
        pen = ImageDraw.Draw(layer)
        def text(x,y,body,size,color=(245,247,250),alpha=1):
            pen.text((round(x*SCALE),round(y*SCALE)),body,font=fonts[size],fill=(*color,round(255*alpha)),anchor='lt')
        appear = smooth(t,.65,1.45)
        text(54,48,'测试完成  /  数据汇聚',19,(174,184,194),appear)
        pen.line([(54*SCALE,88*SCALE),(1226*SCALE,88*SCALE)],fill=(180,190,200,round(110*appear)),width=SCALE)
        text(718,156,'测试完成后',44,alpha=appear)
        text(720,220,'性能、功耗、热等数据同步汇聚',24,(185,195,207),smooth(t,1.45,2.15))
        label_alpha = smooth(t,1.3,2.0)
        text(88,641,'机械手用例复现完成',22,(220,228,235),label_alpha)
        pen.ellipse((54*SCALE,644*SCALE,73*SCALE,663*SCALE),fill=(74,222,128,round(255*label_alpha)))
        # Three curved telemetry channels originate at the tested phone.
        for i,(label,color) in enumerate(zip(('性能','功耗','热'),COLORS)):
            y1 = 334+i*95
            progress = smooth(t,1.65+i*.16,2.8+i*.16)
            points=[]
            for step in range(101):
                u=step/100
                xx=(1-u)**3*450+3*(1-u)**2*u*610+3*(1-u)*u*u*610+u**3*710
                yy=(1-u)**3*460+3*(1-u)**2*u*460+3*(1-u)*u*u*y1+u**3*y1
                points.append((int(xx*SCALE),int(yy*SCALE)))
            end=max(2,round(progress*101))
            if progress>0:
                pen.line(points[:end],fill=(*color,95),width=2*SCALE)
                for particle in range(4):
                    u=((t-1.65-i*.16)*.46-particle*.24)%1
                    if u<=progress:
                        px,py=points[min(100,int(u*100))]
                        pen.ellipse((px-4*SCALE,py-4*SCALE,px+4*SCALE,py+4*SCALE),fill=(*color,round(230*progress)))
            alpha=smooth(t,1.6+i*.17,2.4+i*.17)
            pen.rounded_rectangle((710*SCALE,(y1-32)*SCALE,1220*SCALE,(y1+32)*SCALE),radius=8*SCALE,fill=(8,12,18,round(255*alpha)),outline=(91,104,118,round(255*alpha)),width=SCALE)
            pen.line([(710*SCALE,(y1-20)*SCALE),(710*SCALE,(y1+20)*SCALE)],fill=(*color,round(255*alpha)),width=3*SCALE)
            text(737,y1-14,label,24,color,alpha)
            text(1082,y1-10,'同步汇聚',19,(200,208,218),alpha)
            # Small live trend echoes the curves of the following dashboard.
            waveform=[]
            for j in range(35):
                px=835+j*5
                py=y1+math.sin(j*.65+i*2+t*1.4)*8+math.sin(j*.23)*4
                waveform.append((round(px*SCALE),round(py*SCALE)))
            pen.line(waveform,fill=(*color,round(230*alpha)),width=2*SCALE)
        footer=smooth(t,2.6,3.35)
        text(720,607,'生成数据报表',22,(235,240,245),footer)
        text(720,643,'同一测试任务 · 三类数据同步对齐',16,(125,139,153),footer)
        im=Image.alpha_composite(im.convert('RGBA'),layer).convert('RGB')
        return im.resize((W,H),Image.Resampling.LANCZOS)

    for t in (0,1.5,2.7,3.8):
        frame(t).save(a.out/f'bridge-{t:.1f}s.png')
    if a.preview:
        return
    command=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','medium','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',str(a.out/'analytics-bridge-clean.mp4')]
    process=subprocess.Popen(command,stdin=subprocess.PIPE)
    try:
        for n in range(FPS*SECONDS):
            process.stdin.write(frame(n/FPS).tobytes())
    finally:
        process.stdin.close()
    if process.wait():
        raise RuntimeError('FFmpeg bridge encoding failed')
    print(a.out/'analytics-bridge-clean.mp4')

if __name__=='__main__':
    main()
