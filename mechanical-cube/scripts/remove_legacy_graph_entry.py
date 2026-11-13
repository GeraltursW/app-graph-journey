"""Remove the obsolete full-tree animation at the start of the path demo."""
from pathlib import Path
import subprocess
from PIL import Image
from integrate_scenario_main import write_bridge,smooth


def remove_legacy_graph_entry(previous,following,out,name='06-01'):
    out=Path(out)
    def still(p,d,args):
        subprocess.run(['ffmpeg','-v','error','-y',*args,'-i',str(p),'-frames:v','1',str(d)],check=True)
        return Image.open(d).convert('RGB')
    a=still(previous,out/'graph-clean-end.png',['-sseof','-0.02'])
    b=still(following,out/'path-clean-start.png',['-ss','1'])
    bg=Image.new('RGB',a.size,(9,9,11))
    def frame(t):
        # Separate fades never superimpose the two different graph layouts.
        if t<.42:return Image.blend(a,bg,smooth(t,.12,.42))
        return Image.blend(bg,b,smooth(t,.42,.92))
    write_bridge(out,'graph-to-path-clean',1,frame)
    target=out/(name+'-clean-entry.mp4')
    vf='[0:v]settb=AVTB,setpts=PTS-STARTPTS[a];[1:v]trim=start_frame=60,settb=AVTB,setpts=PTS-STARTPTS[b];[a][b]concat=n=2:v=1:a=0[v]'
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(out/'graph-to-path-clean.mp4'),'-i',str(following),'-filter_complex',vf,'-map','[v]','-an','-r','60','-c:v','libx264','-crf','17','-preset','fast','-pix_fmt','yuv420p','-movflags','+faststart',str(target)],check=True)
    target.replace(out/(name+'.mp4'))
