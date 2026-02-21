import { useState } from "react";

export default function DebugPanel({ data, isOpen, onToggle }) {
  const debug = data?.debug;
  const sources = data?.sources || [];

  if (!isOpen) return null;

  return (
    <div className="w-[300px] min-w-[300px] h-full bg-bg-sidebar border-l border-border/30 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border/30">
        <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
          Debug
        </span>
        <button
          onClick={onToggle}
          className="p-1 rounded text-text-muted hover:text-text-primary hover:bg-bg-hover transition-colors"
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      {!debug ? (
        <div className="flex-1 flex items-center justify-center p-4">
          <p className="text-xs text-text-muted text-center leading-relaxed">
            Send a message to see debug info about model routing, tokens &
            evaluator.
          </p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto p-3 space-y-3">
          {/* Model */}
          <Section title="Model">
            <Row
              label="Model"
              value={
                <span className="font-mono text-[11px] bg-bg-input px-2 py-0.5 rounded border border-border/40">
                  {debug.model_used}
                </span>
              }
            />
            <Row
              label="Classification"
              value={
                <span>
                  {debug.classification === "complex" ? "🟠" : "🟢"}{" "}
                  {debug.classification}
                </span>
              }
            />
            <Row label="Score" value={debug.complex_score} />
          </Section>

          {/* Tokens */}
          <Section title="Tokens & Latency">
            <Row label="Input" value={debug.tokens_input?.toLocaleString()} />
            <Row label="Output" value={debug.tokens_output?.toLocaleString()} />
            <Row
              label="Latency"
              value={`${debug.latency_ms?.toLocaleString()} ms`}
            />
          </Section>

          {/* Evaluator */}
          <Section title="Evaluator">
            <Row
              label="Confidence"
              value={
                <span
                  className={`px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                    debug.confidence === "high"
                      ? "bg-green-500/15 text-green-400 border border-green-500/20"
                      : "bg-amber-500/15 text-amber-400 border border-amber-500/20"
                  }`}
                >
                  {debug.confidence === "high" ? "✓" : "⚠"} {debug.confidence}
                </span>
              }
            />
            {debug.flags?.length > 0 ? (
              <div className="mt-1.5 space-y-1">
                {debug.flags.map((flag, i) => (
                  <div
                    key={i}
                    className="text-[11px] font-mono text-red-400 bg-red-500/10 border border-red-500/15 rounded px-2 py-1"
                  >
                    ⚠ {flag}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-[11px] text-text-muted italic mt-1">
                No flags
              </p>
            )}
          </Section>

          {/* Signals */}
          {debug.signals?.length > 0 && (
            <Section title="Router Signals">
              <div className="space-y-1">
                {debug.signals.map((sig, i) => (
                  <div
                    key={i}
                    className="text-[11px] font-mono text-text-secondary bg-bg-input rounded px-2 py-1 border border-border/30"
                  >
                    {sig}
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Sources */}
          <Section title={`Sources (${sources.length})`}>
            {sources.length > 0 ? (
              <div className="space-y-1.5">
                {sources.map((src, i) => (
                  <div
                    key={i}
                    className="bg-bg-input rounded-lg p-2 border border-border/30"
                  >
                    <div className="text-[11px] font-medium text-accent truncate">
                      📄 {src.document || src.document_name}
                    </div>
                    <div className="text-[10px] text-text-muted mt-0.5 flex gap-3">
                      {src.chunk_id != null && (
                        <span>Chunk #{src.chunk_id}</span>
                      )}
                      <span>
                        {(
                          (src.relevance_score || src.similarity_score) * 100
                        ).toFixed(1)}
                        %
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-[11px] text-text-muted italic">No sources</p>
            )}
          </Section>
        </div>
      )}
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div className="bg-bg-main/50 rounded-lg p-3 border border-border/20">
      <div className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-2">
        {title}
      </div>
      {children}
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex items-center justify-between py-1 text-[12px]">
      <span className="text-text-secondary">{label}</span>
      <span className="text-text-primary font-medium">{value}</span>
    </div>
  );
}
