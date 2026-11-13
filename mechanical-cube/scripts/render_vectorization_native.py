"""Rebuild STEP 05 with crisp supersampled text, vector paths and graph motion."""
import math
import random
import subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from video_fonts import chinese_font
from integrate_scenario_main import write_bridge

S=2;SIZE=(1920,1080);BG=(9,9,11);PANEL=(15,15,19)
WHITE=(244,244,245);MUTED=(164,164,175);EDGE=(75,75,87)
GREEN=(74,222,128);CYAN=(56,189,248)

def ease(t,a,b):
    u=max(0,min(1,(t-a)/(b-a)));return u*u*(3-2*u)

def mix(a,b,u):return tuple(round(x+(y-x)*u) for x,y in zip(a,b))

def render_vectorization(source,out,name='05-01',duration=5.2,preview=False):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    def still(path,target,time=0,last=False):
        args=['-sseof','-0.02'] if last else ['-ss',str(time)]
        subprocess.run(['ffmpeg','-v','error','-y',*args,'-i',str(path),'-frames:v','1',str(out/target)],check=True)
        return Image.open(out/target).convert('RGB')
    previous=still(out/'04-01.mp4','vectors-previous.png',last=True) if (out/'04-01.mp4').exists() else still(source,'vectors-previous.png',18-1/60)
    font_path=chinese_font();face=1 if Path(font_path).name.startswith('STHeiti') else 0
    fonts={n:ImageFont.truetype(font_path,n*S,index=face) for n in (18,20,22,24,26,28,30,32,42)}
    rng=random.Random(5)
    cloud=[(1160+(i%6)*112+rng.uniform(-12,12),410+(i//6)*77+rng.uniform(-12,12)) for i in range(29)]
    graph=[(960,300)]+[(330+i*420,445) for i in range(4)]+[(225+i*210,590) for i in range(8)]+[(172.5+i*105,765) for i in range(16)]
    edges=[(0,1+i) for i in range(4)]+[(1+i//2,5+i) for i in range(8)]+[(5+i//2,13+i) for i in range(16)]

    def frame(t):
        im=Image.new('RGB',(SIZE[0]*S,SIZE[1]*S),BG);d=ImageDraw.Draw(im)
        def text(x,y,body,size=26,c=WHITE,alpha=1,anchor='lt'):
            if alpha>0:d.text((round(x*S),round(y*S)),body,font=fonts[size],fill=mix(BG,c,alpha),anchor=anchor)
        def line(a,b,c=EDGE,width=2,alpha=1):
            d.line([tuple(round(v*S) for v in a),tuple(round(v*S) for v in b)],fill=mix(BG,c,alpha),width=round(width*S))
        def dot(x,y,r=5,c=GREEN,alpha=1):
            d.ellipse(tuple(round(v*S) for v in (x-r,y-r,x+r,y+r)),fill=mix(BG,c,alpha))
        def panel(box,alpha=1):
            d.rounded_rectangle(tuple(round(v*S) for v in box),radius=12*S,fill=mix(BG,PANEL,alpha),outline=mix(BG,EDGE,alpha),width=2*S)
        def moving_line(a,b,progress,c=GREEN,alpha=1):
            q=(a[0]+(b[0]-a[0])*progress,a[1]+(b[1]-a[1])*progress)
            line(a,b,EDGE,2,alpha);line(a,q,c,2.5,alpha)
            if 0<progress<1:dot(*q,5,c,alpha)

        text(1800,41,'APPLICATION KNOWLEDGE GRAPH',20,MUTED,anchor='rt')
        line((120,90),(1800,90),(47,47,54))
        morph=ease(t,2.9,3.65);left_alpha=1-ease(t,2.9,3.35)
        text(120,139,'页面多模态向量化',42,alpha=1-ease(t,2.9,3.2))
        text(120,139,'向量索引连接页面关系',42,alpha=ease(t,3.2,3.5))
        for i,(label,english) in enumerate([('页面截图','Visual'),('控件文本','Text'),('页面结构','Structure')]):
            alpha=ease(t,.12+i*.14,.48+i*.14)*left_alpha;y=270+i*170
            panel((120,y,480,y+126),alpha)
            line((143,y+25),(143,y+101),GREEN,3,alpha)
            text(166,y+25,label,30,alpha=alpha);text(166,y+76,english,20,MUTED,alpha)
            moving_line((480,y+63),(690,503),ease(t,.65+i*.10,1.2+i*.10),alpha=alpha)
        enc=ease(t,.72,1.18)*left_alpha
        panel((690,370,1035,636),enc)
        text(862.5,408,'Page Encoder',32,alpha=enc,anchor='mt')
        text(862.5,469,'多模态编码',26,MUTED,enc,'mt')
        text(862.5,565,'[0.12  -0.38  0.76  …]',22,GREEN,enc,'mt')
        # Sharp feature bars and a packet show encoding and the database write.
        for j,height in enumerate([15,28,21,38,18,32,24,42,17,29]):
            x=758+j*23;h=height*ease(t,1.05+j*.025,1.55+j*.025)
            line((x,548),(x,548-h),GREEN,5,enc)
        moving_line((1035,503),(1110,503),ease(t,1.4,1.95),alpha=left_alpha)
        db=ease(t,1.35,1.85)*left_alpha
        panel((1110,260,1800,820),db)
        text(1140,287,'Vector DB',32,alpha=db)
        text(1140,338,'500+ PAGE EMBEDDINGS',18,MUTED,db)
        ready=ease(t,2.05,2.45)*left_alpha
        dot(1597,306,5,GREEN,ready);text(1768,295,'INDEX READY',18,GREEN,ready,'rt')
        points=[(x+(a-x)*morph,y+(b-y)*morph) for (x,y),(a,b) in zip(cloud,graph)]
        for j,(a,b) in enumerate(edges):
            alpha=ease(t,1.95+j*.018,2.45+j*.018)
            selected=a in (0,1,5) and b in (1,5,13)
            alpha*=1 if selected else .25+.75*morph
            color=GREEN if selected else mix((62,99,79),(104,104,117),morph)
            moving_line(points[a],points[b],ease(t,1.95+j*.018,2.45+j*.018),color,alpha)
        for j,(x,y) in enumerate(points):
            alpha=ease(t,1.6+j*.012,2.0+j*.012)
            color=GREEN if j in (0,1,5,13) else (CYAN if 1<=j<=4 else (154,154,167))
            dot(x,y,8 if j<=4 else 5,color,alpha)
        text(960,262,'ROOT',22,MUTED,morph,'mb')
        line((120,902),(1800,902),(42,42,49))
        text(960,936,'页面特征编码 · Vector DB 建立语义索引 · 连接页面关系',26,WHITE,anchor='mt')
        line((0,1008),(1920,1008),(51,51,59),1)
        result=im.resize(SIZE,Image.Resampling.LANCZOS)
        if t<.28:result=Image.blend(previous,result,ease(t,0,.28))
        return result

    for t in [0,.8,1.8,2.6,3.8,4.6,duration-1/60]:frame(t).save(out/f'vectors-native-{t:.2f}.png')
    if not preview:write_bridge(out,name,duration,frame)
