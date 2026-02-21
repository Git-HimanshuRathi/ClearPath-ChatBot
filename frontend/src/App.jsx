import { useState, useCallback, useRef } from "react";
import Sidebar from "./components/Sidebar";
import MainLayout from "./components/MainLayout";

const API_URL = "http://localhost:8000";

function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

function createNewChat() {
  return {
    id: generateId(),
    title: "New chat",
    messages: [],
    model: null,
    lastDebug: null,
    lastSources: null,
  };
}

export default function App() {
  const [chats, setChats] = useState([createNewChat()]);
  const [activeChatId, setActiveChatId] = useState(chats[0].id);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [debugOpen, setDebugOpen] = useState(false);
  const abortRef = useRef(null);

  const activeChat = chats.find((c) => c.id === activeChatId) || chats[0];

  const updateChat = useCallback((chatId, updater) => {
    setChats((prev) => prev.map((c) => (c.id === chatId ? updater(c) : c)));
  }, []);

  const handleNewChat = useCallback(() => {
    const chat = createNewChat();
    setChats((prev) => [chat, ...prev]);
    setActiveChatId(chat.id);
  }, []);

  const handleDeleteChat = useCallback(
    (chatId) => {
      setChats((prev) => {
        const filtered = prev.filter((c) => c.id !== chatId);
        if (filtered.length === 0) {
          const fresh = createNewChat();
          setActiveChatId(fresh.id);
          return [fresh];
        }
        if (chatId === activeChatId) {
          setActiveChatId(filtered[0].id);
        }
        return filtered;
      });
    },
    [activeChatId],
  );

  const handleSend = useCallback(
    async (text) => {
      if (!text.trim() || isStreaming) return;

      const userMsg = { id: generateId(), role: "user", content: text };
      const assistantMsg = { id: generateId(), role: "assistant", content: "" };
      const chatId = activeChatId;

      updateChat(chatId, (c) => ({
        ...c,
        title: c.messages.length === 0 ? text.slice(0, 40) : c.title,
        messages: [...c.messages, userMsg, assistantMsg],
      }));

      setIsStreaming(true);
      const controller = new AbortController();
      abortRef.current = controller;

      try {
        // Try SSE streaming endpoint
        const res = await fetch(`${API_URL}/chat/stream`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: text, session_id: chatId }),
          signal: controller.signal,
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let fullText = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          let eventType = "";
          for (const line of lines) {
            if (line.startsWith("event: ")) {
              eventType = line.slice(7).trim();
            } else if (line.startsWith("data: ")) {
              try {
                const parsed = JSON.parse(line.slice(6));
                if (eventType === "chunk" && parsed.text) {
                  fullText += parsed.text;
                  updateChat(chatId, (c) => ({
                    ...c,
                    messages: c.messages.map((m) =>
                      m.id === assistantMsg.id
                        ? { ...m, content: fullText }
                        : m,
                    ),
                  }));
                } else if (eventType === "metadata") {
                  const model = parsed.debug?.model_used || null;
                  updateChat(chatId, (c) => ({
                    ...c,
                    model,
                    lastDebug: parsed.debug,
                    lastSources: parsed.sources,
                    messages: c.messages.map((m) =>
                      m.id === assistantMsg.id
                        ? { ...m, sources: parsed.sources, debug: parsed.debug }
                        : m,
                    ),
                  }));
                  // Auto-open debug panel on first response
                  setDebugOpen(true);
                }
              } catch {
                /* skip unparseable lines */
              }
            }
          }
        }
      } catch (err) {
        if (err.name === "AbortError") return;
        // Fallback to non-streaming /chat
        try {
          const res = await fetch(`${API_URL}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: text, session_id: chatId }),
          });
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          const data = await res.json();
          updateChat(chatId, (c) => ({
            ...c,
            model: data.debug?.model_used || null,
            lastDebug: data.debug,
            lastSources: data.sources,
            messages: c.messages.map((m) =>
              m.id === assistantMsg.id
                ? {
                    ...m,
                    content: data.response,
                    sources: data.sources,
                    debug: data.debug,
                  }
                : m,
            ),
          }));
          setDebugOpen(true);
        } catch (fallbackErr) {
          updateChat(chatId, (c) => ({
            ...c,
            messages: c.messages.map((m) =>
              m.id === assistantMsg.id
                ? {
                    ...m,
                    content: `⚠️ Could not connect to backend at ${API_URL}.\n\nIs the server running? Start it with:\n\`uvicorn main:app --port 8000 --reload\`\n\n${fallbackErr.message}`,
                  }
                : m,
            ),
          }));
        }
      } finally {
        setIsStreaming(false);
        abortRef.current = null;
      }
    },
    [activeChatId, isStreaming, updateChat],
  );

  return (
    <div className="flex h-full">
      <Sidebar
        chats={chats}
        activeChatId={activeChatId}
        isOpen={sidebarOpen}
        onSelectChat={setActiveChatId}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
        onToggle={() => setSidebarOpen((o) => !o)}
      />
      <MainLayout
        chat={activeChat}
        isStreaming={isStreaming}
        sidebarOpen={sidebarOpen}
        debugOpen={debugOpen}
        onSend={handleSend}
        onToggleSidebar={() => setSidebarOpen((o) => !o)}
        onToggleDebug={() => setDebugOpen((o) => !o)}
      />
    </div>
  );
}
