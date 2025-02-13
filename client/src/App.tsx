import { useState, useEffect } from "react";
import axios from "axios";
import Chatbox from "./Chatbox";
import Workspace from "./Workspace";
import AuthModal from "./AuthModal";
import "./App.css";

function App() {
  const [sequence, setSequence] = useState<[]>([]);
  const [isAuthModalOpen, setAuthModalOpen] = useState(false);
  const [isLogin, setIsLogin] = useState(true);
  const [user, setUser] = useState<{ username?: string; guest?: boolean } | null>(null);

  useEffect(() => {
    // Check if the user is already logged in
    axios.get("http://localhost:8080/check-session", { withCredentials: true })
      .then(response => {
        if (response.data.username) {
          setUser({ username: response.data.username });
        }
      })
      .catch(error => {
        console.error("Session check failed:", error);
      });
  }, []);

  const openAuthModal = (login: boolean) => {
    setIsLogin(login);
    setAuthModalOpen(true);
  };

  const handleLogout = () => {
    axios.post("http://localhost:8080/logout", {}, { withCredentials: true })
      .then(() => {
        setUser(null);
        setSequence([]); 
        setAuthModalOpen(false);
      })
      .catch(error => {
        console.error("Logout failed:", error);
      });
  };


  return (
    <div className="app-container">
      <div className="auth-buttons">
        {!user ? (
          <>
            <button onClick={() => openAuthModal(true)}>Login</button>
            <button onClick={() => openAuthModal(false)}>Sign Up</button>
            <button onClick={() => setUser({ guest: true })}>Continue as Guest</button>
          </>
        ) : (
          <>
            <p className="welcome-message">Welcome, {user.username || "Guest"}!</p>
            <button onClick={handleLogout}>Logout</button>
          </>
        )}
      </div>

      {isAuthModalOpen && (
        <AuthModal
          isOpen={isAuthModalOpen}
          onClose={() => setAuthModalOpen(false)}
          onAuthSuccess={setUser}
          isLogin={isLogin}
        />
      )}

      <div className="content-container">
        <div className="chatbox-container">
          <Chatbox onSequenceUpdate={setSequence} />
        </div>
        <div className="workspace-container">
          <Workspace sequence={sequence} />
        </div>
      </div>
    </div>
  );
}

export default App;