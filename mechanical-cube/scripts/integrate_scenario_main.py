"""Assemble the approved scene-library/student/context sequence into the full film.

Uses clean masters, two object-matching bridges, one continuous music bed and one
subtitle pass. The old mechanical introduction card is replaced by the context
handoff; every mechanical instruction remains at its original speaking rate.
"""
import argparse,json,math,subprocess
from pathlib import Path
from PIL import Image,ImageDraw
from finalize_subtitled_films import caption_chunks,write_captions

ROOT=Path(__file__).resolve().parents[1]
NAME='application-knowledge-graph-with-mechanical-replay'
BG=(9,9,11);FPS=60;SIZE=(1920,1080)
FIT='scale=1792:1008:flags=lanczos,pad=1920:1080:64:0:color=0x09090b,drawbox=x=0:y=1008:w=1920:h=1:color=0x33333b:t=fill'
def run(args,cwd=None):subprocess.run(['ffmpeg','-v','error','-y',*map(str,args)],cwd=cwd,check=True)
def smooth(t,a,b):
    u=max(0,min(1,(t-a)/(b-a)));return u*u*(3-2*u)
def boxmix(a,b,u):return tuple(round(x+(y-x)*u) for x,y in zip(a,b))

def still(source,path,time,fit=False):
    run(['-ss',time,'-i',source,*(['-vf',FIT] if fit else []),'-frames:v',1,path])
    return Image.open(path).convert('RGB')

def write_bridge(out,name,seconds,frame):
    for t in [0,seconds*.3,seconds*.6,seconds-1/FPS]:frame(t).save(out/f'{name}-{t:.2f}.png')
    process=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','60','-i','-','-an','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(out/f'{name}.mp4')],stdin=subprocess.PIPE)
    try:
        for n in range(round(seconds*FPS)):process.stdin.write(frame(n/FPS).tobytes())
    finally:process.stdin.close()
    if process.wait()!=0:raise RuntimeError(name+' encoding failed')

def bridges(out,head,scene,cfg,manifest):
    mechanical=ROOT/'releases/latest/mechanical-natural-clean.mp4'
    previous=still(head,out/'lab-last.png',cfg['head_end']-1/FPS,True)
    first=still(scene,out/'scenario-first.png',0)
    last=still(scene,out/'scenario-last.png',manifest['duration']-1/FPS)
    next_frame=still(mechanical,out/'mechanical-first.png',0,True)
    cube_source=still(mechanical,out/'mechanical-reference.png',1).crop((0,0,780,720))
    empty=Image.new('RGB',SIZE,BG)
    # Move the full phone silhouette from the laboratory shot into the new shot.
    old_box=(455,210,750,762);new_box=(247,297,533,792)
    phone=previous.crop(old_box);masked=previous.copy();ImageDraw.Draw(masked).rectangle(old_box,fill=BG)
    duration=cfg['entry_bridge_duration']
    def enter(t):
        q=t/max(1/FPS,duration-1/FPS)
        im=Image.blend(masked,empty,smooth(q,0,.6))
        rect=boxmix(old_box,new_box,smooth(q,0,.6))
        im.paste(phone.resize((rect[2]-rect[0],rect[3]-rect[1]),Image.Resampling.LANCZOS),(rect[0],rect[1]))
        return Image.blend(im,first,smooth(q,.6,1))
    write_bridge(out,'lab-to-scenario',duration,enter)
    # Expand the same cube from its context card to the original mechanical frame.
    start_box=(1281,268,1851,795);end_box=(64,0,1156,1008)
    masked_end=last.copy();ImageDraw.Draw(masked_end).rectangle(start_box,fill=BG)
    duration=cfg['exit_bridge_duration']
    def leave(t):
        q=t/max(1/FPS,duration-1/FPS)
        im=Image.blend(masked_end,empty,smooth(q,0,.55))
        rect=boxmix(start_box,end_box,smooth(q,0,.78))
        im.paste(cube_source.resize((rect[2]-rect[0],rect[3]-rect[1]),Image.Resampling.LANCZOS),(rect[0],rect[1]))
        return Image.blend(im,next_frame,smooth(q,.78,1))
    write_bridge(out,'context-to-mechanical',duration,leave)

def timing(cfg,scenario,mechanical):
    start=cfg['head_end']+cfg['entry_bridge_duration']
    exit_start=start+scenario['duration'];mech_start=exit_start+cfg['exit_bridge_duration']
    outro_start=mech_start+mechanical['mechanical_duration'];total=outro_start+cfg['outro_duration']
    return {'version':cfg['version'],'head_end':cfg['head_end'],'entry_bridge_start':cfg['head_end'],'entry_bridge_duration':cfg['entry_bridge_duration'],'scenario_start':start,'scenario_duration':scenario['duration'],
            'scenario_stages':[{**{k:s[k] for k in ['id','title','duration']},'start':start+s['start']} for s in scenario['stages']],
            'exit_bridge_start':exit_start,'exit_bridge_duration':cfg['exit_bridge_duration'],'mechanical_start':mech_start,'mechanical_duration':mechanical['mechanical_duration'],
            'outro_start':outro_start,'duration':total,'resolution':[1920,1080],'fps':60,'audio_time_stretch':1.0,'subtitle_band':[1008,1080],'font':'Microsoft YaHei'}

def captions(out,cfg,scenario,mechanical,timeline):
    script=json.loads((ROOT/'config/main_caption_script.json').read_text(encoding='utf-8'))
    cues=[]
    for s in script['segments']:cues+=caption_chunks(s,s['start'],s['duration'])
    for s in scenario['stages']:cues+=caption_chunks(s,timeline['scenario_start']+s['start']+s['voice_offset'],s['audio_duration'])
    for s in mechanical['segments'][1:]:cues+=caption_chunks(s,timeline['mechanical_start']+s['start']+s['voice_offset'],s['audio_duration'])
    for s in script['outro']:cues+=caption_chunks(s,timeline['outro_start']+s['start'],s['duration'])
    write_captions(out,NAME,cues,cfg);timeline['caption_count']=len(cues)

def sound(out,cfg,scenario,mechanical,timeline):
    run(['-i',ROOT/'assets/audio/main-narration-first-62s.flac','-i',ROOT/'assets/audio/page-exploration-voiceover.wav','-i',ROOT/'assets/audio/scenario-path-voiceover.wav',
         '-filter_complex',f'[0:a]asplit=3[x][y][z];[x]atrim=end=6.6,asetpts=PTS-STARTPTS[a];[y]atrim=start=13.2:end=26,asetpts=PTS-STARTPTS[c];[z]atrim=start=45:end={cfg["head_end"]},asetpts=PTS-STARTPTS[e];[1:a]apad=whole_dur=6.6,atrim=end=6.6,asetpts=PTS-STARTPTS,volume=0.8[b];[2:a]apad=whole_dur=19,atrim=end=19,asetpts=PTS-STARTPTS,volume=0.8[d];[a][b][c][d][e]concat=n=5:v=0:a=1[n]',
         '-map','[n]','-ar','48000','-ac','2','-c:a','pcm_s24le',out/'head-narration.wav'])
    voices=[(out/'head-narration.wav',0)]
    voices += [(ROOT/s['audio'],timeline['scenario_start']+s['start']+s['voice_offset']) for s in scenario['stages']]
    voices += [(ROOT/'releases/latest/mechanical-natural-voiceover.wav',timeline['mechanical_start']), (ROOT/'releases/latest/analytics-outro-voiceover.wav',timeline['outro_start'])]
    args=[];filters=[]
    for i,(path,delay) in enumerate(voices):
        args+=['-i',path];filters.append(f'[{i}:a]aresample=48000,adelay={round(delay*1000)}:all=1[a{i}]')
    total=timeline['duration'];labels=''.join(f'[a{i}]' for i in range(len(voices)))
    filters.append(f'{labels}amix=inputs={len(voices)}:duration=longest:normalize=0,apad=whole_dur={total},atrim=duration={total}[n]')
    run([*args,'-filter_complex',';'.join(filters),'-map','[n]','-c:a','pcm_s24le',out/'narration.wav'])
    overlap=cfg['music_loop_crossfade'];count=math.ceil((total-overlap)/(30-overlap));labels=''.join(f'[m{i}]' for i in range(count))
    filters=[f'[0:a]atrim=end=30,asetpts=PTS-STARTPTS,asplit={count}{labels}'];last='m0'
    for i in range(1,count):filters.append(f'[{last}][m{i}]acrossfade=d={overlap}:c1=qsin:c2=qsin[j{i}]');last=f'j{i}'
    filters.append(f'[{last}]atrim=duration={total},volume={cfg["music_volume"]},afade=t=in:d=0.12,afade=t=out:st={total-1.5}:d=1.5[m]')
    run(['-i',ROOT/'assets/audio/music-first-30s.flac','-filter_complex',';'.join(filters),'-map','[m]','-c:a','pcm_s24le',out/'music-loop.wav'])
    run(['-i',out/'narration.wav','-i',out/'music-loop.wav','-filter_complex','[0:a][1:a]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.87:level=0:latency=1[a]','-map','[a]','-c:a','pcm_s24le',out/'mix.wav'])

def normalize(source,target,duration):
    run(['-i',source,'-vf',FIT,'-an','-t',duration,'-r','60','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',target])

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--scene-source',type=Path,default=ROOT/'releases/latest/scenario-context-clean.mp4')
    p.add_argument('--head-source',type=Path,default=ROOT/'releases/iterations/13-main-pre-subtitles-v1.8.1.mp4')
    p.add_argument('--bridges-only',action='store_true');a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    cfg=json.loads((ROOT/'config/main_scene_integration.json').read_text(encoding='utf-8'))
    scenario=json.loads((ROOT/'assets/audio/scenario-context/manifest.json').read_text(encoding='utf-8'))
    mechanical=json.loads((ROOT/'assets/audio/mechanical-natural/manifest.json').read_text(encoding='utf-8'))
    timeline=timing(cfg,scenario,mechanical);captions(out,cfg,scenario,mechanical,timeline)
    (out/'main-integration-timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    bridges(out,a.head_source.resolve(),a.scene_source.resolve(),cfg,scenario)
    if a.bridges_only:return
    print('BRIDGES_COMPLETE',flush=True)
    normalize(a.head_source.resolve(),out/'head-clean.mp4',cfg['head_end'])
    normalize(ROOT/'releases/latest/mechanical-natural-clean.mp4',out/'mechanical-clean.mp4',mechanical['mechanical_duration'])
    normalize(ROOT/'releases/latest/analytics-outro-typography-clean.mp4',out/'outro-clean.mp4',cfg['outro_duration'])
    parts=[out/'head-clean.mp4',out/'lab-to-scenario.mp4',a.scene_source.resolve(),out/'context-to-mechanical.mp4',out/'mechanical-clean.mp4',out/'outro-clean.mp4']
    (out/'concat.txt').write_text(''.join("file '"+str(path).replace('\\','/')+"'\n" for path in parts),encoding='utf-8')
    run(['-f','concat','-safe','0','-i',out/'concat.txt','-c','copy','-movflags','+faststart',out/'main-clean.mp4'])
    print('PICTURE_ASSEMBLED',flush=True);sound(out,cfg,scenario,mechanical,timeline)
    run(['-i','main-clean.mp4','-i','mix.wav','-vf',f'ass={NAME}.zh-CN.ass','-map','0:v','-map','1:a','-t',timeline['duration'],'-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-af',f'volume={cfg["output_gain"]}','-movflags','+faststart',NAME+'.mp4'],cwd=out)
    print('MAIN_INTEGRATION_COMPLETE',round(timeline['duration'],3),flush=True)

if __name__=='__main__':main()
