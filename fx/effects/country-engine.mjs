export const clamp=(v)=>Math.min(1,Math.max(0,v));
const ease=v=>{v=clamp(v);return v*v*(3-2*v)};
function geometry(ctx,rings){ctx.beginPath();for(const r of rings){ctx.moveTo(...r[0]);for(const p of r.slice(1))ctx.lineTo(...p);ctx.closePath();}}
function trace(ctx,rings,progress){
 let total=0;for(const r of rings)for(let i=1;i<r.length;i++)total+=Math.hypot(r[i][0]-r[i-1][0],r[i][1]-r[i-1][1]);
 let left=total*progress;ctx.beginPath();
 for(const r of rings){ctx.moveTo(...r[0]);for(let i=1;i<r.length;i++){const a=r[i-1],b=r[i],d=Math.hypot(b[0]-a[0],b[1]-a[1]);if(left>=d){ctx.lineTo(...b);left-=d;}else{const q=d?left/d:0;ctx.lineTo(a[0]+(b[0]-a[0])*q,a[1]+(b[1]-a[1])*q);left=0;break;}}if(left<=0)break;}ctx.stroke();
}
export function draw(ctx,t,cfg,maps){
 const W=ctx.canvas.width,H=ctx.canvas.height;ctx.save();ctx.scale(W/1920,H/1080);
 ctx.fillStyle=cfg.background;ctx.fillRect(0,0,1920,1080);
 const glow=ctx.createRadialGradient(970,470,90,960,540,1150);glow.addColorStop(0,'rgba(70,73,104,0.055)');glow.addColorStop(1,'rgba(0,0,0,0.24)');ctx.fillStyle=glow;ctx.fillRect(0,0,1920,1080);
 const rings=maps[cfg.country]||maps['United States of America'];
 const entry=ease(t/.45);const zoom=1.04-.04*ease(t/2.6);
 ctx.save();ctx.translate(960,585);ctx.scale(zoom,zoom);ctx.translate(-960,-585);
 ctx.globalAlpha=entry;geometry(ctx,rings);ctx.fillStyle='#1c1e20';ctx.fill('evenodd');
 ctx.save();geometry(ctx,rings);ctx.clip('evenodd');
 const fill=ease((t-cfg.fillStart)/cfg.fillSeconds);
 if(fill>0){ctx.fillStyle=cfg.fill;ctx.beginPath();ctx.arc(960,610,fill*1080,0,Math.PI*2);ctx.fill();}
 ctx.restore();
 ctx.strokeStyle=cfg.outline;ctx.lineWidth=2.25;ctx.lineJoin='round';ctx.lineCap='round';
 ctx.globalAlpha=entry*.13;geometry(ctx,rings);ctx.stroke();
 ctx.globalAlpha=entry;trace(ctx,rings,ease(t/cfg.outlineSeconds));ctx.restore();
 const typing=clamp((t-cfg.titleStart)/.88);const letters=Math.floor(typing*cfg.title.length);
 if(t>=cfg.titleStart){ctx.font='76px Anton';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle='#f4f4ef';const full=cfg.title;const txt=full.slice(0,letters);ctx.save();ctx.translate(960,122);ctx.scale(.78,1);ctx.fillText(txt,0,0);if(typing<1&&Math.floor(t*8)%2===0){const w=ctx.measureText(txt).width;ctx.fillRect(w/2+11,-36,5,72);}ctx.restore();}
 ctx.restore();
}
