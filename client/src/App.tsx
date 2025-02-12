import { useState } from "react";
import Chatbox from "./Chatbox";
import Workspace from "./Workspace";
import "./App.css";


function App() {

  const [sequence, setSequence] = useState<any[]>([]);

  return (
    <div className="app-container">
      <div className="chatbox-container">
        <Chatbox onSequenceUpdate={setSequence} />
      </div>
      <div className="workspace-container">
        <Workspace sequence={sequence} />
      </div>
    </div>
  );
}

export default App;
