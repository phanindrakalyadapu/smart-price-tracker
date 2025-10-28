import { useState } from "react";
import { FaUserCircle } from "react-icons/fa";
import { AiOutlineEye, AiOutlineEyeInvisible } from "react-icons/ai";
import axiosClient from "../api/axiosClient";
import { Link, useNavigate } from "react-router-dom";
import logo from "../assets/logo.png";

const Login = () => {
  const [form, setForm] = useState({ email: "", password: "" });
  const [message, setMessage] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage("");

    try {
      const res = await axiosClient.post("/users/login", form);

      if (res.data.access_token) {
        localStorage.setItem("token", res.data.access_token);
      }

      if (res.data.user_id) {
        localStorage.setItem("user_id", res.data.user_id);
        localStorage.setItem("lastActivity", Date.now().toString());
      }

      setMessage(res.data.message || "Login successful!");
      navigate("/dashboard");
    } catch (err) {
      setMessage(err.response?.data?.detail || "Invalid email or password");
    }
  };

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-gray-50">
      {/* LEFT SIDE */}
      <div className="w-full md:w-1/2 flex flex-col justify-center items-center p-10 bg-white relative overflow-hidden">
        {/* Decorative gradient ring behind logo */}
        <div className="absolute top-32 left-20 w-64 h-64 bg-purple-200 rounded-full blur-3xl opacity-40 animate-pulse hidden md:block"></div>

        {/* Logo + Welcome Text */}
        <div className="relative z-10 flex flex-col items-center text-center">
          <div className="h-28 w-28 rounded-full bg-gradient-to-tr from-purple-500 to-indigo-500 p-1 shadow-lg mb-6">
            <div className="bg-white rounded-full flex items-center justify-center h-full w-full">
              <img
                src={logo}
                alt="PricePilot AI Logo"
                className="h-24 w-24 rounded-full object-cover"
              />
            </div>
          </div>

          <h1 className="text-4xl font-extrabold text-gray-800 mb-3">
            Welcome to{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-500 to-purple-600">
              PricePilot AI
            </span>
          </h1>

          <p className="text-lg text-gray-600 max-w-md leading-relaxed">
            Track prices intelligently. Get AI-powered deal insights and smart
            alerts — shop smarter, not harder.
          </p>
        </div>
      </div>

      {/* RIGHT SIDE */}
      <div className="w-full md:w-1/2 flex flex-col justify-center items-center p-10 bg-white relative overflow-hidden">
        <div className="bg-white shadow-2xl rounded-2xl p-10 w-full max-w-sm transform transition hover:scale-[1.01] duration-300">
          <div className="flex flex-col items-center mb-6">
            <FaUserCircle className="text-indigo-600 text-6xl mb-3 drop-shadow-sm" />
            <h2 className="text-2xl font-bold text-gray-800 mb-1">
              Welcome
            </h2>
            <p className="text-gray-500 text-sm">
              Don’t have an account?{" "}
              <Link
                to="/register"
                className="text-indigo-600 font-semibold hover:underline"
              >
                Create Account
              </Link>
            </p>
          </div>

          {/* Message Alert */}
          {message && (
            <p
              className={`text-center text-sm mb-4 ${
                message.includes("success")
                  ? "text-green-600"
                  : "text-red-500 font-medium"
              }`}
            >
              {message}
            </p>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="flex flex-col space-y-4">
            <div>
              <input
                type="email"
                name="email"
                placeholder="Email address"
                value={form.email}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-400 transition-all"
              />
            </div>

            {/* Password Field with Toggle */}
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  name="password"
                  placeholder="Password"
                  value={form.password}
                  onChange={handleChange}
                  required
                  className="w-full px-4 py-2 pr-10 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-400 transition-all"
                />
                <span
                  className="absolute right-3 top-2.5 text-gray-500 cursor-pointer hover:text-indigo-600 transition"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <AiOutlineEyeInvisible size={22} />
                  ) : (
                    <AiOutlineEye size={22} />
                  )}
                </span>
              </div>

            <button
              type="submit"
              className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 text-white py-2 rounded-lg font-semibold shadow-md hover:opacity-90 transition-all"
            >
              Sign In
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
