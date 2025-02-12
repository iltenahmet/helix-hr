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

  useEffect(() => {
    socket.on("update_sequence", (sequence) => {
      onSequenceUpdate(sequence); // Pass sequence to parent component
    });
    return () => {
      socket.off("update_sequence");
    };
  }, []);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = { sender: "user", text: input };
    setMessages([...messages, userMessage]); // Update local state

    try {
      const response = await axios.post("http://localhost:8080/api/chat", { message: input });

      const aiMessage: Message = { sender: "ai", text: response.data.message };
      setMessages([...messages, userMessage, aiMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
    }

    setInput(""); // Clear input
  };

  return (
    <div className="chatbox">
      <div className="messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            {msg.text}
          </div>
        ))}
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
