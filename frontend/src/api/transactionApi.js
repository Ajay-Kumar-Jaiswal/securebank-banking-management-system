import axiosClient from "./axiosClient";

export const deposit = (payload) => axiosClient.post("/transactions/deposit", payload);

export const withdraw = (payload) => axiosClient.post("/transactions/withdraw", payload);

export const transfer = (payload) => axiosClient.post("/transactions/transfer", payload);

export const getTransactions = (accountId, filters = {}) =>
  axiosClient.get("/transactions", { params: { accountId, ...filters } });

export const getTransactionDetails = (transactionId) =>
  axiosClient.get(`/transactions/${transactionId}`);
