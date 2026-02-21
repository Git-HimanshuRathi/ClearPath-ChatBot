import { useState } from "react";

export default function Sidebar({
  chats,
  activeChatId,
  isOpen,
  onSelectChat,
  onNewChat,
  onDeleteChat,
  onToggle,
}) {
  const [hoveredId, setHoveredId] = useState(null);

  return (
    <>
      {/* Sidebar */}
      <aside
        className={`
          flex flex-col h-full bg-bg-sidebar
          transition-all duration-300 ease-in-out
          ${isOpen ? "w-[260px] min-w-[260px]" : "w-0 min-w-0 overflow-hidden"}
        `}
      >
        {/* Top section */}
        <div className="flex items-center justify-between p-3 pb-1">
          {/* Toggle sidebar */}
          <button
            onClick={onToggle}
            className="p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-hover transition-colors"
            title="Close sidebar"
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <line x1="9" y1="3" x2="9" y2="21" />
            </svg>
          </button>

          {/* New chat */}
          <button
            onClick={onNewChat}
            className="p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-hover transition-colors"
            title="New chat"
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M12 5v14M5 12h14" />
            </svg>
          </button>
        </div>

        {/* Chat list */}
        <div className="flex-1 overflow-y-auto px-2 py-2">
          <div className="text-[11px] font-medium text-text-muted uppercase tracking-wider px-2 py-2">
            Recent
          </div>
          <nav className="flex flex-col gap-0.5">
            {chats.map((chat) => {
              const isActive = chat.id === activeChatId;
              const isHovered = chat.id === hoveredId;

              return (
                <button
                  key={chat.id}
                  onClick={() => onSelectChat(chat.id)}
                  onMouseEnter={() => setHoveredId(chat.id)}
                  onMouseLeave={() => setHoveredId(null)}
                  className={`
                    group relative flex items-center gap-2 w-full text-left
                    px-3 py-2.5 rounded-lg text-sm transition-colors duration-150
                    ${
                      isActive
                        ? "bg-bg-active text-text-primary"
                        : "text-text-secondary hover:bg-bg-hover hover:text-text-primary"
                    }
                  `}
                >
                  {/* Chat title */}
                  <span className="truncate flex-1">{chat.title}</span>

                  {/* Delete button */}
                  {(isHovered || isActive) && (
                    <span
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteChat(chat.id);
                      }}
                      className="
                        flex-shrink-0 p-0.5 rounded text-text-muted
                        hover:text-red-400 transition-colors cursor-pointer
                      "
                      title="Delete chat"
                    >
                      <svg
                        width="14"
                        height="14"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14" />
                      </svg>
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Bottom */}
        <div className="border-t border-border p-3">
          <div className="flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-bg-hover transition-colors cursor-pointer">
            <div className="w-8 h-8 rounded-full bg-accent flex items-center justify-center text-white text-xs font-semibold">
              C
            </div>
            <span className="text-sm text-text-primary truncate">
              Clearpath AI
            </span>
          </div>
        </div>
      </aside>
    </>
  );
}
