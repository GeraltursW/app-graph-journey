"""Generate normal-rate narration. Video slots follow audio; audio is never sped up."""
import asyncio
import hashlib
import json
import math
import subprocess
from pathlib import Path
import edge_tts

ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/'config/final_delivery.json'
OUT=ROOT/'assets/audio/mechanical-natural'

def duration(path):
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(path)]))

async def synthesize(text,cfg,target,metadata):
    last=None
    for proxy in [None,'http://127.0.0.1:7897','http://127.0.0.1:7897']:
        words=[]
        try:
            voice=edge_tts.Communicate(text,voice=cfg['voice'],rate='+0%',pitch=cfg['pitch'],boundary='WordBoundary',proxy=proxy,connect_timeout=10)
            with target.open('wb') as f:
                async for item in voice.stream():
                    if item['type']=='audio':f.write(item['data'])
                    elif item['type']=='WordBoundary':words.append({k:item[k] for k in ['offset','duration','text']})
            metadata.write_text(json.dumps(words,ensure_ascii=False,indent=2),encoding='utf-8')
            return
        except Exception as exc:
            last=exc
    raise last

def main():
    cfg=json.loads(CFG.read_text(encoding='utf-8'));OUT.mkdir(parents=True,exist_ok=True)
    manifest={'voice':cfg['voice'],'rate':'+0%','pitch':cfg['pitch'],'audio_time_stretch':1.0,'segments':[]}
    cursor=0.0
    for spec in [cfg['chapter'],*cfg['stages']]:
        name=spec['id'];raw=OUT/f'{name}.mp3';wav=OUT/f'{name}.wav';words=OUT/f'{name}.words.json';cache=OUT/f'{name}.cache.json'
        signature=hashlib.sha256(json.dumps([cfg['voice'],'+0%',cfg['pitch'],spec['text']],ensure_ascii=False).encode()).hexdigest()
        if not(raw.exists() and cache.exists() and json.loads(cache.read_text())['signature']==signature):
            print(f'Normal-rate narration: {name}',flush=True)
            asyncio.run(synthesize(spec['text'],cfg,raw,words))
            cache.write_text(json.dumps({'signature':signature}),encoding='utf-8')
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(raw),'-af',
            'highpass=f=75,lowpass=f=11500,acompressor=threshold=0.16:ratio=2.2:attack=18:release=120:makeup=1.7,loudnorm=I=-16:LRA=6:TP=-1.5,aresample=48000,asetpts=N/SR/TB',
            '-ac','2','-c:a','pcm_s16le',str(wav)],check=True)
        length=duration(wav)
        original=(spec['source_frames'][1]-spec['source_frames'][0])/24 if 'source_frames' in spec else 0
        slot=math.ceil(max(original,length+(.95 if name=='chapter' else .7))*60)/60
        item={**spec,'audio_duration':length,'slot_duration':slot,'voice_offset':.35 if name=='chapter' else .25,'audio_time_stretch':1.0,'audio':f'assets/audio/mechanical-natural/{name}.wav','words':f'assets/audio/mechanical-natural/{name}.words.json'}
        if name!='chapter':item['start']=cursor;cursor+=slot
        manifest['segments'].append(item)
    manifest['mechanical_duration']=cursor
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'chapter_duration':manifest['segments'][0]['slot_duration'],'mechanical_duration':cursor,'rate':'+0%','time_stretch':1.0}),flush=True)

if __name__=='__main__':main()
