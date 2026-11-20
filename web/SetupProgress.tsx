type Item=Record<string,any>;
export function SetupProgress({state,navigate}:{state:Item;navigate:(page:string)=>void}){
  const connected=state.providers.some((item:Item)=>!item.archived&&item.models.length>0);
  const authorized=state.grants.some((item:Item)=>!item.revoked);
  const configured=state.agents.some((agent:Item)=>!agent.archived&&agent.grants.some((id:string)=>state.grants.some((grant:Item)=>grant.id===id&&!grant.revoked)));
  if(connected&&authorized&&configured)return null;
  const steps=[{title:'Connect a model',detail:'Local server or hosted API',page:'Providers',done:connected},{title:'Choose a workspace',detail:'Sandbox or explicit host access',page:'Permissions',done:authorized},{title:'Set up your agent',detail:'Instructions, tools, and permissions',page:'Agents',done:configured}];
  const completedCount=steps.filter(s=>s.done).length;
  const currentStepIndex=steps.findIndex(s=>!s.done);
  return <section className="setup-progress" aria-label="Workbench setup"><div><strong>Set up Desk Yantra</strong><span>Three steps to your first task</span></div><div className="setup-steps" role="list" aria-label={`Setup progress: ${completedCount} of ${steps.length} steps completed`}>{steps.map((step,index)=><button key={step.page} className={step.done?'step-complete':''} onClick={()=>navigate(step.page)} role="listitem" aria-current={index===currentStepIndex?'step':undefined} aria-label={`Step ${index+1}: ${step.title} — ${step.done?'completed':'not completed'}. ${step.detail}`}><b aria-hidden="true">{step.done?'✓':index+1}</b><span><strong>{step.title}</strong><small>{step.detail}</small></span><span aria-hidden="true">→</span></button>)}</div></section>;
}
