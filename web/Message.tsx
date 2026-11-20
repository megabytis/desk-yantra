import {ReactNode,useRef,useState} from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function CodeBlock({children}:{children?:ReactNode}){
  const content=useRef<HTMLPreElement>(null);
  const [copied,setCopied]=useState(false);
  async function copy(){try{await navigator.clipboard.writeText(content.current?.textContent||'');setCopied(true);setTimeout(()=>setCopied(false),1800);}catch{setCopied(false);}}
  return <div className="message-code" role="region" aria-label="Code block"><div className="code-toolbar"><span>Code</span><button type="button" onClick={()=>void copy()} aria-label={copied?'Code copied to clipboard':'Copy code'}>{copied?'Copied':'Copy'}</button></div><pre ref={content} tabIndex={0} aria-label="Code content">{children}</pre></div>;
}

export function Message({text}:{text:string}){
  return <div className="markdown-message"><ReactMarkdown remarkPlugins={[remarkGfm]} skipHtml components={{pre:({children})=><CodeBlock>{children}</CodeBlock>,a:({href,children})=><a href={href} target="_blank" rel="noopener noreferrer">{children}</a>,img:({alt})=><span className="external-image-label">[Image: {alt||'external image'} — open its source to view]</span>}}>{text}</ReactMarkdown></div>;
}

export function ActionPreview({action,diff,root}:{action:Record<string,any>;diff?:string;root?:string}){
  if(action.op==='screen')return <div className="action-preview"><div className="action-path">Capture your real desktop</div><p>The screenshot is saved privately. If the selected model is known to support vision, the captured image will also be sent to that model. This is separate from sandbox browser capture.</p></div>;
  if(action.op==='write')return <div className="action-preview"><div className="action-path">▤ {action.path}</div>{diff?<pre className="file-diff" tabIndex={0} aria-label={`File diff for ${action.path}`}>{diff.split('\n').map((line,index)=><span key={index} className={line.startsWith('+')?'diff-add':line.startsWith('-')?'diff-remove':'diff-context'}>{line}{'\n'}</span>)}</pre>:<pre tabIndex={0} aria-label={`File content for ${action.path}`}>{action.content}</pre>}</div>;
  if(action.op==='shell')return <div className="action-preview"><div className="action-path">Terminal · {root||'Authorized workspace'}</div><pre tabIndex={0} aria-label="Shell command to execute"><code>{action.command}</code></pre><p>This exact command will run with the permissions of the selected workspace.</p></div>;
  if(action.op==='browser')return <div className="action-preview"><div className="action-path">Browser action</div><p>{action.url||'Current browser page'}</p>{action.selector&&<pre tabIndex={0} aria-label="Browser action details">{action.content?`Fill ${action.selector}\n${action.content}`:`Click ${action.selector}`}</pre>}<small>Navigation and interaction may affect external services.</small></div>;
  return <div className="action-preview"><pre tabIndex={0} aria-label="Action details">{JSON.stringify(action,null,2)}</pre></div>;
}
