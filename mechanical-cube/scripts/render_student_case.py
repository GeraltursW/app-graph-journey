"""AI-generated student scenario with exact swipe events and fixed bottom tabs.

Phone UI is a monochrome schematic, not a recorded device execution.
All counts and page changes come from config/student_a_case.json.
"""
import math
from PIL import Image,ImageDraw

BG=(9,9,11);PANEL=(15,15,18);WHITE=(244,244,245);MUTED=(163,163,173)
EDGE=(65,65,75);GREEN=(74,222,128);DARKGREEN=(22,48,33);S=1.5
def ease(t,a,b):
    q=max(0,min(1,(t-a)/(b-a)));return q*q*(3-2*q)

def state(case,stage,u):
    events=case['swipe_events'].get(stage,[])
    progress=sum(ease(u,a,b) for a,b in events)
    completed=sum(u>=b for a,b in events)
    taps=case['tap_events']
    if stage=='student_feed':return dict(page='推荐页',step=0,feed=completed,likes=0,taps=0,offset=progress,video=1+completed)
    if stage=='student_tabs':
        if u<taps['me'][1]:return dict(page='推荐页',step=1,feed=2,likes=0,taps=0,offset=2,video=3)
        if u<taps['likes'][1]:return dict(page='我的页面',step=2,feed=2,likes=0,taps=1,offset=0,video=3)
        return dict(page='喜欢列表',step=3,feed=2,likes=0,taps=2,offset=0,video=3)
    if stage=='student_likes':return dict(page='喜欢列表',step=3,feed=2,likes=completed,taps=2,offset=progress,video=3)
    opened=u>=taps['open'][1]
    return dict(page='视频详情' if opened else '喜欢列表',step=5 if opened else 4,feed=2,likes=3,taps=3 if opened else 2,offset=3,video=14 if opened else 3)

class StudentScene:
    def __init__(self,r,case):
        self.r=r;self.case=case
        self.feed=self.feed_strip()
        self.gallery=self.gallery_strip()
    def feed_strip(self):
        im=Image.new('RGB',(360,round(285*4*S)),BG);d=ImageDraw.Draw(im)
        for k in range(4):
            y=k*285*S
            d.rectangle((0,y,359,y+285*S),fill=(18+k*3,18+k*3,22+k*3))
            d.rounded_rectangle((24,y+24,336,y+315),radius=8,outline=EDGE,width=2)
            d.text((180,y+147),f'视频 {k+1:02}',font=self.r.font[28],fill=WHITE,anchor='mm')
            for j in range(3):d.line((48,y+350+j*17,270-j*24,y+350+j*17),fill=EDGE,width=2)
            d.polygon([(166,y+232),(166,y+262),(192,y+247)],fill=WHITE)
        return im
    def gallery_strip(self):
        im=Image.new('RGB',(360,round(74*12*S)),BG);d=ImageDraw.Draw(im)
        for index in range(36):
            row,col=divmod(index,3);x=(5+col*79)*S;y=row*74*S
            d.rounded_rectangle((x,y+3,x+72*S,y+69*S),radius=4,fill=(23,23,28),outline=EDGE,width=1)
            d.text((x+36*S,y+29*S),f'{index+1:02}',font=self.r.font[20],fill=WHITE,anchor='mm')
            d.text((x+36*S,y+52*S),'喜欢的视频',font=self.r.font[12],fill=MUTED,anchor='mm')
        return im
    def plan(self,u,duration):
        r=self.r
        r.text(48,154,'示例用户 × 已有操作序列 → AI 生成具体场景',18,MUTED)
        r.rect((48,205,362,535),PANEL,EDGE,9)
        r.dot(105,267,30,EDGE);r.text(105,267,'A',28,WHITE,anchor='mm')
        r.text(157,244,'大学生 A',24,bold=True);r.text(157,282,'示例用户',14,MUTED)
        r.line((72,320),(338,320),EDGE)
        r.text(72,344,'使用应用',14,MUTED);r.text(72,370,'抖音',24)
        r.text(72,417,'场景目标',14,MUTED)
        r.text(72,444,'浏览推荐视频',20)
        r.text(72,478,'再查看喜欢的内容',20)
        r.rect((438,282,552,396),DARKGREEN,GREEN,10)
        r.text(495,323,'AI',32,anchor='mm',bold=True)
        r.text(495,365,'场景生成',16,GREEN,anchor='mm')
        r.curve((374,339),(425,339),p=ease(u,.6,1.5))
        r.curve((565,339),(629,339),p=ease(u,1.3,2.3))
        r.text(495,444,'页面 / 动作 / 次数',14,MUTED,anchor='mt')
        r.rect((642,205,1232,565),PANEL,EDGE,9)
        r.text(667,225,'AI 生成的场景用例',24,bold=True)
        labels=[('01','推荐页上滑 2 次','浏览 3 条视频'),('02','点击底部「我」','切换到我的页面'),('03','点击「喜欢」Tab','进入喜欢列表'),('04','喜欢列表上滑 3 次','查找目标内容'),('05','打开视频 14','进入视频详情')]
        for j,(num,title,sub) in enumerate(labels):
            alpha=ease(u,1.6+j*.65,2.1+j*.65);y=290+j*52
            r.dot(670,y+10,3,GREEN,alpha);r.text(691,y,num,14,MUTED,alpha)
            r.text(733,y,title,18,WHITE,alpha);r.text(1206,y+3,sub,14,MUTED,alpha,'rt')
        r.text(1230,588,'已生成 · 5 个步骤 · 滑动 5 次 · 点击 3 次',16,GREEN,ease(u,5.1,5.7),'rt')
    def tap(self,cx,cy,u,event):
        a,b=event
        if not a<=u<b:return
        r=self.r;q=(u-a)/(b-a);radius=6+17*q
        color=tuple(round(x+(y-x)*(1-q*.65)) for x,y in zip(BG,GREEN))
        r.d.ellipse(tuple(round(v*S) for v in (cx-radius,cy-radius,cx+radius,cy+radius)),outline=color,width=3)
        r.dot(cx,cy,5,GREEN)
    def phone(self,stage,u,s):
        r=self.r;ox,oy=124,218
        r.rect((112,188,376,596),BG,(210,210,216),14,width=2)
        r.line((230,201),(258,201),MUTED,2)
        # Cached content moves only inside the viewport. Header and bottom tabs stay fixed.
        screen=Image.new('RGB',(360,531),BG);d=ImageDraw.Draw(screen)
        def txt(x,y,t,size=14,c=WHITE,anchor='mm'):d.text((round(x*S),round(y*S)),t,font=r.font[size],fill=c,anchor=anchor)
        page=s['page']
        if page in ('推荐页','视频详情'):
            txt(120,16,'推荐' if page=='推荐页' else '视频详情',18)
            if page=='推荐页':
                top=round(s['offset']*285*S)
                body=self.feed.crop((0,top,360,top+round(285*S)))
            else:
                body=Image.new('RGB',(360,round(285*S)),PANEL);p=ImageDraw.Draw(body)
                p.rounded_rectangle((24,24,336,315),radius=8,outline=GREEN,width=2)
                p.text((180,148),'视频 14',font=r.font[28],fill=WHITE,anchor='mm')
                p.text((180,194),'目标内容',font=r.font[16],fill=GREEN,anchor='mm')
                p.polygon([(165,237),(165,267),(194,252)],fill=WHITE)
            screen.paste(body,(0,round(35*S)))
        else:
            txt(120,15,'我',18)
            d.ellipse((15*S,40*S,61*S,86*S),fill=(42,42,48));txt(38,63,'A',20)
            txt(78,52,'大学生 A',18,anchor='lm');txt(78,78,'个人主页',12,MUTED,anchor='lm')
            for j,name in enumerate(['作品','收藏','喜欢']):txt(40+80*j,128,name,14,GREEN if page=='喜欢列表' and j==2 else WHITE)
            d.line((0,141*S,360,141*S),fill=EDGE,width=1)
            if page=='喜欢列表':
                d.line((170*S,141*S,230*S,141*S),fill=GREEN,width=3)
                offset=round(s['offset']*74*S)
                screen.paste(self.gallery.crop((0,offset,360,offset+round(174*S))),(0,round(146*S)))
                if s['likes']==3:
                    # Video 14 = row 4, column 1, still in the viewport after three swipes.
                    x=84;y=146+4*74-s['offset']*74
                    d=ImageDraw.Draw(screen);d.rounded_rectangle((x*S,(y+3)*S,(x+72)*S,(y+69)*S),radius=4,outline=GREEN,width=3)
            else:
                txt(120,225,'我的作品',18,MUTED)
                for k in range(3):d.rounded_rectangle(((7+79*k)*S,160*S,(78+79*k)*S,205*S),radius=3,outline=EDGE)
        d=ImageDraw.Draw(screen)
        d.rectangle((0,320*S,360,531),fill=BG)
        if page!='视频详情':
            for j,label in enumerate(['首页','朋友','＋','消息','我']):
                selected=(j==0 and page=='推荐页') or (j==4 and page in ('我的页面','喜欢列表'))
                txt(24+48*j,336,label,14,GREEN if selected else MUTED)
        else:txt(120,337,'正在查看目标视频',12,GREEN)
        r.im.paste(screen,(round(ox*S),round(oy*S)));r.d=ImageDraw.Draw(r.im)
        r.line((219,585),(269,585),MUTED,2)
        for a,b in self.case['swipe_events'].get(stage,[]):
            if a<=u<b:
                q=ease(u,a,b);x=ox+211;y=oy+285-120*q
                r.arrow((x,oy+285),(x,oy+165),GREEN,.65,2);r.dot(x,y,7,GREEN)
        if stage=='student_tabs':
            self.tap(ox+216,oy+336,u,self.case['tap_events']['me'])
            self.tap(ox+200,oy+128,u,self.case['tap_events']['likes'])
        if stage=='student_open':self.tap(ox+120,oy+255,u,self.case['tap_events']['open'])
    def play(self,stage,u,duration):
        r=self.r;s=state(self.case,stage,u)
        r.text(48,154,'大学生 A · 抖音场景预演',18,MUTED)
        r.text(1232,154,'AI 生成用例 / 操作示意',14,MUTED,anchor='rt')
        self.phone(stage,u,s)
        r.rect((450,188,1232,550),PANEL,EDGE,9)
        r.rect((474,208,526,247),DARKGREEN,GREEN,5)
        r.text(500,228,'AI',18,WHITE,anchor='mm')
        r.text(543,214,'已生成的场景用例',24,bold=True)
        details=[f'滑动 {s["feed"]}/2 · 视频 {1+s["feed"]}/3','首页 → 我的页面','我的页面 → 喜欢列表',f'滑动 {s["likes"]}/3','喜欢列表 → 视频详情']
        for j,item in enumerate(self.case['steps']):
            y=264+j*54;active=j==s['step'];done=j<s['step']
            if active:r.rect((468,y-2,1213,y+48),DARKGREEN,(42,80,55),5)
            r.text(484,y+11,f'{j+1:02}',14,GREEN if active or done else MUTED)
            r.text(528,y+4,item['display'],18,WHITE if active or done else MUTED)
            r.text(528,y+30,details[j],12,MUTED)
            status='已预演' if done else ('进行中' if active else '待预演')
            if active and j==0:status=f'{s["feed"]} / 2 次'
            if active and j==3:status=f'{s["likes"]} / 3 次'
            r.text(1193,y+20,status,16,GREEN if active or done else MUTED,anchor='rm')
        r.text(450,578,'当前页面：'+s['page'],20,GREEN,anchor='lm')
        r.text(1230,578,f'已预演：滑动 {s["feed"]+s["likes"]}/5 次 · 点击 {s["taps"]}/3 次',16,MUTED,anchor='rm')
        if s['step']==5:
            r.text(244,608,'视频 14 已打开',14,GREEN,anchor='mm')
        else:r.text(244,608,'当前内容随操作切换',12,MUTED,anchor='mm')
