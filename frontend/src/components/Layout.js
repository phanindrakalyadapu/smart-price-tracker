// src/components/Layout.js
import React from "react";
import Navbar from "./Navbar";

const Layout = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-100">
      <Navbar />
      <main className="pt-16 px-6">{children}</main>
    </div>
  );
};

export default Layout;
