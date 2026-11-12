"""Keep global shot labels in sync with the final film's frame timeline."""
import json
from pathlib import Path
from finalize_subtitled_films import stamp

ROOT=Path(__file__).resolve().parents[1]
CONFIG=json.loads((ROOT/'config/film_step_labels.json').read_text('utf-8'))


def step_label(number):
    spec=CONFIG['steps'][number-1]
    return f'STEP {number:02d} / {len(CONFIG["steps"]):02d}   {spec["title"]}'


def prepare_step_labels(out,head,mechanical_duration):
    out=Path(out);segments=[(s['start'],s['duration']) for s in head['shots']]
    segments += [(head['duration'],mechanical_duration),(head['duration']+mechanical_duration,10)]
    assert len(segments)==len(CONFIG['steps'])==20
    entries=[]
    for i,((start,duration),spec) in enumerate(zip(segments,CONFIG['steps']),1):
        assert spec['id']==f'{i:02d}'
        begin=round(start*60);end=round((start+duration)*60)
        if entries:assert entries[-1]['end_frame']==begin
        entries.append({'id':spec['id'],'title':spec['title'],'text':step_label(i),
                        'start':start,'end':start+duration,'start_frame':begin,'end_frame':end})
    assert entries[0]['start_frame']==0 and entries[-1]['end_frame']==6108
    header='[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n'
    header+=f'Style: Step,{CONFIG["font_family"]},{CONFIG["font_size"]},&H00ADA3A3,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'
    x,y=CONFIG['position']
    events=''.join(f'Dialogue: 1,{stamp(e["start"],True)},{stamp(e["end"],True)},Step,,0,0,0,,{{\\pos({x},{y})}}{e["text"]}\n' for e in entries)
    (out/'film-step-labels.ass').write_text(header+events,encoding='utf-8-sig')
    # Erase only legacy left-header glyphs, retaining phone silhouettes and
    # body motion. The late context-to-cube bridge has already faded its old
    # heading before the cube reaches this area, so the mask stops there.
    masks=[(3,5.4,96,20,600,42,'0x040306'),
           (5.4,13.8,96,20,600,58,'0x09090b'),
           (13.8,19,96,20,600,42,'0x040306'),
           (19,33,96,20,800,58,'0x09090b'),
           (33,41.6,64,20,900,58,'0x09090b'),
           (41.6,82.55,64,20,700,58,'0x09090b')]
    filters=[]
    for start,end,x,y,w,h,color in masks:
        # Use presentation timestamps: decoder reinitialization at a concat
        # boundary can reset filter-local frame counters without resetting PTS.
        filters.append(f"drawbox=x={x}:y={y}:w={w}:h={h}:color={color}:t=fill:enable='gte(t,{start})*lt(t,{end})'")
    filters.append('ass=film-step-labels.ass')
    (out/'step-label-timeline.json').write_text(json.dumps({'step_count':20,'entries':entries,'legacy_header_masks':masks},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return entries,','.join(filters)
