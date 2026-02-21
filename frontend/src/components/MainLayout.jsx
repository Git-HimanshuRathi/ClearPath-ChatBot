import Header from "./Header";
import ChatWindow from "./ChatWindow";
import ChatInput from "./ChatInput";
import DebugPanel from "./DebugPanel";

export default function MainLayout({
  chat,
  isStreaming,
  sidebarOpen,
  debugOpen,
  onSend,
  onToggleSidebar,
  onToggleDebug,
}) {
  return (
    <div className="flex-1 flex h-full min-w-0">
      {/* Chat area */}
      <main className="flex-1 flex flex-col h-full min-w-0 bg-bg-main relative">
        <Header
          model={chat.model}
          sidebarOpen={sidebarOpen}
          debugOpen={debugOpen}
          onToggleSidebar={onToggleSidebar}
          onToggleDebug={onToggleDebug}
        />
        <ChatWindow
          messages={chat.messages}
          isStreaming={isStreaming}
          onSuggestionClick={onSend}
        />
        <ChatInput onSend={onSend} disabled={isStreaming} />
      </main>

      {/* Debug panel */}
      <DebugPanel
        data={{ debug: chat.lastDebug, sources: chat.lastSources }}
        isOpen={debugOpen}
        onToggle={onToggleDebug}
      />
    </div>
  );
}
