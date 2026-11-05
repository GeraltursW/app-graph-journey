"""Build text-safe scenario transitions and composite into the complete master.

Entry: 25.2--26.4 s, eased feathered reveal (no double graph exposure).
Exit: 47--48.4 s, matched stationary path into settled case cards.
When provided, matching case cards replace 48.4--52 s as well.
Text fades out before replacement text appears. Existing audio is stream-copied.
"""
from pathlib import Path
import argparse
import json
import subprocess
import numpy as np
from PIL import Image, ImageFilter

ROOT=Path(__file__).resolve().parents[1]
W,H,FPS=1280,720,60
FRAME_BYTES=W*H*3

def smooth(x):
    x=np.clip(x,0,1)
    return x*x*x*(x*(x*6-15)+10)

def run(args):
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',*map(str,args)],check=True)

def still(path,t):
    data=subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(path),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'])
    return np.frombuffer(data,np.uint8).reshape(H,W,3).copy()

def decoder(path,start,duration):
    return subprocess.Popen(['ffmpeg','-v','error','-ss',str(start),'-i',str(path),'-t',str(duration),'-vf','fps=60',
                             '-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)

def next_frame(proc):
    data=proc.stdout.read(FRAME_BYTES)
    if len(data)!=FRAME_BYTES:raise RuntimeError('Incomplete decoded video frame')
    return np.frombuffer(data,np.uint8).reshape(H,W,3)

def encoder(path):
    return subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r','60',
        '-i','-','-an','-c:v','libx264','-preset','medium','-crf','15','-pix_fmt','yuv420p','-movflags','+faststart',str(path)],stdin=subprocess.PIPE)

def text_safe_blend(old,new,p,entry):
    # The central graphic always stays visible; only label bands use staggered
    # fades. A broad, eased reveal makes the graph layout change as one surface.
    if entry:
        edge=-96+(W+192)*smooth(p)
        mask=smooth((edge-np.arange(W,dtype=np.float32))/96+.5)[None,:,None]
    else:
        mask=smooth(p)
    out=old.astype(np.float32)*(1-mask)+new.astype(np.float32)*mask
    old_alpha=1-smooth(p/.40)
    new_alpha=smooth((p-.50)/.50)
    # Retain the source gradients behind fading labels. Feathering the mask
    # avoids visible rectangular bands on the dark background.
    bg=np.asarray(Image.blend(Image.fromarray(old).filter(ImageFilter.GaussianBlur(24)),
                             Image.fromarray(new).filter(ImageFilter.GaussianBlur(24)),float(smooth(p))),dtype=np.float32)
    bands=[(0,79),(638,H)] if entry else [(0,137),(329,423),(630,H)]
    for lo,hi in bands:
        clean=old[lo:hi].astype(np.float32)*old_alpha+new[lo:hi].astype(np.float32)*new_alpha+bg[lo:hi]*(1-old_alpha-new_alpha)
        ys=np.arange(lo,hi,dtype=np.float32)
        ramp=4 if lo==329 else 16
        feather=(smooth((ys-lo)/ramp)*smooth((hi-1-ys)/16))[:,None,None]
        out[lo:hi]=out[lo:hi]*(1-feather)+clean*feather
    # Preserve exact first and last frames for continuous cut boundaries.
    if p<=0:return old.copy()
    if p>=1:return new.copy()
    return np.clip(out,0,255).astype(np.uint8)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=ROOT.parent/'videos/application-knowledge-graph-and-data.mp4')
    p.add_argument('--reference',type=Path,default=ROOT/'releases/iterations/12-app-graph-data-continuous-music-v1.6.mp4')
    p.add_argument('--shot',type=Path,default=ROOT/'releases/latest/scenario-path-clean.mp4')
    p.add_argument('--case',type=Path,default=ROOT/'releases/latest/scenario-case-clean.mp4')
    p.add_argument('--out',type=Path,default=ROOT/'output/scenario-smooth-v2')
    p.add_argument('--output',type=Path,default=ROOT/'output/application-knowledge-graph-smooth.mp4')
    p.add_argument('--reuse-transitions',action='store_true')
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);a.output.parent.mkdir(parents=True,exist_ok=True)
    segment=a.out/'scenario-with-transitions.mp4'
    if not a.reuse_transitions:
        source=decoder(a.reference,25.2,1.2); target=decoder(a.shot,0,.4)
        first=still(a.shot,0);enc=encoder(a.out/'entry.mp4')
        try:
            for i in range(72):
                old=next_frame(source);new=first if i<48 else next_frame(target)
                frame=text_safe_blend(old,new,i/71,True)
                enc.stdin.write(frame.tobytes())
                if i in (0,18,36,54,71):Image.fromarray(frame).save(a.out/f'entry-{i:03d}.png')
        finally:
            enc.stdin.close();source.stdout.close();target.stdout.close()
        if enc.wait() or source.wait() or target.wait():raise RuntimeError('Entry encoding failed')
        old=still(a.shot,20.983334);new=still(a.case,0) if a.case.exists() else still(a.reference,48.4);enc=encoder(a.out/'exit.mp4')
        try:
            for i in range(84):
                frame=text_safe_blend(old,new,i/83,False);enc.stdin.write(frame.tobytes())
                if i in (0,21,42,63,83):Image.fromarray(frame).save(a.out/f'exit-{i:03d}.png')
        finally:enc.stdin.close()
        if enc.wait():raise RuntimeError('Exit encoding failed')
        run(['-i',a.out/'entry.mp4','-i',a.shot,'-i',a.out/'exit.mp4',
            '-filter_complex','[0:v]setpts=PTS-STARTPTS,settb=AVTB[a];'
                '[1:v]trim=start=0.4:end=21,setpts=PTS-STARTPTS,settb=AVTB[b];'
                '[2:v]setpts=PTS-STARTPTS,settb=AVTB[c];[a][b][c]concat=n=3:v=1:a=0[v]',
            '-map','[v]','-an','-r','60','-c:v','libx264','-preset','slow','-crf','15','-pix_fmt','yuv420p','-movflags','+faststart',segment])
    total=subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(a.source)],text=True).strip()
    inputs=['-i',a.source,'-i',segment]
    graph='[1:v]setpts=PTS+25.2/TB[shot];[0:v][shot]overlay=eof_action=pass:enable=\'gte(t,25.2)*lt(t,48.4)\'[scenario];'
    if a.case.exists():
        inputs.extend(['-i',a.case])
        graph+='[2:v]trim=start=1.4:end=5,setpts=PTS-STARTPTS+48.4/TB[case];[scenario][case]overlay=eof_action=pass:enable=\'gte(t,48.4)*lt(t,52)\',format=yuv420p[v]'
    else:
        graph+='[scenario]format=yuv420p[v]'
    run([*inputs,'-filter_complex',graph,
        '-map','[v]','-map','0:a:0','-t',total,'-c:v','libx264','-preset','slow','-crf','16','-c:a','copy','-movflags','+faststart',a.output])
    (a.out/'transition-timeline.json').write_text(json.dumps({'entry':[25.2,26.4],'scenario_body':[26.4,47.0],
        'exit':[47.0,48.4],'matching_case':[48.4,52.0] if a.case.exists() else None,
        'audio':'copied unchanged from current main film','duration':float(total)},indent=2),encoding='utf-8')
    print(a.output)

if __name__=='__main__':main()
