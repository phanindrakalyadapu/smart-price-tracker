import axios from "axios";

const axiosClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL, // ✅ your backend base URL
  headers: {
    "Content-Type": "application/json",
  },
});

export default axiosClient;
