"""Remove only the purple completion note from the retained STEP 06 footage."""
from pathlib import Path
import numpy as np
from PIL import ImageDraw
from patch_case_copy import transform_video


def patch_ai_completion_label(path,spec):
    start,end=spec['source']
    if end<=38.2 or start>=44.8:return
    frames=round(spec['duration']*60)
    source_last=(round((end-start)*60)-1)/60
    def frame(image,index):
        source_time=start+index/max(1,frames-1)*source_last
        if not 38.2<=source_time<44.8:return image
        # This text sits in an empty gap below the sibling-page box. Preserve
        # the arrow and the separate "点击我 / 同级横向跳转" label above it.
        pixels=np.asarray(image)
        background=tuple(np.median(pixels[537:543,1076:1083],axis=(0,1)).astype(int))
        result=image.copy()
        ImageDraw.Draw(result).rectangle((1085,506,1345,540),fill=background)
        return result
    path=Path(path);target=path.with_name(path.stem+'-no-completion-note.mp4')
    transform_video(path,target,frame)
    target.replace(path)
