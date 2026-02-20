function DebugPanel({ data, onClose }) {
  const debug = data?.debug;
  const sources = data?.sources || [];

  return (
    <div className="debug-panel">
      <div className="debug-panel__header">
        <h2>🔧 Debug Info</h2>
        <button
          className="debug-panel__toggle"
          onClick={onClose}
          title="Hide debug panel"
        >
          ✕
        </button>
      </div>

      {!debug ? (
        <div className="debug-panel__empty">
          Send a message to see debug information about the RAG pipeline, model
          routing, and evaluation results.
        </div>
      ) : (
        <div className="debug-panel__content">
          {/* Model Info */}
          <div className="debug-section">
            <div className="debug-section__title">🤖 Model</div>
            <div className="debug-row">
              <span className="debug-row__label">Model</span>
              <span className="debug-row__value debug-row__value--model">
                {debug.model_used}
              </span>
            </div>
            <div className="debug-row">
              <span className="debug-row__label">Classification</span>
              <span className="debug-row__value">
                {debug.classification === "complex" ? "🟠" : "🟢"}{" "}
                {debug.classification}
              </span>
            </div>
            <div className="debug-row">
              <span className="debug-row__label">Complex Score</span>
              <span className="debug-row__value">{debug.complex_score}</span>
            </div>
          </div>

          {/* Tokens */}
          <div className="debug-section">
            <div className="debug-section__title">📊 Tokens & Latency</div>
            <div className="debug-row">
              <span className="debug-row__label">Input Tokens</span>
              <span className="debug-row__value">
                {debug.tokens_input?.toLocaleString()}
              </span>
            </div>
            <div className="debug-row">
              <span className="debug-row__label">Output Tokens</span>
              <span className="debug-row__value">
                {debug.tokens_output?.toLocaleString()}
              </span>
            </div>
            <div className="debug-row">
              <span className="debug-row__label">Latency</span>
              <span className="debug-row__value">
                {debug.latency_ms?.toLocaleString()} ms
              </span>
            </div>
          </div>

          {/* Confidence */}
          <div className="debug-section">
            <div className="debug-section__title">🎯 Evaluation</div>
            <div className="debug-row">
              <span className="debug-row__label">Confidence</span>
              <span
                className={`confidence-badge confidence-badge--${debug.confidence}`}
              >
                {debug.confidence === "high" ? "✓" : "⚠"} {debug.confidence}
              </span>
            </div>
            {debug.flags && debug.flags.length > 0 ? (
              <div className="debug-flags">
                {debug.flags.map((flag, i) => (
                  <span key={i} className="flag-tag">
                    ⚠ {flag}
                  </span>
                ))}
              </div>
            ) : (
              <div className="no-flags">No flags — all checks passed</div>
            )}
          </div>

          {/* Router Signals */}
          {debug.signals && debug.signals.length > 0 && (
            <div className="debug-section">
              <div className="debug-section__title">📡 Router Signals</div>
              <div className="debug-signals">
                {debug.signals.map((sig, i) => (
                  <span key={i} className="signal-tag">
                    {sig}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Sources */}
          <div className="debug-section">
            <div className="debug-section__title">📚 Retrieved Sources</div>
            {sources.length > 0 ? (
              <div className="debug-sources">
                {sources.map((src, i) => (
                  <div key={i} className="debug-source-item">
                    <div className="debug-source-item__name">
                      📄 {src.document_name}
                    </div>
                    <div className="debug-source-item__meta">
                      <span>Chunk #{src.chunk_id}</span>
                      <span>
                        Score: {(src.similarity_score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="no-sources">No sources retrieved</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default DebugPanel;
