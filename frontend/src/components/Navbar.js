import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import logo from "../assets/logo.png"; // 👈 your logo

const Navbar = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    localStorage.removeItem("user_id");
    localStorage.removeItem("token");
    localStorage.removeItem("lastActivity");
    navigate("/login");
  };

  const navLinks = [
    { name: "Dashboard", path: "/dashboard" },
    { name: "Add Product", path: "/add-product" },
    { name: "Wishlist", path: "/wishlist" },
  ];

  return (
    <nav className="fixed top-0 w-full bg-gradient-to-r from-indigo-700 via-purple-700 to-indigo-800 text-white shadow-lg z-50">
      <div className="max-w-7xl mx-auto flex justify-between items-center px-6 h-16">
        {/* Left: Logo + Title */}
        <div
          className="flex items-center space-x-2 cursor-pointer"
          onClick={() => navigate("/dashboard")}
        >
          <img
            src={logo}
            alt="Logo"
            className="h-9 w-9 rounded-full object-cover border border-white/30"
          />
          <h1 className="text-xl font-semibold tracking-wide">
            <span className="text-white">Price</span>
            <span className="text-yellow-300 ml-1">Pilot AI</span>
          </h1>
        </div>

        {/* Center: Navigation Links */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <button
              key={link.name}
              onClick={() => navigate(link.path)}
              className={`text-sm font-medium transition-all ${
                location.pathname === link.path
                  ? "text-yellow-300 border-b-2 border-yellow-300 pb-1"
                  : "text-gray-100 hover:text-yellow-200"
              }`}
            >
              {link.name}
            </button>
          ))}
        </div>

        {/* Right: Logout Button */}
        <button
          onClick={handleLogout}
          className="px-4 py-1.5 bg-white/20 backdrop-blur-md rounded-lg text-sm font-semibold hover:bg-white/30 transition-all"
        >
          Logout
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
