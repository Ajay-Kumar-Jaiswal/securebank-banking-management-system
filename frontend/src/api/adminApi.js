import axiosClient from "./axiosClient";

export const getDashboardMetrics = () => axiosClient.get("/admin/dashboard");

export const getAllCustomers = (params = {}) => {
  const query = typeof params === "string" ? { search: params } : params;
  return axiosClient.get("/admin/customers", { params: query });
};

export const getCustomerDetails = (customerId) =>
  axiosClient.get(`/admin/customers/${customerId}`);

export const updateCustomerStatus = (customerId, status) =>
  axiosClient.put(`/admin/customers/${customerId}/status`, { status });

export const getAllAccounts = (params = {}) => {
  const query = typeof params === "string" ? { search: params } : params;
  return axiosClient.get("/admin/accounts", { params: query });
};

export const updateAccountStatus = (accountId, status) =>
  axiosClient.put(`/admin/accounts/${accountId}/status`, { status });

export const getAllTransactions = (type = "") =>
  axiosClient.get("/admin/transactions", { params: type ? { type } : {} });

export const getAccountRequests = (params = {}) => {
  const query = typeof params === "string" ? { status: params } : params;
  return axiosClient.get("/admin/account-requests", { params: query });
};

export const approveAccountRequest = (requestId, adminNotes = "") =>
  axiosClient.post(`/admin/account-requests/${requestId}/approve`, { adminNotes });

export const rejectAccountRequest = (requestId, adminNotes = "") =>
  axiosClient.post(`/admin/account-requests/${requestId}/reject`, { adminNotes });

export const getClosureRequests = (status = "") =>
  getAccountRequests(status ? { status } : {});

export const approveClosureRequest = (requestId, adminNotes = "") =>
  approveAccountRequest(requestId, adminNotes);

export const rejectClosureRequest = (requestId, adminNotes = "") =>
  rejectAccountRequest(requestId, adminNotes);

export const getAuditLogs = (params = {}) =>
  axiosClient.get("/admin/audit-logs", { params });

export const getAllAdministrators = () =>
  axiosClient.get("/admin/administrators");

export const updateAdministratorStatus = (adminId, status) =>
  axiosClient.put(`/admin/administrators/${adminId}/status`, { status });

