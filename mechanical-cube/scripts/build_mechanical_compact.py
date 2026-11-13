"""Create a four-step mechanical preview under 10 seconds, with natural-rate voice."""
import argparse
import asyncio
import hashlib
import json
import math
import subprocess
from pathlib import Path
from video_fonts import chinese_font
from PIL import Image, ImageDraw, ImageFont
from prepare_natural_mechanical import synthesize, duration
from finalize_subtitled_films import stamp, write_captions

ROOT = Path(__file__).resolve().parents[1]
NAME = 'mechanical-compact-preview'


def run(args, cwd=None):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *map(str, args)], cwd=cwd, check=True)


async def prepare(cfg):
    directory = ROOT / 'assets/audio/mechanical-compact'
    directory.mkdir(parents=True, exist_ok=True)
    async def voice(s):
        raw = directory / (s['id'] + '.mp3')
        wav = raw.with_suffix('.wav')
        words = raw.with_suffix('.words.json')
        cache = raw.with_suffix('.cache.json')
        signature = hashlib.sha256(json.dumps([cfg['voice'], '+0%', cfg['pitch'], s['text']], ensure_ascii=False).encode()).hexdigest()
        regenerate=not (raw.exists() and words.exists() and cache.exists() and json.loads(cache.read_text())['signature'] == signature)
        if regenerate:
            await synthesize(s['text'], cfg, raw, words)
            cache.write_text(json.dumps({'signature': signature}), encoding='utf-8')
        audio_filter = 'highpass=f=75,lowpass=f=11500,acompressor=threshold=0.16:ratio=2.2:attack=18:release=120:makeup=1.7,loudnorm=I=-16:LRA=6:TP=-1.5,aresample=48000,asetpts=N/SR/TB'
        if 'tail_padding_after_last_word' in cfg:
            word_info = json.loads(words.read_text(encoding='utf-8'))
            speech_end = max((w['offset']+w['duration'])/1e7 for w in word_info)
            # Remove only trailing TTS padding; preserve every spoken word at +0%.
            audio_filter += f',atrim=end={speech_end+cfg["tail_padding_after_last_word"]}'
        if regenerate or not wav.exists():run(['-i', raw, '-af', audio_filter, '-ac', '2', '-c:a', 'pcm_s16le', wav])
        return {**s, 'audio_duration': duration(wav), 'audio': wav.relative_to(ROOT).as_posix(), 'words': words.relative_to(ROOT).as_posix(), 'voice_offset': .10}
    stages = await asyncio.gather(*(voice(s) for s in cfg['stages']))
    frames = [s.get('slot_frames', math.ceil(max(s['minimum_duration'], s['audio_duration'] + .22) * cfg['fps'])) for s in stages]
    for s, count in zip(stages, frames):
        if s['voice_offset'] + s['audio_duration'] > count / cfg['fps'] - .04:
            raise ValueError(f'Complete normal-rate voice does not fit {s["id"]}')
    available = round(cfg['duration'] * cfg['fps'])
    if sum(frames) > available:
        raise ValueError(f'Voice needs {sum(frames)/cfg["fps"]:.3f}s; shorten copy instead of speeding up narration: {[s["audio_duration"] for s in stages]}')
    # Keep the final contact visible; allocate extra time to the operation.
    frames[-1] += available - sum(frames)
    cursor = 0
    for s, count in zip(stages, frames):
        s['start'] = cursor / cfg['fps']
        s['duration'] = count / cfg['fps']
        s['frame_count'] = count
        cursor += count
    manifest = {'revision':cfg.get('revision'),'controller_label':cfg.get('controller_label','服务器'),'duration': cursor/cfg['fps'], 'fps': cfg['fps'], 'voice': cfg['voice'], 'rate': '+0%', 'audio_time_stretch': 1.0, 'stages': stages}
    (directory / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return manifest


def panels(out, manifest):
    regular = {n: ImageFont.truetype(chinese_font(), n) for n in [22,24,26,28,30,32,36,40,42]}
    bold = ImageFont.truetype(chinese_font(True), 40)
    white, muted, green, cyan = '#f4f4f5', '#a1a1aa', '#4ade80', '#67e8f9'
    for i, s in enumerate(manifest['stages']):
        im = Image.new('RGBA', (1920,1080)); d = ImageDraw.Draw(im)
        # Match the existing machine plaque's source-space geometry exactly.
        plaque_layer=Image.new('RGBA',(2560,1440))
        plate=Image.new('RGBA',(276,54),(82,73,63,255))
        ImageDraw.Draw(plate).text((16,10),manifest['controller_label'],font=regular[32],fill=(204,211,214),anchor='lt')
        plate=plate.rotate(-11,Image.Resampling.BICUBIC,expand=True)
        plaque_layer.alpha_composite(plate,(558,946))
        im.alpha_composite(plaque_layer.resize((1792,1008),Image.Resampling.LANCZOS),(64,0))
        d.rectangle((1156,0,1856,1008), fill=(2,5,9,255))
        d.text((1204,104), 'AI 控制机械手', font=regular[36], fill=white)
        d.line((1204,186,1795,186), fill='#46636e', width=2)
        d.rounded_rectangle((1715,105,1783,153),radius=5,outline=cyan,width=3)
        d.line((1749,94,1749,105),fill=cyan,width=3)
        for x in [1731,1760]: d.ellipse((x,122,x+7,129),fill=white)
        d.text((1204,270), f'{i+1:02d}', font=regular[28], fill=green)
        d.text((1204,319), s['title'], font=bold, fill=white)
        for j,line in enumerate(s['lines']): d.text((1204,400+j*46), line, font=regular[30], fill='#cdd0d6')
        if s['id']=='coordinate':
            for x,label,coordinate in [(1204,'屏幕像素','(u, v)'),(1555,'机械坐标','(X, Y)')]:
                d.rounded_rectangle((x,528,x+234,655),radius=10,fill='#0d1b22',outline='#385e6b',width=2)
                d.text((x+117,546),label,font=regular[24],fill=muted,anchor='mt')
                d.text((x+117,585),coordinate,font=regular[36],fill=cyan,anchor='mt')
            d.line((1452,591,1537,591),fill=green,width=3)
            d.line((1525,581,1537,591,1525,601),fill=green,width=3)
            d.text((1492,621),'转换',font=regular[22],fill=green,anchor='mt')
        for j,label in enumerate(['采集','AI 识别','转换回传','执行']):
            x=1230+j*176
            if j<3:d.line((x,760,x+176,760),fill='#313a42',width=2)
            color=green if j<=i else '#454b52'
            d.ellipse((x-7,753,x+7,767),fill=color)
            d.text((x,790),label,font=regular[24],fill=white if j==i else muted,anchor='mt')
        im.save(out/f'{s["id"]}-panel.png')


def stage_captions(out, manifest, cfg):
    # Hold each step label until the exact next step. The general speech-caption
    # helper intentionally adds gaps/fades, which caused a blank at 1.73--2.50s.
    cues = [{'start': s['start'], 'end': s['start'] + s['duration'],
             'text': s.get('caption', s['text'].strip('。，'))}
            for s in manifest['stages']]
    write_captions(out, NAME, [], cfg)
    ass = out / f'{NAME}.zh-CN.ass'
    header = ass.read_text(encoding='utf-8-sig')
    body = ''.join(f'Dialogue: 0,{stamp(c["start"], True)},{stamp(c["end"], True)},Caption,,0,0,0,,{c["text"]}\n' for c in cues)
    ass.write_text(header + body, encoding='utf-8-sig')
    srt = '\n\n'.join(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}' for i,c in enumerate(cues)) + '\n'
    (out / f'{NAME}.zh-CN.srt').write_text(srt, encoding='utf-8-sig')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--prepare-only',action='store_true')
    a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    cfg=json.loads((ROOT/'config/mechanical_compact.json').read_text('utf-8'))
    manifest=asyncio.run(prepare(cfg))
    (out/'timeline.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'duration':manifest['duration'],'stages':[(s['id'],s['duration'],s['audio_duration']) for s in manifest['stages']]}),flush=True)
    if a.prepare_only:return
    panels(out,manifest)
    source=ROOT/'releases/latest/mechanical-natural-clean.mp4'
    for s in manifest['stages']:
        start,end=s['source']
        picture_frames=s.get('picture_frames_before_cut',s['frame_count'])
        picture_duration=picture_frames/cfg['fps']
        factor=(picture_duration-1/60)/(end-start-1/60)
        # Use the approved full motion for each retained step; omit the old USB-only step.
        filters=f'[0:v]trim=start={start}:end={end},setpts=(PTS-STARTPTS)*{factor},fps=60,tpad=stop_mode=clone:stop_duration=0.1,trim=end_frame={picture_frames}[retimed];'
        if s.get('remove_picture_frames'):
            a_frame,b_frame=s['remove_picture_frames']
            assert picture_frames-(b_frame-a_frame)==s['frame_count']
            filters+=f'[retimed]split=2[pre][post];[pre]trim=end_frame={a_frame},setpts=PTS-STARTPTS[before];[post]trim=start_frame={b_frame},setpts=PTS-STARTPTS[after];[before][after]concat=n=2:v=1:a=0[edited];'
        else:
            filters+='[retimed]null[edited];'
        filters+='[edited]crop=780:720:0:0,scale=1092:1008:flags=lanczos,pad=1920:1080:64:0:color=0x09090b,drawbox=x=0:y=1008:w=1920:h=1:color=0x33333b:t=fill[body];[body][1:v]overlay=shortest=1,format=yuv420p[v]'
        run(['-i',source,'-loop','1','-framerate','60','-i',out/f'{s["id"]}-panel.png','-filter_complex',filters,'-map','[v]','-an','-t',s['duration'],'-r','60','-c:v','libx264','-preset','fast','-crf','17',out/f'{s["id"]}-clean.mp4'])
    (out/'concat.txt').write_text(''.join(f"file '{s['id']}-clean.mp4'\n" for s in manifest['stages']),encoding='utf-8')
    run(['-f','concat','-safe','0','-i',out/'concat.txt','-c','copy','-movflags','+faststart',out/'mechanical-compact-clean.mp4'])
    args=[];filters=[]
    for i,s in enumerate(manifest['stages']):
        args+=['-i',ROOT/s['audio']]
        delay=round((s['start']+s['voice_offset'])*1000)
        filters.append(f'[{i}:a]adelay={delay}:all=1[n{i}]')
    labels=''.join(f'[n{i}]' for i in range(len(manifest['stages'])))
    filters.append(labels+f'amix=inputs=4:duration=longest:normalize=0,apad=whole_dur={manifest["duration"]},atrim=duration={manifest["duration"]}[n]')
    run([*args,'-filter_complex',';'.join(filters),'-map','[n]','-c:a','pcm_s24le',out/'narration.wav'])
    stage_captions(out,manifest,cfg)
    total=manifest['duration']
    run(['-i',out/'narration.wav','-ss',cfg['music_offset'],'-i',ROOT/'assets/audio/music-first-30s.flac','-filter_complex',f'[1:a]atrim=duration={total},asetpts=PTS-STARTPTS,volume=0.36,afade=t=in:d=0.08,afade=t=out:st={total-.45}:d=0.45[m];[0:a][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.85:level=0:latency=1[a]','-map','[a]','-c:a','pcm_s24le',out/'mix.wav'])
    run(['-i','mechanical-compact-clean.mp4','-i','mix.wav','-vf',f'ass={NAME}.zh-CN.ass','-map','0:v','-map','1:a','-t',total,'-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-af','volume=0.9','-movflags','+faststart',NAME+'.mp4'],cwd=out)
    print('COMPACT_PREVIEW_COMPLETE',total,flush=True)


if __name__=='__main__':main()
