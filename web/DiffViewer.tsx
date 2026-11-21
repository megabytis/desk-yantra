import {useState} from 'react';

export function DiffViewer({
  diff,
  command,
}: {
  diff: string;
  command?: string;
}) {
  const [mode, setMode] = useState<'inline' | 'side-by-side'>('inline');
  const [expanded, setExpanded] = useState(false);

  const rawLines = diff.split('\n');
  const isLarge = rawLines.length > 35;
  const displayLines = isLarge && !expanded ? rawLines.slice(0, 35) : rawLines;

  // For side-by-side parsing:
  // Build paired rows [left: {num, text, type}, right: {num, text, type}]
  const sbsRows: Array<{
    left?: {num?: number; text: string; type: 'context' | 'remove'};
    right?: {num?: number; text: string; type: 'context' | 'add'};
  }> = [];

  if (mode === 'side-by-side') {
    let leftNum = 1;
    let rightNum = 1;

    for (const line of displayLines) {
      if (line.startsWith('---') || line.startsWith('+++') || line.startsWith('index ')) {
        continue;
      }
      if (line.startsWith('@@')) {
        // Hunk header: @@ -l,s +r,s @@
        const match = line.match(/@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
        if (match) {
          leftNum = parseInt(match[1], 10);
          rightNum = parseInt(match[2], 10);
        }
        sbsRows.push({
          left: {text: line, type: 'context'},
          right: {text: line, type: 'context'},
        });
      } else if (line.startsWith('-')) {
        sbsRows.push({
          left: {num: leftNum++, text: line.slice(1), type: 'remove'},
          right: undefined,
        });
      } else if (line.startsWith('+')) {
        // Try pairing with last unpaired left removal if immediate
        const last = sbsRows[sbsRows.length - 1];
        if (last && last.left && last.left.type === 'remove' && !last.right) {
          last.right = {num: rightNum++, text: line.slice(1), type: 'add'};
        } else {
          sbsRows.push({
            left: undefined,
            right: {num: rightNum++, text: line.slice(1), type: 'add'},
          });
        }
      } else {
        const text = line.startsWith(' ') ? line.slice(1) : line;
        sbsRows.push({
          left: {num: leftNum++, text, type: 'context'},
          right: {num: rightNum++, text, type: 'context'},
        });
      }
    }
  }

  return (
    <div className="diff-viewer-wrapper">
      <div className="diff-viewer-toolbar">
        {command && <span className="diff-command">▤ <code>{command}</code></span>}
        <div className="diff-mode-toggle">
          <button
            type="button"
            className={mode === 'inline' ? 'active-diff-mode' : ''}
            onClick={() => setMode('inline')}
            aria-label="Inline diff"
          >
            Inline
          </button>
          <button
            type="button"
            className={mode === 'side-by-side' ? 'active-diff-mode' : ''}
            onClick={() => setMode('side-by-side')}
            aria-label="Side by side diff"
          >
            Side-by-Side
          </button>
        </div>
      </div>

      {mode === 'inline' ? (
        <pre className="file-diff file-diff-inline" tabIndex={0} aria-label="Inline file diff">
          {displayLines.map((line, idx) => (
            <span
              key={idx}
              className={line.startsWith('+') ? 'diff-add' : line.startsWith('-') ? 'diff-remove' : 'diff-context'}
            >
              {line}{'\n'}
            </span>
          ))}
        </pre>
      ) : (
        <div className="file-diff-sbs" tabIndex={0} aria-label="Side-by-side file diff">
          <table className="sbs-table">
            <thead>
              <tr>
                <th colSpan={2}>Original</th>
                <th colSpan={2}>Modified</th>
              </tr>
            </thead>
            <tbody>
              {sbsRows.map((row, idx) => (
                <tr key={idx}>
                  <td className="sbs-num">{row.left?.num ?? ''}</td>
                  <td className={`sbs-content ${row.left ? 'sbs-' + row.left.type : 'sbs-empty'}`}>
                    {row.left?.text ?? ''}
                  </td>
                  <td className="sbs-num">{row.right?.num ?? ''}</td>
                  <td className={`sbs-content ${row.right ? 'sbs-' + row.right.type : 'sbs-empty'}`}>
                    {row.right?.text ?? ''}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {isLarge && (
        <div className="diff-expand-bar">
          <button type="button" onClick={() => setExpanded(!expanded)}>
            {expanded ? '▲ Collapse diff' : `▼ Show full diff (${rawLines.length} lines)`}
          </button>
        </div>
      )}
    </div>
  );
}

