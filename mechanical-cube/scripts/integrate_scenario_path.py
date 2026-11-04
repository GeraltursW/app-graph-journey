"""Composite the scenario-driven shot into master seconds 26--47.

0.4 s dissolves preserve the previous graph and following case layout.
Hold the unfolded path through 48 s so the old node motion stays covered.
Then finalize_long_film.py rebuilds narration and the existing music loop.
"""
from pathlib import Path
import argparse
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=ROOT/'releases/iterations/11-long-film-looped-music-v1.6.mp4')
    p.add_argument('--shot',type=Path,default=ROOT/'releases/latest/scenario-path-clean.mp4')
    p.add_argument('--output',type=Path,default=ROOT/'output/application-knowledge-graph-scenario.mp4')
    p.add_argument('--preserve-source-music',action='store_true',help='Replace only old narration in the 71.4 s continuous-music master.')
    a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    picture=a.output.parent/'scenario-master-picture.mp4'
    if a.preserve_source_music:
        duration=subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(a.source)],text=True).strip()
        # This source uses the matching clean narration at unity gain. Subtract
        # only that reference over 26--45 s; keep its existing music continuously.
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(a.source),'-i',str(a.shot),
            '-i',str(ROOT/'assets/audio/main-narration-first-62s.flac'),
            '-i',str(ROOT/'assets/audio/scenario-path-voiceover.wav'),
            '-filter_complex',
            '[1:v]fps=60,tpad=start_mode=clone:start_duration=0.4:stop_mode=clone:stop_duration=1.4,format=yuva420p,'
            'fade=t=in:st=0:d=0.4:alpha=1,fade=t=out:st=22.4:d=0.4:alpha=1,setpts=PTS+25.6/TB[shot];'
            '[0:v][shot]overlay=eof_action=pass:enable=\'between(t,25.6,48.4)\',format=yuv420p[v];'
            '[0:a]aresample=48000,aformat=channel_layouts=stereo,asplit=3[x][y][z];'
            '[x]atrim=end=26,asetpts=PTS-STARTPTS[a];[y]atrim=start=26:end=45,asetpts=PTS-STARTPTS[b];'
            '[z]atrim=start=45,asetpts=PTS-STARTPTS[c];'
            '[2:a]atrim=start=26:end=45,asetpts=PTS-STARTPTS,aresample=48000,volume=-1[oldvoice];'
            '[3:a]atrim=end=19,asetpts=PTS-STARTPTS,aresample=48000,volume=0.8[newvoice];'
            '[b][oldvoice][newvoice]amix=inputs=3:duration=first:normalize=0,alimiter=limit=0.891:level=0:latency=1[replacement];'
            '[a][replacement][c]concat=n=3:v=0:a=1[audio]',
            '-map','[v]','-map','[audio]','-t',duration,'-c:v','libx264','-preset','slow','-crf','16',
            '-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(a.output)],check=True)
        print(a.output)
        return
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(a.source),'-i',str(a.shot),
        '-filter_complex',
        '[1:v]fps=60,tpad=start_mode=clone:start_duration=0.4:stop_mode=clone:stop_duration=1.4,format=yuva420p,'
        'fade=t=in:st=0:d=0.4:alpha=1,fade=t=out:st=22.4:d=0.4:alpha=1,setpts=PTS+25.6/TB[shot];'
        '[0:v][shot]overlay=eof_action=pass:enable=\'between(t,25.6,48.4)\',format=yuv420p[v]',
        '-map','[v]','-an','-t','88.8','-c:v','libx264','-preset','slow','-crf','16','-movflags','+faststart',str(picture)],check=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/finalize_long_film.py'),
                    '--source',str(picture),'--output',str(a.output)],check=True)
    print(a.output)
if __name__=='__main__':main()
