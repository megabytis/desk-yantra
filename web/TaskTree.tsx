import {useEffect, useState} from 'react';

type Item = Record<string, any>;

interface TreeNode {
  id: string;
  task: string;
  agent: string;
  agent_id: string;
  status: string;
  tools: string[];
  depth: number;
  created: number;
  stop_reason?: string;
  outcome?: string;
  verification?: Item;
  artifacts: Array<{id: string; name: string; created: number}>;
  children: TreeNode[];
}

export function TaskTree({
  runId,
  request,
  onSelectRun,
}: {
  runId?: string;
  request: (path: string, body?: unknown) => Promise<any>;
  onSelectRun: (id: string) => void;
}) {
  const [tree, setTree] = useState<TreeNode | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!runId) {
      setTree(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    request(`runs/${runId}/tree`)
      .then(res => {
        if (!cancelled) setTree(res);
      })
      .catch(err => {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [runId]);

  if (loading && !tree) {
    return <div className="surface-empty"><p>Loading delegation tree…</p></div>;
  }
  if (error) {
    return <div role="alert" className="feedback failure">{error}</div>;
  }
  if (!tree) {
    return (
      <div className="surface-empty">
        <h3>No task tree</h3>
        <p>Select an active or historical run to inspect its task hierarchy.</p>
      </div>
    );
  }

  function renderNode(node: TreeNode, isRoot = false) {
    const isSelected = node.id === runId;
    const vStatus = node.verification?.outcome || node.outcome;
    return (
      <div key={node.id} className={`tree-branch depth-${node.depth}`}>
        <div
          className={`tree-card ${isSelected ? 'tree-selected' : ''}`}
          onClick={() => onSelectRun(node.id)}
          role="button"
          tabIndex={0}
          onKeyDown={e => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              onSelectRun(node.id);
            }
          }}
          aria-label={`Task ${node.id}: ${node.agent} - ${node.task}`}
        >
          <div className="tree-card-header">
            <span className="tree-agent-badge">
              {isRoot ? '★ Root Agent: ' : '↳ Subagent: '}
              <strong>{node.agent}</strong>
            </span>
            <span className={`run-status status-${node.status}`}>{node.status}</span>
            {vStatus && (
              <span className={`verification-badge status-${vStatus.includes('verified') ? 'verified' : 'unverified'}`}>
                {vStatus.replace(/_/g, ' ')}
              </span>
            )}
          </div>
          <p className="tree-task-text">{node.task}</p>
          <div className="tree-card-meta">
            <small>Depth: {node.depth} · Tools: {node.tools.join(', ') || 'none'}</small>
            {node.stop_reason && <small> · Stop reason: {node.stop_reason}</small>}
          </div>
          {node.artifacts && node.artifacts.length > 0 && (
            <div className="tree-artifacts">
              <small>Artifacts:</small>
              {node.artifacts.map(a => (
                <a
                  key={a.id}
                  href={`/api/artifacts/${a.id}`}
                  download
                  onClick={e => e.stopPropagation()}
                  className="tree-artifact-link"
                >
                  ▤ {a.name}
                </a>
              ))}
            </div>
          )}
        </div>
        {node.children && node.children.length > 0 && (
          <div className="tree-children">
            {node.children.map(child => renderNode(child))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="delegation-tree-container">
      <div className="tree-toolbar">
        <strong>Task Hierarchy & Delegation Tree</strong>
        <small>Click any task to inspect its conversation and execution trace.</small>
      </div>
      {renderNode(tree, true)}
    </div>
  );
}

