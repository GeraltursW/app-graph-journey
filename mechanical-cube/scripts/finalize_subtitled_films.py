"""Deliver both films with a unified YaHei subtitle band and natural mechanical voice."""
import argparse,json,math,re,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def run(args,cwd=None):subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',*map(str,args)],cwd=cwd,check=True)
def norm(s):return re.sub(r'[^\w\u4e00-\u9fff]','',s)
def stamp(t,ass=False):
    units=round(t*(100 if ass else 1000));base=100 if ass else 1000
    sec,rem=divmod(units,base);minute,sec=divmod(sec,60);hour,minute=divmod(minute,60)
    return f'{hour}:{minute:02}:{sec:02}.{rem:02}' if ass else f'{hour:02}:{minute:02}:{sec:02},{rem:03}'

def caption_chunks(spec,start,duration):
    parts=spec.get('parts')
    if not parts:
        text=spec['text'].strip('。，')
        if len(text)<=27:parts=[text]
        else:
            clauses=[x.strip('。，') for x in re.split(r'(?<=[，。])',text) if x.strip('。，')]
            parts=[]
            for clause in clauses:
                if parts and len(parts[-1])+len(clause)+1<=27:parts[-1]+='，'+clause
                else:parts.append(clause)
    weights=[max(1,len(norm(x))) for x in parts];total=sum(weights);cursor=0
    word_info=None
    if spec.get('words'):
        words=json.loads((ROOT/spec['words']).read_text(encoding='utf-8'))
        if norm(spec['text'])==''.join(norm(w['text']) for w in words):
            word_info=[];position=0
            for w in words:
                n=len(norm(w['text']));word_info.append((position,position+n,w['offset']/1e7,(w['offset']+w['duration'])/1e7));position+=n
    cues=[]
    for text,weight in zip(parts,weights):
        if word_info:
            group=[w for w in word_info if w[1]>cursor and w[0]<cursor+weight]
            begin=start+group[0][2];end=start+group[-1][3]+.14
        else:begin=start+duration*cursor/total;end=start+duration*(cursor+weight)/total
        cues.append({'start':round(begin,3),'end':round(end,3),'text':text})
        cursor+=weight
    return cues

def write_captions(out,name,cues,cfg):
    cues=sorted(cues,key=lambda c:c['start'])
    for i,c in enumerate(cues[:-1]):c['end']=min(c['end'],cues[i+1]['start']-.02)
    srt='\n\n'.join(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}' for i,c in enumerate(cues))+'\n'
    header='[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n'
    header+=f'Style: Caption,{cfg["font_family"]},{cfg["subtitle_size"]},&H00F5F4F4,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,2,90,90,20,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'
    body=''.join(f'Dialogue: 0,{stamp(c["start"],True)},{stamp(c["end"],True)},Caption,,0,0,0,,{{\\fad(70,70)}}{c["text"]}\n' for c in cues)
    (out/f'{name}.zh-CN.srt').write_text(srt,encoding='utf-8-sig')
    (out/f'{name}.zh-CN.ass').write_text(header+body,encoding='utf-8-sig')
    return cues

def prepare_caption_files(out,cfg,manifest):
    script=json.loads((ROOT/'config/main_caption_script.json').read_text(encoding='utf-8'))
    common=[]
    for s in script['segments']:common+=caption_chunks(s,s['start'],s['duration'])
    chapter=manifest['segments'][0];chapter_start=60.9;mechanical_start=61.4+chapter['slot_duration']-1
    end=mechanical_start+manifest['mechanical_duration'];total=end+10
    main=common.copy();mech=common.copy()
    for s in script['outro']:main+=caption_chunks(s,61.4+s['start'],s['duration'])
    mech+=caption_chunks(chapter,chapter_start+chapter['voice_offset'],chapter['audio_duration'])
    for s in manifest['segments'][1:]:mech+=caption_chunks(s,mechanical_start+s['start']+s['voice_offset'],s['audio_duration'])
    for s in script['outro']:mech+=caption_chunks(s,end+s['start'],s['duration'])
    write_captions(out,'application-knowledge-graph-and-data',main,cfg)
    write_captions(out,'application-knowledge-graph-with-mechanical-replay',mech,cfg)
    timeline={'chapter_start':chapter_start,'chapter_duration':chapter['slot_duration'],'mechanical_start':mechanical_start,'mechanical_duration':manifest['mechanical_duration'],'outro_start':end,'duration':total,'main_duration':71.4,'font':cfg['font_family'],'subtitle_band':[1008,1080],'picture_region':[64,0,1856,1008],'audio_time_stretch':1.0,'main_caption_count':len(main),'mechanical_caption_count':len(mech)}
    (out/'delivery-timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return timeline

def audio(out,manifest,timeline):
    # Reuse current approved narration before the mechanical chapter.
    run(['-i',ROOT/'assets/audio/main-narration-first-62s.flac','-i',ROOT/'assets/audio/page-exploration-voiceover.wav','-i',ROOT/'assets/audio/scenario-path-voiceover.wav',
         '-filter_complex',
         '[0:a]asplit=3[x][y][z];[x]atrim=end=6.6,asetpts=PTS-STARTPTS[a];[y]atrim=start=13.2:end=26,asetpts=PTS-STARTPTS[c];[z]atrim=start=45:end=61.4,asetpts=PTS-STARTPTS[e];'
         '[1:a]apad=whole_dur=6.6,atrim=end=6.6,asetpts=PTS-STARTPTS,volume=0.8[b];[2:a]apad=whole_dur=19,atrim=end=19,asetpts=PTS-STARTPTS,volume=0.8[d];[a][b][c][d][e]concat=n=5:v=0:a=1[n]',
         '-map','[n]','-ar','48000','-ac','2','-c:a','pcm_s24le',out/'approved-main-narration.wav'])
    total=timeline['duration'];chapter=manifest['segments'][0]
    inputs=['-i',out/'approved-main-narration.wav','-i',ROOT/chapter['audio'],'-i',out/'mechanical/mechanical-natural-voiceover.wav','-i',ROOT/'releases/latest/analytics-outro-voiceover.wav']
    delays=[0,timeline['chapter_start']+chapter['voice_offset'],timeline['mechanical_start'],timeline['outro_start']]
    filters=[f'[{i}:a]aresample=48000,adelay={round(t*1000)}:all=1[n{i}]' for i,t in enumerate(delays)]
    filters.append(f'[n0][n1][n2][n3]amix=inputs=4:duration=longest:normalize=0,apad=whole_dur={total},atrim=duration={total}[n]')
    run([*inputs,'-filter_complex',';'.join(filters),'-map','[n]','-c:a','pcm_s24le',out/'narration-natural.wav'])
    repeat=math.ceil((total-.6)/29.4);labels=''.join(f'[m{i}]' for i in range(repeat))
    filters=[f'[0:a]atrim=end=30,asetpts=PTS-STARTPTS,asplit={repeat}{labels}'];last='m0'
    for i in range(1,repeat):filters.append(f'[{last}][m{i}]acrossfade=d=0.6:c1=qsin:c2=qsin[j{i}]');last=f'j{i}'
    filters.append(f'[{last}]atrim=duration={total},volume=0.7,afade=t=in:st=0:d=0.12,afade=t=out:st={total-1.5}:d=1.5[m]')
    run(['-i',ROOT/'assets/audio/music-first-30s.flac','-filter_complex',';'.join(filters),'-map','[m]','-c:a','pcm_s24le',out/'music-loop.wav'])
    run(['-i',out/'narration-natural.wav','-i',out/'music-loop.wav','-filter_complex','[0:a][1:a]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.891:level=0:latency=1[a]','-map','[a]','-ar','48000','-ac','2','-c:a','pcm_s24le',out/'final-mix.wav'])

def burn(source,audio_path,out,name,total):
    # Reserve a real subtitle band instead of covering phones, trees or charts.
    vf=f'scale=1792:1008:flags=lanczos,pad=1920:1080:64:0:color=0x09090b,drawbox=x=0:y=1008:w=1920:h=1:color=0x33333b:t=fill,ass={name}.zh-CN.ass'
    inputs=['-i',source]
    if audio_path:inputs+=['-i',audio_path]
    # Leave encoding headroom for AAC peaks after the mixed narration limiter.
    run([*inputs,'-vf',vf,'-map','0:v:0','-map','1:a:0' if audio_path else '0:a:0','-t',total,'-r','60','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-c:a','aac' if audio_path else 'copy',*(['-af','volume=0.88','-b:a','192k'] if audio_path else []),'-movflags','+faststart',out/f'{name}.mp4'],cwd=out)

def standalone_picture(source,out):
    # Rebuild this outro too, so the old serif mechanical labels cannot flash
    # during its first second. The original continuous music is stream-copied.
    target=out/'main-master-unsubtitled.mp4'
    run(['-i',source,'-i',out/'outro/analytics-outro-clean.mp4','-filter_complex',
         '[0:v]trim=end=61.4,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=0.6,fps=60,settb=AVTB,setsar=1[a];[1:v]fps=60,settb=AVTB,setsar=1[b];[a][b]xfade=transition=fade:duration=0.6:offset=61.4,format=yuv420p[v]',
         '-map','[v]','-map','0:a:0','-t','71.4','-r','60','-c:v','libx264','-preset','fast','-crf','16','-c:a','copy','-movflags','+faststart',target])
    return target

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--subtitles-only',action='store_true')
    p.add_argument('--main-source',type=Path,default=ROOT/'releases/iterations/13-main-pre-subtitles-v1.8.1.mp4')
    p.add_argument('--mechanical-source',type=Path,default=ROOT/'releases/iterations/14-mechanical-pre-subtitles-v1.8.1.mp4')
    a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    cfg=json.loads((ROOT/'config/final_delivery.json').read_text(encoding='utf-8'));manifest=json.loads((ROOT/'assets/audio/mechanical-natural/manifest.json').read_text(encoding='utf-8'))
    timeline=prepare_caption_files(out,cfg,manifest)
    if a.subtitles_only:return
    audio(out,manifest,timeline)
    run(['-i',a.mechanical_source.resolve(),'-i',out/'mechanical/chapter-natural-clean.mp4','-i',out/'mechanical/mechanical-natural-clean.mp4','-i',out/'outro/analytics-outro-clean.mp4',
         '-filter_complex',f'[0:v]trim=end=61.4,setpts=PTS-STARTPTS,fps=60,settb=AVTB,setsar=1[a];[1:v]setpts=PTS-STARTPTS,fps=60,settb=AVTB,setsar=1[b];[2:v]setpts=PTS-STARTPTS,fps=60,settb=AVTB,setsar=1[c];[3:v]setpts=PTS-STARTPTS,fps=60,settb=AVTB,setsar=1[d];[a][b]xfade=transition=fade:duration=0.5:offset=60.9[ab];[ab][c]xfade=transition=fade:duration=0.5:offset={timeline["mechanical_start"]}[abc];[abc][d]concat=n=2:v=1:a=0,format=yuv420p[v]',
         '-map','[v]','-an','-t',timeline['duration'],'-r','60','-c:v','libx264','-preset','fast','-crf','16','-movflags','+faststart',out/'mechanical-master-clean.mp4'])
    burn(standalone_picture(a.main_source.resolve(),out),None,out,'application-knowledge-graph-and-data',71.4)
    burn(out/'mechanical-master-clean.mp4',out/'final-mix.wav',out,'application-knowledge-graph-with-mechanical-replay',timeline['duration'])
    print('FINAL_SUBTITLED_FILMS_COMPLETE',flush=True)

if __name__=='__main__':main()
