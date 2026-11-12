"""Illustrate AI control discovery with interleaved top/bottom Tab visits.

The exploration order is deliberately non-spatial and deterministic for renders.
There is no vertical scan bar. Page content is a separate, visible third region.
"""
import json
import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from render_page_nodes_monochrome import ease, mix
from control_ui_style import phone_shell, focus_box
from film_step_labels import step_label

SIZE=(1920,1080);FPS=60
BG=(9,9,11);PANEL=(14,14,17);EDGE=(78,78,88)
WHITE=(244,244,245);MUTED=(163,163,173);GREEN=(74,222,128)
TOP=['关注','推荐','同城'];BOTTOM=['首页','朋友','消息','我']
# Every Tab is visited once. Alternating zones and non-monotonic columns make
# the cursor read as control discovery instead of a top-to-bottom screen scan.
ORDER=[('top',1),('bottom',1),('top',2),('bottom',3),('top',0),('bottom',2),('bottom',0)]
START=.65;STEP=.58


def render_control_exploration(source,out,name='03-01',duration=5.6,preview=False):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    prior=out/'02-01.mp4';previous_path=out/'control-previous.png'
    args=['-sseof','-0.02','-i',str(prior)] if prior.exists() else ['-ss',str(6-1/FPS),'-i',str(source)]
    subprocess.run(['ffmpeg','-v','error','-y',*args,'-frames:v','1',str(previous_path)],check=True)
    previous=Image.open(previous_path).convert('RGB')
    fonts={s:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',s) for s in (18,20,22,24,26,28,30,32,36,42)}
    bold=ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc',42)
    ui_bold=ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc',30)

    def target(zone,index):
        # Local screen coordinates inside a 420 x 700 phone silhouette.
        return (36+index*117,75,36+index*117+112,129) if zone=='top' else (29+index*92,568,29+index*92+86,632)

    def frame(t):
        im=Image.new('RGB',SIZE,BG);d=ImageDraw.Draw(im)
        d.text((120,38),step_label(3),font=fonts[24],fill=MUTED)
        d.text((1800,41),'APPLICATION KNOWLEDGE GRAPH',font=fonts[20],fill=MUTED,anchor='rt')
        d.line((120,90,1800,90),fill=(47,47,54),width=2)
        d.text((120,139),'AI 寻找控件，交错探索页面',font=bold,fill=WHITE)
        d.text((120,209),'识别页面分区 · 遍历顶部与底部 Tab',font=fonts[26],fill=MUTED)
        completed=max(0,min(len(ORDER),math.floor((t-START-.20)/STEP)+1))
        visited=set(ORDER[:completed]);index=max(0,min(len(ORDER)-1,math.floor((t-START)/STEP)))
        active=ORDER[index];zone,col=active;labels=TOP if zone=='top' else BOTTOM
        finished=t>=START+len(ORDER)*STEP
        phase=(t-START-index*STEP)/STEP

        phone=phone_shell();p=ImageDraw.Draw(phone)
        for rect in [(25,65,395,142),(25,157,395,548),(25,558,395,642)]:
            p.rounded_rectangle(rect,radius=10,outline=(85,85,95),width=1)
        # Content is retained as its own region; it responds to each selected Tab.
        last_zone,last_col=ORDER[completed-1] if completed else ('top',0)
        page=(TOP if last_zone=='top' else BOTTOM)[last_col] if completed else '页面内容'
        p.text((49,178),page,font=ui_bold,fill=WHITE)
        p.text((49,226),'内容区域',font=fonts[20],fill=MUTED)
        for j in range(2):
            yy=272+j*119
            p.rounded_rectangle((47,yy,373,yy+98),radius=9,outline=EDGE,width=1)
            p.rounded_rectangle((61,yy+16,126,yy+81),radius=6,outline=(108,108,118),width=1)
            p.polygon([(86,yy+34),(86,yy+63),(108,yy+48)],fill=MUTED)
            p.line((144,yy+30,335-j*31,yy+30),fill=MUTED,width=2)
            p.line((144,yy+55,292+j*22,yy+55),fill=EDGE,width=2)
        p.text((210,518),'页面内容随 Tab 切换',font=fonts[18],fill=MUTED,anchor='mm')
        for z,items in [('top',TOP),('bottom',BOTTOM)]:
            for k,label in enumerate(items):
                x1,y1,x2,y2=target(z,k);seen=(z,k) in visited
                is_active=(z,k)==active and t>=START and not finished
                if is_active:focus_box(p,(x1,y1,x2,y2))
                p.text(((x1+x2)/2,(y1+y2)/2-3),label,font=fonts[24],fill=WHITE if seen or is_active else MUTED,anchor='mm')
                if seen:p.ellipse(((x1+x2)/2-3,y2-10,(x1+x2)/2+3,y2-4),fill=GREEN)
        p.rounded_rectangle((157,660,263,665),radius=2,fill=EDGE)
        # A small cursor travels between specific controls, in both X and Y.
        if START<=t<START+len(ORDER)*STEP:
            now=target(*active);old=target(*ORDER[max(0,index-1)])
            q=ease(phase,0,.30)
            cx=old[2]-10+(now[2]-old[2])*q;cy=old[1]+10+(now[1]-old[1])*q
            p.ellipse((cx-8,cy-8,cx+8,cy+8),fill=WHITE,outline=(10,10,12),width=2)
            if .28<phase<.80:
                r=9+(phase-.28)*34;alpha=1-(phase-.28)/.52
                p.ellipse((cx-r,cy-r,cx+r,cy+r),outline=mix(PANEL,GREEN,alpha),width=2)

        move=ease(t,0,.55);box=mix((725,68,1195,940),(390,260,810,960),move)
        im.paste(phone.resize((box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS),(box[0],box[1]))
        d=ImageDraw.Draw(im)
        appear=ease(t,.25,.65);c=lambda value:mix(BG,value,appear)
        for label,y,local_y in [('顶部 Tab',365,102),('中间内容',600,355),('底部 Tab',857,600)]:
            d.text((155,y),label,font=fonts[28],fill=c(WHITE),anchor='lm')
            d.line((300,y,367,y),fill=c(EDGE),width=2)
            d.line((367,y,384,260+local_y),fill=c(EDGE),width=2)
        d.rounded_rectangle((940,285,1790,459),radius=14,fill=c(PANEL),outline=c(EDGE),width=2)
        d.rounded_rectangle((968,317,1038,387),radius=12,outline=c(GREEN),width=2)
        d.text((1003,352),'AI',font=fonts[32],fill=c(GREEN),anchor='mm')
        d.text((1073,314),'完成 Tab 遍历' if finished else '寻找并触发可点击控件',font=fonts[30],fill=c(WHITE))
        action='顶部 3 / 3 · 底部 4 / 4' if finished else (('顶部 Tab' if zone=='top' else '底部 Tab')+'  /  '+labels[col])
        d.text((1073,374),action,font=fonts[28],fill=c(GREEN if finished else MUTED))
        for z,items,yy in [('top',TOP,507),('bottom',BOTTOM,686)]:
            count=sum((z,k) in visited for k in range(len(items)))
            d.text((945,yy),'顶部 Tab' if z=='top' else '底部 Tab',font=fonts[28],fill=c(WHITE))
            d.text((1780,yy),f'{count} / {len(items)}',font=fonts[26],fill=c(GREEN),anchor='rt')
            width=254 if z=='top' else 187
            for k,label in enumerate(items):
                xx=944+k*(width+22);seen=(z,k) in visited;selected=(z,k)==active and not finished and t>=START
                d.rounded_rectangle((xx,yy+54,xx+width,yy+121),radius=10,fill=c((16,35,23) if selected else PANEL),outline=c(GREEN if selected else EDGE),width=2 if selected else 1)
                d.text((xx+25,yy+87),label,font=fonts[26],fill=c(WHITE if seen else MUTED),anchor='lm')
                if seen:
                    d.line((xx+width-43,yy+87,xx+width-35,yy+95,xx+width-23,yy+79),fill=c(GREEN),width=3)
        d.line((945,852,1789,852),fill=c((47,47,54)),width=2)
        d.text((945,884),'识别分区  →  寻找控件  →  触发操作  →  记录页面',font=fonts[24],fill=c(MUTED))
        d.line((0,1008,1920,1008),fill=(51,51,59),width=1)
        if t<.34:im=Image.blend(previous,im,ease(t,0,.34))
        return im

    events=[{'time':round(START+i*STEP,3),'region':z,'control':(TOP if z=='top' else BOTTOM)[k]} for i,(z,k) in enumerate(ORDER)]
    (out/'control-exploration-events.json').write_text(json.dumps({'duration':duration,'regions':['顶部 Tab','中间内容','底部 Tab'],'events':events,'top_coverage':3,'bottom_coverage':4},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for t in [0,.7,1.3,1.9,2.5,3.1,3.7,4.3,5.3]:frame(t).save(out/f'controls-{t:.2f}.png')
    if preview:return
    proc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','60','-i','-','-an','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(out/(name+'.mp4'))],stdin=subprocess.PIPE)
    try:
        for n in range(round(duration*FPS)):proc.stdin.write(frame(n/FPS).tobytes())
    finally:proc.stdin.close()
    if proc.wait():raise RuntimeError('Control exploration render failed')


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--preview',action='store_true')
    a=p.parse_args();render_control_exploration(a.source,a.out,preview=a.preview)
