import {useState} from 'react';
type Item=Record<string,any>;
export function BrowserPanel({run,artifacts,request,refresh}:{run?:Item;artifacts:Item[];request:(path:string,body?:unknown)=>Promise<any>;refresh:()=>Promise<void>}){
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[url,setUrl]=useState(''),[text,setText]=useState('');
  const captures=artifacts.filter(item=>item.name==='browser.png').sort((left,right)=>(right.created||0)-(left.created||0));
  const capture=captures[0];
  const controlling=run?.status==='paused';
  async function control(operation:string,body:Item={}){
    if(!run||busy)return;
    setBusy(true);setError('');
    try{await request(`runs/${run.id}/browser-control`,{operation,...body});await refresh();}
    catch(failure){setError(failure instanceof Error?failure.message:String(failure));}
    finally{setBusy(false);}
  }
  return <div className="browser-panel">{error&&<div role="alert" className="feedback failure">{error}</div>}<div className="browser-control-bar"><strong>{controlling?'You’re controlling this browser':'Sandbox browser'}</strong>{run?.mode==='sandbox'&&run.status==='completed'&&<button onClick={()=>void control('begin')} disabled={busy}>Take browser control</button>}{controlling&&<button onClick={()=>void control('end')} disabled={busy}>Return control</button>}</div>{controlling&&<><form className="browser-address" onSubmit={event=>{event.preventDefault();void control('navigate',{url});}}><input aria-label="Browser URL" type="url" required value={url} onChange={event=>setUrl(event.target.value)} placeholder="https://"/><button disabled={busy}>Go</button><button type="button" disabled={busy} onClick={()=>void control('inspect')}>Refresh view</button></form><p className="browser-consent">Clicks and typed text affect this sandbox page. They may submit information to external services. Host desktop input is separate.</p></>}{capture?<img className={controlling?'controlled-browser':''} src={`/api/artifacts/${capture.id}/preview`} alt="Actual sandbox browser capture" onClick={event=>{if(!controlling||busy)return;const image=event.currentTarget;const rectangle=image.getBoundingClientRect();void control('click',{x:Math.round((event.clientX-rectangle.left)*image.naturalWidth/rectangle.width),y:Math.round((event.clientY-rectangle.top)*image.naturalHeight/rectangle.height)});}}/>:<div className="surface-empty">◎<h3>No browser capture yet</h3><p>Browser actions capture the actual Chromium page inside the container.</p></div>}{controlling&&<div className="browser-input"><label>Type into the focused page element<textarea value={text} onChange={event=>setText(event.target.value)} placeholder="Click a field in the browser view, then type here."/></label><div><button disabled={busy||!text} onClick={()=>void control('type',{text})}>Type this text</button>{['Enter','Tab','Backspace','Escape'].map(key=><button key={key} disabled={busy} onClick={()=>void control('press',{key})}>{key}</button>)}</div></div>}{busy&&<p className="browser-consent" role="status">Updating the browser…</p>}</div>;
}
