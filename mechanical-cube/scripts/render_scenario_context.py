"""Render the scene-library -> temporal context preview at native 1080p/60 fps.

Pillow motion graphics; Y-axis perspective projection for the four time lanes.
Narration stays at source rate. Outputs a clean master, captioned MP4, SRT/ASS.
"""
import argparse,json,math,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from finalize_subtitled_films import caption_chunks,write_captions
from render_student_case import StudentScene
from video_fonts import chinese_font

ROOT=Path(__file__).resolve().parents[1]
S=1.5;W,H=1920,1080;FPS=60
BG=(9,9,11);PANEL=(15,15,18);WHITE=(244,244,245);MUTED=(163,163,173);EDGE=(65,65,75)
GREEN=(74,222,128);AMBER=(251,191,80);DARKGREEN=(22,48,33)
def smooth(t,a,b):
    v=max(0,min(1,(t-a)/(b-a)));return v*v*(3-2*v)
def mix(a,b,u):return tuple(round(x+(y-x)*u) for x,y in zip(a,b))
def lerp(a,b,u):return a+(b-a)*u
def run(args):subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',*map(str,args)],check=True)

class Renderer:
    def __init__(self,manifest,out):
        self.manifest=manifest;self.out=out;self.generic=manifest.get('generic_cases',False);self.model_copy=manifest.get('model_copy',{})
        self.font={n:ImageFont.truetype(chinese_font(),round(n*S),index=1 if self.model_copy and Path(chinese_font()).name.startswith('STHeiti') else 0) for n in (12,14,16,18,20,22,24,28,30,32,36)}
        self.bold={n:ImageFont.truetype(chinese_font(True),round(n*S),index=1 if self.model_copy and Path(chinese_font(True)).name.startswith('STHeiti') else 0) for n in (24,28,30,32,36)}
        self.cube=Image.open(out/'mechanical-reference.png').convert('RGB').crop((0,0,780,720)).resize((round(380*S),round(351*S)),Image.Resampling.LANCZOS)
        self.base=Image.new('RGB',(W,H),BG)
        self.text_alpha=1
        self.old_frames={}
        self.student=StudentScene(self,json.loads((ROOT/'config/student_a_case.json').read_text(encoding='utf-8')))
        self.captions=[]
        for s in manifest['stages']:
            self.captions+=caption_chunks(s,s['start']+s['voice_offset'],s['audio_duration'])
    def line(self,a,b,c=EDGE,width=1,alpha=1):
        self.d.line([tuple(round(v*S) for v in a),tuple(round(v*S) for v in b)],fill=mix(BG,c,alpha),width=max(1,round(width*S)))
    def text(self,x,y,body,size=18,c=WHITE,alpha=1,anchor='lt',bold=False):
        alpha*=self.text_alpha
        if alpha>0:self.d.text((round(x*S),round(y*S)),body,font=self.bold[size] if bold else self.font[size],fill=mix(BG,c,alpha),anchor=anchor)
    def rect(self,box,fill=PANEL,edge=EDGE,r=7,alpha=1,width=1):
        self.d.rounded_rectangle(tuple(round(v*S) for v in box),radius=round(r*S),fill=mix(BG,fill,alpha),outline=mix(BG,edge,alpha) if edge else None,width=round(width*S))
    def dot(self,x,y,r=4,c=GREEN,alpha=1):
        self.d.ellipse(tuple(round(v*S) for v in (x-r,y-r,x+r,y+r)),fill=mix(BG,c,alpha))
    def arrow(self,a,b,c=GREEN,alpha=1,width=2):
        self.line(a,b,c,width,alpha);theta=math.atan2(b[1]-a[1],b[0]-a[0])
        for delta in (-.5,.5):self.line(b,(b[0]-8*math.cos(theta+delta),b[1]-8*math.sin(theta+delta)),c,width,alpha)
    def curve(self,a,b,c=GREEN,p=1,alpha=1):
        if p<=0:return
        pts=[]
        for i in range(max(2,round(60*p))):
            v=i/59;x=lerp(a[0],b[0],v);y=lerp(a[1],b[1],smooth(v,0,1));pts.append((x,y))
        for x,y in zip(pts,pts[1:]):self.line(x,y,c,1.5,alpha)
        self.dot(*pts[-1],4,c,alpha)
    def card(self,x,y,label,w=130,h=66,active=True,alpha=1,sub=None):
        self.rect((x-w/2,y-h/2,x+w/2,y+h/2),DARKGREEN if active else PANEL,GREEN if active else EDGE,6,alpha)
        self.dot(x-w/2+13,y-h/2+13,3,GREEN if active else MUTED,alpha)
        self.text(x,y-4 if sub else y,label,18,WHITE,alpha,'mm')
        if sub:self.text(x,y+19,sub,12,MUTED,alpha,'mm')
    def row(self,points,labels,u=1,w=130,h=66,active=True):
        for a,b in zip(points,points[1:]):self.arrow((a[0]+w/2+6,a[1]),(b[0]-w/2-6,b[1]),GREEN if active else EDGE,u)
        for p,label in zip(points,labels):self.card(*p,label,w,h,active,u)
    def phone(self,x,y,w=180,h=320,alpha=1,complete=True):
        self.rect((x-w/2,y,x+w/2,y+h),BG,(210,210,216),12,alpha,2)
        self.line((x-14,y+15),(x+14,y+15),MUTED,2,alpha)
        self.text(x,y+43,'视频详情',18,WHITE,alpha,'mt')
        for j in range(3):
            yy=y+94+j*48
            self.rect((x-w/2+18,yy,x+w/2-18,yy+31),PANEL,EDGE,3,alpha)
            self.line((x-w/2+30,yy+15),(x+w/2-30,yy+15),MUTED,1,alpha)
        self.line((x-w/2+18,y+h-50),(x+w/2-18,y+h-50),EDGE,1,alpha)
        for dx in (-50,0,50):self.dot(x+dx,y+h-28,3,GREEN if dx==50 and complete else MUTED,alpha)
    def title(self,i):
        body_alpha=self.text_alpha;self.text_alpha=1
        self.text(48,26,'应用知识图谱  /  场景演进',16,MUTED)
        self.text(1232,27,self.model_copy.get('header','SCENARIO → CONTEXT'),12,MUTED,anchor='rt')
        self.line((48,60),(1232,60),EDGE)
        self.text_alpha=body_alpha
        self.text(48,90,self.manifest['stages'][i]['title'],32,bold=True)
    def stage(self,i,u):
        duration=self.manifest['stages'][i]['duration']
        stage_id=self.manifest['stages'][i]['id']
        # Let outgoing labels finish fading before incoming labels appear.
        # Geometry can dissolve continuously without doubled Chinese characters.
        self.text_alpha=(smooth(u,.25,.7) if i else 1)*(1-smooth(u,duration-.4,duration) if i<len(self.manifest['stages'])-1 else 1)
        self.im=self.base.copy();self.d=ImageDraw.Draw(self.im);self.title(i)
        if stage_id=='single':
            move=smooth(u,1.4,duration-.3);px=lerp(260,175,move);pw=lerp(190,152,move)
            self.phone(px,198,pw,330-45*move)
            self.dot(px-53,164,4);self.text(px-39,164,'复现通过',18,GREEN,anchor='lm')
            self.text(px,554,'实验室手机 · LAB-01',16,MUTED,anchor='mt')
            points=[(lerp(515+j*209,493+j*226,move),332-20*move) for j in range(4)]
            self.row(points,['ROOT','我的页面','我的喜欢','视频详情'],smooth(u,.15,1.15),w=146,h=74)
            self.curve((px+pw/2+10,380),(points[0][0]-82,points[0][1]),p=smooth(u,.6,1.5))
            self.text(812,212,('一条正确路径，一个可复用测试用例' if self.generic else '一条正确路径，一个可复用场景'),22,anchor='mt')
            self.text(812,438,'识别 → 执行 → 验证',20,MUTED,anchor='mt')
            self.rect((665,493,957,538),DARKGREEN,(39,78,52),5)
            self.text(811,516,'仅保留验证成功的操作路径',16,GREEN,anchor='mm')
        elif stage_id=='library':
            self.text(48,156,'多个用例 → 场景库' if self.generic else '场景库',20);self.text(888,156,'应用知识图谱',20)
            names=['喜欢视频浏览','内容搜索','消息交互','推荐浏览','标签切换','列表筛选']
            for k,name in enumerate(names):
                x=48+(k%2)*342;y=208+(k//2)*116;show=smooth(u,.1+k*.38,.7+k*.38);dy=20*(1-show)
                self.rect((x,y+dy,x+316,y+98+dy),PANEL,EDGE,7,show)
                self.text(x+17,y+15+dy,name,18,alpha=show)
                for n in range(5):
                    xx=x+24+n*61
                    if n<4:self.line((xx,y+66+dy),(xx+61,y+66+dy),GREEN,1.5,show*.65)
                    self.dot(xx,y+66+dy,4,GREEN,show)
            nodes=[(1035,220),(907,314),(1035,314),(1163,314),(862,415),(945,415),(1035,415),(1110,415),(1200,415),(907,514),(1035,514),(1163,514)]
            edges=[(0,1),(0,2),(0,3),(1,4),(1,5),(2,6),(3,7),(3,8),(5,9),(6,10),(7,11)]
            for k,(a,b) in enumerate(edges):
                lit=smooth(u,1+k*.18,1.6+k*.18)
                self.line(nodes[a],nodes[b],mix(EDGE,GREEN,lit),1.8)
            for k,(x,y) in enumerate(nodes):
                lit=smooth(u,.7+k*.18,1.3+k*.18);self.dot(x,y,5,mix(EDGE,GREEN,lit))
            self.text(1035,193,'ROOT',14,MUTED,anchor='mb')
            self.text(1040,562,'已验证路径逐步覆盖',16,GREEN,anchor='mt')
            flow=smooth(u,2.3,3.4)
            self.curve((712,365),(826,365),p=flow)
        elif stage_id=='extract':
            self.text(48,156,'大数据分析 × 应用知识图谱',18,MUTED)
            xs=[213,421,629,837,1045];labels=[['我的页面','列表','滑动','内容','播放'],['首页','列表','滑动','内容','分享'],['搜索页','列表','滑动','内容','收藏']]
            for r,ls in enumerate(labels):
                yy=237+r*90;highlight=smooth(u,.8+r*.25,1.7+r*.25)
                for j in range(4):self.line((xs[j]+70,yy),(xs[j+1]-70,yy),GREEN if j in (1,2) else EDGE,1.5)
                for j,l in enumerate(ls):
                    active=j in (1,2,3)
                    self.card(xs[j],yy,l,140,58,False)
                    if active:self.card(xs[j],yy,l,140,58,True,highlight)
                self.text(72,yy,'场景 '+chr(65+r),14,MUTED,anchor='mm')
            lift=smooth(u,2.7,4.3)
            for j in range(3):
                x=xs[j+1];self.curve((x,448),(x,516),p=lift,alpha=.7)
            if lift:
                points=[(x,550-15*(1-lift)) for x in xs[1:4]]
                self.row(points,['进入列表','连续滑动','打开内容'],lift,w=146,h=62)
            self.text(1127,535,'典型',18,GREEN,lift,anchor='mt');self.text(1127,563,'操作序列',18,GREEN,lift,anchor='mt')
        elif stage_id=='student_plan':
            self.student.plan(u,duration)
        elif stage_id.startswith('student_'):
            self.student.play(stage_id,u,duration)
        elif stage_id=='temporal':
            self.text(48,156,('场景库 × 网络 × 应用状态 × 设备负载' if self.generic else '大学生 A 的用例 × 网络 × 应用状态 × 设备负载'),18,MUTED)
            self.text(1232,156,('典型序列与影响因子按时序对齐' if self.generic else '基于该用例的故障情境示例'),14,MUTED,anchor='rt')
            # Keep STEP 12 lanes fixed; retain the time cursor and condition highlights.
            perspective=0 if self.generic else math.sin(math.pi*smooth(u,.3,3.2))
            theta=math.radians(-20)*perspective
            def p(x,y,z=0):
                xx=x-700;zz=(z-100)*perspective;c=math.cos(theta);s=math.sin(theta)
                xr=xx*c+zz*s;zr=-xx*s+zz*c;f=1550/(1550+zr)
                return (700+xr*f,365+(y-365)*f)
            xs=[374,620,866,1112];ys=[245,328,411,494]
            names=['操作序列','网络状态','应用状态','设备负载']
            values=[(['进入列表','连续滑动','切换后台','打开内容'] if self.generic else ['喜欢列表','上滑 3 次','切换后台','打开视频14']),['稳定','弱网','弱网','弱网'],['前台','前台','后台','恢复前台'],['低负载','升高','高负载','高负载']]
            for j in range(3,-1,-1):
                z=j*68;y=ys[j];quad=[p(x,yy,z) for x,yy in [(300,y-29),(1190,y-29),(1190,y+29),(300,y+29)]]
                self.d.polygon([(round(x*S),round(y*S)) for x,y in quad],fill=(13+j,13+j,17+j),outline=EDGE,width=round(S))
                label=p(80,y,z);self.text(*label,names[j],18,WHITE,anchor='lm')
                for k in range(3):self.line(p(xs[k]+56,y,z),p(xs[k+1]-56,y,z),GREEN if j==0 else EDGE,1.5)
                for k,x in enumerate(xs):
                    q=p(x,y,z);self.text(*q,values[j][k],18,WHITE,anchor='mm');self.dot(q[0]-68,q[1],3,GREEN if j==0 else MUTED)
            for k,x in enumerate(xs):self.text(x,192,'t'+str(k),14,MUTED,anchor='mt')
            scan=smooth(u,3.05,6.25);cursor=lerp(xs[0]-90,xs[3],scan)
            if u>3.05:
                self.line((cursor,217),(cursor,525),GREEN,1.6,.85)
                self.dot(cursor,209,4)
                for yy in ys:self.dot(cursor,yy,5,GREEN,.8)
            focus=smooth(u,6.05,6.65)
            if focus:
                self.rect((1030,207,1194,529),(35,29,17),AMBER,5,focus)
                for j,y in enumerate(ys):self.text(1112,y,values[j][3],18,WHITE,focus,'mm')
                self.line((1112,532),(1112,550),AMBER,1.5,focus)
                self.dot(1112,553,4,AMBER,focus)
                self.text(1230,573,'故障记录：内容响应异常',18,AMBER,focus,'rt')
                self.text(500,570,'锁定故障前后的操作与条件',18,MUTED,focus,'mt')
        else:
            appear=smooth(u,.15,.8)
            self.rect((48,190,734,558),PANEL,EDGE,10)
            self.text(76,216,self.model_copy.get('card_title',('可执行场景 · 故障上下文' if self.generic else '大学生 A · 可执行场景')),24,bold=True)
            self.text(707,220,self.model_copy.get('status','上下文已重建'),16,GREEN,anchor='rt')
            self.line((76,263),(706,263),EDGE)
            fields=[('操作序列',('进入列表 → 连续滑动 → 打开内容' if self.generic else '喜欢列表 → 上滑3次 → 打开视频14')),('影响因子','弱网 · 后台恢复 · 高负载'),('相对时序',('条件变化 → 打开内容 → 检查响应' if self.generic else '条件变化 → 打开视频 → 检查响应')),('验证目标',self.model_copy.get('goal',('目标内容的响应异常是否重现' if self.generic else '目标视频的响应异常是否重现')))]
            for k,(a,b) in enumerate(fields):
                yy=293+k*63;show=smooth(u,.25+k*.22,.85+k*.22)
                self.text(77,yy,a,16,MUTED,show)
                self.text(209,yy,b,20,WHITE,show)
                if k<3:self.line((77,yy+40),(706,yy+40),(35,35,42),1,show)
            self.im.paste(self.cube,(round(854*S),round(179*S)))
            self.d=ImageDraw.Draw(self.im)
            link=smooth(u,2.5,4)
            self.curve((749,367),(866,367),p=link)
            self.text(801,330,'下发',16,GREEN,link,'mm')
            self.text(1044,548,('Test Cube / 实验室手机' if self.generic else '机械手 / 实验室手机'),20,WHITE,appear,'mt')
            self.text(1044,581,'进入复现验证',16,GREEN,link,'mt')
        return self.im
    def frame(self,t,subtitles=False):
        stages=self.manifest['stages'];i=max(j for j,s in enumerate(stages) if t>=s['start']);u=t-stages[i]['start']
        current=self.stage(i,u)
        if i and u<.7:
            if i not in self.old_frames:self.old_frames[i]=self.stage(i-1,stages[i-1]['duration']-.01).copy()
            current=Image.blend(self.old_frames[i],current,smooth(u,0,.7))
        self.im=current;self.d=ImageDraw.Draw(current);self.text_alpha=1
        self.line((48,620),(1232,620),(38,38,45))
        phase=({'single':0,'library':2,'extract':3,'temporal':4,'context':5} if self.generic else {'single':0,'library':1,'extract':2,'temporal':4,'context':5}).get(stages[i]['id'],3)
        for j,label in enumerate(['单个用例','多个用例','场景库','典型操作序列','时序建模',self.model_copy.get('footer','故障上下文')] if self.generic else ['单场景复现','场景库建设','操作序列提取','AI 场景示例','影响因子时序','故障上下文']):
            x=115+j*210;active=j<=phase
            self.dot(x-57,647,3,GREEN if active else EDGE)
            self.text(x-43,647,label,14,WHITE if j==phase else MUTED,anchor='lm')
        self.line((0,672),(1280,672),EDGE)
        if subtitles:
            for c in self.captions:
                if c['start']<=t<=c['end']:self.text(640,696,c['text'],24,WHITE,anchor='mm')
        return current

def audio(manifest,out):
    args=[];filters=[]
    for i,s in enumerate(manifest['stages']):
        args+=['-i',ROOT/s['audio']];filters.append(f'[{i}:a]adelay={round((s["start"]+s["voice_offset"])*1000)}:all=1[a{i}]')
    labels=''.join(f'[a{i}]' for i in range(len(manifest['stages'])))
    filters.append(f'{labels}amix=inputs={len(manifest["stages"])}:duration=longest:normalize=0,apad=whole_dur={manifest["duration"]},atrim=duration={manifest["duration"]}[n]')
    run([*args,'-filter_complex',';'.join(filters),'-map','[n]','-c:a','pcm_s24le',out/'narration.wav'])
    total=manifest['duration']
    repeats=math.ceil((total-.6)/29.4)
    music=[f'[1:a]asplit={repeats}'+''.join(f'[m{i}]' for i in range(repeats))]
    last='m0'
    for i in range(1,repeats):music.append(f'[{last}][m{i}]acrossfade=d=0.6:c1=qsin:c2=qsin[j{i}]');last=f'j{i}'
    music.append(f'[{last}]atrim=duration={total},volume=0.36,afade=t=in:d=0.5,afade=t=out:st={total-1.6}:d=1.6[m];[0:a][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.85:level=0:latency=1[a]')
    run(['-i',out/'narration.wav','-i',ROOT/'assets/audio/music-first-30s.flac','-filter_complex',
         ';'.join(music),
         '-map','[a]','-c:a','pcm_s24le',out/'mix.wav'])

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--stills-only',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((ROOT/'assets/audio/scenario-context/manifest.json').read_text(encoding='utf-8'))
    source=ROOT/'releases/latest/mechanical-natural-clean.mp4'
    if not (a.out/'mechanical-reference.png').exists():run(['-ss',1,'-i',source,'-frames:v',1,a.out/'mechanical-reference.png'])
    renderer=Renderer(manifest,a.out)
    cfg={'font_family':'Microsoft YaHei','subtitle_size':36}
    write_captions(a.out,'scenario-context-preview',renderer.captions,cfg)
    for i,s in enumerate(manifest['stages']):
        dt=min(s['duration']-.7,7 if s['id']=='temporal' else 4.4)
        renderer.frame(s['start']+dt,True).save(a.out/f'preview-{i+1}.png')
    temporal=next(s for s in manifest['stages'] if s['id']=='temporal')
    renderer.frame(temporal['start']+1.65,True).save(a.out/'preview-y-axis.png')
    for s in manifest['stages']:
        if s['id'].startswith('student_'):
            for u in (1.1,2.2,3.4,4.7):
                if u<s['duration']-.4:renderer.frame(s['start']+u,True).save(a.out/f'{s["id"]}-{u:.1f}.png')
    (a.out/'timeline.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if a.stills_only:return
    audio(manifest,a.out)
    command=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(a.out/'scenario-context-clean.mp4')]
    process=subprocess.Popen(command,stdin=subprocess.PIPE)
    try:
        frames=round(manifest['duration']*FPS)
        for n in range(frames):
            process.stdin.write(renderer.frame(n/FPS).tobytes())
            if n%(FPS*3)==0:print(f'RENDER {n/FPS:.1f}/{manifest["duration"]:.1f}s',flush=True)
    finally:process.stdin.close()
    if process.wait()!=0:raise RuntimeError('Video encode failed')
    # ASS uses the same native 1080p font and the same separate subtitle band as the main film.
    subprocess.run(['ffmpeg','-v','error','-y','-i','scenario-context-clean.mp4','-i','mix.wav','-vf','ass=scenario-context-preview.zh-CN.ass','-map','0:v','-map','1:a','-t',str(manifest['duration']),'-c:v','libx264','-preset','fast','-crf','17','-c:a','aac','-b:a','192k','-af','volume=0.9','-movflags','+faststart','scenario-context-preview.mp4'],cwd=a.out,check=True)
    print('SCENARIO_CONTEXT_PREVIEW_COMPLETE',flush=True)

if __name__=='__main__':main()
