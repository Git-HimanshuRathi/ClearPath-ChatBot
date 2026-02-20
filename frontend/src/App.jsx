import { useState, useCallback, useRef } from "react";
import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";
import DebugPanel from "./components/DebugPanel";
import "./App.css";

const API_URL = "http://localhost:8000";

function App() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [debugInfo, setDebugInfo] = useState(null);
  const [showDebug, setShowDebug] = useState(true);
  const sessionId = useRef(`session-${Date.now()}`);

  const sendMessage = useCallback(
    async (text) => {
      if (!text.trim() || isLoading) return;

      // Add user message
      const userMsg = { role: "user", content: text };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);
      setDebugInfo(null);

      // Add placeholder for assistant
      const assistantMsg = { role: "assistant", content: "", streaming: true };
      setMessages((prev) => [...prev, assistantMsg]);

      try {
        // Use SSE streaming endpoint
        const response = await fetch(`${API_URL}/chat/stream`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: text,
            session_id: sessionId.current,
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let fullResponse = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          // Parse SSE events from buffer
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          let eventType = "";
          for (const line of lines) {
            if (line.startsWith("event: ")) {
              eventType = line.slice(7).trim();
            } else if (line.startsWith("data: ")) {
              const data = line.slice(6);
              try {
                const parsed = JSON.parse(data);

                if (eventType === "chunk" && parsed.text) {
                  fullResponse += parsed.text;
                  setMessages((prev) => {
                    const updated = [...prev];
                    const last = updated[updated.length - 1];
                    if (last && last.role === "assistant") {
                      updated[updated.length - 1] = {
                        ...last,
                        content: fullResponse,
                      };
                    }
                    return updated;
                  });
                } else if (eventType === "metadata") {
                  setDebugInfo(parsed);
                  // Update message with sources
                  setMessages((prev) => {
                    const updated = [...prev];
                    const last = updated[updated.length - 1];
                    if (last && last.role === "assistant") {
                      updated[updated.length - 1] = {
                        ...last,
                        streaming: false,
                        sources: parsed.sources,
                      };
                    }
                    return updated;
                  });
                }
              } catch {
                // skip invalid JSON
              }
            }
          }
        }
      } catch (err) {
        console.error("Chat error:", err);
        // Fall back to standard endpoint
        try {
          const response = await fetch(`${API_URL}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              query: text,
              session_id: sessionId.current,
            }),
          });

          if (!response.ok) throw new Error(`HTTP ${response.status}`);

          const data = await response.json();
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              role: "assistant",
              content: data.response,
              sources: data.sources,
              streaming: false,
            };
            return updated;
          });
          setDebugInfo({ sources: data.sources, debug: data.debug });
        } catch (fallbackErr) {
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              role: "assistant",
              content: `⚠️ Error: Could not connect to the backend. Make sure the server is running on ${API_URL}.\n\nDetails: ${fallbackErr.message}`,
              streaming: false,
            };
            return updated;
          });
        }
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading],
  );

  return (
    <div className="app-container">
      <div className="chat-area">
        {/* Header */}
        <header className="chat-header">
          <div className="chat-header__logo">C</div>
          <div className="chat-header__info">
            <h1>Clearpath Support</h1>
            <p>AI-Powered Customer Support Assistant</p>
          </div>
          <div className="chat-header__status">
            <div className="status-dot" />
            <span>Online</span>
          </div>
        </header>

        {/* Messages */}
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          onSuggestionClick={sendMessage}
        />

        {/* Input */}
        <ChatInput onSend={sendMessage} disabled={isLoading} />
      </div>

      {/* Debug sidebar */}
      {showDebug ? (
        <DebugPanel data={debugInfo} onClose={() => setShowDebug(false)} />
      ) : (
        <button
          className="debug-toggle-btn"
          onClick={() => setShowDebug(true)}
          title="Show debug panel"
        >
          🔧
        </button>
      )}
    </div>
  );
}

export default App;
