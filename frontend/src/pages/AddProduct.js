import { useState } from "react";
import axiosClient from "../api/axiosClient";
import useSessionTimeout from "../hooks/useSessionTimeout";

const AddProduct = () => {
  useSessionTimeout(10);

  const [product, setProduct] = useState({
    name: "",
    link: "",
    site: "amazon",
  });

  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setProduct({ ...product, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");

    const userId = localStorage.getItem("user_id");

    try {
      const response = await axiosClient.post("/products/ingest", {
        user_id: Number(userId),
        url: product.link,
        site: product.site,
      });

      console.log("✅ Product added:", response.data);
      setMessage(`✅ ${response.data.name} added successfully!`);
    } catch (error) {
      console.error("❌ Error adding product:", error);
      setMessage(
        `❌ ${
          error.response?.data?.detail ||
          "Failed to add product. Please check the link and try again."
        }`
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-gray-100 to-zinc-100 px-4">
      <div className="relative bg-white/80 backdrop-blur-xl border border-white/40 shadow-xl rounded-2xl w-full max-w-md p-8 transition-all hover:shadow-2xl hover:-translate-y-1 duration-300">
        {/* Decorative Glow */}
        <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-fuchsia-500/5 via-purple-400/10 to-blue-400/10 blur-2xl -z-10"></div>

        {/* Header */}
        <h2 className="text-3xl font-extrabold text-center text-transparent bg-clip-text bg-gradient-to-r from-rose-500 via-fuchsia-600 to-violet-600 mb-6">
          Add Product
        </h2>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex flex-col space-y-5">
          <div>
            <label
              htmlFor="name"
              className="block text-gray-700 font-semibold mb-1"
            >
              Product Name
            </label>
            <input
              id="name"
              name="name"
              type="text"
              value={product.name}
              onChange={handleChange}
              placeholder="Enter product name"
              className="w-full px-4 py-2 border border-gray-200 rounded-lg shadow-sm bg-white/70 focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-fuchsia-400 transition-all"
              required
            />
          </div>

          <div>
            <label
              htmlFor="link"
              className="block text-gray-700 font-semibold mb-1"
            >
              Product Link
            </label>
            <input
              id="link"
              name="link"
              type="url"
              value={product.link}
              onChange={handleChange}
              placeholder="Enter product link"
              className="w-full px-4 py-2 border border-gray-200 rounded-lg shadow-sm bg-white/70 focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-fuchsia-400 transition-all"
              required
            />
          </div>

          {/* Dropdown */}
          <div>
            <label
              htmlFor="site"
              className="block text-gray-700 font-semibold mb-1"
            >
              Site
            </label>
            <select
              id="site"
              name="site"
              value={product.site}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-200 rounded-lg shadow-sm bg-white/70 focus:outline-none focus:ring-2 focus:ring-fuchsia-500 focus:border-fuchsia-400 transition-all"
            >
              <option value="amazon">Amazon</option>
              <option value="generic">Generic</option>
              <option value="auto">Auto Detect</option>
            </select>
          </div>

          {/* Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-fuchsia-600 via-purple-600 to-indigo-600 text-white py-2 rounded-lg font-semibold shadow-md hover:shadow-lg hover:opacity-90 transition-all disabled:opacity-60"
          >
            {loading ? "Adding..." : "Add Product"}
          </button>
        </form>

        {/* Message */}
        {message && (
          <p
            className={`mt-5 text-center font-medium ${
              message.startsWith("✅")
                ? "text-emerald-600"
                : "text-rose-600"
            }`}
          >
            {message}
          </p>
        )}
      </div>
    </div>
  );
};

export default AddProduct;
