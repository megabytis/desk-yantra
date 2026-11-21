import {FormEvent,useEffect,useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {Workspace} from './Workspace';
import {Management} from './Management';
import {ProductPreview} from './ProductPreview';
import {fixtureConnections,personalState} from './visibility';
import './style.css';

type Item=Record<string,any>;
class ApiError extends Error {constructor(message:string,public status:number){super(message);}}
async function api(path:string,body?:unknown){
  const response=await fetch('/api/'+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json','X-PAW':'1'},body:body===undefined?undefined:JSON.stringify(body)});
  const result=await response.json();
  if(!response.ok)throw new ApiError(result.detail||'The request could not be completed',response.status);
  return result;
}
const pages=['Chat','Providers','Agents','Permissions','Runs','Artifacts','Diagnostics'];
function route(){const [page,id]=window.location.hash.slice(1).split('/');return {page:pages.includes(page)?page:'Chat',id:id||''};}
function App(){
  const [state,setState]=useState<Item|null>(null);
  const [current,setCurrent]=useState(route);
  const [history,setHistory]=useState<Item[]>([]);
  const [auth,setAuth]=useState(false);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState('');
  const [pairing,setPairing]=useState(false);
  const [online,setOnline]=useState(true);
  const [showTestData,setShowTestData]=useState(()=>sessionStorage.getItem('paw.showTestData')==='true');
  const [connectionStatus,setConnectionStatus]=useState('');
  const prevOnlineRef=useRef(true);
  async function refresh(){
    try{const result=await api('state');setState(result);setAuth(false);setError('');setOnline(true);}
    catch(failure){setOnline(false);if(failure instanceof ApiError&&failure.status===401){setAuth(true);setState(null);}else if(!state)setError('The local service is unavailable. Start the workbench, then retry.');}
    finally{setLoading(false);}
  }
  useEffect(()=>{void refresh();const timer=setInterval(()=>void refresh(),2500);return()=>clearInterval(timer);},[]);
  useEffect(()=>{const listener=()=>setCurrent(route());window.addEventListener('hashchange',listener);return()=>window.removeEventListener('hashchange',listener);},[]);
  useEffect(()=>{
    setHistory([]);if(!current.id||!state)return;
    const source=new EventSource(`/api/runs/${current.id}/events`);
    source.onmessage=message=>{const item=JSON.parse(message.data);setHistory(previous=>previous.some(old=>old.seq===item.seq)?previous:[...previous,item]);};
    return()=>source.close();
  },[current.id,!!state]);
  useEffect(()=>{
    if(prevOnlineRef.current && !online) setConnectionStatus('Connection lost. Reconnecting to your workbench…');
    else if(!prevOnlineRef.current && online) setConnectionStatus('Connection restored.');
    prevOnlineRef.current=online;
  },[online]);
  function navigate(page:string){const id=route().id;window.location.hash=page+(id?'/'+id:'');}
  function select(id:string){window.location.hash='Chat'+(id?'/'+id:'');}
  async function pair(event:FormEvent<HTMLFormElement>){
    event.preventDefault();setPairing(true);setError('');
    try{await api('login',{token:new FormData(event.currentTarget).get('token')});await refresh();}
    catch(failure){setError(failure instanceof Error?failure.message:String(failure));}
    finally{setPairing(false);}
  }
  if(!state)return <div className="pairing-screen"><a href="#main-content" className="skip-link">Skip to main content</a><div className="pairing-story"><div className="pairing-logo">◈ Desk Yantra</div><div><small>YOUR PERSONAL AGENT ENVIRONMENT</small><h1>A place to think.<br/>A machine to act.</h1><p>Connect your models. Give your agents a workspace.<br/>Follow the work, and keep the final say.</p></div><span>Self-hosted · Local control · Your providers</span></div><main id="main-content" className="pairing-form" role="main"><span className="eyebrow">DESK YANTRA</span><h2>{loading?'Connecting to your workbench…':auth?'Connect this browser':'Desk Yantra is offline'}</h2>{auth?<><p>Use the pairing token from your local launcher. This gives your browser access to this workbench.</p><form onSubmit={event=>void pair(event)}><label>Launch token<input name="token" type="password" required autoComplete="off" placeholder="Paste your local pairing token" autoFocus/></label>{error&&<p className="pairing-error" role="alert">{error}</p>}<button disabled={pairing}>{pairing?'Connecting…':'Connect to workbench →'}</button></form><small>Provider credentials are entered separately in Settings.</small></>:<><p>{error||'Looking for the local service…'}</p>{!loading&&<button onClick={()=>void refresh()}>Retry connection</button>}</>}<a className="preview-entry" href="/?preview=1">Explore the product preview →</a></main></div>;
  const visible=showTestData?state:personalState(state);
  const active=visible.runs.find((run:Item)=>run.id===current.id);
  return <><a href="#main-content" className="skip-link">Skip to main content</a><div aria-live="polite" aria-atomic="true" className="sr-only">{connectionStatus}</div>{!online&&<div className="connection-banner" role="alert">Connection lost. Reconnecting to your workbench… Run history will reload when the service returns.</div>}{current.page==='Chat'?<Workspace state={visible} active={active} history={history} select={select} navigate={navigate} request={api} refresh={refresh}/>:<Management state={visible} page={current.page} navigate={navigate} request={api} refresh={refresh} select={select}/>}{fixtureConnections(state).size>0&&<label className="test-data-switch"><input type="checkbox" checked={showTestData} onChange={event=>{setShowTestData(event.target.checked);sessionStorage.setItem('paw.showTestData',String(event.target.checked));}}/>Show test records</label>}</>;
}
createRoot(document.getElementById('root')!).render(new URLSearchParams(window.location.search).has('preview')?<ProductPreview/>:<App/>);
