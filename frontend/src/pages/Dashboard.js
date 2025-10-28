// src/pages/Dashboard.js
import React, { useEffect, useState } from "react";
import axiosClient from "../api/axiosClient";
import { FaBox, FaHeart, FaChartLine, FaRobot } from "react-icons/fa";

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalProducts: 0,
    wishlistItems: 0,
    priceDrops: 0,
  });
  const [recentAIInsights, setRecentAIInsights] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const userId = localStorage.getItem("user_id");
    if (!userId) return;

    const fetchDashboardData = async () => {
      try {
        const res = await axiosClient.get(`/wishlist/${userId}`);
        const wishlist = res.data || [];

        const total = wishlist.length;
        const drops = wishlist.filter(
          (item) =>
            item.ai_summary &&
            item.ai_summary.toLowerCase().includes("drop")
        ).length;

        const insights = wishlist
          .filter((w) => w.ai_summary)
          .slice(-3)
          .reverse();

        setStats({
          totalProducts: total,
          wishlistItems: total,
          priceDrops: drops,
        });
        setRecentAIInsights(insights);
      } catch (error) {
        console.error("❌ Error loading dashboard:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading)
    return (
      <div className="flex justify-center items-center min-h-screen text-gray-500 text-lg">
        Loading your dashboard...
      </div>
    );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-gray-100 to-zinc-100 pt-24 px-6 pb-16">
      {/* Header */}
      <div className="mb-10 text-center">
        <h1 className="text-4xl font-extrabold bg-gradient-to-r from-rose-500 via-fuchsia-600 to-violet-600 bg-clip-text text-transparent drop-shadow-sm">
          Welcome to PricePilot AI
        </h1>
        <p className="text-gray-600 mt-2 text-base">
          Monitor your products, track price changes, and get AI buying insights.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8 mb-14 max-w-6xl mx-auto">
        {[
          {
            title: "Total Products",
            value: stats.totalProducts,
            icon: <FaBox className="text-fuchsia-500 text-3xl" />,
            gradient: "from-fuchsia-500/10 to-fuchsia-200/30",
          },
          {
            title: "Wishlist Items",
            value: stats.wishlistItems,
            icon: <FaHeart className="text-rose-500 text-3xl" />,
            gradient: "from-rose-500/10 to-rose-200/30",
          },
          {
            title: "Price Drops Detected",
            value: stats.priceDrops,
            icon: <FaChartLine className="text-emerald-500 text-3xl" />,
            gradient: "from-emerald-500/10 to-emerald-200/30",
          },
        ].map((stat, i) => (
          <div
            key={i}
            className={`bg-gradient-to-br ${stat.gradient} rounded-2xl shadow-md hover:shadow-xl transform hover:-translate-y-1 transition-all duration-300 p-6 flex items-center gap-5 border border-white/40 backdrop-blur-md`}
          >
            <div className="p-4 bg-white/60 rounded-full shadow-sm">
              {stat.icon}
            </div>
            <div>
              <h3 className="text-sm text-gray-600 font-medium">
                {stat.title}
              </h3>
              <p className="text-3xl font-semibold text-gray-800 mt-1">
                {stat.value}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Recent AI Insights */}
      <div className="max-w-5xl mx-auto bg-white/80 backdrop-blur-lg rounded-2xl shadow-md p-8 border border-white/50">
        <h2 className="text-2xl font-semibold flex items-center gap-2 mb-4 text-gray-800">
          <FaRobot className="text-fuchsia-600 text-2xl" />
          Recent AI Insights
        </h2>

        {recentAIInsights.length === 0 ? (
          <div className="text-gray-500 italic py-6 text-center">
            No AI insights available yet. Once prices change, you'll see intelligent recommendations here.
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {recentAIInsights.map((item, idx) => (
              <div
                key={idx}
                className="py-4 hover:bg-gray-50/70 rounded-lg px-2 transition-all duration-200"
              >
                <p className="text-gray-900 font-medium">{item.product_name}</p>
                <p className="text-gray-600 text-sm italic mt-1">
                  “{item.ai_summary}”
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
