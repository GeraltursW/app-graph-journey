"""Brief AI-created student case, followed by a silent static step list."""
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from integrate_scenario_main import smooth, write_bridge
from film_step_labels import step_label

BG=(9,9,11)
WHITE=(244,244,245)
MUTED=(163,163,173)
EDGE=(65,65,75)
GREEN=(74,222,128)
ROOT=Path(__file__).resolve().parents[1]


def render_student_summary(source,out,name,seconds,preview):
    case=json.loads((ROOT/preview['source']).read_text(encoding='utf-8'))
    show=preview['show_start'];hold=preview['hold_duration'];fade_in=preview['fade_in']
    assert not preview['narrate_steps'] and 1<=hold<=2
    assert abs(show+hold-(seconds-.7))<1e-6
    previous_path=out/'student-summary-previous.png'
    subprocess.run(['ffmpeg','-v','error','-y','-ss','78.8833333333','-i',str(source),'-frames:v','1',str(previous_path)],check=True)
    previous=Image.open(previous_path).convert('RGB')
    fonts={s:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',s) for s in [18,21,24,27,30,36,42,48,54]}
    bold={s:ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc',s) for s in [36,42,48,54]}
    def state(t,show_steps=False):
        im=Image.new('RGB',(1920,1080),BG);d=ImageDraw.Draw(im)
        # Text clears before the next shot's title fades in.
        title_alpha=1-smooth(t,seconds-.7,seconds-.45)
        body_alpha=1-smooth(t,seconds-.7,seconds-.45)
        def text(x,y,value,size,color=WHITE,alpha=1,heavy=False,anchor='lt'):
            c=tuple(round(a+(b-a)*alpha) for a,b in zip(BG,color))
            d.text((x,y),value,font=(bold if heavy else fonts)[size],fill=c,anchor=anchor)
        text(120,38,step_label(12),24,MUTED)
        text(1848,40,'SCENARIO → CONTEXT',18,MUTED,anchor='rt')
        d.line((72,90,1848,90),fill=EDGE,width=2)
        text(72,135,'AI 创建大学生场景用例',48,alpha=title_alpha,heavy=True)
        text(72,220,'典型操作序列 → AI 场景生成',27,MUTED,alpha=title_alpha)
        reveal=smooth(t,.2,.9)
        ai=(245,405,425,585)
        d.rounded_rectangle(ai,radius=18,fill=(15,15,18),outline=GREEN,width=2)
        text(335,495,'AI',54,GREEN,reveal,True,'mm')
        text(335,625,'场景生成',27,MUTED,body_alpha,anchor='mt')
        flow=smooth(t,.45,1.25);end=460+220*flow
        d.line((460,495,end,495),fill=GREEN,width=3)
        if flow>.98:d.line((665,484,680,495,665,506),fill=GREEN,width=3)
        y=315+round(18*(1-reveal))
        d.rounded_rectangle((720,y,1740,y+515),radius=16,fill=(15,15,18),outline=EDGE,width=2)
        d.rounded_rectangle((768,y+48,885,y+92),radius=7,fill=(22,48,33),outline=(39,78,52))
        text(826,y+70,'AI 生成',21,GREEN,body_alpha,anchor='mm')
        if show_steps:
            text(924,y+54,'大学生 A · 用例步骤',36,alpha=body_alpha,heavy=True)
            for i,step in enumerate(case['steps'],1):
                row=y+128+(i-1)*67
                d.rounded_rectangle((768,row,1692,row+54),radius=6,fill=(18,18,21),outline=(44,44,50))
                text(795,row+27,f'{i:02d}',24,GREEN,body_alpha,anchor='lm')
                text(856,row+27,step['display'],30,alpha=body_alpha,anchor='lm')
        else:
            text(768,y+128,'大学生 A · 场景用例',48,alpha=body_alpha,heavy=True)
            text(768,y+210,'基于典型操作序列生成',30,MUTED,body_alpha)
            done=smooth(t,1.15,1.75)*body_alpha
            d.line((771,y+324,783,y+336,806,y+309),fill=tuple(round(a+(b-a)*done) for a,b in zip(BG,GREEN)),width=4)
            text(832,y+305,'创建完成',36,GREEN,done,True)
        d.line((72,930,1848,930),fill=(38,38,45),width=2)
        labels=['单场景复现','场景库建设','操作序列提取','AI 场景示例','影响因子时序','故障上下文']
        for j,label in enumerate(labels):
            x=round((115+j*210)*1.5)
            d.ellipse((x-90,966,x-81,975),fill=GREEN if j<=3 else EDGE)
            text(x-64,970,label,21,WHITE if j==3 else MUTED,anchor='lm')
        d.line((0,1008,1920,1008),fill=EDGE,width=1)
        return im
    def frame(t):
        if t<show-fade_in:im=state(t)
        elif t<show:im=Image.blend(state(t),state(t,True),smooth(t,show-fade_in,show))
        else:im=state(t,True)
        return Image.blend(previous,im,smooth(t,0,.6)) if t<.6 else im
    write_bridge(out,name,seconds,frame)
    frame(show+.5).save(out/'student-steps-static.png')
    (out/'student-step-preview.json').write_text(json.dumps({'steps':[s['display'] for s in case['steps']],
        'static_start':show,'static_end':show+hold,'static_seconds':hold,'step_narration':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
