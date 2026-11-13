"""Replace the old moving-phone entrance with a fixed-layout dissolve."""
from pathlib import Path
import subprocess
from PIL import Image
from integrate_scenario_main import smooth,write_bridge


def repair_connection_handoff(previous,following,out,name='03-01',seconds=.6):
    out=Path(out)
    def still(path,destination,args):
        subprocess.run(['ffmpeg','-v','error','-y',*args,'-i',str(path),'-frames:v','1',str(destination)],check=True)
        return Image.open(destination).convert('RGB')
    first=still(previous,out/'connection-handoff-start.png',['-sseof','-0.02'])
    last=still(following,out/'connection-handoff-target.png',['-ss',str(seconds)])
    write_bridge(out,'connection-handoff-fixed',seconds,lambda t:Image.blend(first,last,smooth(t,0,seconds-1/60)))
    target=out/(name+'-fixed.mp4')
    filters=f'[0:v]settb=AVTB,setpts=PTS-STARTPTS[a];[1:v]trim=start_frame={round(seconds*60)},settb=AVTB,setpts=PTS-STARTPTS[b];[a][b]concat=n=2:v=1:a=0[v]'
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(out/'connection-handoff-fixed.mp4'),'-i',str(following),'-filter_complex',filters,'-map','[v]','-an','-r','60','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(target)],check=True)
    target.replace(out/(name+'.mp4'))
