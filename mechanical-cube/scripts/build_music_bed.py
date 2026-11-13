"""Build a sample-counted continuous music bed with equal-power loop joins."""
from pathlib import Path
import subprocess
import numpy as np


def build_music_bed(source,target,duration,gain=.7,overlap=.6,level_windows=None):
    rate=48000
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(source),'-t','30','-ar',str(rate),'-ac','2','-f','f32le','-'])
    clip=np.frombuffer(raw,dtype='<f4').reshape(-1,2)
    n=round(overlap*rate);total=round(duration*rate)
    assert len(clip)>n and np.isfinite(clip).all()
    phase=np.linspace(0,np.pi/2,n,endpoint=True,dtype=np.float32)[:,None]
    bed=clip.copy()
    while len(bed)<total:
        join=bed[-n:]*np.cos(phase)+clip[:n]*np.sin(phase)
        bed=np.concatenate([bed[:-n],join,clip[n:]],axis=0)
    bed=bed[:total].copy()*gain
    # Smooth only requested loop regions with a slow, bounded level envelope.
    for start,end in level_windows or []:
        lo=round(start*rate);hi=min(len(bed),round(end*rate))
        mono=bed.mean(axis=1).astype(np.float64)
        power=np.concatenate([[0],np.cumsum(mono*mono)])
        indices=np.arange(lo,hi);left=np.maximum(0,indices-rate//2);right=np.minimum(len(bed),indices+rate//2)
        rms=np.sqrt((power[right]-power[left])/(right-left)+1e-12)
        target_rms=float(np.median(rms))
        correction=np.clip(target_rms/rms,.7,1.3)
        t=(indices-lo)/rate;length=(hi-lo)/rate
        weight=np.minimum(np.clip(t,0,1),np.clip(length-t,0,1));weight=weight*weight*(3-2*weight)
        bed[lo:hi]*=(1+weight*(correction-1))[:,None]
    fade_in=round(.08*rate);fade_out=round(1.5*rate)
    bed[:fade_in]*=np.linspace(0,1,fade_in,dtype=np.float32)[:,None]
    bed[-fade_out:]*=np.linspace(1,0,fade_out,dtype=np.float32)[:,None]
    assert len(bed)==total
    subprocess.run(['ffmpeg','-v','error','-y','-f','f32le','-ar',str(rate),'-ac','2','-i','-','-c:a','pcm_s24le',str(target)],input=bed.astype('<f4').tobytes(),check=True)
