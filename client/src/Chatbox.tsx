import { useState, useEffect } from "react";
import axios from "axios";
import { io } from "socket.io-client";

const socket = io("http://localhost:8080");

interface Message {
  sender: "user" | "ai";
  text: string;
}

const Chatbox = ({ onSequenceUpdate }: { onSequenceUpdate: (seq: any) => void }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  // Track status: idle, generating, or editing
  const [status, setStatus] = useState<"idle" | "generating" | "editing">("idle");

  useEffect(() => {
    // This existing event updates the parent with the final sequence
    socket.on("update_sequence", (sequence) => {
      onSequenceUpdate(sequence);
    });

    // Show "generating" or "editing" in the chatbox
    socket.on("sequence_status", (data) => {
      if (data.status === "generating") {
        setStatus("generating");
      } else if (data.status === "editing") {
        setStatus("editing");
      }
    });

    // Once done generating, go back to idle
    socket.on("sequence_done", (data) => {
      onSequenceUpdate(data.sequence);
      setStatus("idle");
    });

    // Once done editing, go back to idle
    socket.on("sequence_edited", (data) => {
      onSequenceUpdate(data.updatedSequence);
      setStatus("idle");
    });

    // IMPORTANT: we do NOT listen for "sequence_step" here,
    // so the Chatbox never sees partial steps.

    return () => {
      socket.off("update_sequence");
      socket.off("sequence_status");
      socket.off("sequence_done");
      socket.off("sequence_edited");
    };
  }, [onSequenceUpdate]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = { sender: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await axios.post("http://localhost:8080/api/chat", {
        message: input,
      });
      const aiMessage: Message = { sender: "ai", text: response.data.message };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
    }

    setInput("");
  };

  return (
    <div className="chatbox">
      <div className="messages">
        {/* Existing user/AI messages */}
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            {msg.text}
          </div>
        ))}

        {/* If generating or editing, show a single status line */}
        {status === "generating" && (
          <div className="message system">Generating sequence...</div>
        )}
        {status === "editing" && (
          <div className="message system">Editing sequence...</div>
        )}
      </div>

        <input
          type="text"
          placeholder="Type a message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />
        <button onClick={sendMessage}>Send</button>
      </div>
  );
};

export default Chatbox;
