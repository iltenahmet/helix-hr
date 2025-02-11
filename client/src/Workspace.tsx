import { useState, useEffect } from "react";
import axios from "axios";

const Workspace = () => {
  const [sequence, setSequence] = useState("");

  useEffect(() => {
    const fetchSequence = async () => {
      try {
        const response = await axios.get("http://localhost:5000/api/sequence");
        setSequence(response.data.sequence);
      } catch (error) {
        console.error("Error fetching sequence:", error);
      }
    };

    fetchSequence();
  }, []);

  const updateSequence = async () => {
    try {
      await axios.post("http://localhost:5000/api/sequence", { sequence });
      console.log("Sequence updated");
    } catch (error) {
      console.error("Error updating sequence:", error);
    }
  };

  return (
    <div className="workspace">
      <textarea
        value={sequence}
        onChange={(e) => setSequence(e.target.value)}
        onBlur={updateSequence} // Save on blur
      />
    </div>
  );
};

export default Workspace;
