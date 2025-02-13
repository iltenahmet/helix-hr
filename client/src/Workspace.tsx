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

    // 1) update_sequence: we keep this so if the server fires it at any point
    // we get the entire updated sequence
    socket.on("update_sequence", (updatedSequence: string[]) => {
      console.log("Received updated sequence from SocketIO:", updatedSequence);
      setLocalSequence(updatedSequence);
    });

    // 2) partial steps as they come in
    socket.on("sequence_step", (data) => {
      // data = { stepNumber, stepText }
      // Because steps come in order, we can:
      setLocalSequence((prev) => {
        // If the stepNumber is exactly prev.length + 1, we append
        // or you could just append blindly, but let's do it carefully
        const newSequence = [...prev];
        const index = data.stepNumber - 1;
        // Ensure it fits in the array. If not, expand it
        if (newSequence.length < index) {
          // fill the gap if needed (rare case)
          while (newSequence.length < index) {
            newSequence.push("");
          }
        }
        // Insert or replace the step
        newSequence[index] = data.stepText;
        return newSequence;
      });
    });

    // 3) final creation or editing
    socket.on("sequence_done", (data) => {
      // data = { sequence }
      setLocalSequence(data.sequence);
    });

    socket.on("sequence_edited", (data) => {
      // data = { updatedSequence }
      setLocalSequence(data.updatedSequence);
    });

    return () => {
      socket.off("update_sequence");
      socket.off("sequence_step");
      socket.off("sequence_done");
      socket.off("sequence_edited");
    };
  }, []);

  // keep localSequence in sync if the parent prop "sequence" changes
  // e.g. if the user receives an entire new sequence from the Chatbox
  useEffect(() => {
    setLocalSequence(sequence);
  }, [sequence]);

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
}

export default Workspace;
