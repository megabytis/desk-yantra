type Item=Record<string,any>;
export function fixtureConnections(state:Item):Set<string>{
  return new Set(state.providers.filter((provider:Item)=>{
    try{const url=new URL(provider.url);if(!['localhost','127.0.0.1'].includes(url.hostname))return false;const scripted=url.port==='18767'&&provider.name.startsWith('Fixture');const live=url.port==='18768'&&['Live llama.cpp Qwen3 0.6B','Live llama.cpp local model','Live sandbox local model','Live local repair model'].includes(provider.name);return scripted||live;}
    catch{return false;}
  }).map((provider:Item)=>provider.id));
}
export function personalState(state:Item):Item{
  const fixtures=fixtureConnections(state);
  const hiddenAgents=new Set(state.agents.filter((agent:Item)=>fixtures.has(agent.connection)||agent.model?.startsWith('fixture-')).map((agent:Item)=>agent.id));
  const agents=state.agents.filter((agent:Item)=>!hiddenAgents.has(agent.id));
  const hiddenGrants=new Set(state.agents.filter((agent:Item)=>hiddenAgents.has(agent.id)).flatMap((agent:Item)=>agent.grants));
  const visibleGrants=new Set(agents.flatMap((agent:Item)=>agent.grants));
  const runs=state.runs.filter((run:Item)=>!fixtures.has(run.connection)&&!hiddenAgents.has(run.agent));
  const runIds=new Set(runs.map((run:Item)=>run.id));
  return {...state,providers:state.providers.filter((provider:Item)=>!fixtures.has(provider.id)),agents,runs,grants:state.grants.filter((grant:Item)=>!hiddenGrants.has(grant.id)||visibleGrants.has(grant.id)),defaults:state.defaults.filter((item:Item)=>!fixtures.has(item.connection)),approvals:state.approvals.filter((item:Item)=>runIds.has(item.run)),artifacts:state.artifacts.filter((item:Item)=>runIds.has(item.run))};
}
