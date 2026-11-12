"""Shared monochrome phone and control feedback for exploration and replay."""
from PIL import Image, ImageDraw

BG=(9,9,11);PANEL=(14,14,17);EDGE=(78,78,88)
WHITE=(244,244,245);MUTED=(163,163,173);GREEN=(74,222,128)


def phone_shell():
    im=Image.new('RGB',(420,700),BG);d=ImageDraw.Draw(im)
    d.rounded_rectangle((1,1,418,698),radius=31,fill=(7,7,9),outline=(212,212,216),width=3)
    d.rounded_rectangle((15,16,404,682),radius=23,fill=PANEL,outline=(57,57,64),width=1)
    d.rounded_rectangle((170,25,250,32),radius=3,fill=EDGE)
    return im


def focus_box(draw,box):
    draw.rounded_rectangle(box,radius=7,fill=(16,35,23),outline=GREEN,width=2)


def checkmark(draw,x,y):
    draw.line((x-10,y,x-2,y+8,x+10,y-8),fill=GREEN,width=3)


def cursor(draw,x,y,pulse=None):
    draw.ellipse((x-8,y-8,x+8,y+8),fill=WHITE,outline=(10,10,12),width=2)
    if pulse is not None and 0<=pulse<=1:
        r=9+pulse*18;color=tuple(round(a+(b-a)*(1-pulse)) for a,b in zip(PANEL,GREEN))
        draw.ellipse((x-r,y-r,x+r,y+r),outline=color,width=2)
