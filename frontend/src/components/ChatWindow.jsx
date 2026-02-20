import { useRef, useEffect } from "react";

const SUGGESTIONS = [
  "What is Clearpath?",
  "What are the pricing plans?",
  "How do I reset my password?",
  "Explain the GitHub integration",
];

function ChatWindow({ messages, isLoading, onSuggestionClick }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="chat-window">
        <div className="chat-window__empty">
          <div className="chat-window__empty-icon">💬</div>
          <h3>Welcome to Clearpath Support</h3>
          <p>
            Ask me anything about Clearpath — features, billing,
            troubleshooting, and more. I'll answer using our official
            documentation.
          </p>
          <div className="chat-window__suggestions">
            {SUGGESTIONS.map((s, i) => (
              <button
                key={i}
                className="suggestion-chip"
                onClick={() => onSuggestionClick(s)}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-window">
      {messages.map((msg, i) => (
        <div key={i} className={`message message--${msg.role}`}>
          <div className="message__avatar">
            {msg.role === "user" ? "U" : "C"}
          </div>
          <div className="message__content">
            {msg.content || (
              <div className="typing-indicator">
                <span />
                <span />
                <span />
              </div>
            )}
            {/* Source citations for assistant messages */}
            {msg.role === "assistant" &&
              msg.sources &&
              msg.sources.length > 0 &&
              !msg.streaming && (
                <div className="message__sources">
                  <div className="message__sources-title">📎 Sources</div>
                  {msg.sources.map((src, j) => (
                    <span key={j} className="source-tag">
                      📄 {src.document_name.replace(".pdf", "")} #{src.chunk_id}{" "}
                      ({(src.similarity_score * 100).toFixed(0)}%)
                    </span>
                  ))}
                </div>
              )}
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}

export default ChatWindow;
