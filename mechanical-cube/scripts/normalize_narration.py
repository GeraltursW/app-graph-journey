"""Match spoken segment loudness using constant gain, without changing timing."""
from pathlib import Path
import json,subprocess

def normalize_narration(path,target=-18):
    path=Path(path)
    result=subprocess.run(['ffmpeg','-hide_banner','-i',str(path),'-af',f'loudnorm=I={target}:TP=-1.5:LRA=6:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
    info=json.loads(result.stderr[result.stderr.rfind('{'):]);gain=target-float(info['input_i'])
    if abs(gain)<.05:return
    assert float(info['input_tp'])+gain<-.5, 'Insufficient peak headroom for constant-gain normalization'
    temp=path.with_name(path.stem+'-level.wav')
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(path),'-af',f'volume={gain}dB','-c:a','pcm_s16le',str(temp)],check=True)
    temp.replace(path)
