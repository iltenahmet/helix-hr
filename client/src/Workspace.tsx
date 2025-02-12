import { useState, useEffect } from "react";
import axios from "axios";

interface SequenceStep {
  id: number;
  text: string;
}

const Workspace = ({ sequence }: { sequence: any[] }) => {
	const [localSequence, setLocalSequence] = useState<SequenceStep[]>([]);

	useEffect(() => {
		setLocalSequence(sequence);
	}, [sequence]);


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
  }, []);

  const updateSequence = async (id: number, newText: string) => {
    const updatedSequence = localSequence.map((step) =>
      step.id === id ? { ...step, text: newText } : step
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
        {localSequence.map((step, index) => (
          <div key={step.id} className="sequence-step">
            <strong>Step {index + 1}:</strong>
            <textarea
              value={step.text}
              onChange={(e) => updateSequence(step.id, e.target.value)}
              className="sequence-textarea"
            />
          </div>
        ))}
      </div>
    </div>
  );
};

export default Workspace;
