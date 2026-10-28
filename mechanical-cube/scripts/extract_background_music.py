"""Recover the first 30 s of music using the matching clean narration reference.

This is reference subtraction for these aligned source files, not general source
separation. NumPy and FFmpeg are required; the resulting FLAC is included so that
normal film assembly does not need NumPy or an online model.
"""
import argparse
import json
import subprocess
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    data = subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-t','30','-vn','-ar','44100','-ac','2','-f','f32le','-'])
    return np.frombuffer(data, np.float32).reshape(-1, 2)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mixed',type=Path,default=ROOT.parent/'videos/10月27日.mp4')
    p.add_argument('--reference',type=Path,default=ROOT/'assets/audio/main-narration-first-62s.flac')
    p.add_argument('--output',type=Path,default=ROOT/'assets/audio/music-first-30s.flac')
    a = p.parse_args()
    y, x = read(a.mixed), read(a.reference)
    n = min(len(y), len(x))
    y, x = y[:n], x[:n]
    corr = float(np.corrcoef(y.mean(axis=1),x.mean(axis=1))[0,1])
    if corr < .4:
        raise RuntimeError('The clean reference does not match the mixed source at zero delay.')
    gains = np.sum(x.astype(np.float64)*y,axis=0)/np.sum(x.astype(np.float64)**2,axis=0)
    music = (y-x*gains).astype(np.float32)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['ffmpeg','-v','error','-y','-f','f32le','-ar','44100','-ac','2','-i','-',
                    '-af','aresample=48000,apad=whole_dur=30,atrim=end=30',
                    '-c:a','flac','-sample_fmt','s32',str(a.output)],input=music.tobytes(),check=True)
    report={'method':'aligned clean-reference subtraction','excerpt_seconds':30,
            'sample_rate':48000,'reference_correlation':corr,'reference_gain':gains.tolist(),
            'residual_reference_correlation':[float(np.corrcoef(music[:,i],x[:,i])[0,1]) for i in (0,1)]}
    a.output.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
