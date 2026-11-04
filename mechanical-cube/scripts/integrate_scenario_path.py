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
    a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    picture=a.output.parent/'scenario-master-picture.mp4'
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
