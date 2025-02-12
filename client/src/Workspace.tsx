import { useState, useEffect } from "react";
import axios from "axios";
import { io } from "socket.io-client";

const socket = io("http://localhost:8080");

interface WorkspaceProps {
  sequence: any[];
}

function Workspace({ sequence }: WorkspaceProps) {
  const [localSequence, setLocalSequence] = useState<string[]>(sequence);

  useEffect(() => {
    const fetchSequence = async () => {
      try {
        const response = await axios.get("http://localhost:8080/api/sequence");
        setLocalSequence(response.data);
      } catch (error) {
        console.error("Error fetching sequence:", error);
      }
    };

    fetchSequence();

    // Listen for sequence updates via SocketIO
    socket.on("update_sequence", (updatedSequence: string[]) => {
      console.log("Received updated sequence from SocketIO:", updatedSequence);
      setLocalSequence(updatedSequence);
    });

    // Cleanup socket listener
    return () => {
      socket.off("update_sequence");
    };
  }, []);

  const updateSequence = async (index: number, newText: string) => {
    const updatedSequence = localSequence.map((stepText, i) =>
      i === index ? newText : stepText
    );
    setLocalSequence(updatedSequence);

    try {
      await axios.post("http://localhost:8080/api/sequence", updatedSequence);
      console.log("Sequence updated");
    } catch (error) {
      console.error("Error updating sequence:", error);
    }
  };

  return (
    <div className="workspace">
      <h2>Sequence</h2>
      <div className="sequence-container">
        {localSequence.map((stepText, index) => (
          <div key={index} className="sequence-step">
            <strong>Step {index + 1}:</strong>
            <textarea
              value={stepText}
              onChange={(e) => updateSequence(index, e.target.value)}
              className="sequence-textarea"
            />
          </div>
        ))}
      </div>
    </div>
  );
};

export default Workspace;
