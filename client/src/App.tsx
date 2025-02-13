import { useState } from "react";
import Chatbox from "./Chatbox";
import Workspace from "./Workspace";
import AuthModal from "./AuthModal";
import "./App.css";

function App() {
  const [sequence, setSequence] = useState<[]>([]);
  const [isAuthModalOpen, setAuthModalOpen] = useState(false);
  const [isLogin, setIsLogin] = useState(true);
  const [user, setUser] = useState<{ username?: string; guest?: boolean } | null>(null);

  const openAuthModal = (login: boolean) => {
    setIsLogin(login);
    setAuthModalOpen(true);
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
          <p className="welcome-message">Welcome, {user.username || "Guest"}!</p>
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
