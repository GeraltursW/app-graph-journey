"""Crisp device connection shot using the exploration shot's page grid."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from video_fonts import chinese_font
from integrate_scenario_main import write_bridge, smooth

S=2
BG=(9,9,11);PANEL=(14,14,17);EDGE=(78,78,88)
WHITE=(244,244,245);MUTED=(163,163,173);GREEN=(74,222,128)

def render_connection_native(out,name='02-01',duration=2.4,preview=False):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    path=chinese_font();face=1 if Path(path).name.startswith('STHeiti') else 0
    fonts={n:ImageFont.truetype(path,n*S,index=face) for n in (18,20,24,26,28,30,32,42)}
    def frame(t):
        im=Image.new('RGB',(1920*S,1080*S),BG);d=ImageDraw.Draw(im)
        def text(x,y,value,size=26,color=WHITE,anchor=None):
            d.text((x*S,y*S),value,font=fonts[size],fill=color,anchor=anchor)
        def line(points,color=EDGE,width=2):
            d.line([(int(x*S),int(y*S)) for x,y in points],fill=color,width=width*S)
        def box(rect,radius=10,fill=PANEL,edge=EDGE,width=1):
            d.rounded_rectangle(tuple(int(v*S) for v in rect),radius=radius*S,fill=fill,outline=edge,width=width*S)
        text(1800,41,'APPLICATION KNOWLEDGE GRAPH',20,MUTED,'rt')
        line([(120,90),(1800,90)],(47,47,54))
        text(120,139,'连接设备，开始探索',42)
        text(120,209,'设备连接 · 进入应用页面',26,MUTED)
        # Match STEP 03: 420 x 700 phone at (390, 260), same Tab/content grid.
        box((391,261,808,958),31,(7,7,9),(212,212,216),3)
        box((405,276,794,942),23,PANEL,(57,57,64))
        box((560,285,640,292),3,EDGE,EDGE)
        for rect in [(415,325,785,402),(415,417,785,808),(415,818,785,902)]:box(rect,10,PANEL,(85,85,95))
        for k,label in enumerate(['关注','推荐','同城']):text(482+k*117,359,label,24,MUTED,'mm')
        for k,label in enumerate(['首页','朋友','消息','我']):text(462+k*92,857,label,24,MUTED,'mm')
        text(439,438,'页面内容',30);text(439,486,'内容区域',20,MUTED)
        for j in range(2):
            y=532+j*119;box((437,y,763,y+98),9)
            box((451,y+16,516,y+81),6,PANEL,(108,108,118))
            d.polygon([(476*S,(y+34)*S),(476*S,(y+63)*S),(498*S,(y+48)*S)],fill=MUTED)
            line([(534,y+30),(725-j*31,y+30)],MUTED)
            line([(534,y+55),(682+j*22,y+55)])
        text(600,778,'应用',18,MUTED,'mm')
        box((547,920,653,925),2,EDGE,EDGE)
        for label,y,local in [('顶部 Tab',365,102),('中间内容',600,355),('底部 Tab',857,600)]:
            text(155,y,label,28,WHITE,'lm');line([(300,y),(367,y),(384,260+local)])
        ready=t>=.7
        box((940,285,1790,459),14,PANEL,EDGE,2)
        box((968,317,1038,387),12,PANEL,GREEN,2)
        # USB plug icon, with explicit connection status alongside it.
        box((990,334,1016,365),4,PANEL,GREEN,2)
        line([(997,326),(997,334)],GREEN);line([(1009,326),(1009,334)],GREEN)
        line([(1003,365),(1003,378)],GREEN)
        text(1073,314,'设备已连接' if ready else '正在连接设备',30)
        text(1073,374,'开始探索' if ready else '连接设备',28,GREEN if ready else MUTED)
        text(945,507,'设备连接',28)
        text(1780,507,'已就绪' if ready else '连接中',26,GREEN,'rt')
        box((944,561,1790,628),10)
        text(969,595,'USB',26,WHITE,'lm')
        line([(1060,595),(1650,595)])
        q=smooth(t,.05,.7);x=1060+590*q
        line([(1060,595),(x,595)],GREEN)
        d.ellipse(((x-5)*S,590*S,(x+5)*S,600*S),fill=GREEN)
        text(1765,595,'设备',26,WHITE,'rm')
        text(945,686,'应用页面',28)
        box((944,740,1790,807),10)
        text(969,774,'应用',26,WHITE,'lm')
        text(1765,774,'准备探索' if ready else '等待连接',26,GREEN if ready else MUTED,'rm')
        line([(945,852),(1789,852)],(47,47,54))
        text(945,884,'连接设备  →  设备就绪  →  开始探索',24,MUTED)
        line([(0,1008),(1920,1008)],(51,51,59),1)
        return im.resize((1920,1080),Image.Resampling.LANCZOS)
    frame(1.2).save(out/'connection-native-preview.png')
    if not preview:write_bridge(out,name,duration,frame)
