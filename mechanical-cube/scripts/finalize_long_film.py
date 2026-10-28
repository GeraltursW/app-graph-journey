"""Replace the black opening, rebuild clean narration and loop 30 s of music."""
from pathlib import Path
import argparse
import json
import math
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def run(args):
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',*args],check=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=ROOT.parent/'videos/application-knowledge-graph-with-mechanical-replay.mp4')
    p.add_argument('--output',type=Path,default=ROOT/'output/application-knowledge-graph-final-music.mp4')
    p.add_argument('--config',type=Path,default=ROOT/'config/long_film_audio.json')
    a=p.parse_args()
    if a.source.resolve()==a.output.resolve():
        raise ValueError('Render to a new file before replacing the published master.')
    c=json.loads(a.config.read_text(encoding='utf-8'))
    total=float(c['duration'])
    work=a.output.parent/'audio-master-work'
    work.mkdir(parents=True,exist_ok=True)
    narration=work/'narration.wav'
    audio_filters=[
        '[0:a]aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS,apad=whole_dur=62,atrim=end=62[a]',
        '[1:a]aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS,apad=whole_dur=4,atrim=end=4[b]',
        '[2:a]atrim=start=13.25:end=27.25,asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,apad=whole_dur=14,atrim=end=14,afade=t=out:st=13.9:d=0.1[c]',
        '[3:a]aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS,apad=whole_dur=10,atrim=end=10[d]',
        '[a][b]acrossfade=d=0.6:c1=tri:c2=tri[ab]',
        '[ab][c]acrossfade=d=0.6:c1=tri:c2=tri[abc]',
        '[abc][d]concat=n=2:v=0:a=1[out]'
    ]
    run(['-i',str(ROOT/c['narration_source']),
         '-i',str(ROOT/'releases/latest/mechanical-transition-card-voiceover.mp4'),
         '-i',str(ROOT/'releases/latest/mechanical-cube-main-ai-integrated-voiceover.mp4'),
         '-i',str(ROOT/'releases/latest/analytics-outro-voiceover.wav'),
         '-filter_complex',';'.join(audio_filters),'-map','[out]','-c:a','pcm_s24le',str(narration)])

    excerpt=float(c['music_excerpt_seconds'])
    overlap=float(c['music_crossfade_seconds'])
    repeats=max(1,math.ceil((total-overlap)/(excerpt-overlap)))
    labels=''.join(f'[m{i}]' for i in range(repeats))
    filters=[f'[0:a]atrim=end={excerpt},asetpts=PTS-STARTPTS,asplit={repeats}{labels}']
    last='m0'
    for i in range(1,repeats):
        label=f'join{i}'
        filters.append(f'[{last}][m{i}]acrossfade=d={overlap}:c1=qsin:c2=qsin[{label}]')
        last=label
    filters.append(f'[{last}]atrim=end={total},volume={c["music_gain"]},'
                   f'afade=t=in:st=0:d={c["music_fade_in_seconds"]},'
                   f'afade=t=out:st={total-c["music_fade_out_seconds"]}:d={c["music_fade_out_seconds"]}[music]')
    music=work/'music-loop.wav'
    run(['-i',str(ROOT/c['music_source']),'-filter_complex',';'.join(filters),'-map','[music]',
         '-ar','48000','-c:a','pcm_s24le',str(music)])
    run(['-i',str(a.source),'-loop','1','-framerate','60','-i',str(ROOT/c['opening_frame']),
         '-i',str(narration),'-i',str(music),
         '-filter_complex',f"[0:v][1:v]overlay=enable='lt(t,{c['opening_hold_seconds']})':shortest=1,format=yuv420p[v];"
                           '[2:a][3:a]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.891:level=0:latency=1[a]',
         '-map','[v]','-map','[a]','-t',str(total),'-r','60','-c:v','libx264','-crf','16','-preset','slow',
         '-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(a.output)])
    (work/'render-report.json').write_text(json.dumps({'duration':total,'music_excerpt':excerpt,
        'music_repeats':repeats,'crossfade':overlap,'loop_starts':[i*(excerpt-overlap) for i in range(repeats)],
        'opening_hold':c['opening_hold_seconds'],'music_gain':c['music_gain']},indent=2),encoding='utf-8')
    print(a.output)

if __name__=='__main__':
    main()
