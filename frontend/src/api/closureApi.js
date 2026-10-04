import axiosClient from "./axiosClient";

export const createClosureRequest = (payload) =>
  axiosClient.post("/account-requests/closure", payload);

export const createReopenRequest = (payload) =>
  axiosClient.post("/account-requests/reopen", payload);

export const getMyAccountRequests = () =>
  axiosClient.get("/account-requests/my");

export const getMyClosureRequests = getMyAccountRequests;

