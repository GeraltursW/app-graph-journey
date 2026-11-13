"""Render the configured head sequence with natural narration and smooth joins."""
import argparse
import asyncio
import hashlib
import json
import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw
from prepare_natural_mechanical import synthesize, duration
from finalize_subtitled_films import stamp, write_captions
from integrate_scenario_main import smooth, boxmix, write_bridge
from render_page_nodes_monochrome import render_page_nodes
from render_control_exploration import render_control_exploration
from render_lab_replay_monochrome import render_lab_replay, render_lab_context_bridge
from render_student_summary import render_student_summary
from render_case_library import render_case_library
from patch_case_copy import patch_case_copy
from patch_ai_completion_label import patch_ai_completion_label
from render_vectorization_native import render_vectorization
from render_opening_native import render_opening_native
from normalize_narration import normalize_narration
from render_connection_native import render_connection_native
from remove_legacy_graph_entry import remove_legacy_graph_entry

ROOT=Path(__file__).resolve().parents[1]
NAME='head-compact-preview'


def run(args,cwd=None):
    subprocess.run(['ffmpeg','-v','error','-y',*map(str,args)],cwd=cwd,check=True)


async def prepare(cfg):
    folder=ROOT/'assets/audio/head-compact';folder.mkdir(parents=True,exist_ok=True)
    sem=asyncio.Semaphore(4)
    async def voice(shot,s):
        async with sem:
            raw=folder/(s['id']+'.mp3');wav=raw.with_suffix('.wav')
            words=raw.with_suffix('.words.json');cache=raw.with_suffix('.cache.json')
            signature=hashlib.sha256(json.dumps([cfg['voice'],'+0%',cfg['pitch'],s['text']],ensure_ascii=False).encode()).hexdigest()
            regenerate=not (raw.exists() and words.exists() and cache.exists() and json.loads(cache.read_text())['signature']==signature)
            if regenerate:
                print('VOICE',s['id'],flush=True)
                await synthesize(s['text'],cfg,raw,words)
                cache.write_text(json.dumps({'signature':signature}),encoding='utf-8')
            word_info=json.loads(words.read_text('utf-8'))
            speech_end=max((w['offset']+w['duration'])/1e7 for w in word_info)
            padding=s.get('tail_padding_after_last_word',.24)
            if regenerate or not wav.exists():run(['-i',raw,'-af',f'highpass=f=75,lowpass=f=11500,acompressor=threshold=0.16:ratio=2.2:attack=18:release=120:makeup=1.7,loudnorm=I=-16:LRA=6:TP=-1.5,aresample=48000,asetpts=N/SR/TB,atrim=end={speech_end+padding}','-ac','2','-c:a','pcm_s16le',wav])
            if 'target_lufs' in s:normalize_narration(wav,s['target_lufs'])
            length=duration(wav);window=s.get('window',shot['duration']-s['offset']-.06)
            return {**s,'shot':shot['id'],'start':shot['start']+s['offset'],'audio_duration':length,'speech_end':speech_end,'window':window,'audio':wav.relative_to(ROOT).as_posix(),'words':words.relative_to(ROOT).as_posix(),'time_stretch':1.0}
    voices=await asyncio.gather(*(voice(shot,s) for shot in cfg['shots'] for s in shot['voices']))
    manifest={'revision':cfg.get('revision'),'duration':cfg['duration'],'fps':cfg['fps'],'voice':cfg['voice'],'rate':'+0%','audio_time_stretch':1.0,'shots':cfg['shots'],'voices':voices}
    (folder/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    invalid=[(s['id'],s['audio_duration'],s['window']) for s in voices if s['audio_duration']>s['window']+.015]
    if invalid:raise ValueError('Shorten copy to fit natural-rate speech: '+repr(invalid))
    return manifest


def captions(out,cfg,manifest):
    cues=[]
    for shot in cfg['shots']:
        voices=[s for s in manifest['voices'] if s['shot']==shot['id']]
        for i,s in enumerate(voices):
            begin=shot['start'] if i==0 else s['start']
            end=voices[i+1]['start'] if i+1<len(voices) else shot['start']+shot['duration']
            cues.append({'start':begin,'end':end,'text':s['text'].strip('。，')})
    write_captions(out,NAME,[],cfg)
    ass=out/(NAME+'.zh-CN.ass');header=ass.read_text('utf-8-sig')
    body=''.join(f'Dialogue: 0,{stamp(c["start"],True)},{stamp(c["end"],True)},Caption,,0,0,0,,{c["text"]}\n' for c in cues)
    ass.write_text(header+body,encoding='utf-8-sig')
    (out/(NAME+'.zh-CN.srt')).write_text('\n\n'.join(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}' for i,c in enumerate(cues))+'\n',encoding='utf-8-sig')
    return cues


def picture_piece(source,out,name,spec):
    a,b=spec['source'];count=round(spec['duration']*60);source_count=round((b-a)*60)
    factor=(count-1)/(source_count-1)
    vf=f'trim=end_frame={source_count},setpts=(PTS-STARTPTS)*{factor},fps=60,tpad=stop_mode=clone:stop_duration=0.1,trim=end_frame={count},setsar=1'
    run(['-ss',a,'-i',source,'-vf',vf,'-an','-frames:v',count,'-r','60','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',out/(name+'.mp4')])


def final_bridge(source,mechanical,out,name,seconds):
    context=out/'13-01.mp4'
    run([*(['-sseof','-0.02','-i',context] if context.exists() else ['-ss',124.7666666667,'-i',source]),'-frames:v',1,out/'context-last.png'])
    run(['-i',mechanical,'-frames:v',1,out/'mechanical-first.png'])
    previous=Image.open(out/'context-last.png').convert('RGB')
    next_frame=Image.open(out/'mechanical-first.png').convert('RGB')
    cube=next_frame.crop((64,0,1156,1008))
    start_box=(1281,268,1851,795);end_box=(64,0,1156,1008)
    masked=previous.copy();ImageDraw.Draw(masked).rectangle(start_box,fill=(9,9,11))
    empty=Image.new('RGB',(1920,1080),(9,9,11))
    def frame(t):
        q=t/(seconds-1/60);im=Image.blend(masked,empty,smooth(q,0,.55))
        box=boxmix(start_box,end_box,smooth(q,0,.78))
        im.paste(cube.resize((box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS),(box[0],box[1]))
        return Image.blend(im,next_frame,smooth(q,.78,1))
    write_bridge(out,name,seconds,frame)


def smooth_join(previous,following,out,seconds):
    """End the outgoing shot on the next shot's first frame, without a time cut."""
    target=out/(previous.stem+'-next-first.png')
    run(['-i',following,'-frames:v',1,target])
    length=duration(previous);start=round((length-seconds)*60)/60
    result=out/(previous.stem+'-smooth.mp4')
    filters=f'[0:v]fps=60,settb=AVTB,setsar=1[a];[1:v]fps=60,settb=AVTB,setsar=1[b];[a][b]xfade=transition=fade:duration={seconds}:offset={start},trim=end_frame={round(length*60)},format=yuv420p[v]'
    run(['-i',previous,'-loop','1','-framerate','60','-i',target,'-filter_complex',filters,'-map','[v]','-an','-frames:v',round(length*60),'-r','60','-c:v','libx264','-preset','fast','-crf','17','-movflags','+faststart',result])
    return result


def context_thumbnail(source,mechanical,out,seconds):
    """Use the same server-labelled device in the context card and next shot."""
    target=out/'context-server.png'
    run(['-ss',1,'-i',mechanical,'-vf','crop=1092:1008:64:0,scale=570:527:flags=lanczos','-frames:v',1,target])
    result=out/(source.stem+'-server.mp4')
    filters='[1:v]format=rgba,fade=t=in:d=0.51:alpha=1[thumb];[0:v][thumb]overlay=x=1281:y=268:shortest=1,format=yuv420p[v]'
    run(['-i',source,'-loop','1','-framerate','60','-i',target,'-filter_complex',filters,'-map','[v]','-an','-frames:v',round(seconds*60),'-r','60','-c:v','libx264','-preset','fast','-crf','17','-movflags','+faststart',result])
    return result


def soundtrack(out,cfg,manifest):
    args=[];filters=[]
    for i,s in enumerate(manifest['voices']):
        args+=['-i',ROOT/s['audio']];filters.append(f'[{i}:a]adelay={round(s["start"]*1000)}:all=1[n{i}]')
    labels=''.join(f'[n{i}]' for i in range(len(manifest['voices'])))
    total=cfg['duration'];filters.append(labels+f'amix=inputs={len(manifest["voices"])}:duration=longest:normalize=0,apad=whole_dur={total},atrim=duration={total}[n]')
    run([*args,'-filter_complex',';'.join(filters),'-map','[n]','-c:a','pcm_s24le',out/'narration.wav'])
    count=math.ceil((total-.6)/29.4);filters=[f'[1:a]atrim=end=30,asplit={count}'+''.join(f'[m{i}]' for i in range(count))];last='m0'
    for i in range(1,count):filters.append(f'[{last}][m{i}]acrossfade=d=0.6:c1=qsin:c2=qsin[j{i}]');last=f'j{i}'
    filters.append(f'[{last}]atrim=duration={total},volume=0.36,afade=t=in:d=0.08,afade=t=out:st={total-.8}:d=0.8[m];[0:a][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.85:level=0:latency=1[a]')
    run(['-i',out/'narration.wav','-i',ROOT/'assets/audio/music-first-30s.flac','-filter_complex',';'.join(filters),'-map','[a]','-c:a','pcm_s24le',out/'mix.wav'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--source',type=Path,default=ROOT/'releases/iterations/16-source-main-v1.10-clean.mp4')
    p.add_argument('--mechanical',type=Path,default=ROOT/'releases/latest/compact-mechanical/mechanical-compact-clean.mp4')
    p.add_argument('--prepare-only',action='store_true');p.add_argument('--reuse-picture',action='store_true');a=p.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    cfg=json.loads((ROOT/'config/head_compact.json').read_text('utf-8'));cursor=0
    for shot in cfg['shots']:
        shot['start']=cursor/60;cursor+=round(shot['duration']*60)
        if 'pieces' in shot:assert round(sum(s['duration'] for s in shot['pieces'])*60)==round(shot['duration']*60)
    assert cursor==round(cfg['duration']*60)
    manifest=asyncio.run(prepare(cfg));manifest['captions']=captions(out,cfg,manifest)
    (out/'timeline.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('VOICE_READY',[(s['id'],s['audio_duration']) for s in manifest['voices']],flush=True)
    if a.prepare_only:return
    # Prepare the new opening frame before the laboratory-to-case bridge.
    case=next(s for s in cfg['shots'] if s.get('case_stage')=='single')
    if not (a.reuse_picture and (out/'09-01.mp4').exists()):
        render_case_library(a.mechanical.resolve(),out,'09-01',case['duration'],'single',case['title'])
    parts=[]
    for shot in cfg['shots']:
        for j,spec in enumerate(shot.get('pieces',[shot]),1):
            name=f'{shot["id"]}-{j:02d}';path=out/(name+'.mp4')
            if not(a.reuse_picture and path.exists()):
                if spec.get('type')=='mechanical_bridge':final_bridge(a.source.resolve(),a.mechanical.resolve(),out,name,spec['duration'])
                elif spec.get('type')=='lab_context_bridge':render_lab_context_bridge(a.source.resolve(),out,name,spec['duration'])
                elif spec.get('renderer')=='lab_replay_monochrome':render_lab_replay(a.source.resolve(),out,name,spec['duration'])
                elif spec.get('renderer')=='control_exploration':render_control_exploration(a.source.resolve(),out,name,spec['duration'],aligned_entry=cfg['shots'][1].get('renderer')=='connection_native')
                elif spec.get('renderer')=='connection_native':render_connection_native(out,name,spec['duration'])
                elif spec.get('renderer')=='opening_native':render_opening_native(out,name,spec['duration'])
                elif spec.get('renderer')=='vectorization_native':render_vectorization(a.source.resolve(),out,name,spec['duration'])
                elif spec.get('renderer')=='page_nodes_monochrome':render_page_nodes(a.source.resolve(),out,name,spec['duration'])
                elif spec.get('renderer')=='case_library':render_case_library(a.mechanical.resolve(),out,name,spec['duration'],spec['case_stage'],spec.get('title',shot['title']),spec.get('model_copy'))
                elif spec.get('renderer')=='student_summary':render_student_summary(a.source.resolve(),out,name,spec['duration'],spec['step_preview'])
                else:picture_piece(a.source.resolve(),out,name,spec)
                if shot.get('remove_legacy_graph_entry') and j==1:remove_legacy_graph_entry(out/'05-01.mp4',path,out,name)
                if spec.get('page_copy'):patch_case_copy(path,spec['page_copy'])
                if shot.get('hide_ai_completion_label'):patch_ai_completion_label(path,spec)
            parts.append(context_thumbnail(path,a.mechanical.resolve(),out,spec['duration']) if spec.get('replace_mechanical_thumbnail') else path)
        print('SHOT_READY',shot['id'],shot['duration'],flush=True)
    for i,shot in enumerate(cfg['shots'][:-1]):
        if shot.get('transition_to_next'):
            previous=out/f'{shot["id"]}-{len(shot.get("pieces",[shot])):02d}.mp4'
            following=out/f'{cfg["shots"][i+1]["id"]}-01.mp4'
            parts[parts.index(previous)]=smooth_join(previous,following,out,shot['transition_to_next'])
    (out/'concat.txt').write_text(''.join("file '"+str(p).replace('\\','/')+"'\n" for p in parts),encoding='utf-8')
    run(['-f','concat','-safe','0','-i',out/'concat.txt','-c','copy','-movflags','+faststart',out/'head-compact-clean.mp4'])
    soundtrack(out,cfg,manifest)
    run(['-i','head-compact-clean.mp4','-i','mix.wav','-vf',f'ass={NAME}.zh-CN.ass','-map','0:v','-map','1:a','-t',cfg['duration'],'-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-af','volume=0.9','-movflags','+faststart',NAME+'.mp4'],cwd=out)
    print('HEAD_COMPACT_COMPLETE',cfg['duration'],flush=True)


if __name__=='__main__':main()
