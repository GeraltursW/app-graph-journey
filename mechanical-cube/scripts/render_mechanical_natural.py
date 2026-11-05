"""Re-time the five mechanical steps to normal narration and redraw YaHei labels."""
import argparse,json,math,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
W,H,S=1280,720,2

def run(args):subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',*map(str,args)],check=True)

def panels(cfg,manifest,out):
    regular={n:ImageFont.truetype(cfg['font_regular'],n*S) for n in [14,16,18,20,22,24,26,28,32,36]}
    bold=ImageFont.truetype(cfg['font_bold'],44*S)
    for i,spec in enumerate(manifest['segments'][1:]):
        im=Image.new('RGBA',(W*S,H*S));d=ImageDraw.Draw(im)
        d.rectangle((780*S,0,W*S,H*S),fill=(2,5,9,255))
        d.text((816*S,78*S),'PLC 内 AI',font=regular[28],fill=(244,244,245),anchor='lt')
        d.line((816*S,145*S,1230*S,145*S),fill=(77,130,146),width=2*S)
        # One visual language for the AI icon and all explanatory labels.
        d.rectangle((1156*S,75*S,1218*S,119*S),outline='white',width=3*S)
        d.line((1187*S,58*S,1187*S,74*S),fill='white',width=3*S)
        d.rectangle((1181*S,53*S,1193*S,59*S),fill=(103,232,249))
        for x in [1172,1197]:d.rectangle((x*S,91*S,(x+8)*S,99*S),fill=(103,232,249))
        d.text((816*S,214*S),f'{i+1:02d}  {spec["title"]}',font=regular[32],fill=(244,244,245),anchor='lt')
        for j,line in enumerate(spec['lines']):d.text((816*S,(292+j*44)*S),line,font=regular[22],fill=(205,208,214),anchor='lt')
        for j,label in enumerate(['采集','回传','识别','定位','点击']):
            x=830+j*89;c=(74,222,128) if j<=i else (69,75,82)
            d.ellipse(((x-5)*S,482*S,(x+5)*S,492*S),fill=c)
            if j<4:d.line((x*S,487*S,(x+89)*S,487*S),fill=(49,58,66),width=S)
            d.text((x*S,510*S),label,font=regular[14],fill=(210,214,220) if j==i else (120,129,140),anchor='mt')
        # Replace the old serif engraving with a small matching machine label.
        plate=Image.new('RGBA',(138*S,27*S),(82,73,63,255));p=ImageDraw.Draw(plate)
        p.text((8*S,5*S),'PLC 主机',font=regular[16],fill=(204,211,214),anchor='lt')
        plate=plate.rotate(-11,Image.Resampling.BICUBIC,expand=True)
        im.alpha_composite(plate,(279*S,473*S))
        im.resize((W,H),Image.Resampling.LANCZOS).save(out/f'{spec["id"]}-overlay.png')
    im=Image.new('RGB',(W*S,H*S),(2,5,9));d=ImageDraw.Draw(im)
    for x in range(0,W,80):d.line((x*S,0,x*S,H*S),fill=(9,17,23),width=S)
    for y in range(0,H,80):d.line((0,y*S,W*S,y*S),fill=(9,17,23),width=S)
    d.text((640*S,170*S),'09  /  机械手复现',font=regular[20],fill=(161,170,181),anchor='mt')
    d.text((640*S,292*S),'接下来演示',font=bold,fill=(244,244,245),anchor='mt')
    d.text((640*S,368*S),'AI 控制机械手完成用例复现',font=regular[28],fill=(130,218,237),anchor='mt')
    d.text((640*S,565*S),'采集  ·  回传  ·  识别  ·  定位  ·  点击',font=regular[18],fill=(150,163,175),anchor='mt')
    im.resize((W,H),Image.Resampling.LANCZOS).save(out/'chapter.png')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--preview-only',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    cfg=json.loads((ROOT/'config/final_delivery.json').read_text(encoding='utf-8'))
    manifest=json.loads((ROOT/'assets/audio/mechanical-natural/manifest.json').read_text(encoding='utf-8'))
    panels(cfg,manifest,a.out)
    if a.preview_only:return
    source=ROOT/'releases/latest/c159cc4d19a03485a4677970789f6f1a.mp4'
    for stage in manifest['segments'][1:]:
        name=stage['id'];start,end=[v/24 for v in stage['source_frames']];duration=stage['slot_duration'];factor=duration/(end-start)
        print(f'Render {name}: {duration:.3f}s, normal audio speed',flush=True)
        # Optical flow keeps the original 24 fps motion smooth when a step grows.
        vf=f'[0:v]trim=start={start}:end={end},setpts=(PTS-STARTPTS)*{factor},crop=780:720:0:0,tpad=stop_mode=clone:stop_duration=0.3,minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:me_mode=bidir,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=0.2,trim=duration={duration},pad=1280:720:0:0:color=0x020509[body];[body][1:v]overlay=shortest=1,format=yuv420p[v]'
        run(['-i',source,'-loop','1','-framerate','60','-i',a.out/f'{name}-overlay.png','-filter_complex',vf,'-map','[v]','-an','-t',duration,'-r','60','-c:v','libx264','-preset','fast','-crf','16',a.out/f'{name}.mp4'])
    stages=manifest['segments'][1:];(a.out/'concat.txt').write_text('\n'.join(f"file '{x['id']}.mp4'" for x in stages),encoding='utf-8')
    run(['-f','concat','-safe','0','-i',a.out/'concat.txt','-c','copy','-movflags','+faststart',a.out/'mechanical-natural-clean.mp4'])
    inputs=[];filters=[];labels=[]
    for i,stage in enumerate(stages):
        inputs+=['-i',ROOT/stage['audio']];delay=round((stage['start']+stage['voice_offset'])*1000)
        filters.append(f'[{i}:a]adelay={delay}:all=1[a{i}]');labels.append(f'[a{i}]')
    filters.append(''.join(labels)+f'amix=inputs={len(stages)}:duration=longest:normalize=0,apad=whole_dur={manifest["mechanical_duration"]},atrim=duration={manifest["mechanical_duration"]}[a]')
    run([*inputs,'-filter_complex',';'.join(filters),'-map','[a]','-c:a','pcm_s16le',a.out/'mechanical-natural-voiceover.wav'])
    run(['-i',a.out/'mechanical-natural-clean.mp4','-i',a.out/'mechanical-natural-voiceover.wav','-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',a.out/'mechanical-natural-voiceover.mp4'])
    chapter=manifest['segments'][0]
    run(['-loop','1','-framerate','60','-i',a.out/'chapter.png','-vf',f'fade=t=in:st=0:d=0.35,fade=t=out:st={chapter["slot_duration"]-.6}:d=0.6',
         '-an','-t',chapter['slot_duration'],'-c:v','libx264','-preset','fast','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',a.out/'chapter-natural-clean.mp4'])
    print('MECHANICAL_NATURAL_RENDER_COMPLETE',flush=True)

if __name__=='__main__':main()
