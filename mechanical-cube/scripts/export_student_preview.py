"""Export the new student example and its rebased captions for focused review."""
import argparse,json,subprocess
from pathlib import Path
from finalize_subtitled_films import caption_chunks,write_captions

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve()
    manifest=json.loads((out/'timeline.json').read_text(encoding='utf-8'))
    stages=[s for s in manifest['stages'] if s['id'].startswith('student_')]
    if not stages:raise RuntimeError('No student example found')
    start=stages[0]['start'];end=stages[-1]['start']+stages[-1]['duration']-.4;duration=end-start
    cues=[]
    for s in stages:
        cues+=caption_chunks(s,s['start']-start+s['voice_offset'],s['audio_duration'])
    for c in cues:c['end']=min(c['end'],duration)
    write_captions(out,'student-a-case',cues,{'font_family':'Microsoft YaHei','subtitle_size':36})
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(start),'-i',str(out/'scenario-context-preview.mp4'),'-t',str(duration),'-c:v','libx264','-preset','fast','-crf','17','-c:a','aac','-b:a','192k','-af',f'afade=t=in:d=0.08,afade=t=out:st={duration-.35}:d=0.35','-movflags','+faststart',str(out/'student-a-case-preview.mp4')],check=True)
    (out/'student-clip-timeline.json').write_text(json.dumps({'start_in_full_preview':start,'end_in_full_preview':end,'duration':duration,'caption_count':len(cues)},indent=2)+'\n',encoding='utf-8')
    print('STUDENT_CASE_EXPORTED',round(duration,3),flush=True)

if __name__=='__main__':main()
