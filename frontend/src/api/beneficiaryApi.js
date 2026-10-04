import axiosClient from "./axiosClient";

export const getBeneficiaries = () => axiosClient.get("/beneficiaries");

export const addBeneficiary = (payload) => axiosClient.post("/beneficiaries", payload);

export const updateBeneficiary = (id, payload) => axiosClient.put(`/beneficiaries/${id}`, payload);

export const deleteBeneficiary = (id) => axiosClient.delete(`/beneficiaries/${id}`);
