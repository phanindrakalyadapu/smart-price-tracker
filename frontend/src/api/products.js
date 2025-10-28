// src/api/products.js
import axios from "./axiosClient";

export const ingestProduct = async ({ userId, url }) => {
  const { data } = await axios.post("/products/ingest", {
    user_id: userId,
    url,
  });
  return data; // ProductResponse
};
