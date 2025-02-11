import Chatbox from "./Chatbox";
import Workspace from "./Workspace";
import "./App.css";

function App() {
  return (
    <div className="app-container">
      <div className="chatbox-container">
        <Chatbox />
      </div>
      <div className="workspace-container">
        <Workspace />
      </div>
    </div>
  );
}

export default App;
