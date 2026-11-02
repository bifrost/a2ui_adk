import {A2UIRenderer, bound, consumeSSE, element, renderMarkdown, renderTable} from '/shared/a2ui-renderer.js';
const CATALOG = 'https://example.org/catalogs/accounting/v2.json';
const history = document.getElementById('history');
const form = document.getElementById('form');
const promptInput = document.getElementById('prompt');
const send = document.getElementById('send');
const status = document.getElementById('status');
let sessionId = Array.from(crypto.getRandomValues(new Uint8Array(16)), b => b.toString(16).padStart(2, '0')).join('');

function renderCard(c, surface) {
  const wrapper = element('div', null, 'metric-grid');
  for (const metric of (c.metrics || []).slice(0, 8)) {
    const tile = element('div', null, 'metric-tile');
    tile.append(element('div', metric.label, 'metric-label'));
    const v = bound(surface, metric.value);
    tile.append(element('div', `${Number(v || 0).toLocaleString()}${metric.suffix || ''}`, 'metric-value'));
    wrapper.append(tile);
  }
  return wrapper;
}
function renderChart(c, surface) {
  if (c.chartType !== 'bar') throw Error('Unknown chart kind');
  const rows = bound(surface, c.rows) || [];
  const valid = (Array.isArray(rows) ? rows : []).slice(0, 24);
  const max = Math.max(1, ...valid.map(r => Math.max(0, Number(r[c.yKey]) || 0)));
  const chart = element('div', null, 'chart');
  for (const row of valid) {
    const line = element('div', null, 'chart-row');
    line.append(element('span', row[c.xKey], 'chart-name'));
    const track = element('div', null, 'chart-track');
    const bar = element('div', null, 'chart-bar');
    bar.style.width = `${100 * Math.max(0, Number(row[c.yKey]) || 0) / max}%`;
    track.append(bar); line.append(track);
    line.append(element('span', `${Number(row[c.yKey] || 0).toLocaleString()} ${c.unit || ''}`, 'chart-value'));
    chart.append(line);
  }
  return chart;
}
form.addEventListener('submit', async e => {
  e.preventDefault(); const message=promptInput.value.trim();if(!message)return;
  const user=element('div',message,'message user');history.append(user);
  const assistant=element('div',null,'message'), content=element('div',null,'content');
  assistant.append(content);history.append(assistant);
  const renderer=new A2UIRenderer(assistant,{catalog:CATALOG,components:{Table:renderTable,Card:renderCard,Chart:renderChart}});let text='';let failed=false;let renderError=null;
  promptInput.value='';send.disabled=true;status.textContent='Streaming…';
  try {
    const response=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message,session_id:sessionId})});
    await consumeSSE(response,(kind,data)=>{
      if(kind==='text_delta'){text+=data.text;renderMarkdown(content,text);}
      if(kind==='a2ui'){try{renderer.safeProcess(data);}catch(err){renderError??=err;}}
      if(kind==='error'){failed=true;status.textContent=data.message;status.className='error';}
    });
    if(renderError&&!failed){status.textContent='Could not render component: '+renderError.message;status.className='error';}
    else if(!failed){status.textContent='Done';status.className='';}
  } catch(err) {status.textContent='Error: '+err.message;status.className='error';}
  finally {send.disabled=false;promptInput.focus();history.scrollIntoView({block:'end',behavior:'smooth'});}
});
