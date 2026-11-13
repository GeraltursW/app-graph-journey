"""Replay the saved successful case using the same control UI as AI exploration.

Only the saved route is executed: Me -> Likes -> current video. Each control
is located, highlighted and clicked before the phone changes page. The final
phone moves into the existing scene-library shot with no historical-frame flash.
"""
import json
import subprocess
from pathlib import Path
from video_fonts import chinese_font
from PIL import Image, ImageDraw, ImageFont
from render_page_nodes_monochrome import ease, mix
from control_ui_style import BG,PANEL,EDGE,WHITE,MUTED,GREEN,phone_shell,focus_box,checkmark,cursor
from integrate_scenario_main import write_bridge,boxmix
from film_step_labels import step_label

SIZE=(1920,1080);FPS=60;PHONE=(390,260,810,960)
EVENTS=[{'target':'我','begin':.9,'click':1.15,'page_change':1.32,'box':[305,568,391,632]},
        {'target':'喜欢','begin':1.85,'click':2.1,'page_change':2.27,'box':[273,226,384,278]},
        {'target':'当前视频','begin':2.8,'click':3.05,'page_change':3.22,'box':[47,320,143,420]}]
STEPS=['启动应用','点击底部「我」','点击「喜欢」Tab','点击当前视频','验证目标页面']
COMPLETE=[.65,1.32,2.27,3.22,3.85]


def decoded(source,target,time=None,last=False):
    args=['-sseof','-0.02'] if last else ['-ss',str(time or 0)]
    subprocess.run(['ffmpeg','-v','error','-y',*args,'-i',str(source),'-frames:v','1',str(target)],check=True)
    return Image.open(target).convert('RGB')


def render_lab_replay(source,out,name='08-01',duration=4.6,preview=False):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    previous=decoded(out/'07-01.mp4',out/'lab-entry-previous.png',last=True) if (out/'07-01.mp4').exists() else decoded(source,out/'lab-entry-previous.png',52-1/FPS)
    fonts={s:ImageFont.truetype(chinese_font(),s) for s in (18,20,22,24,26,28,30,32,42)}
    bold=ImageFont.truetype(chinese_font(True),42)
    ui_bold=ImageFont.truetype(chinese_font(True),30)

    def phone(t):
        im=phone_shell();d=ImageDraw.Draw(im)
        page=sum(t>=e['page_change'] for e in EVENTS)
        active=next((e for e in EVENTS if e['begin']<=t<e['page_change']),None)
        if page==0:
            d.rounded_rectangle((25,65,395,142),radius=10,outline=(85,85,95),width=1)
            for i,label in enumerate(['关注','推荐','同城']):
                d.text((92+i*117,99),label,font=fonts[24],fill=WHITE if i==1 else MUTED,anchor='mm')
            d.ellipse((207,125,213,131),fill=GREEN)
            d.rounded_rectangle((25,157,395,548),radius=10,outline=(85,85,95),width=1)
            d.text((49,178),'首页',font=ui_bold,fill=WHITE)
            d.text((49,226),'推荐内容',font=fonts[20],fill=MUTED)
            for i in range(2):
                y=272+i*119;d.rounded_rectangle((47,y,373,y+98),radius=9,outline=EDGE,width=1)
                d.rounded_rectangle((61,y+16,126,y+81),radius=6,outline=(108,108,118),width=1)
                d.polygon([(86,y+34),(86,y+63),(108,y+48)],fill=MUTED)
                d.line((144,y+30,335,y+30),fill=MUTED,width=2)
                d.line((144,y+55,292,y+55),fill=EDGE,width=2)
        elif page<3:
            d.text((210,81),'我的页面',font=ui_bold,fill=WHITE,anchor='mt')
            d.ellipse((43,132,109,198),outline=MUTED,width=2)
            d.line((132,150,340,150),fill=MUTED,width=2)
            d.line((132,179,272,179),fill=EDGE,width=2)
            d.rounded_rectangle((25,215,395,289),radius=10,outline=(85,85,95),width=1)
            for i,label in enumerate(['作品','收藏','喜欢']):
                x=39+i*117;box=(x,226,x+111,278)
                if active and active['target']=='喜欢' and i==2:focus_box(d,box)
                selected=i==(2 if page==2 else 0) or (active and active['target']=='喜欢' and i==2)
                d.text((x+55,249),label,font=fonts[24],fill=WHITE if selected else MUTED,anchor='mm')
                if page==2 and i==2:d.ellipse((x+52,267,x+58,273),fill=GREEN)
            for row in range(2):
                for col in range(3):
                    x=47+col*115;y=320+row*117;box=(x,y,x+96,y+100)
                    if row==0 and col==0 and active and active['target']=='当前视频':
                        focus_box(d,EVENTS[2]['box'])
                    else:d.rounded_rectangle(box,radius=7,outline=EDGE,width=1)
                    d.polygon([(x+37,y+29),(x+37,y+57),(x+58,y+43)],fill=MUTED)
                    d.line((x+14,y+77,x+78,y+77),fill=EDGE,width=2)
        else:
            d.text((210,81),'视频详情',font=ui_bold,fill=WHITE,anchor='mt')
            d.rounded_rectangle((43,145,377,513),radius=12,outline=EDGE,width=2)
            d.polygon([(185,284),(185,348),(238,316)],fill=WHITE)
            d.line((65,477,355,477),fill=EDGE,width=2)
            d.line((65,477,233,477),fill=WHITE,width=2)
            d.text((210,548),'目标视频已打开',font=fonts[24],fill=WHITE,anchor='mt')
            if t>=3.85:
                d.rounded_rectangle((84,594,336,643),radius=9,fill=(16,35,23),outline=(38,91,58),width=1)
                checkmark(d,113,618);d.text((138,618),'页面验证通过',font=fonts[22],fill=GREEN,anchor='lm')
        if page<3:
            d.rounded_rectangle((25,558,395,642),radius=10,outline=(85,85,95),width=1)
            for i,label in enumerate(['首页','朋友','消息','我']):
                box=(29+i*92,568,115+i*92,632)
                if active and active['target']=='我' and i==3:focus_box(d,box)
                selected=i==(0 if page==0 else 3) or (active and active['target']=='我' and i==3)
                d.text(((box[0]+box[2])/2,597),label,font=fonts[24],fill=WHITE if selected else MUTED,anchor='mm')
                if page>0 and i==3:d.ellipse(((box[0]+box[2])/2-3,622,(box[0]+box[2])/2+3,628),fill=GREEN)
        d.rounded_rectangle((157,660,263,665),radius=2,fill=EDGE)
        if active:
            k=EVENTS.index(active);now=active['box'];previous_box=EVENTS[k-1]['box'] if k else (324,185,390,250)
            progress=ease(t,active['begin'],active['click']-.03)
            x=previous_box[2]-10+(now[2]-previous_box[2])*progress
            y=previous_box[1]+10+(now[1]-previous_box[1])*progress
            pulse=(t-active['click'])/.17 if t>=active['click'] else None
            cursor(d,x,y,pulse)
        return im

    def frame(t):
        im=Image.new('RGB',SIZE,BG);d=ImageDraw.Draw(im)
        d.text((120,38),step_label(8),font=fonts[24],fill=MUTED)
        d.text((1800,41),'APPLICATION KNOWLEDGE GRAPH',font=fonts[20],fill=MUTED,anchor='rt')
        d.line((120,90,1800,90),fill=(47,47,54),width=2)
        d.text((120,139),'实验室手机执行',font=bold,fill=WHITE)
        d.text((120,209),'沿用例路径执行 · 定位控件 · 进入并验证页面',font=fonts[26],fill=MUTED)
        im.paste(phone(t),(PHONE[0],PHONE[1]));d=ImageDraw.Draw(im)
        for text,y in [('顶部区域',365),('页面内容',600),('验证结果' if t>=3.22 else '底部 Tab',857)]:
            d.text((155,y),text,font=fonts[28],fill=WHITE,anchor='lm')
            d.line((300,y,383,y),fill=EDGE,width=2)
        d.text((600,978),'实验室手机 · LAB-01',font=fonts[20],fill=MUTED,anchor='mt')
        done=sum(t>=end for end in COMPLETE);current=min(4,done);passed=done==5
        d.rounded_rectangle((940,285,1790,450),radius=14,fill=PANEL,outline=EDGE,width=2)
        d.rounded_rectangle((968,317,1038,387),radius=12,outline=GREEN,width=2)
        d.text((1003,352),'AI',font=fonts[32],fill=GREEN,anchor='mm')
        title='用例已下发 · 执行中' if t>=.65 else '正在下发测试用例'
        if passed:title='复现成功 · 页面验证通过'
        d.text((1073,314),title,font=fonts[30],fill=WHITE)
        d.text((1073,374),'5 / 5 步骤完成' if passed else ('LAB-01  /  '+STEPS[current]),font=fonts[26],fill=GREEN if passed else MUTED)
        for i,label in enumerate(STEPS):
            yy=479+i*94;selected=i==current and not passed;complete=i<done
            d.rounded_rectangle((944,yy,1789,yy+76),radius=10,fill=(16,35,23) if selected else PANEL,outline=GREEN if selected else EDGE,width=2 if selected else 1)
            d.text((971,yy+38),f'{i+1:02d}',font=fonts[22],fill=GREEN if selected or complete else MUTED,anchor='lm')
            d.text((1040,yy+38),label,font=fonts[26],fill=WHITE if selected or complete else MUTED,anchor='lm')
            if complete:checkmark(d,1747,yy+38)
            elif selected:d.ellipse((1741,yy+32,1753,yy+44),fill=GREEN)
        if t<.65:
            # A single packet carries the saved case into the connected phone.
            q=ease(t,.18,.65);d.line((836,345,931,345),fill=EDGE,width=2)
            x=931-95*q;d.ellipse((x-4,341,x+4,349),fill=GREEN)
        d.line((0,1008,1920,1008),fill=(51,51,59),width=1)
        if t<.34:im=Image.blend(previous,im,ease(t,0,.34))
        return im

    info={'duration':duration,'route':['ROOT','我','喜欢','当前视频'],'click_count':3,'events':EVENTS,'completed_step_times':COMPLETE,'phone_box':PHONE,'style_source':'control_ui_style.py'}
    (out/'lab-replay-events.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for t in [0,.55,1.22,2.17,3.12,3.95,4.58]:frame(t).save(out/f'lab-{t:.2f}.png')
    if not preview:write_bridge(out,name,duration,frame)


def render_lab_context_bridge(source,out,name='08-02',duration=.6):
    out=Path(out)
    previous=decoded(out/'08-01.mp4',out/'lab-exit-previous.png',last=True)
    following=decoded(out/'09-01.mp4',out/'lab-exit-following.png') if (out/'09-01.mp4').exists() else decoded(source,out/'lab-exit-following.png',61.4)
    cutout=previous.crop(PHONE);masked=previous.copy();ImageDraw.Draw(masked).rectangle(PHONE,fill=BG)
    empty=Image.new('RGB',SIZE,BG);end=(249,298,532,793)
    def frame(t):
        q=t/(duration-1/FPS);im=Image.blend(masked,empty,ease(q,0,.58))
        box=boxmix(PHONE,end,ease(q,0,.60))
        im.paste(cutout.resize((box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS),(box[0],box[1]))
        # Finish the move before revealing the next phone silhouette; otherwise
        # two offset outlines are visible during the dissolve.
        return Image.blend(im,following,ease(q,.66,1))
    write_bridge(out,name,duration,frame)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--preview',action='store_true')
    a=p.parse_args();render_lab_replay(a.source,a.out,preview=a.preview)
