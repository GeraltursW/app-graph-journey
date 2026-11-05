"""Friends -> swipe/search -> direct sibling tab switch to Me. No back action.

21 seconds at master 26--47 plus five seconds of matching case cards.
The Friends-to-Me edge is initially absent and added by AI at 12.2 seconds.
"""
from pathlib import Path
import argparse, math, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageOps
ROOT=Path(__file__).resolve().parents[1]
S=2; W,H=1280,720
WHITE=(244,244,245); MUTED=(161,161,170); GRAY=(83,83,94)
CYAN=(56,189,248); GREEN=(74,222,128); PURPLE=(192,132,252); AMBER=(251,191,36)
NODES={'r':(800,165),'f':(620,300),'m':(1025,300),'l':(1025,455),'v':(1025,577),'s':(458,300),'x':(1195,300),'f1':(555,455),'f2':(685,455),'m1':(875,455)}
EDGES=[('r',n) for n in ['s','f','m','x']]+[('f','f1'),('f','f2'),('m','m1'),('m','l'),('l','v')]
ROUTE=['r','f','m','l','v'];LABELS={'r':'ROOT','f':'朋友页面','m':'我的页面','l':'我的喜欢','v':'视频详情'}
CASE_POS=[(142+i*249,315) for i in range(5)]
def ease(t,a,b):
    u=max(0,min(1,(t-a)/(b-a)));return u*u*(3-2*u)
def lerp(a,b,u):return tuple(a[i]+(b[i]-a[i])*u for i in range(2))
def col(c,a=1):return (*c,round(max(0,min(1,a))*255))

class Renderer:
    def __init__(self):
        self.font={n:ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',n*S) for n in [12,14,16,18,20,22,24,26,28,32]}
        self.bg=Image.new('RGBA',(W*S,H*S),(9,9,11,255))
        self.images={k:Image.open(ROOT/'assets/screenshots'/n).convert('RGB') for k,n in [('f','myfriends.jpg'),('m','myprofile1.png'),('l','myliketab.png'),('v','mylike.jpg')]}
        self.phone={k:ImageOps.fit(im,(220*S,322*S),method=Image.Resampling.LANCZOS) for k,im in self.images.items()}
        self.thumbs={k:ImageOps.contain(im,(180*S,285*S),method=Image.Resampling.LANCZOS) for k,im in self.images.items()}
    def canvas(self):
        im=self.bg.copy();layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer)
        def line(a,b,c=GRAY,width=1,alpha=1):d.line([tuple(round(v*S) for v in a),tuple(round(v*S) for v in b)],fill=col(c,alpha),width=max(1,round(width*S)))
        def text(x,y,s,size=18,c=WHITE,alpha=1,anchor='lt'):d.text((round(x*S),round(y*S)),s,font=self.font[size],fill=col(c,alpha),anchor=anchor)
        def rect(box,c=(17,17,20),outline=(52,52,59),alpha=1,r=10):d.rounded_rectangle(tuple(round(v*S) for v in box),radius=r*S,fill=col(c,alpha),outline=col(outline,alpha),width=S)
        def dot(pos,r=5,c=GRAY,alpha=1,ring=False):
            x,y=pos;d.ellipse(((x-r)*S,(y-r)*S,(x+r)*S,(y+r)*S),outline=col(c,alpha) if ring else None,fill=None if ring else col(c,alpha),width=2*S)
        def arrow(a,b,c=CYAN,width=2,alpha=1):
            line(a,b,c,width,alpha);angle=math.atan2(b[1]-a[1],b[0]-a[0])
            for o in [-.5,.5]:line(b,(b[0]-10*math.cos(angle+o),b[1]-10*math.sin(angle+o)),c,width,alpha)
        return im,layer,d,line,text,rect,dot,arrow
    def frame(self,t):
        im,layer,d,line,text,rect,dot,arrow=self.canvas();morph=ease(t,18.8,20.8);ui=1-morph
        text(42,25,'05  /  疑似问题场景',18);text(1238,28,'APPLICATION KNOWLEDGE GRAPH',12,MUTED,anchor='rt');line((42,65),(1238,65),(63,63,70))
        rect((42,94,370,198),alpha=ui);text(62,111,'输入疑似问题场景',16,MUTED,ui);text(62,145,'查找「我的喜欢」',24,WHITE,ui)
        # Screenshots are enclosed by a complete monochrome phone frame.
        rect((78,218,328,566),(9,9,11),(161,161,170),ui,r=18)
        key='f' if t<14.3 else ('m' if t<15.9 else ('l' if t<17.2 else 'v'))
        pic=self.phone[key].copy()
        if key=='f' and t>6.5:
            # Only the content scrolls; bottom navigation stays fixed.
            extra=round(60*S*ease(t,6.5,6.9))
            body=pic.crop((0,28*S,220*S,278*S)).resize((220*S,250*S+extra),Image.Resampling.LANCZOS)
            offset=round(extra*ease(t,6.7,9.3));pic.paste(body.crop((0,offset,220*S,offset+250*S)),(0,28*S))
        pic=pic.convert('RGBA');pic.putalpha(round(255*ui));layer.alpha_composite(pic,(93*S,231*S))
        if 4.9<=t<6.4 or 12.2<=t<14.4:
            x=158 if t<6.4 else 292;dot((x,526),15,CYAN if t<6.4 else PURPLE,ui,True);dot((x,526),4,WHITE,ui)
        if 6.6<=t<9.9:
            u=((t-6.6)/1.55)%1;arrow((277,465),(277,355),CYAN,2,ui*.75);dot((277,465-105*ease(u,0,1)),8,WHITE,ui)
            text(203,579,'↑  上滑查找「我的喜欢」',16,CYAN,ui,anchor='mt')
        else:
            caption,color=('未找到「我的喜欢」',AMBER) if 9.9<=t<12.2 else (('点击底部「我」Tab',PURPLE) if 12.2<=t<14.4 else (('在「我」中发现「喜欢」',GREEN) if 14.4<=t<16 else (('找到喜欢列表，打开视频',GREEN) if t>=16 else ('点击底部「朋友」Tab',CYAN))))
            text(203,579,caption,16,color,ui,anchor='mt')
        if 14.4<=t<16:rect((283,368,310,389),(20,40,25),GREEN,ui,r=4);text(297,372,'喜欢',12,WHITE,ui,anchor='mt')
        # Equal Y coordinates explicitly express sibling tabs.
        for label,y in [('应用入口',165),('同级 TAB 页面',300),('页面内功能',455),('内容详情',577)]:
            text(404,y-48,label,12,MUTED,ui);line((402,y+42),(1238,y+42),(39,39,46),1,ui)
        for a,b in EDGES:line(NODES[a],NODES[b],GRAY,1.5,ui*.75)
        rect((573,249,1072,349),(14,14,18),(75,75,86),ui,r=12)
        text(822,225,'「朋友」与「我」：底部 Tab，同一层级',18,WHITE,ui,anchor='mt')
        if t<12.2:text(822,294,'尚未记录这条切换关系',14,MUTED,ui,anchor='mt')
        travel=ease(t,4.8,6.2)
        if travel:arrow(NODES['r'],lerp(NODES['r'],NODES['f'],travel),CYAN,3,ui)
        if 6.2<=t<12.2:
            dot(NODES['f'],18,CYAN if t<10 else AMBER,ui,True);text(620,366,'滑动查找' if t<10 else '未命中目标',18,CYAN if t<10 else AMBER,ui,anchor='mt')
        bridge=ease(t,12.2,14.3)
        if bridge:
            arrow(NODES['f'],lerp(NODES['f'],NODES['m'],bridge),PURPLE,4,ui)
            text(822,267,'点击「我」 · 同级横向跳转',16,PURPLE,ui,anchor='mt');text(822,365,'AI 补全同级页面连接 +1',16,PURPLE,ui,anchor='mt')
        for a,b,start,end in [('m','l',15.0,16.1),('l','v',16.2,17.4)]:
            u=ease(t,start,end)
            if u:arrow(NODES[a],lerp(NODES[a],NODES[b],u),GREEN,3,ui)
        done=ease(t,17.4,18.1)
        if done:
            for a,b in zip(ROUTE,ROUTE[1:]):arrow(NODES[a],NODES[b],PURPLE if a=='f' else GREEN,3,done*ui)
        for n,pos in NODES.items():
            if n in ROUTE and morph>0:continue
            active=(n=='r' and t>=4.8 or n=='f' and t>=6.2 or n=='m' and t>=14.3 or n=='l' and t>=16.1 or n=='v' and t>=17.4)
            dot(pos,8 if n in ROUTE else 4,GREEN if done and n in ROUTE else (CYAN if active else GRAY),ui)
            if n in LABELS:text(pos[0],pos[1]+18,LABELS[n],18,WHITE,ui,anchor='mt')
        if t>=17.4:dot(NODES['v'],17,GREEN,done*ui,True);text(1025,627,'目标确认 · 路径验证成功',16,GREEN,done*ui,anchor='mt')
        stages=[(0,'理解问题场景'),(1.8,'向量召回候选页面'),(4.8,'进入朋友页面'),(6.5,'滑动查找目标'),(10,'当前页未命中'),(12.2,'点击「我」同级切换'),(14.4,'发现「我的喜欢」'),(17.4,'验证成功')]
        stage=next(s[1] for s in reversed(stages) if t>=s[0]);rect((42,614,370,651),(12,20,27),(44,89,111),ui,r=7);text(62,623,'AI',16,CYAN,ui);text(103,623,stage,16,WHITE,ui)
        if morph:
            positions=[lerp(NODES[n],CASE_POS[i],morph) for i,n in enumerate(ROUTE)]
            for i,(a,b) in enumerate(zip(positions,positions[1:])):arrow(a,b,PURPLE if i==1 else GREEN,3,morph)
            for i,pos in enumerate(positions):dot(pos,8,GREEN);text(pos[0],pos[1]+20,LABELS[ROUTE[i]],18,WHITE,morph,anchor='mt')
            text(640,90,'固化目标路径为可复用用例',22,GREEN,morph,anchor='mt')
        footer='输入疑似问题场景 · AI 根据页面内容寻找目标'
        if t>=6.5:footer='识别页面内容 · 上滑查找「我的喜欢」'
        if t>=10:footer='在朋友页滑动查找 · 未发现「我的喜欢」'
        if t>=12.2:footer='直接点击底部「我」 · 朋友与我属于同级 Tab 跳转'
        if t>=15.9:footer='进入「喜欢」列表 · 打开视频 · 验证成功'
        if t>=18.8:footer='将实际操作路径固化，交给实验室设备复现'
        text(640,677,footer,20,WHITE,anchor='mt');im=Image.alpha_composite(im,layer)
        recall=ease(t,1.8,2.1)*(1-ease(t,4.3,4.8))
        if recall:
            overlay=Image.new('RGBA',im.size);p=ImageDraw.Draw(overlay)
            p.rounded_rectangle((402*S,101*S,1240*S,640*S),radius=12*S,fill=col((12,12,15),recall),outline=col((63,63,70),recall),width=S)
            p.text((439*S,125*S),'Vector DB · 召回相似页面',font=self.font[24],fill=col(WHITE,recall))
            for i,(key,label) in enumerate([('f','朋友页面'),('m','我的页面'),('l','我的喜欢')]):
                x=431+i*265;img=self.thumbs[key].convert('RGBA');img.putalpha(round(255*recall))
                p.rounded_rectangle((x*S,184*S,(x+240)*S,593*S),radius=8*S,fill=col((20,20,24),recall),outline=col(GRAY,recall),width=S)
                overlay.alpha_composite(img,(round((x+120)*S-img.width/2),205*S));p.text(((x+120)*S,511*S),label,font=self.font[20],fill=col(WHITE,recall),anchor='mt');p.text(((x+120)*S,550*S),'相似页面候选',font=self.font[14],fill=col(GREEN,recall),anchor='mt')
            im=Image.alpha_composite(im,overlay)
        return im.convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
    def case_frame(self,t):
        im,layer,d,line,text,rect,dot,arrow=self.canvas();text(42,25,'08  /  将目标路径固化为测试用例',18);line((42,65),(1238,65),(63,63,70));text(640,90,'固化目标路径为可复用用例',22,GREEN,anchor='mt')
        actions=['点击「朋友」','点击「我」','点击「喜欢」','点击当前视频']
        for i,(a,b) in enumerate(zip(CASE_POS,CASE_POS[1:])):
            arrow((a[0]+70,315),(b[0]-70,315),PURPLE if i==1 else GREEN,3);text((a[0]+b[0])/2,252,actions[i],16,WHITE,anchor='mt')
            if i==1:text((a[0]+b[0])/2,278,'同级切换',14,PURPLE,anchor='mt')
        for i,(x,y) in enumerate(CASE_POS):
            rect((x-69,y-19,x+69,y+99),(13,13,16),(72,72,82),r=8);dot((x,y),8,GREEN);text(x,y+22,LABELS[ROUTE[i]],18,WHITE,anchor='mt');text(x,y+62,['测试起点','滑动查找未命中','同级 Tab 页面','喜欢列表','目标视频'][i],12,MUTED,anchor='mt')
        rect((462,470,818,522),(12,24,18),(38,91,58),r=8);text(640,485,'路径验证成功 · 用例已保存',20,GREEN,anchor='mt');text(640,677,'页面成为节点 · 操作写入箭头 · 用例可保存并重复执行',20,WHITE,anchor='mt')
        return Image.alpha_composite(im,layer).convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
def encode(path,frames):
    proc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r','60','-i','-','-an','-c:v','libx264','-preset','medium','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',str(path)],stdin=subprocess.PIPE)
    try:
        for frame in frames:proc.stdin.write(frame.tobytes())
    finally:proc.stdin.close()
    if proc.wait():raise RuntimeError('Scenario encoding failed')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,default=ROOT/'output/scenario-path-v1');p.add_argument('--preview-only',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);r=Renderer()
    for t in [1,3,6,8.8,11,12.8,14.6,16.2,17.8,20.9]:r.frame(t).save(a.out/f'scenario-{t}.png')
    r.case_frame(2).save(a.out/'case-preview.png')
    if a.preview_only:return
    encode(a.out/'scenario-path-clean.mp4',(r.frame(n/60) for n in range(21*60)))
    case=r.case_frame(0);encode(a.out/'scenario-case-clean.mp4',(case for _ in range(5*60)));print('FRIENDS_SCENARIO_COMPLETE',flush=True)
if __name__=='__main__':main()
