import { useState, useRef } from "react";

function ChatInput({ onSend, disabled }) {
  const [text, setText] = useState("");
  const inputRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (text.trim() && !disabled) {
      onSend(text.trim());
      setText("");
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="chat-input-wrapper">
      <form className="chat-input" onSubmit={handleSubmit}>
        <input
          ref={inputRef}
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about Clearpath..."
          disabled={disabled}
          autoFocus
        />
        <button
          type="submit"
          className="chat-input__send"
          disabled={disabled || !text.trim()}
          title="Send message"
        >
          ↑
        </button>
      </form>
      <div className="chat-input__hint">
        Powered by Groq • RAG-grounded responses from Clearpath documentation
      </div>
    </div>
  );
}

export default ChatInput;
