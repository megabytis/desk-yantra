import {useEffect,useRef,useState} from 'react';
import './workspace.css';
import {Message,ActionPreview} from './Message';
import {SetupProgress} from './SetupProgress';
import {BrowserPanel} from './BrowserPanel';
import {TaskTree} from './TaskTree';

type Item = Record<string, any>;
type Props = {state:Item; active:Item|undefined; history:Item[]; select:(id:string)=>void; navigate:(page:string)=>void; request:(path:string,body?:unknown)=>Promise<any>; refresh:()=>Promise<void>};

export function Workspace({state,active,history,select,navigate,request,refresh}:Props) {
  const [task,setTask] = useState('');
  const [agent,setAgent] = useState(()=>localStorage.getItem('paw.lastAgent')||'');
  const [grant,setGrant] = useState(()=>localStorage.getItem('paw.lastGrant')||'');
  const [tab,setTab] = useState('Terminal');
  const [error,setError] = useState('');
  const [busy,setBusy] = useState(false);
  const [modelSelection,setModelSelection] = useState('');
  const [showSurface,setShowSurface]=useState(false);
  const [reviewNote,setReviewNote]=useState('');
  const [messages,setMessages] = useState<Item[]>([]);
  useEffect(()=>{
    let cancelled = false;
    setMessages([]);
    if (!active) return;
    const load = () => request(`conversations/${active.conversation || active.id}`).then(result=>{if (!cancelled) setMessages(result.messages);}).catch(()=>{});
    void load();
    const timer = setInterval(load,2000);
    return ()=>{cancelled=true;clearInterval(timer);};
  },[active?.conversation,active?.id]);
  const profile = state.agents.find((item:Item)=>item.id === (active?.agent || agent));
  const permissions = state.grants.filter((item:Item)=>!item.revoked && profile?.grants.includes(item.id));
  const workspace = state.grants.find((item:Item)=>item.id === (active?.grant || grant));
  const selectedModel=modelSelection?JSON.parse(modelSelection):{};
  const provider = state.providers.find((item:Item)=>item.id === (active?.connection || selectedModel.connection || profile?.connection || state.defaults[0]?.connection));
  const parentRun = active?.parent ? state.runs.find((item:Item)=>item.id === active.parent) : null;
  const parentAgent = parentRun ? state.agents.find((item:Item)=>item.id === parentRun.agent) : null;
  const artifacts = state.artifacts.filter((item:Item)=>item.run === active?.id);
  const budget = state.budgets?.find((b: Item) => b.id === (active?.root_run || active?.id));
  const running = active && ['queued','running','approval'].includes(active.status);
  const pending = state.approvals.filter((item:Item)=>item.run === active?.id && item.status === 'pending');
  const scroll=useRef<HTMLDivElement>(null);
  const pinned=useRef(true);
  useEffect(()=>{if(agent&&!state.agents.some((item:Item)=>item.id===agent&&!item.archived)){setAgent('');setGrant('');}},[state.agents,agent]);
  useEffect(()=>{if(pinned.current&&scroll.current)scroll.current.scrollTop=scroll.current.scrollHeight;},[messages.length,history.length,pending.length]);
  useEffect(()=>{pinned.current=true;setReviewNote('');},[active?.id]);
  useEffect(()=>{localStorage.setItem('paw.lastAgent',agent);localStorage.setItem('paw.lastGrant',grant);},[agent,grant]);
  async function action(path:string,body:unknown) {
    setError('');
    try {const result=await request(path,body); await refresh(); return result;}
    catch(failure) {setError(String(failure)); return null;}
  }
  async function send() {
    if (!task.trim() || busy) return;
    if(active&&!['completed','reviewed'].includes(active.status))return;
    if(!active&&(!agent||!grant)){setError('Choose an agent and an authorized workspace before sending your task.');return;}
    setBusy(true);
    const override = modelSelection ? JSON.parse(modelSelection) : {};
    const result = await action(active && ['completed','reviewed'].includes(active.status) ? `runs/${active.id}/followup` : 'runs', {task,agent,grant,...override});
    if (result) {select(result.id); setTask('');}
    setBusy(false);
  }
  const conversations=new Map<string,Item>();
  for(const run of [...state.runs].filter((item:Item)=>!item.parent).sort((left:Item,right:Item)=>left.created-right.created)){
    const id=run.conversation||run.id;
    conversations.set(id,{...run,title:conversations.get(id)?.title||run.task});
  }
  const sessions=[...conversations.values()].sort((left:Item,right:Item)=>right.created-left.created);
  return <div className={'agent-shell '+(showSurface?'surface-open':'')}>
    <aside className="agent-sidebar">
      <div className="agent-wordmark">◈ <strong>Desk Yantra</strong></div>
      <button className="new-task" onClick={()=>select('')}>＋ New conversation</button>
      <nav className="workspace-shortcuts"><button onClick={()=>navigate('Runs')}>Runs</button><button onClick={()=>navigate('Artifacts')}>Artifacts</button></nav>
      <div className="sidebar-caption">CONVERSATIONS</div>
      <div className="session-list">{sessions.map((item:Item)=><button key={item.id} className={active&&(active.conversation||active.id)===(item.conversation||item.id)?'current-session':''} onClick={()=>select(item.id)}><span>{item.title}</span><small>{item.outcome==='needs_review'?'Review needed':item.status} · {item.model}</small></button>)}</div>
      <div className="sidebar-bottom"><button onClick={()=>navigate('Agents')}>◎ Agents</button><button onClick={()=>navigate('Providers')}>⚙ Settings & providers</button><button onClick={()=>navigate('Permissions')}>◇ Computer access</button><small>{state.capabilities.machine || 'Companion unavailable'}</small></div>
    </aside>
    <div className="agent-center"><header className="agent-topbar"><details className="mobile-navigation"><summary aria-label="Open navigation">☰</summary><nav><button onClick={()=>select('')}>New conversation</button>{['Agents','Providers','Permissions','Runs','Artifacts'].map(page=><button key={page} onClick={()=>navigate(page)}>{page==='Providers'?'Providers & models':page==='Permissions'?'Computer access':page}</button>)}</nav></details><span>{active ? active.task.slice(0,65) : 'New conversation'}</span><span className="execution-pill">{workspace?.mode || 'No workspace selected'} · {active?.status || 'idle'}</span><button className="surface-toggle" onClick={()=>setShowSurface(!showSurface)}>{showSurface?'Conversation':'Workspace'}</button></header>
    <div className="conversation-scroll" ref={scroll} onScroll={event=>{const element=event.currentTarget;pinned.current=element.scrollHeight-element.scrollTop-element.clientHeight<80;}}>
      {!active&&<SetupProgress state={state} navigate={navigate}/>}
      {parentRun && <button className="parent-task-link" onClick={()=>select(parentRun.id)}>↰ Parent task: <strong>{parentAgent?.name || 'Parent'}</strong> · {parentRun.task.slice(0, 50)}</button>}
      {active && <div className="task-identity"><small>{profile?.name} · {provider?.name} · {active.model} · {active.machine}{budget ? ` · budget: ${budget.used}/90` : ''}{active.stop_reason ? ` · ${active.stop_reason.replace('_', ' ')}` : ''}{active.verification ? ` · ${active.verification.outcome.replace('_', ' ')}` : ''}</small>{active.verification && <span className={`verification-badge status-${active.verification.verified ? 'verified' : 'unverified'}`} title={active.verification.reason}>{active.verification.verified ? '✓ Verified' : '⚠ Unverified'}</span>}<button onClick={()=>navigate('Runs')}>Run monitor</button></div>}
      {active?.outcome==='needs_review'&&<div className="verification-warning" role="alert"><strong>Finished with an unresolved command failure</strong><p>The last executed command exited with status {active.last_command?.exit_status}. No later passing command verified a fix. Check the terminal output and actual files before relying on the agent’s conclusion.</p><code>{active.last_command?.command}</code></div>}
      {active && state.runs.filter((item:Item)=>item.parent === active.id).map((child:Item)=><button className="delegated-task" key={child.id} onClick={()=>select(child.id)}>↳ {state.agents.find((item:Item)=>item.id === child.agent)?.name} (depth {child.depth}) · {child.task} · <span className={'run-status status-'+child.status}>{child.status}</span></button>)}
      {!active && <div className="agent-welcome"><div className="welcome-mark">◈</div><h1>What do you want to get done?</h1><p>Work on a project, research something, or create a file.<br/>You can follow the work as it happens.</p>{!state.agents.length && <div className="setup-guidance"><h3>Connect your first model</h3><p>Add a provider, grant a workspace, then create your agent.</p><button onClick={()=>navigate('Providers')}>Connect a model →</button></div>}<div className="starter-tasks">{['Inspect my project and explain how it works','Find and fix a failing test','Research a topic and save a report'].map(text=><button key={text} onClick={()=>setTask(text)}>{text} ↗</button>)}</div></div>}
      {active && <>{messages.length ? messages.map(message=><div key={message.id} className={message.role === 'user' ? 'user-message' : 'assistant-message'}>{message.role === 'assistant' && <span className="assistant-avatar">◈</span>}{message.role==='assistant'?<Message text={message.text}/>:<div>{message.text}</div>}</div>) : <div className="user-message">{active.task}</div>}
      <div className="work-trace">{history.filter(item=>['tool_call','tool_result','tool_error','file_diff','delegation','recovery','error'].includes(item.kind)).map(item=>item.kind==='file_diff'?(<details key={item.seq} className="diff-trace-card" open><summary>▤ File diff from: <code>{item.data.command}</code></summary><pre className="file-diff" tabIndex={0} aria-label={`Changes from ${item.data.command}`}>{item.data.diff.split('\n').map((line:string,idx:number)=><span key={idx} className={line.startsWith('+')?'diff-add':line.startsWith('-')?'diff-remove':'diff-context'}>{line}{'\n'}</span>)}</pre></details>):(<details key={item.seq}><summary>{item.kind === 'tool_call' ? `↳ ${item.data.op} ${item.data.path || item.data.command || item.data.url || ''}` : item.kind.replaceAll('_',' ')}</summary><pre>{typeof item.data === 'string' ? item.data : JSON.stringify(item.data,null,2)}</pre></details>))}</div>
      {pending.map((item:Item)=><div className="inline-approval" key={item.id}><h3>Your approval is needed · {item.action.op}</h3><ActionPreview action={item.action} diff={item.diff} root={workspace?.root}/><div><button onClick={()=>void action(`approvals/${item.id}`,{approved:false})}>Deny</button><button onClick={()=>void action(`approvals/${item.id}`,{approved:true})}>Approve this action</button></div></div>)}
      {running && <p className="working-indicator">◈ {pending.length ? 'Waiting for your approval' : 'Agent is working'} <button onClick={()=>void action(`runs/${active.id}/stop`,{})}>■ Stop</button></p>}
      {['review','failed','stopped'].includes(active.status)&&<section className="inline-approval review-resolution"><h3>Review interrupted work</h3><p>Inspect the action history, actual files, and any external effects. Nothing will be replayed. Closing this review stops remaining tools and removes this conversation’s sandbox container; saved artifacts remain.</p><label>What did you inspect and what happened?<textarea aria-label="Review notes" value={reviewNote} onChange={event=>setReviewNote(event.target.value)} maxLength={8000} placeholder="Record the observed outcome and what needs to happen next."/></label><button disabled={busy||!reviewNote.trim()} onClick={()=>{setBusy(true);void action(`runs/${active.id}/resolve-review`,{note:reviewNote}).finally(()=>setBusy(false));}}>Close review without replaying actions</button></section>}{active.review_resolution&&<div className="verification-warning"><strong>Reviewed by you · previous state: {active.review_resolution.previous_status}</strong><p>{active.review_resolution.note}</p><small>No interrupted actions were replayed. A follow-up starts a new run with fresh approvals.</small></div>}</>}
    </div>
    <div className="composer-area">{error && <p role="alert" className="error">{error}</p>}<form className="agent-composer" onSubmit={event=>{event.preventDefault(); void send();}}><textarea aria-label="Message" value={task} onChange={event=>setTask(event.target.value)} placeholder={active ? 'Ask a follow-up…' : 'Give your agent a task…'} disabled={!!running}/><div className="composer-toolbar">{!active ? <><select aria-label="Agent" value={agent} onChange={event=>{setAgent(event.target.value);setGrant('');setModelSelection('');}} required><option value="">Choose agent</option>{state.agents.filter((item:Item)=>!item.archived).map((item:Item)=><option key={item.id} value={item.id}>{item.name}</option>)}</select><select aria-label="Workspace" value={grant} onChange={event=>setGrant(event.target.value)} required><option value="">Choose workspace</option>{permissions.map((item:Item)=><option key={item.id} value={item.id}>{item.mode} · {item.root}</option>)}</select><select aria-label="Task model" value={modelSelection} onChange={event=>setModelSelection(event.target.value)}><option value="">Agent default · {profile?.model || state.defaults[0]?.model || 'unset'}</option>{state.providers.filter((connection:Item)=>!connection.archived).map((connection:Item)=><optgroup key={connection.id} label={connection.name}>{connection.models.map((model:Item)=><option key={model.id} value={JSON.stringify({connection:connection.id,model:model.id})}>{model.id} · {model.source}</option>)}</optgroup>)}</select></> : <small>{profile?.name} · {active.model}</small>}<button type="submit" aria-label={active ? 'Send follow-up' : 'Start task'} disabled={busy || !!running || !task.trim() || (!!active && !['completed','reviewed'].includes(active.status))}>↑</button></div></form><p className="composer-footnote">{provider?.name || 'No model connected'}{provider?.name?.toLowerCase().includes('fixture') && ' · Scripted test fixture, not a real model'}{workspace?.mode === 'host' && ' · Host shell can reach your whole user account'}</p></div></div>
    <section className="work-surface"><div className="surface-heading"><strong>Workspace</strong><small>{!workspace ? 'No workspace selected' : workspace.mode === 'host' ? state.capabilities.machine : 'Docker sandbox'}</small></div><div className="surface-tabs">{['Terminal','Browser','Files','Task Tree','Activity'].map(name=><button key={name} className={tab === name ? 'active-tab' : ''} onClick={()=>setTab(name)}>{name}</button>)}</div><div className="surface-content">
    {tab === 'Terminal' && <><div className="terminal-title">TERMINAL OUTPUT</div><pre className="terminal-output">{history.filter(item=>item.kind === 'terminal').map(item=>item.data.output).join('') || 'Command output will appear here when the agent runs a terminal tool.'}</pre></>}
    {tab === 'Browser' && <BrowserPanel run={active} artifacts={artifacts} request={request} refresh={refresh}/>}
    {tab === 'Files' && <>{artifacts.map((item:Item)=><a className="artifact-file" key={item.id} href={`/api/artifacts/${item.id}`} download>▤ {item.name}<span>↓</span></a>)}{!artifacts.length && <div className="surface-empty">▤<h3>No output files yet</h3><p>Files produced by this run will be available to inspect and download here.</p></div>}</>}
    {tab === 'Task Tree' && <TaskTree runId={active?.id} request={request} onSelectRun={select}/>}
    {tab === 'Activity' && history.map(item=><details key={item.seq}><summary>{item.kind} · {new Date(item.time*1000).toLocaleTimeString()}</summary><pre>{JSON.stringify(item.data,null,2)}</pre></details>)}
    </div></section>
  </div>;
}
