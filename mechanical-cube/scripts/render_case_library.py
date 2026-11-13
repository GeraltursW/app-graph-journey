"""Generic case → case library → temporal model, without a persona example."""
from pathlib import Path
from render_scenario_context import Renderer, run
from integrate_scenario_main import write_bridge


def render_case_library(mechanical, out, name, seconds, stage_id, title, model_copy=None):
    out = Path(out)
    run(['-i', mechanical, '-vf', 'crop=1092:1008:64:0,scale=780:720',
         '-frames:v', 1, out/'mechanical-reference.png'])
    animation = {'single':4.8, 'library':6.5, 'extract':6.2,
                 'temporal':8, 'context':6.6166666667}[stage_id]
    stage = {'id':stage_id, 'title':title, 'start':0, 'duration':animation,
             'voice_offset':0, 'audio_duration':0, 'text':''}
    renderer = Renderer({'generic_cases':True, 'model_copy':model_copy or {}, 'stages':[stage]}, out)
    write_bridge(out, name, seconds, lambda t: renderer.frame(t*animation/seconds))
