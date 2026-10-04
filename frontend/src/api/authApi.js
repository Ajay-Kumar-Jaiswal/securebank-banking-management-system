import axiosClient from "./axiosClient";

export const registerUser = (payload) => axiosClient.post("/auth/register", payload);

export const loginUser = (payload) => axiosClient.post("/auth/login", payload);

export const getCurrentUser = () => axiosClient.get("/auth/me");

export const updateProfile = (payload) => axiosClient.put("/users/profile", payload);

export const changePassword = (payload) => axiosClient.post("/users/change-password", payload);
