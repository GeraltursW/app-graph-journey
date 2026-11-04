"""Replace shot 02 and its original narration, preserving the full film's music.

Input must be the pre-v1.7.2 master (or a fresh build-scenario-path intermediate).
Do not apply this replacement twice to an already updated film.
"""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--shot', type=Path, default=ROOT / 'releases/latest/page-exploration-clean.mp4')
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error('Source and output must be different files.')
    cfg = json.loads((ROOT / 'config/page_exploration.json').read_text(encoding='utf-8'))
    start, length = cfg['start'], cfg['duration']
    end = start + length
    audio_start, audio_end = cfg['audio_replace_start'], cfg['audio_replace_end']
    audio_length = audio_end - audio_start
    total = float(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', str(args.source)
    ]))
    filters = [
        '[0:v]split=2[head][tail]',
        f'[head]trim=end={start},setpts=PTS-STARTPTS,fps=60,setsar=1,settb=AVTB[v0]',
        f'[1:v]trim=duration={length},setpts=PTS-STARTPTS,fps=60,setsar=1,settb=AVTB[v1]',
        f'[tail]trim=start={end},setpts=PTS-STARTPTS,fps=60,setsar=1,settb=AVTB[v2]',
        '[v0][v1][v2]concat=n=3:v=1:a=0[v]',
        '[0:a]aresample=48000,asetpts=PTS-STARTPTS[original]',
        f'[2:a]aresample=48000,atrim=start={audio_start}:end={audio_end},'
        f'asetpts=PTS-STARTPTS,volume=-1,adelay={round(audio_start * 1000)}:all=1[old]',
        f'[3:a]aresample=48000,apad=whole_dur={audio_length},atrim=duration={audio_length},'
        f'asetpts=PTS-STARTPTS,volume={cfg["voice_gain"]},'
        f'adelay={round(audio_start * 1000)}:all=1[new]',
        '[original][old][new]amix=inputs=3:duration=first:normalize=0,'
        'alimiter=limit=0.891:level=0:latency=1,aresample=48000[a]'
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
        '-i', str(args.source), '-i', str(args.shot),
        '-i', str(ROOT / 'assets/audio/main-narration-first-62s.flac'),
        '-i', str(ROOT / 'assets/audio/page-exploration-voiceover.wav'),
        '-filter_complex', ';'.join(filters), '-map', '[v]', '-map', '[a]',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '17', '-pix_fmt', 'yuv420p',
        '-r', '60', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2',
        '-t', str(total), '-movflags', '+faststart', str(args.output)
    ], check=True)
    print(f'Updated shot 02: {args.output}', flush=True)


if __name__ == '__main__':
    main()
