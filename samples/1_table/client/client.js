import {A2UIRenderer, consumeSSE, element, renderMarkdown, renderTable} from '/shared/a2ui-renderer.js';
const CATALOG = 'https://example.org/catalogs/accounting/v1.json';
const history = document.getElementById('history');
const form = document.getElementById('form');
const promptInput = document.getElementById('prompt');
const send = document.getElementById('send');
const status = document.getElementById('status');
let sessionId = crypto.randomUUID();

// Reveals received text gradually so bursty chunks still look like typing.
function createTypewriter(node) {
  let target = '', shown = 0, timer = null, waiters = [];
  const tick = () => {
    const backlog = target.length - shown;
    if (backlog <= 0) { timer = null; waiters.splice(0).forEach(r => r()); return; }
    shown += Math.min(backlog, Math.max(1, Math.ceil(backlog / 40)));
    renderMarkdown(node, target.slice(0, shown));
    timer = setTimeout(tick, 18);
  };
  return {
    push(t) { target += t; if (!timer) timer = setTimeout(tick, 0); },
    drain() { return timer ? new Promise(r => waiters.push(r)) : Promise.resolve(); },
  };
}
form.addEventListener('submit', async e => {
  e.preventDefault(); const message=promptInput.value.trim();if(!message)return;
  const user=element('div',message,'message user');history.append(user);
  const assistant=element('div',null,'message'), content=element('div',null,'content');
  assistant.append(content);history.append(assistant);
  const renderer=new A2UIRenderer(assistant,{catalog:CATALOG,components:{Table:renderTable}});const typer=createTypewriter(content), surfaces=[];
  promptInput.value='';send.disabled=true;status.className='';status.textContent='Streaming…';
  try {
    const response=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message,session_id:sessionId})});
    await consumeSSE(response,(kind,data)=>{
      if(kind==='text_delta')typer.push(data.text);
      if(kind==='a2ui')surfaces.push(data);
      if(kind==='error'){status.textContent=data.message;status.className='error';}
    });
    await typer.drain();
    let renderError=null;
    for(const m of surfaces){try{renderer.safeProcess(m);}catch(err){renderError??=err;}}
    if(renderError){status.textContent='Could not render component: '+renderError.message;status.className='error';}
    else if(status.className!=='error')status.textContent='Done';
  } catch(err) {status.textContent='Error: '+err.message;status.className='error';}
  finally {send.disabled=false;promptInput.focus();history.scrollIntoView({block:'end',behavior:'smooth'});}
});
