// src/pages/Wishlist.js
import React, { useEffect, useState } from "react";
import axiosClient from "../api/axiosClient";
import { FaBoxOpen, FaTrashAlt } from "react-icons/fa";

const Wishlist = () => {
  const [wishlist, setWishlist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // 🧠 Fetch Wishlist on page load
  useEffect(() => {
    const fetchWishlist = async () => {
      try {
        const userId = localStorage.getItem("user_id");
        console.log("🧭 Fetching wishlist for user:", userId);

        if (!userId) {
          setError("No user logged in.");
          setLoading(false);
          return;
        }

        const response = await axiosClient.get(`/wishlist/${userId}`);
        console.log("✅ Wishlist response:", response.data);
        setWishlist(response.data);
      } catch (err) {
        console.error("❌ Error fetching wishlist:", err);
        setError("Failed to fetch wishlist. Please try again later.");

        //Hndle specific error cases 404 data not found 
        if (err.response && err.response.status === 404) {
          setWishlist([]); // Set to empty if no wishlist found
          setError("No items in wishlist. Add some products to get started!");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchWishlist();
  }, []);

  // 🗑 Delete product from wishlist
  const handleDelete = async (productId) => {
  const userId = localStorage.getItem("user_id");
  if (!userId) {
    alert("User not logged in");
    return;
  }

  if (!window.confirm("Are you sure you want to remove this product from your wishlist?")) {
    return;
  }

  try {
    console.log(`🗑 Sending delete request for user ${userId}, product ${productId}`);
    await axiosClient.delete(`/wishlist/user/${userId}/product/${productId}`);

    // ✅ Immediately update local state (this will re-render UI)
    setWishlist((prevWishlist) =>
      prevWishlist.filter((item) => item.product_id !== productId)
    );

    console.log("✅ Product deleted locally and from server");
  } catch (error) {
    console.error("❌ Error deleting product:", error);
    alert("Failed to delete product. Please try again later.");
  }
};

  // 🌀 Loading state
  if (loading)
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-500 text-lg">Loading your wishlist...</p>
      </div>
    );

  // ❌ Error state
  if (error)
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-red-500 text-lg">{error}</p>
      </div>
    );

  // 😕 Empty wishlist
  if (wishlist.length === 0)
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50">
        <h2 className="text-2xl font-bold text-gray-700 mb-3">Your Wishlist is Empty 😕</h2>
        <p className="text-gray-500">Add some products to start tracking price changes!</p>
      </div>
    );

  // 💜 Wishlist UI
  return (
    <div className="min-h-screen bg-gray-50 pt-24 pb-10 px-6">
      <div className="max-w-5xl mx-auto">
        <h2 className="text-3xl font-bold text-gray-800 mb-8 text-center">
          💜 Your Wishlist
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {wishlist.map((item, index) => (
            <div
              key={index}
              className="relative bg-white shadow-md rounded-xl p-6 hover:shadow-lg transition-shadow duration-300 text-center flex flex-col items-center"
            >
              {/* 🗑 Delete Button */}
              <button
                onClick={() => handleDelete(item.product_id)}
                className="absolute top-3 right-3 text-red-500 hover:text-red-700"
                title="Remove from Wishlist"
              >
                <FaTrashAlt size={18} />
              </button>

              {/* 📦 Product Icon */}
              <div className="bg-purple-100 text-purple-600 p-4 rounded-full mb-3">
                <FaBoxOpen size={28} />
              </div>

              {/* 🏷 Product Name */}
              <h3 className="text-lg font-semibold text-gray-800 mb-1">
                {item.product_name}
              </h3>

              {/* 💰 Product Price */}
              <p className="text-gray-700 mb-2">
                <span className="font-medium">Current Price:</span>{" "}
                <span className="text-green-600 font-semibold">
                  ${item.current_price?.toFixed(2) || "N/A"}
                </span>
              </p>

              {/* 🔗 Product Link */}
              <a
                href={item.product_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-purple-600 hover:text-purple-800 text-sm mb-4"
              >
                View Product →
              </a>

              {/* 🧠 AI Insight */}
              <div className="w-full">
                {item.ai_summary ? (
                  <div className="bg-purple-50 border-l-4 border-purple-400 p-3 rounded">
                    <p className="text-sm text-gray-700 italic">
                      “{item.ai_summary}”
                    </p>
                  </div>
                ) : (
                  <div className="bg-gray-50 border-l-4 border-gray-300 p-3 rounded">
                    <p className="text-sm text-gray-500 italic">
                      “Tracking started. Waiting for first price change…” 
                    </p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Wishlist;
