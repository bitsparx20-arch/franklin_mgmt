import axios from "axios";

// Dev: use relative /api (CRA proxy → backend). Set REACT_APP_BACKEND_URL only if not using proxy.
const envBase = (process.env.REACT_APP_BACKEND_URL || "").replace(/\/$/, "");
const BASE =
  process.env.NODE_ENV === "development" && !envBase ? "" : envBase;
export const API_BASE = BASE ? `${BASE}/api` : "/api";

const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("fw_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err?.response?.status === 401 && !window.location.pathname.includes("/login")) {
      localStorage.removeItem("fw_token");
      localStorage.removeItem("fw_user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export default api;
