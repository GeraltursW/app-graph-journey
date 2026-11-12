"""Join the configured head and mechanical demonstration with analytics.

Use clean pictures and separate narration stems. The soundtrack is mixed once
for the entire film, and subtitles are rendered once at native 1920x1080.
"""
import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from finalize_subtitled_films import stamp, write_captions
from integrate_scenario_main import FIT
from film_step_labels import prepare_step_labels

ROOT = Path(__file__).resolve().parents[1]
NAME = 'application-knowledge-graph-with-mechanical-replay'


def run(args, cwd=None):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *map(str, args)], cwd=cwd, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--head-dir', type=Path, required=True)
    parser.add_argument('--mechanical-dir', type=Path, default=ROOT/'releases/latest/compact-mechanical')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--reuse-bridge', action='store_true')
    a = parser.parse_args()
    head, mech, out = a.head_dir.resolve(), a.mechanical_dir.resolve(), a.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    outro = out/'outro'; outro.mkdir(exist_ok=True)
    h = json.loads((head/'timeline.json').read_text('utf-8'))
    m = json.loads((mech/'timeline.json').read_text('utf-8'))
    cfg = json.loads((ROOT/'config/head_compact.json').read_text('utf-8'))
    mechanical_start = h['duration']
    outro_start = mechanical_start + m['duration']
    total = outro_start + 10
    assert round(h['duration']*60)==round(cfg['duration']*60), 'Rebuild head after changing its config'
    mechanical_cfg=json.loads((ROOT/'config/mechanical_compact.json').read_text('utf-8'))
    assert h.get('revision')==cfg.get('revision'), 'Head cache revision is stale'
    assert m.get('revision')==mechanical_cfg.get('revision'), 'Mechanical cache revision is stale'

    bridge_layout={'global_step_header':True,'mechanical_sha256':hashlib.sha256((mech/'mechanical-compact-clean.mp4').read_bytes()).hexdigest()}
    bridge_stamp=outro/'bridge-layout.json'
    reusable=(a.reuse_bridge and (outro/'analytics-bridge-clean.mp4').exists() and bridge_stamp.exists()
              and json.loads(bridge_stamp.read_text('utf-8'))==bridge_layout)
    if not reusable:
        subprocess.run([sys.executable, ROOT/'scripts/render_analytics_bridge.py',
                        '--source', mech/'mechanical-compact-clean.mp4', '--out', outro,
                        '--native-framed-source', '--native-output', '--hide-chapter-label'], check=True)
        bridge_stamp.write_text(json.dumps(bridge_layout,indent=2)+'\n',encoding='utf-8')
    # The device holds its exact final pose as it shrinks; the following chart
    # shares the existing five-second bridge with a one-second dissolve.
    run(['-i', outro/'analytics-bridge-clean.mp4', '-i', ROOT/'releases/latest/final-analytics-v3-clean.mp4',
         '-filter_complex', f'[0:v]fps=60,settb=AVTB,setsar=1[a];[1:v]{FIT},drawbox=x=64:y=0:w=1792:h=76:color=0x09090b:t=fill,fps=60,settb=AVTB,setsar=1[b];'
         '[a][b]xfade=transition=fade:duration=1:offset=4,format=yuv420p[v]',
         '-map', '[v]', '-an', '-t', 10, '-r', 60, '-c:v', 'libx264', '-preset', 'fast', '-crf', 17,
         '-movflags', '+faststart', out/'outro-clean.mp4'])
    parts = [head/'head-compact-clean.mp4', mech/'mechanical-compact-clean.mp4', out/'outro-clean.mp4']
    (out/'concat.txt').write_text(''.join("file '"+p.as_posix()+"'\n" for p in parts), encoding='utf-8')
    run(['-f', 'concat', '-safe', 0, '-i', out/'concat.txt', '-c', 'copy', '-movflags', '+faststart', out/'main-clean.mp4'])
    print('PICTURE_COMPLETE', total, flush=True)

    cues = [dict(c) for c in h['captions']]
    for stage in m['stages']:
        cues.append({'start':mechanical_start+stage['start'],
                     'end':mechanical_start+stage['start']+stage['duration'],
                     'text':stage.get('caption', stage['text'].strip('。，'))})
    for start, end, text in [(0.65, 2.5, '测试完成后'), (2.5, 6.9, '性能、功耗、热等数据同步汇聚'), (6.9, 10, '数据报表一目了然')]:
        cues.append({'start':outro_start+start, 'end':outro_start+end, 'text':text})
    write_captions(out, NAME, [], cfg)
    ass = out/(NAME+'.zh-CN.ass')
    header = ass.read_text('utf-8-sig')
    ass.write_text(header+''.join(f'Dialogue: 0,{stamp(c["start"],True)},{stamp(c["end"],True)},Caption,,0,0,0,,{c["text"]}\n' for c in cues), encoding='utf-8-sig')
    (out/(NAME+'.zh-CN.srt')).write_text('\n\n'.join(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}' for i,c in enumerate(cues))+'\n', encoding='utf-8-sig')

    stems = [head/'narration.wav', mech/'narration.wav', ROOT/'releases/latest/analytics-outro-voiceover.wav']
    durations = [h['duration'], m['duration'], 10]
    filters = [f'[{i}:a]aresample=48000,aformat=channel_layouts=stereo,apad=whole_dur={dur},atrim=duration={dur},asetpts=N/SR/TB[n{i}]' for i,dur in enumerate(durations)]
    filters.append('[n0][n1][n2]concat=n=3:v=0:a=1[n]')
    run([*[item for p in stems for item in ['-i', p]], '-filter_complex', ';'.join(filters), '-map', '[n]', '-c:a', 'pcm_s24le', out/'narration.wav'])
    count = math.ceil((total-.6)/29.4)
    filters = [f'[1:a]atrim=end=30,asetpts=PTS-STARTPTS,asplit={count}'+''.join(f'[m{i}]' for i in range(count))]
    last = 'm0'
    for i in range(1,count):
        filters.append(f'[{last}][m{i}]acrossfade=d=0.6:c1=qsin:c2=qsin[j{i}]'); last = f'j{i}'
    filters.append(f'[{last}]atrim=duration={total},volume=0.36,afade=t=in:d=0.08,afade=t=out:st={total-1.5}:d=1.5[m];'
                   '[0:a][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.85:level=0:latency=1[a]')
    run(['-i', out/'narration.wav', '-i', ROOT/'assets/audio/music-first-30s.flac', '-filter_complex', ';'.join(filters),
         '-map', '[a]', '-ar', 48000, '-ac', 2, '-c:a', 'pcm_s24le', out/'mix.wav'])
    print('AUDIO_AND_CAPTIONS_COMPLETE', len(cues), flush=True)
    step_labels,step_filter=prepare_step_labels(out,h,m['duration'])
    run(['-i', 'main-clean.mp4', '-i', 'mix.wav', '-vf', f'{step_filter},ass={NAME}.zh-CN.ass', '-map', '0:v', '-map', '1:a',
         '-t', total, '-c:v', 'libx264', '-preset', 'fast', '-crf', 17, '-pix_fmt', 'yuv420p',
         '-c:a', 'aac', '-b:a', '192k', '-af', 'volume=0.9', '-movflags', '+faststart', NAME+'.mp4'], cwd=out)
    timeline = {'version':'v1.13.0', 'duration':total, 'fps':60, 'frame_count':round(total*60),
                'resolution':[1920,1080], 'font':'Microsoft YaHei', 'subtitle_band':[1008,1080],
                'head_duration':h['duration'], 'mechanical_start':mechanical_start, 'mechanical_duration':m['duration'],
                'outro_start':outro_start, 'outro_duration':10, 'caption_count':len(cues), 'captions':cues,
                'shots':h['shots'], 'mechanical_stages':m['stages'], 'audio_time_stretch':1.0,
                'music_loop_seconds':30, 'music_crossfade_seconds':0.6, 'music_volume':0.36,
                'source_head':head.relative_to(ROOT).as_posix() if head.is_relative_to(ROOT) else str(head),
                'source_mechanical':mech.relative_to(ROOT).as_posix() if mech.is_relative_to(ROOT) else str(mech),
                'step_count':len(step_labels),'step_labels':step_labels}
    (out/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('FULL_FILM_COMPLETE', total, flush=True)


if __name__ == '__main__':
    main()
