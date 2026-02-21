export default function Header({
  model,
  sidebarOpen,
  debugOpen,
  onToggleSidebar,
  onToggleDebug,
}) {
  return (
    <header className="sticky top-0 z-10 flex items-center justify-between h-12 px-4 bg-bg-main">
      <div className="flex items-center">
        {/* Toggle sidebar */}
        {!sidebarOpen && (
          <button
            onClick={onToggleSidebar}
            className="p-2 mr-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-hover transition-colors"
            title="Open sidebar"
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
        )}

        {/* Model indicator */}
        <div className="flex items-center gap-2 cursor-default select-none">
          <span className="text-sm font-medium text-text-primary">
            {model || "Clearpath AI"}
          </span>
          <svg
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className="text-text-muted"
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </div>
      </div>

      {/* Debug toggle */}
      <button
        onClick={onToggleDebug}
        className={`
          p-2 rounded-lg transition-colors text-sm flex items-center gap-1.5
          ${
            debugOpen
              ? "bg-bg-active text-text-primary"
              : "text-text-secondary hover:text-text-primary hover:bg-bg-hover"
          }
        `}
        title="Toggle debug panel"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M12 15a3 3 0 100-6 3 3 0 000 6z" />
          <path d="M8 9l-5-5M8 15l-5 5M16 9l5-5M16 15l5 5M12 3v3M12 18v3M3 12h3M18 12h3" />
        </svg>
        <span className="text-xs hidden sm:inline">Debug</span>
      </button>
    </header>
  );
}
