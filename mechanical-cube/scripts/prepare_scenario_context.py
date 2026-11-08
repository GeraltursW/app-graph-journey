"""Prepare natural-rate Chinese narration and a timing manifest for the preview."""
import asyncio, hashlib, json, math, subprocess
from pathlib import Path
from prepare_natural_mechanical import synthesize, duration

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/audio/scenario-context'

async def prepare():
    cfg=json.loads((ROOT/'config/scenario_context.json').read_text(encoding='utf-8'))
    OUT.mkdir(parents=True,exist_ok=True)
    semaphore=asyncio.Semaphore(2)
    async def one(s):
        name=s['id'];mp3=OUT/f'{name}.mp3';words=OUT/f'{name}.words.json';cache=OUT/f'{name}.cache.json'
        signature=hashlib.sha256(json.dumps([cfg['voice'],cfg['rate'],cfg['pitch'],s['text']],ensure_ascii=False).encode()).hexdigest()
        async with semaphore:
            if not(mp3.exists() and words.exists() and cache.exists() and json.loads(cache.read_text())['signature']==signature):
                print('VOICE',name,flush=True)
                await synthesize(s['text'],cfg,mp3,words)
                cache.write_text(json.dumps({'signature':signature}),encoding='utf-8')
            wav=OUT/f'{name}.wav'
            subprocess.run(['ffmpeg','-v','error','-y','-i',str(mp3),'-af','highpass=f=75,lowpass=f=11500,loudnorm=I=-17:LRA=6:TP=-2,aresample=48000','-ac','2','-c:a','pcm_s16le',str(wav)],check=True)
            seconds=duration(wav)
            return {**s,'audio_duration':seconds,'duration':math.ceil(max(s['minimum_duration'],seconds+.95)*60)/60,'voice_offset':.4,'audio':f'assets/audio/scenario-context/{name}.wav','words':f'assets/audio/scenario-context/{name}.words.json'}
    stages=await asyncio.gather(*(one(s) for s in cfg['stages']))
    t=0
    for s in stages:s['start']=t;t+=s['duration']
    manifest={'voice':cfg['voice'],'rate':cfg['rate'],'audio_time_stretch':1,'fps':60,'resolution':[1920,1080],'stages':stages,'duration':t}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'duration':t,'stages':[(s['id'],s['duration']) for s in stages]}),flush=True)

if __name__=='__main__':asyncio.run(prepare())
