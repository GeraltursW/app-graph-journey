"""Decode and validate the completed compact film and its edit boundaries."""
import argparse
import json
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

NAME='application-knowledge-graph-with-mechanical-replay'
ROOT=Path(__file__).resolve().parents[1]


def source_path(value):
    path=Path(value)
    return path if path.is_absolute() else ROOT/path


def audio(path, rate=16000):
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-vn','-ac','1','-ar',str(rate),'-f','f32le','-'])
    return np.frombuffer(raw,dtype='<f4')


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    out=a.out.resolve();movie=out/(NAME+'.mp4');timeline=json.loads((out/'timeline.json').read_text('utf-8'))
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)]))
    v=next(s for s in probe['streams'] if s['codec_type']=='video')
    aud=next(s for s in probe['streams'] if s['codec_type']=='audio')
    assert [v['width'],v['height']]==[1920,1080]
    assert v['avg_frame_rate']=='60/1' and int(v['nb_frames'])==6108
    assert abs(float(v['duration'])-101.8)<.001 and abs(float(aud['duration'])-101.8)<.025
    decoded=subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(movie),'-f','null','-'],capture_output=True,text=True)
    assert decoded.returncode==0 and not decoded.stderr, decoded.stderr
    cues=timeline['captions'];assert len(cues)==30
    assert all(0<=c['start']<c['end']<=101.801 for c in cues)
    assert all(c['end']<=n['start']+.001 for c,n in zip(cues,cues[1:]))
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',36)
    max_width=max(font.getlength(c['text']) for c in cues);assert max_width<1740
    narration=audio(out/'narration.wav');final=audio(movie);mix=audio(out/'mix.wav')
    assert len(narration)==round(101.8*16000)
    aligned=[]
    for start,duration,path in [(0,83,source_path(timeline['source_head'])/'narration.wav'),
                               (83,8.8,source_path(timeline['source_mechanical'])/'narration.wav')]:
        stem=audio(path);offset=round(start*16000);sample=narration[offset:offset+len(stem)]
        corr=float(np.corrcoef(stem[320:-320],sample[320:-320])[0,1]);assert corr>.9999
        aligned.append({'start':start,'duration':duration,'source_correlation':corr,'time_stretch':1.0})
    length=min(len(mix),len(final));corr=float(np.corrcoef(mix[:length],final[:length])[0,1]);assert corr>.99
    peak=float(np.max(np.abs(final)));assert peak<1
    times=[0,12,33.3,55,82.983333,83,85.8,90.5,91.783333,91.8,92.3,93.3,95.6,96.8,99,101.7,
           5.383333,5.4,6.8,7.5,9,10.983333,11,19.4,
           36.383333,36.4,37.62,38.57,39.52,40.35,40.983333,41,41.583333,41.6]
    frames=[]
    for i,t in enumerate(times):
        target=out/f'qa-{i:02d}.png'
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(movie),'-frames:v','1',str(target)],check=True)
        im=Image.open(target).convert('RGB');frames.append(im.copy())
        assert float(np.mean(np.asarray(im)[:1008]))>1, f'Unexpected black frame at {t}'
    label=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',22)
    for page in range((len(times)+7)//8):
        sheet=Image.new('RGB',(1280,4*390),(25,25,28));d=ImageDraw.Draw(sheet)
        for j in range(8):
            i=page*8+j;x=(j%2)*640;y=(j//2)*390
            if i>=len(times):break
            sheet.paste(frames[i].resize((640,360),Image.Resampling.LANCZOS),(x,y+30))
            d.text((x+10,y+2),f'{times[i]:.3f}s',font=label,fill='white')
        sheet.save(out/f'qa-contact-{page+1}.jpg',quality=92)
    # Exclude deliberately changing global step labels and speech subtitles.
    continuity={}
    for label,left,right in [('context_to_mechanical',4,5),('mechanical_to_analytics',8,9),
                             ('connection_to_exploration',16,17),('exploration_to_nodes',21,22),
                             ('saved_case_to_lab',24,25),('lab_to_bridge',30,31),('lab_bridge_to_context',32,33)]:
        a=np.asarray(frames[left],dtype=np.float32)[110:1008];b=np.asarray(frames[right],dtype=np.float32)[110:1008]
        mse=float(np.mean((a-b)**2));psnr=float(10*np.log10(255**2/max(mse,1e-10)))
        assert psnr>30,(label,psnr);continuity[label]={'psnr_db':psnr,'mean_absolute_pixel_difference':float(np.mean(np.abs(a-b)))}
    report={'duration':101.8,'resolution':[1920,1080],'fps':60,'frames':6108,'decode':'passed',
            'av_duration_difference_seconds':abs(float(v['duration'])-float(aud['duration'])),
            'caption_count':30,'maximum_caption_width_px':max_width,'font':'Microsoft YaHei',
            'normal_rate_narration':aligned,'aac_mix_correlation':corr,'decoded_peak':peak,
            'join_continuity':continuity,'sampled_frame_times':times,'file_bytes':movie.stat().st_size}
    (out/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':main()
