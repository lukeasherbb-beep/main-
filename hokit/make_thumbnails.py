import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter, ImageEnhance
R="/home/user/fight-scope/hokit/"; T="/tmp/claude-0/-home-user/fb6b1853-165e-5f36-880c-e21a3ce1871c/scratchpad/thumb/"
F="/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf"
W,H=1280,720; GOLD=(196,142,22); RED=(220,30,30)
def img(p):
    im=Image.open(p)
    if im.mode in("RGBA","P","LA"):
        im=im.convert("RGBA"); bg=Image.new("RGBA",im.size,(255,255,255,255)); im=Image.alpha_composite(bg,im)
    return im.convert("RGB")
def pop(im):
    im=ImageEnhance.Contrast(im).enhance(1.15); im=ImageEnhance.Color(im).enhance(1.15)
    return im.filter(ImageFilter.UnsharpMask(2,120,2))
def base():
    c=Image.new("RGB",(W,H),(14,14,16)); d=ImageDraw.Draw(c)
    for i in range(H): d.line([(0,i),(W,i)],fill=(14+i//40,14+i//45,16+i//45))
    return c
def half(c,im,box,centering=(0.5,0.3)):
    x0,y0,x1,y1=box; c.paste(pop(ImageOps.fit(im,(x1-x0,y1-y0),Image.LANCZOS,centering=centering)),(x0,y0))
def slash(c):
    d=ImageDraw.Draw(c); d.polygon([(610,0),(670,0),(610,H),(550,H)],fill=GOLD); d.polygon([(670,0),(682,0),(622,H),(610,H)],fill=(10,10,12))
def circle(c,im,cx,cy,r,centering=(0.5,0.3),ring=RED):
    f=pop(ImageOps.fit(im,(2*r,2*r),Image.LANCZOS,centering=centering)); m=Image.new("L",(2*r,2*r),0); ImageDraw.Draw(m).ellipse([0,0,2*r,2*r],fill=255)
    d=ImageDraw.Draw(c); d.ellipse([cx-r-10,cy-r-10,cx+r+10,cy+r+10],fill=ring); c.paste(f,(cx-r,cy-r),m)
def arrow(c,x0,y0,x1,y1):
    d=ImageDraw.Draw(c); import math
    a=math.atan2(y1-y0,x1-x0); d.line([(x0,y0),(x1,y1)],fill=RED,width=22)
    L=55; p=[(x1+math.cos(a)*20,y1+math.sin(a)*20),(x1-L*math.cos(a-0.55),y1-L*math.sin(a-0.55)),(x1-L*math.cos(a+0.55),y1-L*math.sin(a+0.55))]
    d.polygon(p,fill=RED)
def text(c,s,cx,y,size,fill=(255,255,255),maxw=1200):
    d=ImageDraw.Draw(c)
    while True:
        f=ImageFont.truetype(F,size)
        if d.textlength(s,font=f)<=maxw or size<40: break
        size-=4
    d.text((cx,y),s,font=f,fill=fill,anchor="mm",stroke_width=max(8,size//12),stroke_fill=(0,0,0))
def label(c,s,cx,y,fill=GOLD):
    d=ImageDraw.Draw(c); f=ImageFont.truetype(F,40); w=d.textlength(s,font=f)+40
    d.rectangle([cx-w/2,y-30,cx+w/2,y+30],fill=(10,10,12)); d.text((cx,y),s,font=f,fill=fill,anchor="mm")
hokit=img(T+"h14_4.png").crop((560,0,1360,1000))
jones=img(R+"images/jones_interview.png"); gane=img(R+"images/gane_freedom250_64.jpg")
pereira=img(R+"images/pereira_oval_office.jpg").crop((380,60,880,560)); buffer=img(R+"images/buffer_ufc.png").crop((330,0,830,500))
logo=Image.open("/home/user/fight-scope/assets/logo_square.png").convert("RGBA").resize((110,110))
def badge(c): c.paste(logo,(18,18),logo)
# A: LITTLE MAN
c=base(); half(c,hokit,(0,0,640,H),(0.5,0.25)); half(c,jones,(640,0,W,H),(0.5,0.3)); slash(c)
text(c,"\"LITTLE MAN\"",640,96,130,fill=GOLD); circle(c,pereira,175,565,110,(0.5,0.5))
label(c,"JONES",960,650,(255,255,255)); badge(c); c.save(R+"thumbnails/thumb_A_little_man.jpg",quality=92)
# B: HE GOT ROBBED?
c=base(); half(c,hokit,(0,0,640,H),(0.5,0.25)); half(c,gane,(640,0,W,H),(0.5,0.25)); slash(c)
circle(c,pereira,640,250,130,(0.5,0.5),GOLD); text(c,"ROBBED?",500,620,150); arrow(c,820,330,1010,200)
badge(c); c.save(R+"thumbnails/thumb_B_robbed.jpg",quality=92)
# C: SAME COACHES...
c=base(); half(c,jones,(0,0,640,H),(0.5,0.3)); half(c,hokit,(640,0,W,H),(0.5,0.25)); slash(c)
text(c,"SAME COACHES...",640,96,120,fill=(255,255,255)); text(c,"DIFFERENT RESULTS",480,630,80,fill=GOLD,maxw=900)
circle(c,buffer,640,420,110,(0.5,0.5),GOLD); badge(c); c.save(R+"thumbnails/thumb_C_same_coaches.jpg",quality=92)
