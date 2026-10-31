const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const b=await chromium.launch();const p=await b.newPage();
await p.goto('file://'+__dirname+'/standings.html');await p.waitForTimeout(500);
const out={};
for(const [med,k] of [[false,'h'],[true,'m']]){
 out[k]=await p.evaluate(([med,k])=>{set(med);OPEN.clear&&OPEN.clear();draw(med);
  const L=document.getElementById('list');let n=0;
  [...L.querySelectorAll(':scope > .r')].forEach(r=>{const id=`x${k}${n++}`;
   const lab=document.createElement('label');for(const a of r.attributes)lab.setAttribute(a.name,a.value);
   lab.removeAttribute('tabindex');lab.removeAttribute('role');lab.removeAttribute('aria-expanded');lab.classList.remove('open');lab.setAttribute('for',id);
   lab.innerHTML=r.innerHTML;const st=lab.querySelector('.strip');st.removeAttribute('hidden');
   const cb=document.createElement('input');cb.type='checkbox';cb.className='xp';cb.id=id;
   r.replaceWith(cb,lab)});
  return L.innerHTML},[med,k]);}
fs.writeFileSync(__dirname+'/lists.json',JSON.stringify(out));await b.close();})();
