import { useRef, useEffect } from "react";
import ChatMessage from "./ChatMessage";

const SUGGESTIONS = [
  { text: "What is Clearpath?", icon: "💡" },
  { text: "What are the pricing plans?", icon: "💰" },
  { text: "How do I reset my password?", icon: "🔑" },
  { text: "Explain the GitHub integration", icon: "🔗" },
];

export default function ChatWindow({
  messages,
  isStreaming,
  onSuggestionClick,
}) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Empty state
  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center px-4">
        <div className="w-12 h-12 rounded-full bg-accent/10 flex items-center justify-center mb-6">
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            className="text-accent"
          >
            <path
              d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <h1 className="text-2xl font-semibold text-text-primary mb-8">
          How can I help you today?
        </h1>
        <div className="grid grid-cols-2 gap-3 max-w-lg w-full">
          {SUGGESTIONS.map((s, i) => (
            <button
              key={i}
              onClick={() => onSuggestionClick?.(s.text)}
              className="
                text-left p-4 rounded-xl border border-border
                bg-transparent hover:bg-bg-hover
                text-sm text-text-secondary
                transition-colors duration-150 cursor-pointer
              "
            >
              <span className="mr-2">{s.icon}</span>
              {s.text}
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-[768px] mx-auto px-4 py-6">
        {messages.map((msg, i) => (
          <ChatMessage
            key={msg.id}
            message={msg}
            isLast={i === messages.length - 1}
            isStreaming={
              isStreaming &&
              i === messages.length - 1 &&
              msg.role === "assistant"
            }
          />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
