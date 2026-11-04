"""Scenario input, layered AI search and an explicitly absent-then-added edge.

21 seconds at 60 fps, intended for master seconds 26--47. Pillow + FFmpeg.
The horizontal cyan scan is a temporary search indicator, never a graph edge.
The purple connection does not exist in EDGES and appears only at 13.4 seconds.
"""
from pathlib import Path
import argparse
import math
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
S=2
W,H=1280,720
WHITE=(244,244,245); MUTED=(148,148,158); GRAY=(83,83,94)
CYAN=(56,189,248); GREEN=(74,222,128); PURPLE=(192,132,252)
NODES={'r':(800,180),'a':(470,270),'b':(650,270),'c':(920,270),'d':(1150,270)}
for row,y in [(2,375),(3,480),(4,580)]:
    for i,x in enumerate([460,600,740,880,1020,1180]): NODES[f'{row}{i}']=(x,y)
EDGES=[('r',n) for n in 'abcd']+[
    ('a','20'),('a','21'),('b','22'),('c','23'),('c','24'),('d','25'),
    ('20','30'),('21','31'),('23','32'),('23','33'),('25','35')]+[(f'3{i}',f'4{i}') for i in range(6)]
ROUTE=['r','b','22','34','44']
LABELS={'r':'ROOT','b':'抖音首页','22':'我的页面','34':'我的喜欢','44':'视频详情'}
def ease(t,a,b):
    u=max(0,min(1,(t-a)/(b-a)));return u*u*(3-2*u)
def lerp(a,b,u):return tuple(a[i]+(b[i]-a[i])*u for i in range(2))
def col(c,alpha):return (*c,round(max(0,min(1,alpha))*255))

class Renderer:
    def __init__(self):
        self.font={n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n*S) for n in [12,14,16,18,20,22,24,26,28,32]}
        self.bg=Image.new('RGBA',(W*S,H*S),(9,9,11,255))
        self.images=[]
        for name in ['myprofile1.png','myliketab.png','mylike.jpg']:
            im=Image.open(ROOT/'assets/screenshots'/name).convert('RGB')
            im.thumbnail((142*S,230*S),Image.Resampling.LANCZOS)
            self.images.append(im)

    def frame(self,t):
        im=self.bg.copy(); layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer)
        def line(a,b,c=GRAY,width=1,alpha=1):d.line([tuple(round(v*S) for v in a),tuple(round(v*S) for v in b)],fill=col(c,alpha),width=max(1,round(width*S)))
        def text(x,y,s,size=18,c=WHITE,alpha=1,anchor='lt'):
            d.text((round(x*S),round(y*S)),s,font=self.font[size],fill=col(c,alpha),anchor=anchor)
        def rect(box,c=(17,17,20),outline=(52,52,59),alpha=1,r=10):
            d.rounded_rectangle(tuple(round(v*S) for v in box),radius=r*S,fill=col(c,alpha),outline=col(outline,alpha),width=S)
        def dot(pos,r=5,c=GRAY,alpha=1,ring=False):
            x,y=pos;box=((x-r)*S,(y-r)*S,(x+r)*S,(y+r)*S)
            d.ellipse(box,outline=col(c,alpha) if ring else None,fill=None if ring else col(c,alpha),width=2*S)
        morph=ease(t,18.8,20.8); ui=1-morph
        text(42,25,'05  /  疑似问题场景',18)
        text(1238,28,'APPLICATION KNOWLEDGE GRAPH',12,MUTED,anchor='rt')
        line((42,65),(1238,65),(63,63,70))
        # Input stays visible while the graph is explored.
        rect((42,96,366,357),alpha=ui)
        text(64,118,'输入源',14,MUTED,ui)
        text(64,147,'疑似问题场景',28,WHITE,ui)
        rect((63,199,345,300),(9,9,11),(63,63,70),ui)
        content_alpha=ease(t,.15,.75)*ui
        text(79,219,'进入「我」，查看喜欢列表，',18,WHITE,content_alpha)
        text(79,251,'再打开其中的视频。',18,WHITE,content_alpha)
        text(64,324,'场景描述 → 语义向量',14,MUTED,ease(t,.8,1.3)*ui)
        rect((42,378,366,596),alpha=ui)
        rect((62,398,104,434),(8,27,39),(36,117,158),ui,r=6)
        text(83,408,'AI',20,CYAN,ui,anchor='mt')
        stages=[(0,'理解疑似问题场景','构建场景语义查询'),(1.8,'召回相关页面','Vector DB · 相似页面'),
                (4.8,'从 ROOT 逐层探索','沿已有页面关系向下定位'),(8.1,'同层横向查找','比较页面语义与操作上下文'),
                (12.0,'发现缺失关联','两端页面已存在，连接未记录'),(13.4,'自动补全连接','新增 1 条场景关联'),
                (16.1,'用户实际场景','首页 → 我 → 喜欢 → 视频')]
        stage=next(s for s in reversed(stages) if t>=s[0])
        text(116,408,stage[1],18,WHITE,ui)
        text(64,458,stage[2],16,MUTED,ui)
        for k,(label,c) in enumerate([('已有页面关系',GRAY),('AI 搜索轨迹',CYAN),('AI 新增连接',PURPLE)]):
            line((65,503+k*27),(88,503+k*27),c,2,ui);text(100,495+k*27,label,14,MUTED,ui)
        # Graph levels and stable overview.
        for name,y in [('ROOT',180),('LEVEL 1',270),('LEVEL 2',375),('LEVEL 3',480),('LEVEL 4',580)]:
            text(399,y-26,name,12,MUTED,ui*.75)
            line((420,y+38),(1238,y+38),(35,35,41),1,ui*.7)
        for a,b in EDGES:line(NODES[a],NODES[b],GRAY,1.5,ui*.7)
        # Existing route travels down two levels before the missing relation.
        for a,b,start,end in [('r','b',5.15,6.35),('b','22',6.4,7.6)]:
            u=ease(t,start,end)
            if u>0:line(NODES[a],lerp(NODES[a],NODES[b],u),CYAN,3,ui)
        active=None
        if 4.8<=t<7.7:
            if t<5.15:active=NODES['r']
            elif t<6.4:active=lerp(NODES['r'],NODES['b'],ease(t,5.15,6.35))
            else:active=lerp(NODES['b'],NODES['22'],ease(t,6.4,7.6))
        # Search beams run above a level, not through node centers as edges do.
        for row,start,end in [(2,7.8,9.7),(3,9.8,12.0)]:
            if start<=t<=end:
                u=(t-start)/(end-start); x=600+420*u;y=375 if row==2 else 480
                line((580,y-29),(1060,y-29),CYAN,1.3,ui*.45)
                dot((x,y-29),5,CYAN,ui)
                for i in range(1,5):
                    pos=NODES[f'{row}{i}'];alpha=max(0,1-abs(pos[0]-x)/100)*ui
                    if alpha:dot(pos,14,CYAN,alpha,True)
                text(1040,y-53,'横向查找',14,CYAN,ui,anchor='rt')
        # Highlight the two disconnected endpoints without drawing a fake edge.
        missing=ease(t,11.8,12.35)*(1-ease(t,14.5,15))
        if missing:
            for n in ['22','34']:dot(NODES[n],17,PURPLE,missing*ui,True)
            rect((813,403,1069,445),(19,13,27),(109,72,143),missing*ui,r=6)
            text(941,416,'原图谱中没有这条连接',16,PURPLE,missing*ui,anchor='mt')
        # AI adds the absent connection; the midpoint is an association marker,
        # not an invented extra page, keeping the actual five-step case intact.
        bridge=ease(t,13.4,15.3)
        if bridge:
            a,b=NODES['22'],NODES['34'];point=lerp(a,b,bridge)
            line(a,point,PURPLE,4,ui)
            dot(point,6,WHITE,ui*(1-ease(t,15.3,15.8)))
            mid=lerp(a,b,.62)
            dot(mid,9,PURPLE,ease(t,14,14.5)*ui,True)
            if t>=14.6:
                rect((946,396,1212,432),(18,12,25),(105,65,140),ease(t,14.6,15)*ui,r=6)
                text(1079,407,'AI 补全连接 +1',16,PURPLE,ease(t,14.6,15)*ui,anchor='mt')
        end=ease(t,15.4,16.2)
        if end:line(NODES['34'],lerp(NODES['34'],NODES['44'],end),GREEN,3,ui)
        done=ease(t,16.1,16.8)
        for a,b in zip(ROUTE,ROUTE[1:]):
            if done:line(NODES[a],NODES[b],PURPLE if (a,b)==('22','34') else GREEN,3,done*ui)
        if bridge:
            dot(lerp(NODES['22'],NODES['34'],.62),9,PURPLE,ease(t,14,14.5)*ui,True)
        for n,pos in NODES.items():
            if n in ROUTE and morph>0:continue
            c=GREEN if done and n in ROUTE else (CYAN if (n=='r' and t>=4.8 or n=='b' and t>=6.35 or n=='22' and t>=7.6) else GRAY)
            dot(pos,7 if n in ROUTE else 4,c,ui)
            if n in LABELS:text(pos[0],pos[1]+14,LABELS[n],16,WHITE if n=='r' else MUTED,ui,anchor='mt')
        if active:dot(active,13,CYAN,ui,True)
        if t>=16.2:
            dot(NODES['44'],17,GREEN,done*ui,True)
            text(1018,626,'用户实际场景路径',18,GREEN,done*ui,anchor='mt')
        # Continuous hand-off: the selected path unfolds into the existing case.
        if morph>0:
            positions=[lerp(NODES[n],(142+i*249,315),morph) for i,n in enumerate(ROUTE)]
            for i,(a,b) in enumerate(zip(positions,positions[1:])):line(a,b,PURPLE if i==2 else GREEN,3,morph)
            for i,pos in enumerate(positions):
                dot(pos,8,GREEN)
                text(pos[0],pos[1]+20,LABELS[ROUTE[i]],18,WHITE,morph,anchor='mt')
            text(640,90,'固化目标路径为可复用用例',22,GREEN,morph,anchor='mt')
        footer='从疑似问题场景出发 · AI 逐层探索与横向查找'
        if t>=12:footer='发现未记录的页面关联 · AI 自动补全连接'
        if t>=16:footer='连接分散页面 · 还原用户实际操作的场景路径'
        if t>=19:footer='将这条场景路径固化，交给实验室手机和机械手复现'
        text(640,677,footer,20,WHITE,1,anchor='mt')
        im=Image.alpha_composite(im,layer)
        # Dedicated 2.7 s vector-recall view retains the established database beat.
        recall=ease(t,1.8,2.1)*(1-ease(t,4.3,4.8))
        if recall>0:
            overlay=Image.new('RGBA',im.size);p=ImageDraw.Draw(overlay)
            p.rounded_rectangle((402*S,101*S,1240*S,640*S),radius=12*S,fill=(12,12,15,round(250*recall)),outline=col((63,63,70),recall),width=S)
            p.text((439*S,125*S),'Vector DB · 召回相似页面',font=self.font[24],fill=col(WHITE,recall))
            for i,img in enumerate(self.images):
                x=458+i*252
                p.rounded_rectangle((x*S,185*S,(x+220)*S,582*S),radius=8*S,fill=col((20,20,24),recall),outline=col((80,80,90),recall),width=S)
                pic=img.convert('RGBA');pic.putalpha(round(255*recall));overlay.alpha_composite(pic,(round((x+110)*S-pic.width/2),216*S))
                p.text(((x+110)*S,493*S),['个人主页','喜欢列表','视频页面'][i],font=self.font[20],fill=col(WHITE,recall),anchor='mt')
                p.text(((x+110)*S,537*S),'相似页面候选',font=self.font[14],fill=col(GREEN,recall),anchor='mt')
            im=Image.alpha_composite(im,overlay)
        return im.convert('RGB').resize((W,H),Image.Resampling.LANCZOS)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,default=ROOT/'output/scenario-path-v1');p.add_argument('--preview-only',action='store_true');a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True);r=Renderer()
    for t in [1,3,6,8.8,11,12.8,15.4,17.5,20.7]:r.frame(t).save(a.out/f'scenario-{t}.png')
    if a.preview_only:return
    cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r','60','-i','-','-an','-c:v','libx264','-preset','medium','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',str(a.out/'scenario-path-clean.mp4')]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for n in range(21*60):proc.stdin.write(r.frame(n/60).tobytes())
    finally:proc.stdin.close()
    if proc.wait():raise RuntimeError('Scenario render failed')
    print(a.out/'scenario-path-clean.mp4')

if __name__=='__main__':main()
