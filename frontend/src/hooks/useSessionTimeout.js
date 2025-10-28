import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

const useSessionTimeout = (timeoutMinutes = 10) => {
  const navigate = useNavigate();
  const timeoutMs = timeoutMinutes * 60 * 1000;

  useEffect(() => {
    const updateLastActivity = () => {
      localStorage.setItem("lastActivity", Date.now().toString());
    };

    // Save activity when user moves or presses keys
    window.addEventListener("mousemove", updateLastActivity);
    window.addEventListener("keydown", updateLastActivity);

    const interval = setInterval(() => {
      const lastActivity = parseInt(localStorage.getItem("lastActivity"), 10);
      const userId = localStorage.getItem("user_id");

      if (userId && lastActivity) {
        const now = Date.now();
        if (now - lastActivity > timeoutMs) {
          // Inactive for > 10 mins
          localStorage.removeItem("user_id");
          localStorage.removeItem("lastActivity");
          alert("Session expired. Please log in again.");
          navigate("/login");
        }
      }
    }, 30000); // check every 30 seconds

    // initialize timestamp when user logs in
    updateLastActivity();

    return () => {
      clearInterval(interval);
      window.removeEventListener("mousemove", updateLastActivity);
      window.removeEventListener("keydown", updateLastActivity);
    };
  }, [navigate, timeoutMs]);
};

export default useSessionTimeout;
