"""Decode and validate the completed compact film and its edit boundaries."""
import argparse
import json
import subprocess
from pathlib import Path
from video_fonts import chinese_font
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
    total=timeline['duration'];fps=timeline['fps'];head=timeline['head_duration'];mechanical=timeline['mechanical_duration'];outro=timeline['outro_start']
    assert v['avg_frame_rate']==f'{fps}/1' and int(v['nb_frames'])==round(total*fps)
    assert abs(float(v['duration'])-total)<.001 and abs(float(aud['duration'])-total)<.025
    decoded=subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(movie),'-f','null','-'],capture_output=True,text=True)
    assert decoded.returncode==0 and not decoded.stderr, decoded.stderr
    cues=timeline['captions'];assert len(cues)==timeline['caption_count']
    assert all(0<=c['start']<c['end']<=total+.001 for c in cues)
    assert all(c['end']<=n['start']+.001 for c,n in zip(cues,cues[1:]))
    font=ImageFont.truetype(chinese_font(),36)
    max_width=max(font.getlength(c['text']) for c in cues);assert max_width<1740
    narration=audio(out/'narration.wav');final=audio(movie);mix=audio(out/'mix.wav')
    assert len(narration)==round(total*16000)
    aligned=[]
    for start,duration,path in [(0,head,source_path(timeline['source_head'])/'narration.wav'),
                               (head,mechanical,source_path(timeline['source_mechanical'])/'narration.wav')]:
        stem=audio(path);offset=round(start*16000);sample=narration[offset:offset+len(stem)]
        corr=float(np.corrcoef(stem[320:-320],sample[320:-320])[0,1]);assert corr>.9999
        aligned.append({'start':start,'duration':duration,'source_correlation':corr,'time_stretch':1.0})
    length=min(len(mix),len(final));corr=float(np.corrcoef(mix[:length],final[:length])[0,1]);assert corr>.99
    music_report=None
    if (out/'music-restored.wav').exists():
        music=audio(out/'music-restored.wav')
        assert len(music)==round(total*16000), 'Music must cover the complete film'
        levels=[float(np.sqrt(np.mean(music[i*16000:(i+1)*16000]**2))) for i in range(int(total))]
        assert all(np.isfinite(x) and x>.001 for x in levels), 'Unexpected gap in music bed'
        music_report={'duration':len(music)/16000,'coverage':'continuous','minimum_one_second_rms_db':float(20*np.log10(min(levels)))}
    # Test actual stereo channels: FFmpeg's mono downmix can add 3 dB.
    stereo_raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(movie),'-vn','-ac','2','-ar','48000','-f','f32le','-'])
    peak=float(np.max(np.abs(np.frombuffer(stereo_raw,dtype='<f4'))));assert peak<1
    shots=timeline['shots']
    factor=next(s for s in shots if s.get('case_stage')=='temporal')
    factor_start=factor['start']
    assert shots[10]['title']=='提取典型操作序列'
    assert abs(shots[10]['start']+shots[10]['duration']-factor_start)<.001
    assert len(shots)==13 and total==83.6
    assert not any(s.get('renderer')=='student_summary' for s in shots)
    assert not any('大学生' in c['text'] for c in cues)
    times=[0,12,33.3,43,46,50,55,58,61,total-.1]
    boundaries={'connection_to_exploration':5.4,'exploration_to_nodes':11,
                'nodes_to_vectorization':13.8,'vectorization_to_path':19,
                'saved_case_to_lab':36.4,'lab_to_bridge':41,'lab_bridge_to_case':41.6,
                'single_to_library':44,'library_to_sequence':48.4,
                'sequence_to_factors':factor_start,'factors_to_context':59,
                'context_to_mechanical':head,'mechanical_to_analytics':outro}
    pairs={}
    for label,t in boundaries.items():
        pairs[label]=(len(times),len(times)+1);times.extend([t-1/fps,t])
    frames=[]
    for i,t in enumerate(times):
        target=out/f'qa-{i:02d}.png'
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(movie),'-frames:v','1',str(target)],check=True)
        im=Image.open(target).convert('RGB');frames.append(im.copy())
        assert float(np.mean(np.asarray(im)[:1008]))>1, f'Unexpected black frame at {t}'
    label=ImageFont.truetype(chinese_font(),22)
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
    for label,(left,right) in pairs.items():
        a=np.asarray(frames[left],dtype=np.float32)[110:1008];b=np.asarray(frames[right],dtype=np.float32)[110:1008]
        mse=float(np.mean((a-b)**2));psnr=float(10*np.log10(255**2/max(mse,1e-10)))
        assert psnr>30,(label,psnr);continuity[label]={'psnr_db':psnr,'mean_absolute_pixel_difference':float(np.mean(np.abs(a-b)))}
    steps=json.loads((out/'step-label-timeline.json').read_text('utf-8'))['entries']
    assert len(steps)==timeline['step_count']==15
    assert [s['id'] for s in steps]==[f'{i:02d}' for i in range(1,len(steps)+1)]
    assert steps[0]['start_frame']==0 and steps[-1]['end_frame']==round(total*fps)
    assert all(a['end_frame']==b['start_frame'] for a,b in zip(steps,steps[1:]))
    assert not any('喜欢列表上滑三次' in c['text'] for c in cues)
    removed_voice_ids={'student_feed','student_tabs','student_likes','student_open'}
    assert not removed_voice_ids.intersection(s['id'] for shot in timeline['shots'] for s in shot['voices'])
    assert 'student_plan' not in {v['id'] for shot in shots for v in shot['voices']}
    assert steps[11]['title']=='影响因子时序建模'
    assert timeline['mechanical_stages'][-1]['text']=='机械手操作。'
    assert not any('点击' in s['text'] for s in timeline['mechanical_stages'])
    assert json.loads((source_path(timeline['source_mechanical'])/'timeline.json').read_text('utf-8'))['controller_label']=='服务器'
    # The closing statement remains in the subtitle band, with no duplicate green title.
    assert timeline['analytics_conclusion']=='subtitle_only'
    assert cues[-1]['text']=='数据报表一目了然' and abs(cues[-1]['end']-total)<.001
    raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(total-1.4),'-i',str(movie),
        '-vf','crop=448:84:736:882','-f','rawvideo','-pix_fmt','rgb24','-'])
    strip=np.frombuffer(raw,dtype=np.uint8).reshape(-1,84,448,3).astype(np.int16)
    green=(strip[:,:,:,1]>35)&(strip[:,:,:,1]>strip[:,:,:,0]+15)&(strip[:,:,:,1]>strip[:,:,:,2]+15)
    green_pixels=int(green.sum());assert green_pixels==0,('Duplicate green conclusion remains',green_pixels)
    report={'duration':total,'resolution':[1920,1080],'fps':fps,'frames':round(total*fps),'decode':'passed',
            'av_duration_difference_seconds':abs(float(v['duration'])-float(aud['duration'])),
            'caption_count':len(cues),'step_count':len(steps),'step_coverage':'continuous','controller_label':'服务器',
            'mechanical_narration':'机械手操作','maximum_caption_width_px':max_width,'font':'Microsoft YaHei',
            'case_progression':['single_case','multiple_cases','scenario_library','typical_sequence','temporal_model'],
            'sequence_to_factors_transition_seconds':shots[10]['transition_to_next'],
            'analytics_conclusion':'subtitle_only','ending_green_title_pixels':green_pixels,
            'background_music':music_report,'normal_rate_narration':aligned,'aac_mix_correlation':corr,'decoded_peak':peak,
            'join_continuity':continuity,'sampled_frame_times':times,'file_bytes':movie.stat().st_size}
    (out/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':main()
