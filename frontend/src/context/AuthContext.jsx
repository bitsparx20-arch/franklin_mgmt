import React, { createContext, useContext, useEffect, useState } from "react";
import api from "../lib/api";

const AuthCtx = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(undefined); // undefined = loading
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("fw_token");
    const stored = localStorage.getItem("fw_user");
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    if (stored) {
      try { setUser(JSON.parse(stored)); } catch { setUser(null); }
    }
    api.get("/auth/me")
      .then((r) => {
        setUser(r.data);
        localStorage.setItem("fw_user", JSON.stringify(r.data));
      })
      .catch(() => {
        localStorage.removeItem("fw_token");
        localStorage.removeItem("fw_user");
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    localStorage.setItem("fw_token", data.token);
    localStorage.setItem("fw_user", JSON.stringify(data.user));
    setUser(data.user);
    return data.user;
  };

  const logout = async () => {
    try { await api.post("/auth/logout"); } catch {}
    localStorage.removeItem("fw_token");
    localStorage.removeItem("fw_user");
    setUser(null);
  };

  return (
    <AuthCtx.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthCtx.Provider>
  );
};

export const useAuth = () => useContext(AuthCtx);
