import React,{useEffect,useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {HttpAgent} from '@ag-ui/client';
import {marked} from 'marked';
import DOMPurify from 'dompurify';
import {toA2UI,readSurface} from './a2ui';
import './style.css';

class Boundary extends React.Component{
 state={failed:null};
 static getDerivedStateFromError(e){return {failed:e};}
 render(){return this.state.failed?<div className="error">Kunne ikke vise komponenten: {String(this.state.failed.message||this.state.failed)}</div>:this.props.children;}
}
function Visual({messages}) {
 const {type,data}=readSurface(messages);
 if(type==='Table')return <div className="panel"><h3>Fakturaer</h3><table><thead><tr>{data.columns.map(c=><th key={c.key}>{c.label}</th>)}</tr></thead><tbody>{data.rows.map((r,i)=><tr key={i}>{data.columns.map(c=><td key={c.key}>{r[c.key]}</td>)}</tr>)}</tbody></table></div>;
 if(type==='Card')return <div className="panel"><h3>{data.title}</h3><div className="metrics">{data.metrics.map(m=><div className="metric" key={m.label}><small>{m.label}</small><strong>{m.value}</strong></div>)}</div></div>;
 const maximum=Math.max(...data.points.map(p=>p.amount));return <div className="panel"><h3>{data.title}</h3><div className="bars">{data.points.map(p=><div className="barcol" key={p.month}><span>{p.amount.toLocaleString('da-DK')}</span><div style={{height:Math.max(6,145*p.amount/maximum)}}/><small>{p.month}</small></div>)}</div></div>;
}
const url='http://127.0.0.1:8000';
function App(){
 const [mode,setMode]=useState(null),[query,setQuery]=useState(''),[busy,setBusy]=useState(false),[chat,setChat]=useState([]),[error,setError]=useState('');
 const thread=useRef(crypto.randomUUID());const agent=useRef(null);
 // The backend's DEMO_MODE (mock | adk) decides which endpoint to talk to.
 useEffect(()=>{fetch(url+'/health').then(r=>r.json()).then(h=>setMode(h.mode==='adk'?'adk':'mock')).catch(()=>setError('Kan ikke nå backend på '+url));},[]);
 async function send(text){if(!text.trim()||busy||!mode)return;setBusy(true);setError('');setQuery('');const id=crypto.randomUUID();setChat(s=>[...s,{id:'u'+id,role:'user',text},{id,role:'assistant',text:'',ui:[]}]);
  // The official @ag-ui/client owns the wire protocol and event stream.
  const endpoint=url+(mode==='mock'?'/mock-agent':'/agent');
  if(!agent.current || agent.current.endpoint!==endpoint){agent.current={endpoint,client:new HttpAgent({url:endpoint,threadId:thread.current})};}
  const client=agent.current.client;
  client.messages.push({id:'u'+id,role:'user',content:text});
  let sawContent=false;let reported=false;const rendered=new Set();
  function fail(msg){reported=true;setError(msg);}
  // Reveal text gradually so bursty chunks still look like typing; components wait until it finishes.
  let target='',shown=0,timer=null,finishing=false;const waiters=[],pendingUi=[];
  function tick(){const backlog=target.length-shown;if(backlog<=0){timer=null;waiters.splice(0).forEach(r=>r());return;}shown+=Math.min(backlog,Math.max(1,Math.ceil(backlog/(finishing?5:20))));const t=target.slice(0,shown);setChat(s=>s.map(m=>m.id===id?{...m,text:t}:m));timer=setTimeout(tick,8);}
  function appendText(delta){sawContent=true;target+=delta;if(!timer)timer=setTimeout(tick,0);}
  const drain=()=>{finishing=true;return timer?new Promise(r=>waiters.push(r)):Promise.resolve();};
  function renderKind(kind,toolId){if(rendered.has(toolId))return; if(!['table','card','chart'].includes(kind))throw new Error('Ukendt komponent: '+kind);rendered.add(toolId);pendingUi.push(toA2UI(kind,toolId));}
  const unsubscribe=client.subscribe({
   onTextMessageContentEvent:({event})=>appendText(event.delta||''),
   // Render from the tool's result, not the model's streamed args, so a rejected call shows nothing.
   onToolCallResultEvent:({event})=>{try{const result=JSON.parse(event.content||'{}');if(result.error)throw new Error(result.error);renderKind(result.kind,event.toolCallId);}catch(e){console.error('show_ui failed',e);fail('Kunne ikke vise komponenten: '+(e.message||e));}},
   onRunErrorEvent:({event})=>fail(event.message||'Agent error'),
  });
  try{await client.runAgent({tools:[]});}catch(e){if(!reported)fail(String(e.message||e));if(!sawContent){client.messages=client.messages.filter(m=>m.id!=='u'+id);setChat(s=>s.filter(m=>m.id!==id&&m.id!=='u'+id));}}finally{unsubscribe.unsubscribe();await drain();if(pendingUi.length)setChat(s=>s.map(m=>m.id===id?{...m,ui:[...m.ui,...pendingUi]}:m));setBusy(false);}
 }
 return <main><header><div><h1>Accounting Assistant</h1><p>Google ADK · AG-UI transport · A2UI v1 surfaces</p></div><span className="mode">{mode==='adk'?'Gemini ADK':mode==='mock'?'Offline mock':'…'}</span></header><section className="chat">{chat.length===0&&<div className="welcome"><h2>Prøv demoen</h2><p>Markdown streames via officielle AG-UI events. UI vælges via tool-kald og omsættes til A2UI v1.</p><div className="examples">{['Vis mine fakturaer','Vis mit KPI-overblik','Vis omsætning som graf'].map(x=><button key={x} onClick={()=>send(x)}>{x}</button>)}</div></div>}{chat.map(m=><article key={m.id} className={m.role}><div className="bubble">{m.role==='user'?m.text:<div dangerouslySetInnerHTML={{__html:DOMPurify.sanitize(marked.parse(m.text||''))}}/>}</div>{m.ui?.map((messages,i)=><Boundary key={i}><Visual messages={messages}/></Boundary>)}</article>)}{error&&<div className="error">{error}</div>}</section><form onSubmit={e=>{e.preventDefault();send(query)}}><input placeholder="Spørg om fakturaer, KPI eller omsætning..." value={query} onChange={e=>setQuery(e.target.value)}/><button disabled={busy||!mode||!query.trim()}>{busy?'Arbejder…':'Send'}</button></form><footer>Demoen viser udelukkende syntetiske regnskabsdata.</footer></main>
}
createRoot(document.getElementById('root')).render(<App/>);
