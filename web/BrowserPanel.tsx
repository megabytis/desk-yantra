import {useRef,useState} from 'react';
type Item=Record<string,any>;
export function BrowserPanel({run,artifacts,request,refresh}:{run?:Item;artifacts:Item[];request:(path:string,body?:unknown)=>Promise<any>;refresh:()=>Promise<void>}){
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[url,setUrl]=useState(''),[text,setText]=useState('');
  const [clickAnnouncement,setClickAnnouncement]=useState('');
  const [statusAnnouncement,setStatusAnnouncement]=useState('');
  const [lastResult,setLastResult]=useState<Item|null>(null);
  const imageRef=useRef<HTMLImageElement>(null);
  const captures=artifacts.filter(item=>item.name==='browser.png').sort((left,right)=>(right.created||0)-(left.created||0));
  const capture=captures[0];
  const controlling=run?.status==='paused';
  async function control(operation:string,body:Item={}){
    if(!run||busy)return;
    setBusy(true);setError('');setStatusAnnouncement(`Performing ${operation}…`);
    try{
      const response = await request(`runs/${run.id}/browser-control`,{operation,...body});
      if(response?.result) setLastResult(response.result);
      await refresh();
      setStatusAnnouncement(`${operation} completed.`);
    }
    catch(failure){setError(failure instanceof Error?failure.message:String(failure));setStatusAnnouncement(`${operation} failed.`);}
    finally{setBusy(false);}
  }
  function handleImageClick(event:React.MouseEvent<HTMLImageElement>){
    if(!controlling||busy)return;
    const image=event.currentTarget;
    const rectangle=image.getBoundingClientRect();
    const x=Math.round((event.clientX-rectangle.left)*image.naturalWidth/rectangle.width);
    const y=Math.round((event.clientY-rectangle.top)*image.naturalHeight/rectangle.height);
    setClickAnnouncement(`Clicked at coordinates ${x}, ${y}`);
    void control('click',{x,y});
  }
  function handleImageKeyDown(event:React.KeyboardEvent<HTMLImageElement>){
    if(!controlling||busy)return;
    if(event.key==='Enter'||event.key===' '){
      event.preventDefault();
      const image=event.currentTarget;
      const x=Math.round(image.naturalWidth/2);
      const y=Math.round(image.naturalHeight/2);
      setClickAnnouncement(`Clicked at center coordinates ${x}, ${y}`);
      void control('click',{x,y});
    }
  }
  const tabs = (lastResult?.tabs as Item[]) || [];
  const pageTitle = lastResult?.title || '';
  const elementCount = lastResult?.elements?.length || 0;
  const requiresTakeover = lastResult?.requires_user_takeover;

  return <div className="browser-panel">
    {error&&<div role="alert" className="feedback failure">{error}</div>}
    {requiresTakeover&&<div role="alert" className="feedback warning">⚠️ CAPTCHA / verification challenge detected. Complete the verification in this view.</div>}
    <div aria-live="polite" aria-atomic="true" className="sr-only" style={{position:'absolute',left:'-9999px',width:'1px',height:'1px',overflow:'hidden'}}>{statusAnnouncement}</div>
    <div aria-live="polite" aria-atomic="true" className="sr-only" style={{position:'absolute',left:'-9999px',width:'1px',height:'1px',overflow:'hidden'}}>{clickAnnouncement}</div>
    <div className="browser-control-bar">
      <div>
        <strong>{controlling?'You\'re controlling this browser':'Sandbox browser'}</strong>
        {pageTitle && <span className="browser-page-title" title={pageTitle}> — {pageTitle}</span>}
        {elementCount > 0 && <span className="browser-elements-badge">({elementCount} interactive elements)</span>}
      </div>
      <div>
        {run?.mode==='sandbox'&&run.status==='completed'&&<button onClick={()=>void control('begin')} disabled={busy}>Take browser control</button>}
        {controlling&&<button onClick={()=>void control('end')} disabled={busy}>Return control</button>}
      </div>
    </div>
    {controlling && tabs.length > 0 && (
      <div className="browser-tab-bar" role="tablist" aria-label="Browser tabs">
        {tabs.map(tab => (
          <div key={tab.id} className={`browser-tab ${tab.active ? 'active-tab' : ''}`} role="tab" aria-selected={tab.active} onClick={()=>void control('switch_tab', {tab_id: tab.id})}>
            <span className="tab-title">{tab.title || `Tab ${tab.id + 1}`}</span>
            {tabs.length > 1 && (
              <button type="button" className="tab-close" aria-label={`Close tab ${tab.id + 1}`} onClick={e=>{e.stopPropagation(); void control('close_tab', {tab_id: tab.id});}}>×</button>
            )}
          </div>
        ))}
        <button type="button" className="new-tab-btn" aria-label="New tab" onClick={()=>void control('new_tab')} disabled={busy}>+</button>
      </div>
    )}
    {controlling&&<>
      <form className="browser-address" onSubmit={event=>{event.preventDefault();void control('navigate',{url});}}>
        <input aria-label="Browser URL" type="url" required value={url} onChange={event=>setUrl(event.target.value)} placeholder="https://"/>
        <button disabled={busy}>Go</button>
        <button type="button" disabled={busy} onClick={()=>void control('inspect')}>Refresh view</button>
        <button type="button" disabled={busy} onClick={()=>void control('scroll',{delta_y: -300})} title="Scroll up" aria-label="Scroll up">↑</button>
        <button type="button" disabled={busy} onClick={()=>void control('scroll',{delta_y: 300})} title="Scroll down" aria-label="Scroll down">↓</button>
      </form>
      <p className="browser-consent">Clicks and typed text affect this sandbox page. They may submit information to external services. Host desktop input is separate.</p>
    </>}
    {capture?<img ref={imageRef} className={controlling?'controlled-browser':''} src={`/api/artifacts/${capture.id}/preview`} alt="Actual sandbox browser capture" tabIndex={controlling?0:-1} role={controlling?'button':undefined} aria-label={controlling?'Browser view — click to interact, press Enter to click center':'Sandbox browser capture'} onClick={handleImageClick} onKeyDown={handleImageKeyDown}/>:<div className="surface-empty">◎<h3>No browser capture yet</h3><p>Browser actions capture the actual Chromium page inside the container.</p></div>}
    {controlling&&<div className="browser-input"><label>Type into the focused page element<textarea value={text} onChange={event=>setText(event.target.value)} placeholder="Click a field in the browser view, then type here."/></label><div>{['Enter','Tab','Backspace','Escape'].map(key=><button key={key} disabled={busy} onClick={()=>void control('press',{key})} aria-label={`Press ${key} key`}>{key}</button>)}<button disabled={busy||!text} onClick={()=>void control('type',{text})}>Type this text</button></div></div>}
    {busy&&<p className="browser-consent" role="status">Updating the browser…</p>}
  </div>;
}
