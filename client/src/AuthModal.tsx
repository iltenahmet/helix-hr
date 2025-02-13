import { useState } from "react";
import axios from "axios";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAuthSuccess: (user: { username?: string; guest?: boolean }) => void;
  isLogin: boolean; 
}

const AuthModal = ({ isOpen, onClose, onAuthSuccess, isLogin }: AuthModalProps) => {
  const [formData, setFormData] = useState<{ username: string; password: string; company?: string; phone_number?: string }>({ username: "", password: "" });
  const [error, setError] = useState("");

  if (!isOpen) return null;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async () => {
    try {
      const url = isLogin ? "http://localhost:8080/login" : "http://localhost:8080/signup";
      const response = await axios.post(url, formData);
      console.log("auth success Response:", response.data.username);
      onAuthSuccess(response.data);
      onClose();
    } catch (err) {
      console.error("Authentication error:", err);
      setError("Authentication failed. Please try again.");
    }
  };

  return (
    <div className="modal">
      <div className="modal-content">
        <h2>{isLogin ? "Login" : "Sign Up"}</h2>
        {error && <p className="error">{error}</p>}
        <input type="text" name="username" placeholder="Username" onChange={handleChange} />
        <input type="password" name="password" placeholder="Password" onChange={handleChange} />
        {!isLogin && (
          <>
            <input type="text" name="company" placeholder="Company" onChange={handleChange} />
            <input type="text" name="phone_number" placeholder="Phone Number" onChange={handleChange} />
          </>
        )}
        <button onClick={handleSubmit}>{isLogin ? "Login" : "Sign Up"}</button>
        <button onClick={onClose}>Close</button>
      </div>
    </div>
  );
};

export default AuthModal;
