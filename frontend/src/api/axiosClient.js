import axios from "axios";

/**
 * Central Axios instance for talking to the Spring Boot backend.
 *
 * - baseURL points at the backend REST API (see .env / vite config).
 * - The request interceptor attaches the JWT (if present) as
 *   "Authorization: Bearer <token>" on every outgoing request.
 * - The response interceptor watches for 401 Unauthorized responses
 *   (expired/invalid token) and forces a logout + redirect to /login.
 */
const axiosClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api",
  headers: {
    "Content-Type": "application/json",
  },
});

axiosClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("bms_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

axiosClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("bms_token");
      localStorage.removeItem("bms_user");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default axiosClient;
