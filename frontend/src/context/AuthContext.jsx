import { createContext, useContext, useEffect, useState } from "react";
import { loginUser, getCurrentUser } from "../api/authApi";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem("bms_user");
    return stored ? JSON.parse(stored) : null;
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (user) {
      localStorage.setItem("bms_user", JSON.stringify(user));
    } else {
      localStorage.removeItem("bms_user");
    }
  }, [user]);

  const login = async (email, password) => {
    setLoading(true);
    setError(null);
    try {
      const response = await loginUser({ email, password });
      const data = response.data;
      localStorage.setItem("bms_token", data.token);
      const userInfo = {
        userId: data.userId,
        fullName: data.fullName,
        email: data.email,
        role: data.role,
        status: data.status,
      };
      setUser(userInfo);
      return userInfo;
    } catch (err) {
      const message =
        err.response?.data?.message || "Login failed. Please check your credentials.";
      setError(message);
      throw new Error(message);
    } finally {
      setLoading(false);
    }
  };

  const updateUser = (updatedFields) => {
    setUser((prev) => (prev ? { ...prev, ...updatedFields } : null));
  };

  const refreshProfile = async () => {
    try {
      const res = await getCurrentUser();
      const updated = {
        userId: res.data.userId,
        fullName: res.data.fullName,
        email: res.data.email,
        role: res.data.role,
        status: res.data.status,
      };
      setUser(updated);
    } catch {
      // Ignore if offline or token expired
    }
  };

  const logout = () => {
    localStorage.removeItem("bms_token");
    localStorage.removeItem("bms_user");
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        logout,
        updateUser,
        refreshProfile,
        loading,
        error,
        isAdmin: user?.role === "ADMIN",
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
