(()=>{
const card=document.getElementById('glass'), inner=document.getElementById('card-inner');
let current=document.body.dataset.mode==='signup'?'signup':'login',busy=false;
const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
function reveal(mode, navigation){
 document.querySelectorAll('.auth-view').forEach(v=>v.hidden=v.dataset.view!==mode);
 document.body.dataset.mode=mode; current=mode;
 if(navigation) history.pushState({auth:mode},'',mode==='signup'?'/signup':'/login');
}
async function switchTo(mode,navigation=true){
 if(busy||mode===current)return;
 busy=true;
 if(document.activeElement instanceof HTMLElement)document.activeElement.blur();
 if(reduced){reveal(mode,navigation);busy=false;return;}
 // The reference animation flips the whole glass surface to its logo back,
 // then turns forward to expose the newly selected form.
 const start=card.getBoundingClientRect().height;
 card.style.height=start+'px';
 card.classList.remove('flip-complete','is-returning');
 card.classList.add('is-turning');
 await wait(940);
 reveal(mode,navigation);
 const next=inner.scrollHeight;
 card.style.height=next+'px';
 card.classList.remove('is-turning');
 card.classList.add('is-returning');
 await wait(930);
 card.classList.add('flip-complete');
 card.classList.remove('is-returning');
 card.style.height='';
 busy=false;
}
document.querySelectorAll('[data-switch]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();switchTo(a.dataset.switch)}));
window.addEventListener('popstate',()=>switchTo(location.pathname==='/signup'?'signup':'login',false));
document.querySelectorAll('.eye').forEach(b=>b.addEventListener('click',()=>{const input=b.parentElement.querySelector('input');input.type=input.type==='password'?'text':'password';b.setAttribute('aria-label',input.type==='password'?'Show password':'Hide password')}));
card.addEventListener('pointermove',e=>{if(reduced||busy)return;const r=card.getBoundingClientRect();card.style.setProperty('--mx',((e.clientX-r.left)/r.width*100)+'%');card.style.setProperty('--my',((e.clientY-r.top)/r.height*100)+'%')});
})();
// Instinct AI — bright, larger falling light particles. Canvas only, no external assets.
(()=>{
 const canvas=document.getElementById('auth-particles');if(!canvas)return;
 const ctx=canvas.getContext('2d',{alpha:true});if(!ctx)return;
 const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
 let w=0,h=0,dpr=1,particles=[],last=0;
 const rand=(a,b)=>a+Math.random()*(b-a);
 function create(initial=false){
   const depth=rand(.55,1.45), size=rand(1.9,4.3)*depth;
   return {x:rand(0,w),y:initial?rand(-h*.2,h*1.05):rand(-h*.4,-20),
    speed:rand(85,230)*depth,len:rand(35,125)*depth,size,depth,
    alpha:rand(.72,1),drift:rand(-7,7),phase:rand(0,6.28),hue:Math.random()<.18?260:195};
 }
 function resize(){
   w=innerWidth;h=innerHeight;dpr=Math.min(devicePixelRatio||1,1.75);
   canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);
   canvas.style.width=w+'px';canvas.style.height=h+'px';ctx.setTransform(dpr,0,0,dpr,0,0);
   const count=Math.min(650,Math.max(220,Math.round(w*h/2700)));
   particles=Array.from({length:count},()=>create(true));
 }
 function draw(t){
   const dt=Math.min((t-last)/1000||0,.045);last=t;
   ctx.clearRect(0,0,w,h);
   for(let i=0;i<particles.length;i++){
     const p=particles[i];if(!reduced){p.y+=p.speed*dt;p.x+=p.drift*dt;}
     if(p.y-p.len>h+25||p.x<-40||p.x>w+40){particles[i]=create();continue;}
     const shimmer=.88+.12*Math.sin(t*.002+p.phase),alpha=p.alpha*shimmer;
     const cyan=p.hue===195,base=cyan?'78,210,255':'166,126,255';
     const tail=ctx.createLinearGradient(p.x,p.y-p.len,p.x,p.y+2);
     tail.addColorStop(0,`rgba(${base},0)`);
     tail.addColorStop(.45,`rgba(${base},${alpha*.26})`);
     tail.addColorStop(1,`rgba(${base},${alpha*.92})`);
     ctx.beginPath();ctx.strokeStyle=tail;ctx.lineWidth=Math.max(1.5,p.size*.55);
     ctx.lineCap='butt';ctx.moveTo(p.x,p.y-p.len);ctx.lineTo(p.x,p.y);ctx.stroke();

   }
   if(!reduced)requestAnimationFrame(draw);
 }
 addEventListener('resize',resize,{passive:true});resize();requestAnimationFrame(draw);
})();
