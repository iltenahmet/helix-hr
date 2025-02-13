import { useState, useEffect } from "react";
import axios from "axios";
import { io } from "socket.io-client";

const socket = io("http://localhost:8080");

interface Message {
  sender: "user" | "ai";
  text: string;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const Chatbox = ({ onSequenceUpdate }: { onSequenceUpdate: (seq: any) => void }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<"idle" | "generating" | "editing">("idle");

  useEffect(() => {
    socket.on("update_sequence", (sequence) => {
      onSequenceUpdate(sequence);
    });

    socket.on("sequence_status", (data) => {
      if (data.status === "generating") {
        setStatus("generating");
      } else if (data.status === "editing") {
        setStatus("editing");
      }
    });

    socket.on("sequence_done", (data) => {
      onSequenceUpdate(data.sequence);
      setStatus("idle");
    });

    socket.on("sequence_edited", (data) => {
      onSequenceUpdate(data.updatedSequence);
      setStatus("idle");
    });

    socket.on("logout", () => {
      setMessages([]);
      onSequenceUpdate([]);
    });

  return () => {
    socket.off("update_sequence");
    socket.off("sequence_status");
    socket.off("sequence_done");
    socket.off("sequence_edited");
    socket.off("logout");
  };
}, [onSequenceUpdate]);

const sendMessage = async () => {
  if (!input.trim()) return;

  const userMessage: Message = { sender: "user", text: input };
  setMessages((prev) => [...prev, userMessage]);

  try {
    const response = await axios.post(
      "http://localhost:8080/api/chat",
      { message: input },
      { withCredentials: true }
    );
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
      {messages.map((msg, index) => (
        <div key={index} className={`message ${msg.sender}`}>
          {msg.text}
        </div>
      ))}

      {status === "generating" && (
        <div className="message system">Generating sequence...</div>
      )}
      {status === "editing" && (
        <div className="message system">Editing sequence...</div>
      )}
    </div>

    <div className="input-container">
      <input
        type="text"
        placeholder="Type a message..."
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && sendMessage()}
      />
      <button onClick={sendMessage}>Send</button>
    </div>
  </div>
);
};

export default Chatbox;
