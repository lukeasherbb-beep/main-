// Shared deterministic Canvas renderer. Browser preview and offline exports use this same module.

export const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));

export const ease=x=>1-Math.pow(1-clamp(x),3);

// en-US digit grouping with the decimals given (never the machine's locale): 407000 -> "407,000", 5.5 with 2 -> "5.50"
export const fmt=(n,d=0)=>Number(n).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});
// group a figure that is printed as given: decimals kept as they are, a non-number (a label) is returned untouched
export const fmtAs=v=>{const n=Number(v);return typeof v==='boolean'||v===''||v==null||!Number.isFinite(n)?String(v??''):fmt(n,(String(v).split('.')[1]||'').replace(/\D.*/,'').length)};

const mix=(a,b,t)=>a+(b-a)*t, TAU=Math.PI*2;

function baseDefaults(item){return {template:item.id,title:item.name,subtitle:'A new perspective',body:'Every detail contributes to the bigger picture. Follow the evidence, compare the possibilities, and discover what changes next.',label:'FIELD NOTES',labels:['Discovery','Context','Evidence','Insight','Outcome','Next chapter'],images:['assets/landscape-1.png','assets/landscape-2.png','assets/landscape-3.png','assets/person-1.png','assets/person-2.png','assets/mark.png'],backgroundImage:'',accent:'#39d9bd',secondary:'#f49768',background:'#102328',foreground:'#f7f2e7',theme:'dark',font:'Arimo',duration:item.duration,enter:0.22,exit:0.12,motion:1,transparent:false,number:73,prefix:'',suffix:'%',yearStart:1995,yearEnd:2026,chapter:'01',highlight:'bigger picture',country:'United States of America',countries:['France','Germany','Italy'],mapBounds:[-135,15,45,65],points:[[-122.4,37.8],[-74,40.7],[2.35,48.86]],pointLabels:['San Francisco','New York','Paris'],focusX:.5,focusY:.45,zoom:1.7,fit:'cover',data:[{label:'North',values:[14,22,36,42,66,82],value:82},{label:'Central',values:[72,64,52,46,30,20],value:62},{label:'South',values:[8,12,24,27,40,55],value:46},{label:'East',values:[12,19,25,31,38,46],value:35},{label:'West',values:[5,10,18,21,25,30],value:24}],axisLabels:['2021','2022','2023','2024','2025','2026'],unit:'',mediaStart:0,crops:[],...(['profile'].includes(item.family)?{images:['assets/person-1.png','assets/person-2.png','assets/mark.png']}:{})};}

export function defaults(item){

 const q=baseDefaults(item),v=item.variant;

 if(item.family==='board')q.title='Follow the evidence';

 if(item.family==='gallery'){q.title='A different perspective';q.labels=['First light','New horizons','The details','Another angle','In focus','What comes next'];}

 if(item.family==='profile'){q.title='Alex Morgan';q.subtitle='A story worth telling';q.labels=['Alex Morgan','Jordan Lee'];if(['headline','legacy','falling'].includes(v))q.title='HORIZONS';if(['token','echo','stat','cost'].includes(v)){q.images=['assets/mark.png','assets/person-1.png'];q.title='Ideas into action';}if(v==='stat'){q.number=42000000;q.prefix='$';q.suffix='';}if(v==='cost'){q.prefix='$';q.number=.5;q.suffix=' / unit';q.title='A small change adds up';}}

 if(item.family==='title'){q.title='Make the connection';q.subtitle='The next chapter starts here';if(v==='question')q.title='What changed?';if(v==='clock')q.title='07:30';if(['date','date-slide'].includes(v)){q.title='24 September';q.subtitle='2026';}if(v==='money'){q.number=42.5;q.prefix='$';q.suffix='';q.subtitle='One decision. A different outcome.';}if(v==='life'){q.title='Alex Morgan';q.subtitle='1989 — 2026';}if(v==='chapter')q.title='A turning point';}

 if(item.family==='article'){q.title='The details change the story';q.label='THE FIELD JOURNAL';if(v==='typewriter')q.title='A story begins';if(v==='highlights')q.highlight='Every detail|bigger picture|possibilities';}

 if(item.family==='chart'){q.title='A changing landscape';q.label='ILLUSTRATIVE DATA';q.suffix='';if(v==='donut')q.subtitle='Share of the total';}

 if(item.family==='diagram'){q.title='Ideas become connections';q.images=['assets/mark.png','assets/person-1.png','assets/person-2.png','assets/landscape-1.png','assets/landscape-2.png','assets/landscape-3.png'];q.suffix='';if(v==='population'||v==='crowd-callouts'){q.number=120;q.title='Every person counts';}if(v==='wealth'){q.number=120000000;q.prefix='$';q.title='A network of value';q.images=['assets/person-1.png','assets/mark.png','assets/mark.png','assets/mark.png','assets/mark.png'];}if(v==='org'){q.labels=['Alex Morgan','Research','Design','Production','Review'];q.images=['assets/person-1.png','assets/person-2.png','assets/person-1.png','assets/person-2.png','assets/person-1.png'];}}

 if(item.family==='map'){q.title='Where the story unfolds';q.subtitle='24 September, 2026';if(['border','labels','outlines'].includes(v))q.mapBounds=[-15,32,40,62];if(['aerial','circle','callout','zoom'].includes(v)){q.images=['assets/map-sketch.png','assets/mark.png'];q.pointLabels=['Area of interest'];}if(v==='person'||v==='sovereign')q.images=['assets/person-1.png','assets/mark.png'];if(v==='split')q.images=['assets/landscape-2.png'];}

 if(item.family==='transition'){q.labels=['Before','After'];q.exit=0;}

 return q;

}

export function normalize(item,input={}){

 const base=defaults(item),c={...base,...input};c.duration=clamp(Number(c.duration)||6,.3,60);c.enter=clamp(Number(c.enter)||.22,.03,.45);c.exit=clamp(Number(c.exit)||0,0,.4);c.number=clamp(Number(c.number)||0,0,1e15);c.motion=clamp(Number(c.motion)||0,0,2);

 c.labels=Array.isArray(c.labels)?c.labels.map(String).slice(0,12):[];

 c.data=Array.isArray(c.data)?c.data.filter(d=>d&&typeof d==='object').slice(0,8).map(d=>({label:String(d.label??''),value:Math.max(0,Number(d.value)||0),values:(Array.isArray(d.values)?d.values:[0,Number(d.value)||0]).map(Number).filter(Number.isFinite).map(x=>Math.max(0,x)).slice(0,300)})).filter(d=>d.values.length>=2):[];

 c.images=Array.isArray(c.images)?c.images.map(x=>typeof x==='string'?x:'').slice(0,12):[];

 c.countries=Array.isArray(c.countries)?c.countries.map(String).slice(0,12):base.countries;

 c.points=Array.isArray(c.points)?c.points.filter(x=>Array.isArray(x)&&x.length===2&&x.every(v=>Number.isFinite(Number(v)))).map(x=>x.map(Number)).slice(0,24):base.points;

 c.pointLabels=Array.isArray(c.pointLabels)?c.pointLabels.map(String):[];c.axisLabels=Array.isArray(c.axisLabels)?c.axisLabels.map(String):[];

 if(!Array.isArray(c.mapBounds)||c.mapBounds.length!==4||!c.mapBounds.every(x=>Number.isFinite(Number(x)))||Number(c.mapBounds[0])>=Number(c.mapBounds[2])||Number(c.mapBounds[1])>=Number(c.mapBounds[3]))c.mapBounds=base.mapBounds;else c.mapBounds=c.mapBounds.map(Number);

 c.focusX=clamp(Number(c.focusX)||0);c.focusY=clamp(Number(c.focusY)||0);c.zoom=clamp(Number(c.zoom)||1,1,4);c.crops=Array.isArray(c.crops)?c.crops:[];

 return c;

}

function round(c,x,y,w,h,r=12){c.beginPath();c.roundRect(x,y,w,h,r);}

function box(c,x,y,w,h,color,r=12){c.fillStyle=color;round(c,x,y,w,h,r);c.fill();}

function circle(c,x,y,r,color){c.beginPath();c.arc(x,y,Math.max(.01,r),0,TAU);c.fillStyle=color;c.fill();}

function line(c,pts,color,width=3,progress=1){if(pts.length<2)return;c.save();c.lineCap='round';c.lineJoin='round';c.strokeStyle=color;c.lineWidth=width;c.beginPath();c.moveTo(...pts[0]);let count=(pts.length-1)*clamp(progress),n=Math.floor(count);for(let i=1;i<=n;i++)c.lineTo(...pts[i]);if(n<pts.length-1)c.lineTo(mix(pts[n][0],pts[n+1][0],count-n),mix(pts[n][1],pts[n+1][1],count-n));c.stroke();c.restore();}

function font(c,size=36,weight=600,family='Arimo'){c.font=`${weight} ${size}px "${family}"`;c.textBaseline='middle';}

function text(c,str,x,y,size,color,max=1100,align='left',weight=600,family='Arimo'){

 str=String(str??'');font(c,size,weight,family);while(c.measureText(str).width>max&&size>10){size-=1;font(c,size,weight,family);}c.fillStyle=color;c.textAlign=align;c.fillText(str,x,y);return size;

}

function wrap(c,str,x,y,w,size,color,opts={}){

 const lh=size*1.3; font(c,size,opts.weight||500,opts.font||'Arimo');const words=String(str??'').split(/\s+/),lines=[];let l='';for(const word of words){if(c.measureText(l+' '+word).width>w&&l){lines.push(l);l=word;}else l+=(l?' ':'')+word;}if(l)lines.push(l);let limit=opts.lines||7;

 lines.slice(0,limit).forEach((s,i)=>text(c,s,x,y+i*lh,size,color,w,opts.align||'left',opts.weight||500,opts.font||'Arimo'));return Math.min(lines.length,limit)*lh;

}

function badge(c,str,x,y,color,ink,max=900,size=25){if(String(str??'').trim()==='')return 0;font(c,size,700);let w=Math.min(max,c.measureText(String(str)).width+36);box(c,x,y-23,w,46,color,6);text(c,str,x+18,y,size,ink,w-32);return w;}

function photo(c,img,x,y,w,h,fit='cover',crop={}){

 if(!img)return;const iw=img.videoWidth||img.width,ih=img.videoHeight||img.height;if(!iw||!ih)return;c.save();c.beginPath();c.rect(x,y,w,h);c.clip();let s=(fit==='contain'?Math.min:Math.max)(w/iw,h/ih)*(Number(crop.zoom)||1);let dx=x+(w-iw*s)*(crop.x??.5),dy=y+(h-ih*s)*(crop.y??.5);c.drawImage(img,dx,dy,iw*s,ih*s);c.restore();

}

function asset(c,env,i,x,y,w,h,fit='cover',cfg={}){photo(c,env.images?.[i%Math.max(1,env.images?.length||1)],x,y,w,h,fit,cfg.crops?.[i]||{});}

function shadow(c){c.shadowColor='#00000045';c.shadowBlur=24;c.shadowOffsetY=12;}

function card(c,env,i,x,y,w,h,angle=0,cfg={},label=''){

 c.save();c.translate(x+w/2,y+h/2);c.rotate(angle);shadow(c);box(c,-w/2-9,-h/2-9,w+18,h+18+(label?46:0),'#f7f2e7',4);c.shadowColor='transparent';asset(c,env,i,-w/2,-h/2,w,h,cfg.fit,cfg);if(label)text(c,label,0,h/2+27,22,'#172b30',w-12,'center');c.restore();

}

function grid(c,C){c.save();c.globalAlpha=.12;c.strokeStyle=C.fg;c.lineWidth=1;for(let x=0;x<1600;x+=48){c.beginPath();c.moveTo(x,0);c.lineTo(x,900);c.stroke();}for(let y=0;y<900;y+=48){c.beginPath();c.moveTo(0,y);c.lineTo(1600,y);c.stroke();}c.restore();}

function arrow(c,x1,y1,x2,y2,color,width=5){line(c,[[x1,y1],[x2,y2]],color,width);let a=Math.atan2(y2-y1,x2-x1);line(c,[[x2-20*Math.cos(a-.5),y2-20*Math.sin(a-.5)],[x2,y2],[x2-20*Math.cos(a+.5),y2-20*Math.sin(a+.5)]],color,width);}

function ring(c,x,y,r,color,progress=1,width=4){c.save();c.strokeStyle=color;c.lineWidth=width;c.lineCap='round';c.beginPath();c.arc(x,y,r,-Math.PI/2,-Math.PI/2+TAU*Math.min(.999999,clamp(progress)));c.stroke();c.restore();}

function person(c,x,y,s,color){circle(c,x,y,s*.2,color);box(c,x-s*.22,y+s*.28,s*.44,s*.6,color,s*.08);line(c,[[x-s*.15,y+s*.73],[x-s*.19,y+s*1.18]],color,s*.14);line(c,[[x+s*.15,y+s*.73],[x+s*.19,y+s*1.18]],color,s*.14);}

function header(c,C,cfg,p){}

function bg(c,cfg,env,C,gridOn=false){}

function palette(cfg){let light=cfg.theme==='light';return {light,bg:light?'#eeeae0':cfg.background,fg:light?'#172c32':cfg.foreground,muted:light?'#666666':'#999999',accent:cfg.accent,secondary:cfg.secondary,panel:light?'#ffffffdd':'#292929'};}

export function render(ctx,item,input,time,env={}){

 const cfg=normalize(item,input),C=palette(cfg),p=clamp(time/cfg.duration),e=ease(p/cfg.enter),out=cfg.exit?ease((1-p)/cfg.exit):1;

 ctx.save();ctx.scale(ctx.canvas.width/1600,ctx.canvas.height/900);ctx.globalAlpha=item.family==='transition'?1:out;

 if(item.family==='transition'){drawTransition(ctx,item.variant,cfg,p,env,C);ctx.restore();return;}

 bg(ctx,cfg,env,C,['chart','diagram','board'].includes(item.family)||item.variant==='caption-grid');

 const draw={title:drawTitle,gallery:drawGallery,profile:drawProfile,article:drawArticle,chart:drawChart,diagram:drawDiagram,map:drawMap,board:drawBoard}[item.family];

 if(!draw)throw Error('Unknown renderer family '+item.family);draw(ctx,item.variant,cfg,p,e,env,C);ctx.restore();

}

function drawTitle(c,v,q,p,e,env,C){

 const a=C.accent,ink=C.fg; c.save();

 if(['lower','life','circled'].includes(v)){

  let x=88-(1-e)*600,y=v==='life'?720:745;

  if(v==='lower'){badge(c,q.label,x,y-72,a,C.bg);box(c,x,y-42,1280,82,ink,3);text(c,q.title,x+28,y,48,C.bg,1224);}

  else if(v==='life'){c.globalAlpha=e;c.translate(0,(1-e)*45);text(c,q.title,800,y,48,ink,1300,'center');text(c,q.subtitle,800,y+53,26,C.muted,1200,'center');}

  else {let bw=badge(c,q.title,x,y,ink,C.bg,1200,37);c.save();c.translate(x+bw/2,y);c.scale((bw+55)/290,.47);ring(c,0,0,145,a,ease((p-.2)/.45),2);c.restore();}c.restore();return;

 }

 if(v==='clock'){box(c,610,90,380*e,125,a,14);text(c,q.title==='Time stamp'?'07:30':q.title,800,145,61,C.bg,335,'center');text(c,q.subtitle,800,245,27,ink,1300,'center');c.restore();return;}

 if(v==='year'){line(c,[[240,460],[1360,460]],C.muted,2);let x=mix(240,1360,ease(p/.8));circle(c,x,460,12,a);text(c,Math.round(mix(q.yearStart,q.yearEnd,ease(p/.8))),x,525,55,ink,350,'center');text(c,q.title,800,315,40,ink,1350,'center');c.restore();return;}

 if(v==='money'){let value=q.prefix+fmt(q.number*ease(p/.55),q.decimals??2)+q.suffix;text(c,value,800,450,112,ink,1380,'center');text(c,q.subtitle,800,580,31,C.muted,1380,'center');c.restore();return;}

 if(v==='caption'||v==='caption-grid'||v==='phrases'){

  let source=v==='phrases'?(q.labels[Math.min(q.labels.length-1,Math.floor(p*q.labels.length))]||q.title):(q.body||q.title);let words=source.split(/\s+/);let str=words.slice(0,Math.ceil(words.length*clamp(p/.78))).join(' ');wrap(c,str,800,v==='caption'?740:400,1300,42,ink,{align:'center',lines:3,font:q.font});c.restore();return;

 }

 if(v==='chapter'){c.globalAlpha=.15*e;font(c,580,700,q.font);c.strokeStyle=ink;c.lineWidth=2;c.textAlign='center';c.strokeText(q.chapter,800,430);c.globalAlpha=1;}

 if(v==='date'||v==='date-slide'){c.globalAlpha=e;c.translate(0,v==='date'?(1-e)*60:0);text(c,q.title,800+(v==='date-slide'?(1-e)*550:0),405,96,ink,1390,'center',600,q.font);text(c,q.subtitle,800,515,46,a,1350,'center');c.restore();return;}

 if(v==='magnify'){

  text(c,q.title,800,450,66,ink,1340,'center',700,q.font);let x=mix(240,1360,clamp((p-.1)/.8)),y=450;

  c.save();c.beginPath();c.arc(x,y,145,0,TAU);c.clip();box(c,x-160,y-160,320,320,C.bg,0);c.translate(x,y);c.scale(q.zoom,q.zoom);c.translate(-x,-y);text(c,q.title,800,450,66,ink,1340,'center',700,q.font);c.restore();ring(c,x,y,148,a,1,7);line(c,[[x+103,y+104],[x+200,y+220]],a,20);c.restore();return;

 }

 let title=q.title;

 if(['type','opening'].includes(v))title=title.slice(0,Math.ceil(title.length*clamp(p/.5)));

 let scale=v==='push'?1+q.motion*.15*p:1;c.translate(800,450);c.scale(scale,scale);c.translate(-800,-450);

 c.globalAlpha=e;c.translate(0,(1-e)*70);

 if(['highlight','question'].includes(v)){

  let parts=v==='highlight'?title.split(/\s+/).reduce((arr,w,i)=>{let j=Math.floor(i/3);arr[j]=(arr[j]?arr[j]+' ':'')+w;return arr;},[]):[title];

  parts.slice(0,4).forEach((s,i)=>{let f=ease((p-i*.07)/.2);font(c,62,700,q.font);let w=Math.min(1370,c.measureText(s).width+64);c.save();c.globalAlpha*=f;box(c,800-w/2,355+i*92,w,77,a,4);text(c,s,800,393+i*92,62,C.bg,w-44,'center',700,q.font);c.restore();});

 }else if(v==='hierarchy'){text(c,q.subtitle,800,340,43,a,1350,'center',500,'Gelasio');text(c,title,800,475,100,ink,1370,'center',700,q.font);}

 else if(v==='headline'){font(c,80,700,q.font);let rows=[],row='';for(let word of title.split(/\s+/)){if(c.measureText(row+' '+word).width>1120&&row){rows.push(row);row=word;}else row+=(row?' ':'')+word;}if(row)rows.push(row);rows.slice(0,4).forEach((str,i)=>{let f=ease((p-i*.10)/.22);c.save();c.globalAlpha=f;text(c,str,240,310+i*104+(1-f)*40,80,ink,1120,'left',700,q.font);c.restore();});}

 else{text(c,title,800,420,v==='chapter'?94:78,ink,1380,'center',600,q.font);text(c,q.subtitle,800,522,32,C.muted,1340,'center',400,q.font);}

 if(v==='scribble'){c.save();c.translate(800,435);c.scale(2.2,.68);ring(c,0,0,226,a,ease((p-.22)/.55),2.7);c.restore();}

 if(['opening','chapter','type'].includes(v))line(c,[[540,580],[1060,580]],a,3,ease((p-.25)/.4));c.restore();

}

function drawTransition(c,v,q,p,env,C){

 const prog=p<=0?0:p>=1?1:p*p*(3-2*p);asset(c,env,0,0,0,1600,900,q.fit,q);

 if(v==='dissolve'){c.save();c.globalAlpha=prog;asset(c,env,1,0,0,1600,900,q.fit,q);c.restore();return;}

 if(v==='split'){c.save();c.beginPath();c.rect(0,0,1600,900*prog);c.clip();asset(c,env,1,0,0,1600,900,q.fit,q);c.restore();if(p>0&&p<1){line(c,[[0,900*prog],[1600,900*prog]],C.accent,5);badge(c,q.labels[0]||'Before',80,850,C.bg,C.fg);badge(c,q.labels[1]||'After',80,50,C.accent,C.bg);}return;}

 // A true two-input flip: endpoints remain full outgoing/incoming media, middle is a framed card turn.

 if(p===0||p===1){asset(c,env,p===0?0:1,0,0,1600,900,q.fit,q);return;}

 box(c,0,0,1600,900,C.bg,0);let sx=Math.max(.012,Math.abs(Math.cos(Math.PI*prog))),inset=Math.sin(Math.PI*prog)*80;c.save();c.translate(800,450);c.scale(sx,1);card(c,env,p<.5?0:1,-800+inset,-450+inset,1600-2*inset,900-2*inset,Math.sin(TAU*prog)*.03,q);c.restore();

}

function drawGallery(c,v,q,p,e,env,C){

 const labels=q.labels;const a=C.accent;

 if(['focus','magnifier'].includes(v)){

  let x=240,y=180,w=1120,h=560;if(v==='focus'){c.save();c.filter='blur(14px)';asset(c,env,0,-22,-22,1644,944,q.fit,q);c.restore();c.fillStyle='#061317a6';c.fillRect(0,0,1600,900);let fx=q.focusX*1600,fy=q.focusY*900;c.save();round(c,fx-260,fy-185,520,370,22);c.clip();asset(c,env,0,0,0,1600,900,q.fit,q);c.restore();c.strokeStyle=a;c.lineWidth=3;round(c,fx-260,fy-185,520,370,22);c.stroke();badge(c,q.title,88,805,a,C.bg,1350,28);}

  else{card(c,env,0,x,y,w,h,0,q);let lx=mix(450,1120,ease(p/.8)),ly=460+Math.sin(p*TAU)*70;c.save();c.beginPath();c.arc(lx,ly,140,0,TAU);c.clip();c.translate(lx,ly);c.scale(q.zoom,q.zoom);c.translate(-lx,-ly);asset(c,env,0,x,y,w,h,q.fit,q);c.restore();ring(c,lx,ly,144,a,1,7);line(c,[[lx+98,ly+102],[lx+190,ly+210]],a,17);}return;

 }

 if(v==='film'){c.save();c.globalAlpha=e;card(c,env,0,180,175,1240,550,0,q);for(let j=0;j<24;j++){box(c,195+j*50,138,25,17,C.fg,2);box(c,195+j*50,745,25,17,C.fg,2);}badge(c,q.label,225,210,C.bg,C.fg,800,16);text(c,q.title,800,822,31,C.fg,1300,'center');c.restore();return;}

 if(v==='reel'){for(let i=0;i<6;i++){let x=360+(i%2)*465,y=-(i%3)*475+(p*430)+170;card(c,env,i,x,y,380,430,(i%2?.015:-.015),q);}return;}

 if(v==='timeline'){c.save();let cam=ease(p/.9)*1000*q.motion;c.translate(-cam,0);line(c,[[220,610],[2380,610]],C.muted,2);for(let i=0;i<6;i++){let x=220+i*420;card(c,env,i,x-170,270,340,225,0,q);circle(c,x,610,12,i<=p*6?a:C.muted);text(c,labels[i]||`Stage ${i+1}`,x,680,26,C.fg,380,'center');}line(c,[[220,610],[2380,610]],a,5,p);c.restore();return;}

 if(v==='callouts'){

  let s=mix(1.6,1,ease(p/.35));c.save();c.translate(800,450);c.scale(s,s);card(c,env,0,-300,-185,600,370,0,q);c.restore();[[190,225],[1150,255],[950,760]].forEach(([x,y],i)=>{let f=ease((p-.22-i*.08)/.25);line(c,[[i?1080:510,i===2?630:290],[x+65,y]],a,2,f);c.save();c.globalAlpha=f;badge(c,labels[i]||'Detail',x,y,a,C.bg,500,24);c.restore();});return;

 }

 if(v==='symbols'||v==='logos'){header(c,C,q,p);for(let i=0;i<Math.min(6,env.images?.length||4);i++){let f=ease((p-i*.06)/.28);c.save();c.globalAlpha=f;asset(c,env,i,145+i*220,340+(1-f)*160,175,175,'contain',q);text(c,labels[i]||'',230+i*220,595,23,C.fg,205,'center');c.restore();}return;}

 if(v==='stack'||v==='collage'||v==='annotated'){

  let n=v==='stack'?Math.min(6,env.images?.length||5):4;

  for(let i=0;i<n;i++){let f=ease((p-i*.075)/.24);if(f<=0)continue;let x,y,w,h,rot;

   if(v==='stack'){x=420+i*9;y=220+i*7;w=740;h=425;rot=(i%2?1:-1)*(.065+i*.012);}

   else{x=[120,730,430,980][i];y=[170,110,440,415][i];w=500;h=285;rot=[-.07,.05,.04,-.055][i];}

   c.save();c.globalAlpha=f;card(c,env,i,x+(1-f)*800,y,w,h,rot,q,v==='annotated'?labels[i]||'Detail':'');c.restore();

   if(v==='annotated'&&p>.55){c.save();c.translate(x+w/2,y+h+25);c.scale(1.8,.4);ring(c,0,0,95,a,ease((p-.55)/.35),2);c.restore();}

  }return;

 }

 if(v==='vertical'){for(let i=0;i<3;i++){let f=ease((p-i*.11)/.32),cx=800+(i-1)*390*f;c.save();c.globalAlpha=f;c.beginPath();c.rect(cx-165*f,155,330*f,610);c.clip();card(c,env,i,cx-165,170,330,540,0,q,labels[i]||'');c.restore();}return;}

 if(['pair','connected','diagonal'].includes(v)){header(c,C,q,p);for(let i=0;i<2;i++){let f=ease((p-i*.09)/.3),x=140+i*720,y=280;if(v==='diagonal')y=230+i*145+(1-f)*(i?-600:600);c.save();c.globalAlpha=f;card(c,env,i,x,y,580,350,v==='diagonal'?(i?.03:-.03):0,q,labels[i]||'');c.restore();}if(v==='connected')arrow(c,735,440,865,440,a,5);return;}

 // Featured media card

 c.save();c.globalAlpha=e;card(c,env,0,340,190+(1-e)*220,920,520,0,q,q.title);c.restore();

}

function drawProfile(c,v,q,p,e,env,C){

 let a=C.accent,ink=C.fg;

 if(['token','echo','stat','cost'].includes(v)){

  let x=v==='cost'?1030:800,y=v==='cost'?410:370;

  if(v==='echo'){c.save();c.filter='blur(28px)';c.globalAlpha=.12;c.translate(800,450);c.rotate(-.15+p*.12);asset(c,env,0,-620,-580,1240,1160,'contain',q);c.restore();}

  c.save();c.translate(x,y);let s=(.3+.7*e);c.scale(s*(v==='token'?Math.max(.15,Math.cos((1-e)*Math.PI*1.8)):1),s);if(v==='token')circle(c,0,0,165,C.panel);asset(c,env,0,-140,-140,280,280,'contain',q);c.restore();

  if(v==='stat'){badge(c,q.prefix+fmt(Math.round(q.number*ease(p/.6)))+q.suffix,370,640,a,C.bg,1100,44);text(c,q.title,800,743,40,ink,1380,'center');}

  else if(v==='cost'){text(c,q.prefix+fmtAs(q.number)+q.suffix,190,280,72,a,760);text(c,q.title,190,375,36,ink,740);arrow(c,480,510,270,710,ink,14);}

  else{text(c,q.title,800,665,52,ink,1360,'center');text(c,q.subtitle,800,737,26,C.muted,1300,'center');}return;

 }

 if(v==='falling'){

  for(let i=0;i<10;i++){let z=.5+(i%3)*.3,x=(i*197)%1600,y=((p*(850+i*70)*q.motion+i*160)%1400)-260;c.save();c.globalAlpha=.25+z*.4;c.translate(x,y);c.rotate(.3+i*.7+p);asset(c,env,i%3,-100*z,-130*z,200*z,260*z,'contain',q);c.restore();}

  text(c,q.title,800,440,134,ink,1380,'center',500,'Gelasio');text(c,q.subtitle,800,572,30,a,1300,'center');return;

 }

 if(['pair','archive','age','specimens'].includes(v)){

  header(c,C,q,p);for(let i=0;i<2;i++){let f=ease((p-i*.15)/.25),x=225+i*680;c.save();c.globalAlpha=f;asset(c,env,i,x,240+(1-f)*120,470,450,v==='specimens'?'contain':q.fit,q);if(v==='archive'){c.translate(x+235,742);c.transform(1,0,-.18,1,0,0);box(c,-260,-27,520,56,ink,0);text(c,q.labels[i]||'',0,0,29,C.bg,490,'center',600,'Gelasio');}else text(c,q.labels[i]||'',x+235,754,33,ink,540,'center');c.restore();}

  if(v==='age')arrow(c,737,455,862,455,a,11);if(v==='specimens')text(c,q.subtitle,800,834,29,C.muted,1360,'center');return;

 }

 if(v==='legacy'||v==='headline'){

  text(c,q.title,800,235+(1-e)*50,170,v==='legacy'?a:ink,1450,'center',v==='legacy'?500:700,v==='legacy'?'Gelasio':q.font);c.save();c.globalAlpha=e;asset(c,env,0,450,295+(1-e)*500,700,630,'contain',q);c.restore();text(c,q.subtitle,800,817,30,ink,1380,'center');return;

 }

 let sx=v==='quote'?875:120,sy=190,sw=650,sh=710;

 if(v==='ribbon'){c.save();c.globalAlpha=.3;box(c,50,350,1440*e,155,a,0);c.restore();}

 c.save();c.globalAlpha=e;asset(c,env,0,sx+(1-e)*(v==='quote'?500:-500),sy,sw,sh,'contain',q);c.restore();

 if(v==='quote'){text(c,'“',140,250,135,a,100);wrap(c,q.body,160,335,660,45,ink,{lines:6,font:'Gelasio'});text(c,q.title,160,725,31,a,650);text(c,q.subtitle,160,782,23,C.muted,650);return;}

 

 if(v==='torn'){c.save();c.fillStyle='#f4edde';c.beginPath();c.moveTo(760,280);for(let x=760;x<=1520;x+=24)c.lineTo(x,280+Math.sin(x*1.7)*7);c.lineTo(1520,630);for(let x=1520;x>=760;x-=24)c.lineTo(x,630+Math.sin(x*1.2)*8);c.closePath();c.fill();c.restore();ink='#102328';}

 text(c,q.label,860,325,25,a,650);wrap(c,q.title,850,425,650,70,ink,{lines:3,font:v==='torn'?'Gelasio':q.font,weight:700});text(c,q.subtitle,850,675,28,C.muted,650);

 if(v==='callout'){let pts=[];for(let i=0;i<=40;i++){let t=i/40;pts.push([mix(1140,600,t),610+Math.sin(t*Math.PI)*100]);}line(c,pts,a,4,ease((p-.25)/.5));circle(c,600,610,7,a);}

}

function highlighted(c,body,phrase,x,y,w,size,C,progress=1,maxLines=8){

 font(c,size,400,'Gelasio');let raw=String(body),words=[...raw.matchAll(/\S+/g)],rows=[[]],width=0,space=c.measureText(' ').width;

 const spans=String(phrase||'').split('|').map(v=>v.trim()).filter(Boolean).flatMap((ph,j)=>{let out=[],at=0;while((at=raw.toLowerCase().indexOf(ph.toLowerCase(),at))>=0){out.push({start:at,end:at+ph.length,order:j});at+=ph.length;}return out;});

 for(let match of words){let ww=c.measureText(match[0]).width;if(width+ww>w&&rows.at(-1).length){rows.push([]);width=0;}rows.at(-1).push({str:match[0],start:match.index,end:match.index+match[0].length,x:width,w:ww});width+=ww+space;}

 rows.slice(0,maxLines).forEach((row,i)=>row.forEach(word=>{let ph=spans.find(v=>word.start<v.end&&word.end>v.start),f=ph?ease((progress-ph.order*.13-i*.03)/.35):0;if(f>0)box(c,x+word.x-2,y+i*size*1.55-size*.52,(word.w+space)*f,size*1.13,C.accent,1);text(c,word.str,x+word.x,y+i*size*1.55,size,f>.92?C.bg:C.fg,word.w+2,'left',400,'Gelasio');}));

}

function drawArticle(c,v,q,p,e,env,C){

 const paper={...C,bg:'#f7f2e7',fg:'#213237',muted:'#657274',accent:q.accent};

 if(v==='paragraph'){header(c,C,q,p);highlighted(c,q.body,q.highlight,240,365,1120,43,C,clamp((p-.2)/.6),7);return;}

 if(v==='column'){line(c,[[190,250],[1410,250]],C.accent,5,e);wrap(c,q.title,190,340,1220,62,C.fg,{font:'Gelasio',lines:3});highlighted(c,q.body,q.highlight,190,565,1190,30,C,p,5);return;}

 if(v==='news'){header(c,C,q,p);c.save();c.globalAlpha=e;card(c,env,0,430,290,740,410,0,q);c.restore();text(c,q.subtitle,800,800,27,C.muted,1400,'center');return;}

 if(v==='typewriter'){

  c.save();c.translate(0,mix(90,0,e));shadow(c);box(c,180,130,1240,610,paper.bg,3);c.shadowColor='transparent';text(c,q.label,265,214,25,paper.muted,1000);let s=q.title.slice(0,Math.ceil(q.title.length*clamp(p/.65)));text(c,s,800,365,80,paper.fg,1070,'center',500,'Gelasio');line(c,[[260,510],[1340,510]],'#b5b5ab',2);text(c,q.subtitle,265,600,30,paper.muted,1090);c.restore();box(c,120,737,1360,130,'#243236',14);for(let i=0;i<34;i++)box(c,145+i*38,762,26,20,'#6c7778',3);return;

 }

 function sheet(x,y,w,h,angle,index=0){c.save();c.translate(x+w/2,y+h/2);c.rotate(angle);shadow(c);box(c,-w/2,-h/2,w,h,paper.bg,3);c.shadowColor='transparent';let xx=-w/2+55,yy=-h/2+58;text(c,index?q.labels[index]||q.label:q.label,xx,yy,20,paper.muted,w-110);line(c,[[xx,yy+30],[w/2-55,yy+30]],paper.fg,2);let th=wrap(c,q.title,xx,yy+80,w-110,38,paper.fg,{lines:3,font:'Gelasio',weight:700});let bodyY=yy+105+th;if(v==='zoom'){asset(c,env,0,xx,bodyY,w-110,190,q.fit,q);bodyY+=230;}let available=Math.max(1,Math.floor((h/2-45-bodyY)/(23*1.55)));highlighted(c,q.body,q.highlight,xx,bodyY,w-110,23,paper,ease((p-.2)/.7),Math.min(12,available));c.restore();}

 if(v==='stack'){for(let i=0;i<4;i++){let f=ease((p-i*.14)/.22);if(f)sheet(515+i*12+(1-f)*900,95+i*13,590,710,(i%2?-.055:.06),i);}return;}

 let scale=v==='zoom'?mix(.82,1.14,ease(p/.9)):1;c.save();c.translate(800,450);c.scale(scale,scale);c.translate(-800,-450);sheet(415,70+(1-e)*450,770,760,-.018);c.restore();

}

function drawBoard(c,v,q,p,e,env,C){

 const coords=v==='wall'?[[155,235],[780,180],[1170,505],[425,560],[1040,50],[60,625]]:[[650,280],[120,175],[1110,160],[150,560],[1080,575],[675,610]];

 c.save();let zoom=v==='wall'?1+.48*Math.sin(p*Math.PI)*q.motion:1+.14*p*q.motion;let target=coords[Math.min(5,Math.floor(p*6))];let pan=v==='wall'?Math.sin(p*TAU)*150:0;c.translate(800+pan,450);c.scale(zoom,zoom);c.translate(-800,-450);

 for(let i=1;i<coords.length;i++)line(c,[[coords[0][0]+140,coords[0][1]],[coords[i][0]+130,coords[i][1]]],C.accent,3,ease((p-i*.035)/.2));

 coords.forEach(([x,y],i)=>{let f=ease((p-i*.02)/.16);c.save();c.globalAlpha=f;card(c,env,i,x,y+(1-f)*100,260,165,(i%2?-.06:.045),q,q.labels[i]||`Evidence ${i+1}`);circle(c,x+130,y-5,9,C.secondary);c.restore();});c.restore();badge(c,q.title,65,67,C.bg,C.fg,1400,28);

}

function drawChart(c,v,q,p,e,env,C){

 const data=q.data.length?q.data:[{label:'Value',value:q.number,values:[0,q.number]}],colors=[C.accent,C.secondary,'#819afa','#c6a2ef','#eecb68','#7fbbc8','#e287b8','#82c58c'];

 header(c,C,q,p);let progress=ease((p-.12)/.64);

 if(v==='donut'||v==='pies'){

  let n=v==='pies'?2:1;for(let i=0;i<n;i++){let x=n===1?800:500+i*600,y=445,val=v==='pies'?clamp(Number(data[i]?.value??q.number),0,100):clamp(q.number,0,100);ring(c,x,y,175,C.panel,1,55);ring(c,x,y,175,colors[i],val/100*progress,55);text(c,Math.round(val*progress)+'%',x,y,76,C.fg,325,'center');text(c,n===1?q.subtitle:data[i]?.label||'',x,700,31,C.muted,520,'center');}return;

 }

 if(v==='table'){let n=Math.min(6,data.length);box(c,300,225,1000,90*n+40,C.panel,16);for(let i=0;i<n;i++){let f=ease((p-.12-i*.06)/.25),y=290+i*90;c.save();c.globalAlpha=f;asset(c,env,i,335,y-28,56,56,'contain',q);text(c,data[i].label,425,y,30,C.fg,560);text(c,q.prefix+fmt(Number(data[i].value||0))+q.suffix,1240,y,32,colors[i],350,'right');line(c,[[335,y+40],[1260,y+40]],C.muted,1);c.restore();}return;}

 let x=210,y=725,w=1200,h=470;

 if(v==='panel'){box(c,130,190,1340,615,C.panel,18);}

 let series=data.slice(0,['single','scatter','logo-line','area'].includes(v)?1:v==='three-lines'?3:2);let isBar=['bars','portraits','horizontal'].includes(v);let vals=isBar?data.map(d=>Number(d.value)||0):series.flatMap(d=>d.values.map(Number));let rawMax=Math.max(1,...vals),step=10**Math.floor(Math.log10(rawMax))/2,max=Math.ceil(rawMax*1.08/step)*step;

 if(v!=='horizontal')for(let i=0;i<=4;i++){let yy=y-i*h/4;line(c,[[x,yy],[x+w,yy]],C.muted,1);text(c,q.prefix+fmt(max*i/4,Number.isInteger(max*i/4)?0:1)+q.suffix,x-23,yy,20,C.muted,125,'right');}

 if(v!=='horizontal')line(c,[[x,y-h],[x,y],[x+w,y]],C.fg,2);

 if(v==='horizontal'){

  let ds=data.slice(0,6),mx=Math.max(1,...ds.map(d=>Number(d.value)||0))*1.15;c.save();

  ds.forEach((d,i)=>{let yy=285+i*83,ww=1000*(Number(d.value)||0)/mx*ease((p-.12-i*.035)/.55);text(c,d.label,350,yy,26,C.fg,245,'right');box(c,390,yy-24,Math.max(1,ww),48,colors[i],4);text(c,q.prefix+fmt(Number(d.value)||0)+q.suffix,410+ww,yy,23,C.fg,200);});c.restore();return;

 }

 if(v==='bars'||v==='portraits'){

  let ds=data.slice(0,v==='bars'?2:4),gap=w/ds.length;ds.forEach((d,i)=>{let bh=(Number(d.value)||0)/max*h*ease((p-.1-i*.06)/.55),bw=Math.min(200,gap*.6),bx=x+gap*(i+.5)-bw/2;box(c,bx,y-bh,bw,Math.max(.01,bh),colors[i],4);text(c,q.prefix+fmt(Math.round((Number(d.value)||0)*progress))+q.suffix,bx+bw/2,y-bh-30,25,C.fg,gap-15,'center');text(c,d.label,bx+bw/2,y+45,25,C.fg,gap-10,'center');if(v==='portraits')asset(c,env,i,bx+bw/2-55,y-110,110,110,'cover',q);});return;

 }

 series.forEach((d,i)=>{let pts=d.values.map((val,j)=>[x+j*w/Math.max(1,d.values.length-1),y-Number(val)/max*h]);

  if(v==='area'){c.save();c.beginPath();c.moveTo(x,y);pts.forEach(pt=>c.lineTo(...pt));c.lineTo(x+w,y);c.closePath();c.clip();c.beginPath();c.rect(x,y-h,w*progress,h);c.clip();asset(c,env,0,x,y-h,w,h,'cover',q);c.fillStyle=C.accent+'60';c.fillRect(x,y-h,w,h);c.restore();}

  line(c,pts,colors[i],v==='scatter'?2:5,progress);

  if(v==='scatter')pts.forEach((pt,j)=>{if(j/(pts.length-1)<=progress)circle(c,...pt,6,colors[i]);});

  let at=progress*(pts.length-1),ix=Math.min(pts.length-2,Math.floor(at)),end=pts.length===1?pts[0]:[mix(pts[ix][0],pts[ix+1][0],at-ix),mix(pts[ix][1],pts[ix+1][1],at-ix)];

  if(v==='logo-line')asset(c,env,0,end[0]-35,end[1]-35,70,70,'contain',q);else circle(c,...end,7,colors[i]);

  text(c,d.label,400+i*420,830,24,colors[i],380,'center');

 });

 (q.axisLabels||[]).slice(0,8).forEach((label,i,arr)=>text(c,label,x+i*w/Math.max(1,arr.length-1),y+36,20,C.muted,145,'center'));

}

function drawDiagram(c,v,q,p,e,env,C){

 const a=C.accent,labels=q.labels.length?q.labels:['One','Two','Three'];

 function node(i,x,y,r,show=1){if(show<=0)return;c.save();c.globalAlpha*=show;circle(c,x,y,r,C.panel);ring(c,x,y,r,a,1,2);c.save();c.beginPath();c.arc(x,y,r*.83,0,TAU);c.clip();asset(c,env,i,x-r*.78,y-r*.78,r*1.56,r*1.56,'contain',q);c.restore();c.restore();}

 if(['population','crowd-callouts','image-crowd'].includes(v)){

  header(c,C,q,p);let n=Math.min(350,Math.max(1,Math.round(q.number))),shown=Math.floor(n*ease((p-.13)/.65)),cols=Math.min(25,Math.ceil(Math.sqrt(n*2))),rows=Math.ceil(n/cols),w=v==='image-crowd'?640:1120,x=v==='image-crowd'?830:240,size=Math.min(38,w/cols*.67,460/rows*.66),gap=w/cols;

  if(v==='image-crowd'){card(c,env,0,110,270,550,335,0,q);arrow(c,675,438,805,438,a,4);}

  for(let i=0;i<n;i++){let xx=x+(i%cols)*gap,yy=260+Math.floor(i/cols)*Math.min(gap*1.6,490/rows);if(i<shown){if(q.symbolMode==='image')asset(c,env,0,xx-size/2,yy-size/2,size,size*1.5,'contain',q);else person(c,xx,yy,size,a);}else person(c,xx,yy,size,C.panel);}

  let s=q.prefix+fmt(Math.round(q.number*ease((p-.13)/.65)))+q.suffix;text(c,s,800,805,62,C.fg,1350,'center');

  if(v==='crowd-callouts'){for(let i=0;i<2;i++){let xx=i?1470:125;ring(c,xx,475,48,C.secondary,ease((p-.5)/.35),3);text(c,labels[i]||'',xx,566,25,C.fg,225,'center');}}return;

 }

 if(v==='checklist'){c.save();c.translate((1-e)*800,0);box(c,850,130,650,640,'#f6f1e7',12);badge(c,q.title,900,192,a,'#102328',550,28);labels.slice(0,6).forEach((s,i)=>{let f=ease((p-.12-i*.08)/.2),yy=305+i*70;round(c,908,yy-16,28,28,3);c.strokeStyle='#657776';c.lineWidth=2;c.stroke();line(c,[[913,yy],[922,yy+6],[934,yy-10]],'#157b68',3,f);c.save();c.globalAlpha=f;text(c,s,963,yy,29,'#193034',475);c.restore();});c.restore();return;}

 if(v==='bullets'){header(c,C,q,p);node(0,450,490,152,e);ring(c,450,490,181,a,clamp(p/.8),3);labels.slice(0,4).forEach((s,i)=>{let f=ease((p-.15-i*.1)/.25),y=350+i*112;c.save();c.globalAlpha=f;circle(c,830,y,8,a);text(c,s,865,y,37,C.fg,600);c.restore();});return;}

 if(v==='steps'){header(c,C,q,p);let n=Math.min(5,labels.length);line(c,[[240,460],[1360,460]],C.muted,2,ease((p-.2)/.6));for(let i=0;i<n;i++){let xx=240+i*1120/(n-1||1),f=ease((p-i*.11)/.27);node(i,xx,460,83,f);c.save();c.globalAlpha=f;text(c,labels[i],xx,610,29,C.fg,260,'center');c.restore();}return;}

 if(v==='org'){header(c,C,q,p);node(0,800,335,100,e);text(c,labels[0],800,478,28,C.fg,650,'center');line(c,[[800,430],[800,530],[230,530],[230,608]],a,2,ease((p-.2)/.4));line(c,[[800,530],[1370,530],[1370,608]],a,2,ease((p-.2)/.4));for(let i=0;i<4;i++){let xx=230+i*380,f=ease((p-.25-i*.07)/.25);line(c,[[xx,530],[xx,610]],a,2,f);node(i+1,xx,658,64,f);c.save();c.globalAlpha=f;text(c,labels[i+1]||`Member ${i+1}`,xx,770,26,C.fg,335,'center');c.restore();}return;}

 if(v==='journey'){

  let pts=[];for(let i=0;i<=200;i++){let t=i/200;pts.push([160+2600*t,450+220*Math.sin(t*TAU*1.5)]);}let cam=ease(p/.9)*1370*q.motion;c.save();c.translate(-cam,0);line(c,pts,C.muted,2);line(c,pts,a,4,clamp(p/.85));for(let i=0;i<6;i++){let t=i/5,x=160+2600*t,y=450+220*Math.sin(t*TAU*1.5);circle(c,x,y,14,a);text(c,String(i+1).padStart(2,'0'),x,y-65,47,C.secondary,200,'center');text(c,labels[i]||'Milestone',x,y+70,34,C.fg,430,'center');}c.restore();badge(c,q.title,70,74,C.bg,C.fg,1400,25);return;

 }

 header(c,C,q,p);let n=v==='cycle'?4:v==='hub'?4:v==='wealth'?4:Math.min(8,Math.max(4,labels.length)),cx=800,cy=v==='wealth'?510:505,r=260;

 if(v==='wealth'){text(c,q.prefix+fmt(Math.round(q.number*e))+q.suffix,1460,240,45,a,620,'right');asset(c,env,0,620,385,360,450,'contain',q);}

 else if(v!=='cycle')node(0,cx,cy,100,e);

 if(v==='cycle')ring(c,cx,cy,r,C.muted,1,2);

 for(let i=0;i<n;i++){let angle=-Math.PI/2+i*TAU/n+(v==='wealth'?Math.sin(p*3)*.04:0),xx=cx+Math.cos(angle)*r,yy=cy+Math.sin(angle)*r,f=ease((p-.08-i*.07)/.25);

  if(v==='cycle'){c.save();c.strokeStyle=a;c.lineWidth=3;c.beginPath();c.arc(cx,cy,r,angle,angle+TAU/n*f);c.stroke();c.restore();}

  else line(c,[[cx,cy],[xx,yy]],a,2,f);

  node(i+1,xx,yy,62,f);c.save();c.globalAlpha=f;text(c,labels[i]||'Connection',xx,yy+94,23,C.fg,270,'center');c.restore();

 }

}

function drawMap(c,v,q,p,e,env,C){

 const features=env.world?.features||[],a=C.accent;let bounds=[...q.mapBounds];

 const selected=features.find(f=>[f.properties.ADMIN,f.properties.NAME,f.properties.ISO_A3].includes(q.country));

 const polys=f=>f.geometry.type==='Polygon'?[f.geometry.coordinates]:f.geometry.coordinates;

 if(q.autoFit!==false&&selected&&['person','date','dots','trace','flags','split','sovereign'].includes(v)){

  let area=ring=>Math.abs(ring.reduce((n,a,i)=>{let b=ring[(i+1)%ring.length];return n+a[0]*b[1]-b[0]*a[1];},0));let mainland=[...polys(selected)].sort((a,b)=>area(b[0])-area(a[0]))[0];let pts=mainland[0];let xs=pts.map(pt=>pt[0]),ys=pts.map(pt=>pt[1]);let left=Math.min(...xs),right=Math.max(...xs),bottom=Math.min(...ys),top=Math.max(...ys),pad=Math.max(right-left,top-bottom)*.15;bounds=[left-pad,bottom-pad,right+pad,top+pad];

 }

 const project=([lon,lat])=>{let scale=Math.min((v==='split'?680:1400)/(bounds[2]-bounds[0]),640/(bounds[3]-bounds[1]));return [(v==='split'?405:800)+(lon-(bounds[0]+bounds[2])/2)*scale,485-(lat-(bounds[1]+bounds[3])/2)*scale];};

 const imageMap=['aerial','callout','circle','zoom'].includes(v);

 if(imageMap){asset(c,env,0,0,0,1600,900,'cover',q);c.fillStyle=C.bg+'30';c.fillRect(0,0,1600,900);if(v==='aerial'){c.save();c.translate(800,450);let z=1+q.motion*p*.35;c.scale(z,z);c.translate(-800+p*90*q.motion,-450);asset(c,env,0,0,0,1600,900,'cover',q);c.restore();badge(c,q.title,80,800,C.bg,C.fg,1350,28);return;}if(v==='zoom'){c.save();c.translate(800,450);let z=1+q.motion*.5*ease(p/.8);c.scale(z,z);c.translate(-800,-450);asset(c,env,0,0,0,1600,900,'cover',q);c.restore();if(p<.55){c.save();c.globalAlpha=1-ease(clamp((p-.1)/.45));bg(c,{...q,transparent:false}, {},C);c.translate(800,450);let z=1+q.motion*3*ease(p/.55);c.scale(z,z);c.translate(-800,-450);drawBase();c.restore();}}}

 else drawBase();

 function shape(f,fill,stroke,progress=1){for(let poly of polys(f)){for(let ri=0;ri<poly.length;ri++){let pts=poly[ri].map(project);c.beginPath();pts.forEach((pt,i)=>i?c.lineTo(...pt):c.moveTo(...pt));c.closePath();if(fill&&ri===0){c.fillStyle=fill;c.fill();}if(stroke)line(c,[...pts,pts[0]],stroke,2,progress);}}}

 function drawBase(){c.save();c.beginPath();c.rect(0,0,1600,900);c.clip();let cacheKey=JSON.stringify([bounds,v==='alert',C.panel,C.muted]);env.mapBases||={};if(!env.mapBases[cacheKey]){let original=c,surface=env.createCanvas(1600,900);c=surface.getContext('2d');features.forEach(f=>shape(f,v==='alert'?'#eeeeee':C.panel,C.muted+'55'));c=original;env.mapBases[cacheKey]=surface;}c.drawImage(env.mapBases[cacheKey],0,0);let arr=['route','flight','pie','alert','city'].includes(v)?[]:v==='border'||v==='outlines'||v==='labels'?q.countries:[q.country];arr.forEach((name,i)=>{let f=features.find(f=>[f.properties.ADMIN,f.properties.NAME,f.properties.ISO_A3].includes(name));if(!f)return;let t=ease((p-.1-i*.08)/.4);c.save();c.globalAlpha=.25+.7*t;shape(f,v==='outlines'||v==='border'||(v==='trace'&&p<.45)?null:[a,C.secondary,'#8c9afb'][i%3],v==='outlines'?[a,C.secondary,'#8c9afb'][i%3]:a,['trace','outlines','border'].includes(v)?t:1);c.restore();if(v==='labels'||v==='border'){let pt=[f.properties.LABEL_X??0,f.properties.LABEL_Y??0],xy=project(pt);c.save();c.globalAlpha=t;badge(c,name,xy[0]-75,xy[1],C.bg,C.fg,330,18);if(v==='labels'){let d=q.data[i];text(c,d?q.prefix+fmtAs(d.value)+q.suffix:(q.labels[i]||''),xy[0]+10,xy[1]+43,25,C.fg,300,'center');}c.restore();}});c.restore();}

 if(!['aerial','circle','callout','zoom'].includes(v))header(c,C,q,p);

 let route=(q.points||[]).map(project);

 if(v==='route'||v==='flight'){

  if(route.length<2)return;let curved=[];for(let k=0;k<route.length-1;k++){let aa=route[k],bb=route[k+1],dx=bb[0]-aa[0],dy=bb[1]-aa[1],len=Math.hypot(dx,dy)||1;for(let j=0;j<=32;j++){let t=j/32,bend=Math.sin(Math.PI*t)*Math.min(120,len*.18);curved.push([mix(aa[0],bb[0],t)+dy/len*bend,mix(aa[1],bb[1],t)-dx/len*bend]);}}let prog=ease((p-.1)/.7);line(c,curved,a,6,prog);route.forEach((pt,i)=>{circle(c,...pt,9,C.secondary);text(c,q.pointLabels?.[i]||'',pt[0],pt[1]+37,21,C.fg,300,'center');});let pos=prog*(curved.length-1),i=Math.min(curved.length-2,Math.floor(pos)),pt=[mix(curved[i][0],curved[i+1][0],pos-i),mix(curved[i][1],curved[i+1][1],pos-i)];if(v==='flight'){c.save();c.translate(...pt);let ang=Math.atan2(curved[i+1][1]-curved[i][1],curved[i+1][0]-curved[i][0]);c.rotate(ang);if(q.markerImage)asset(c,env,1,-35,-35,70,70,'contain',q);else{c.fillStyle=C.fg;c.beginPath();c.moveTo(30,0);c.lineTo(-22,-19);c.lineTo(-12,0);c.lineTo(-22,19);c.closePath();c.fill();}c.restore();}return;

 }

 if(v==='dots'&&selected){let pts=polys(selected).flatMap(poly=>poly[0]);let b=bounds;let n=Math.min(80,Math.max(1,Math.round(q.number)));function inside(x,y,poly){let yes=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){let a=poly[i],bb=poly[j];if(((a[1]>y)!==(bb[1]>y))&&(x<(bb[0]-a[0])*(y-a[1])/(bb[1]-a[1])+a[0]))yes=!yes;}return yes;}let valid=[];for(let i=0;i<3000&&valid.length<n;i++){let lon=mix(b[0],b[2],((i*.61803398875)%1)),lat=mix(b[1],b[3],((i*.41421356237)%1));if(polys(selected).some(poly=>inside(lon,lat,poly[0])))valid.push(project([lon,lat]));}valid.forEach((pt,i)=>{let f=ease((p-i/n*.5)/.2);circle(c,...pt,7*f,C.secondary);});return;}

 if(v==='pie'){let value=clamp(q.number,0,100)*ease(p/.65);circle(c,800,480,132,C.bg);ring(c,800,480,118,a,value/100,42);text(c,Math.round(value)+'%',800,480,63,C.fg,230,'center');return;}

 if(v==='alert'){(q.points||[]).forEach((pt,i)=>{let [x,y]=project(pt),f=ease((p-i*.1)/.3);circle(c,x,y,10*f,C.secondary);ring(c,x,y,20+20*((p*2+i*.13)%1),C.secondary,f,2);});badge(c,q.subtitle,610,665,C.secondary,C.bg,850,30);return;}

 if(v==='person'||v==='sovereign'){asset(c,env,0,110,300+(1-e)*500,430,560,'contain',q);badge(c,q.subtitle,115,835,C.bg,C.fg,710,26);return;}

 if(v==='flags'){for(let i=0;i<3;i++)asset(c,env,i,600+i*140,410+(1-e)*100,115,90,'contain',q);text(c,q.subtitle,800,790,32,C.fg,1320,'center');return;}

 if(v==='split'){c.save();c.beginPath();c.rect(800,180,760,630);c.clip();asset(c,env,0,800+(1-e)*760,180,760,630,'cover',q);c.restore();line(c,[[800,180],[800,810]],a,4);return;}

 if(v==='trace'){text(c,q.country,800,790,42,C.fg,1400,'center');return;}

 if(v==='date'){c.save();c.globalAlpha=e;text(c,q.title,800,118,92,C.fg,1400,'center',600,q.font);c.restore();text(c,q.subtitle,800,790,42,C.fg,1400,'center');}

 if(['callout','circle','city','zoom','date'].includes(v)){

  let xy=imageMap?[1600*clamp(q.focusX),900*clamp(q.focusY)]:(route[0]||[800,460]);circle(c,...xy,9,a);if(v==='circle')ring(c,...xy,220,a,ease((p-.12)/.55),6);else ring(c,...xy,24,a,e,3);line(c,[xy,[xy[0]+160,xy[1]-90]],a,3,e);badge(c,q.pointLabels?.[0]||q.title,clamp(xy[0]+165,50,1070),xy[1]-90,C.bg,C.fg,460,27);

 }

}

