import {useEffect, useState} from 'react';

type Item = Record<string, any>;

export function ArtifactPreviewModal({
  artifact,
  request,
  onClose,
}: {
  artifact: Item | null;
  request: (path: string, body?: unknown) => Promise<any>;
  onClose: () => void;
}) {
  const [textData, setTextData] = useState<{content: string; size: number; truncated: boolean} | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState('');

  const name = artifact?.name || '';
  const isImage = /\.(png|jpe?g|webp|gif|svg)$/i.test(name);

  useEffect(() => {
    if (!artifact) {
      setTextData(null);
      setError('');
      return;
    }
    if (isImage) return;

    let cancelled = false;
    setLoading(true);
    setError('');
    request(`artifacts/${artifact.id}/text`)
      .then(res => {
        if (!cancelled) setTextData(res);
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
  }, [artifact?.id]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!artifact) return null;

  async function copyText() {
    if (!textData?.content) return;
    try {
      await navigator.clipboard.writeText(textData.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
    }
  }

  return (
    <div
      className="modal-backdrop"
      onMouseDown={e => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <section
        className="editor-modal artifact-preview-modal"
        role="dialog"
        aria-modal="true"
        aria-label={`Preview of ${name}`}
      >
        <div className="editor-heading">
          <div>
            <small>ARTIFACT PREVIEW</small>
            <h2>{name}</h2>
          </div>
          <button aria-label="Close preview" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="artifact-preview-body">
          {error && <div className="feedback failure" role="alert">{error}</div>}
          {loading && <p className="muted">Loading artifact content…</p>}
          {isImage ? (
            <div className="artifact-image-container">
              <img src={`/api/artifacts/${artifact.id}/preview`} alt={name} />
            </div>
          ) : textData ? (
            <div className="artifact-text-container">
              <div className="artifact-text-toolbar">
                <small>
                  Size: {textData.size} bytes
                  {textData.truncated ? ' (preview truncated at 500KB)' : ''}
                </small>
                <button type="button" onClick={copyText}>
                  {copied ? '✓ Copied' : 'Copy content'}
                </button>
              </div>
              <pre className="artifact-text-content" tabIndex={0}>
                {textData.content}
              </pre>
            </div>
          ) : !loading && !error ? (
            <div className="surface-empty">
              <p>Binary or non-text file.</p>
            </div>
          ) : null}
        </div>

        <div className="editor-actions">
          <button type="button" onClick={onClose}>
            Close
          </button>
          <a
            className="primary button-link"
            href={`/api/artifacts/${artifact.id}`}
            download={name}
          >
            Download file ↓
          </a>
        </div>
      </section>
    </div>
  );
}

