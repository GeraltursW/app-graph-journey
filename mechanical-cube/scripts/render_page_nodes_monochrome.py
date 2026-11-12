"""Native 1080p monochrome page-node scene matching the compact film's UI.

Three representative pages become reusable nodes. No colored window chrome,
particle cloud or bloom. The first/last frames match the adjacent clean shots.
"""
import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from film_step_labels import step_label

SIZE=(1920,1080);FPS=60
BG=(9,9,11);PANEL=(14,14,17);EDGE=(78,78,88)
WHITE=(244,244,245);MUTED=(163,163,173);GREEN=(74,222,128)


def ease(t,a,b):
    u=max(0,min(1,(t-a)/(b-a)));return u*u*(3-2*u)


def mix(a,b,u):return tuple(round(x+(y-x)*u) for x,y in zip(a,b))


def render_page_nodes(source,out,name='04-01',duration=2.8):
    out=Path(out);source=Path(source);out.mkdir(parents=True,exist_ok=True)
    def still(time,name):
        path=out/name
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(time),'-i',str(source),'-frames:v','1',str(path)],check=True)
        return Image.open(path).convert('RGB')
    # A rebuilt exploration scene must also feed this entry dissolve; using
    # the historical master here would briefly restore the removed scan line.
    exploration=out/'03-01.mp4'
    if exploration.exists():
        path=out/'nodes-previous.png'
        subprocess.run(['ffmpeg','-v','error','-y','-sseof','-0.02','-i',str(exploration),'-frames:v','1',str(path)],check=True)
        previous=Image.open(path).convert('RGB')
    else:
        previous=still(14-1/FPS,'nodes-previous.png')
    following=still(18,'nodes-following.png')
    fonts={s:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',s) for s in (20,22,24,26,28,30,36,42)}
    bold=ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc',42)
    def frame(t):
        im=Image.new('RGB',SIZE,BG);d=ImageDraw.Draw(im)
        d.text((120,38),step_label(4),font=fonts[24],fill=MUTED)
        d.text((1800,41),'APPLICATION KNOWLEDGE GRAPH',font=fonts[20],fill=MUTED,anchor='rt')
        d.line((120,90,1800,90),fill=(47,47,54),width=2)
        d.text((120,139),'探索结果，沉淀为可复用节点',font=bold,fill=WHITE)
        d.text((120,209),'保留每个页面的截图、控件与结构',font=fonts[26],fill=MUTED)
        centers=[]
        for j,(label,target) in enumerate(zip(['首页','我的页面','喜欢列表'],[470,960,1450])):
            progress=ease(t,.20,.85);x=960+(target-960)*progress;y=320+18*(1-progress)
            alpha=ease(t,.13+j*.09,.53+j*.09);centers.append(x)
            color=lambda c:mix(BG,c,alpha)
            box=(round(x-190),round(y),round(x+190),round(y+400))
            d.rounded_rectangle(box,radius=14,fill=color(PANEL),outline=color(EDGE),width=2)
            d.text((x,y+29),label,font=fonts[30],fill=color(WHITE),anchor='mt')
            d.line((x-160,y+83,x+160,y+83),fill=color((47,47,54)),width=2)
            # Small UI fragments suggest each page without importing colored screenshots.
            if j==0:
                d.rounded_rectangle((x-134,y+109,x+134,y+259),radius=6,outline=color((100,100,110)),width=2)
                d.polygon([(x-9,y+168),(x-9,y+198),(x+16,y+183)],fill=color(WHITE))
                for k in range(2):d.line((x-134,y+285+k*22,x+78-k*70,y+285+k*22),fill=color(EDGE),width=2)
            elif j==1:
                d.ellipse((x-132,y+111,x-74,y+169),outline=color((150,150,160)),width=2)
                d.line((x-52,y+126,x+119,y+126),fill=color(MUTED),width=2)
                d.line((x-52,y+151,x+52,y+151),fill=color(EDGE),width=2)
                for k,tab in enumerate(['作品','收藏','喜欢']):
                    xx=x-106+k*106;d.text((xx,y+208),tab,font=fonts[22],fill=color(GREEN if k==2 else MUTED),anchor='mt')
                for k in range(3):d.rounded_rectangle((x-140+k*98,y+250,x-56+k*98,y+311),radius=4,outline=color(EDGE),width=2)
            else:
                for row in range(2):
                    for col in range(3):
                        xx=x-140+col*98;yy=y+110+row*105
                        d.rounded_rectangle((xx,yy,xx+84,yy+87),radius=4,outline=color(EDGE),width=2)
                        d.line((xx+18,yy+64,xx+66,yy+64),fill=color(MUTED),width=2)
            d.text((x,y+351),'截图  ·  控件  ·  结构',font=fonts[22],fill=color(MUTED),anchor='mt')
            active=ease(t,.75+j*.12,1.13+j*.12)
            d.line((x,y+401,x,786),fill=mix(BG,EDGE,active),width=2)
            d.ellipse((x-7,786,x+7,800),fill=mix(BG,GREEN,active))
        progress=ease(t,1.03,1.5)
        for a,b in zip(centers,centers[1:]):
            d.line((a+14,793,a+14+(b-a-28)*progress,793),fill=mix(BG,(105,105,114),progress),width=2)
        d.text((960,853),'可复用页面节点',font=fonts[28],fill=mix(BG,WHITE,ease(t,.9,1.3)),anchor='mt')
        d.line((0,1008,1920,1008),fill=(51,51,59),width=1)
        # Text and geometry share a short gentle dissolve at each clean-shot boundary.
        if t<.34:im=Image.blend(previous,im,ease(t,0,.34))
        if t>duration-.30:im=Image.blend(im,following,ease(t,duration-.30,duration-1/FPS))
        return im
    for t in [0,.3,.8,1.5,2.2,duration-1/FPS]:frame(t).save(out/f'nodes-{t:.2f}.png')
    proc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','60','-i','-','-an','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(out/(name+'.mp4'))],stdin=subprocess.PIPE)
    try:
        for n in range(round(duration*FPS)):proc.stdin.write(frame(n/FPS).tobytes())
    finally:proc.stdin.close()
    if proc.wait():raise RuntimeError('Monochrome page-node rendering failed')


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();render_page_nodes(a.source,a.out)
