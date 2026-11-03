
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000",
  headers: {
    "Content-Type": "application/json",
  },
});

// Attach JWT token automatically to protected API requests.
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("compvista_token");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

export default api;
