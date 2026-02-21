import { useState, useRef, useEffect, useCallback } from "react";

export default function ChatInput({ onSend, disabled }) {
  const [text, setText] = useState("");
  const textareaRef = useRef(null);

  // Auto resize textarea
  const resize = useCallback(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 200) + "px";
  }, []);

  useEffect(() => {
    resize();
  }, [text, resize]);

  const handleSubmit = () => {
    if (!text.trim() || disabled) return;
    onSend(text.trim());
    setText("");
    // Reset height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const canSend = text.trim().length > 0 && !disabled;

  return (
    <div className="sticky bottom-0 w-full bg-bg-main pb-4 pt-2 px-4">
      <div className="max-w-[768px] mx-auto">
        <div
          className="
            flex items-end gap-2
            bg-bg-input border border-border/50
            rounded-2xl px-4 py-3
            focus-within:border-text-muted/30
            transition-colors duration-150
          "
        >
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message Clearpath AI..."
            disabled={disabled}
            rows={1}
            className="
              flex-1 bg-transparent border-none outline-none resize-none
              text-text-primary text-sm leading-6
              placeholder:text-text-muted
              max-h-[200px]
            "
          />
          <button
            onClick={handleSubmit}
            disabled={!canSend}
            className={`
              flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center
              transition-all duration-150
              ${
                canSend
                  ? "bg-white text-bg-main hover:bg-gray-200 cursor-pointer"
                  : "bg-text-muted/20 text-text-muted cursor-not-allowed"
              }
            `}
            title="Send message"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z" />
            </svg>
          </button>
        </div>
        <p className="text-center text-[11px] text-text-muted mt-2">
          Clearpath AI can make mistakes. Responses are grounded in Clearpath
          documentation.
        </p>
      </div>
    </div>
  );
}
