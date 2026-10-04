import axiosClient from "./axiosClient";

export const getMyAccounts = () => axiosClient.get("/accounts");

export const getAccountDetails = (accountId) => axiosClient.get(`/accounts/${accountId}`);

export const createAccount = (accountType) =>
  axiosClient.post("/accounts", { accountType });
