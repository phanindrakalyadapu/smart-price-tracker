import { useNavigate } from "react-router-dom";

const LogoutButton = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    // ✅ Clear localStorage and session
    localStorage.removeItem("user_id");
    localStorage.removeItem("token");
    localStorage.removeItem("lastActivity");

    // Redirect to login
    navigate("/login");
  };

  return (
    <button
      onClick={handleLogout}
      className="bg-red-500 text-white px-4 py-2 rounded-lg font-semibold hover:bg-red-600 transition"
    >
      Logout
    </button>
  );
};

export default LogoutButton;
