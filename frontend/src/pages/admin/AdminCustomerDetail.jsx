import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getCustomerDetails } from "../../api/adminApi";
import {
  extractErrorMessage,
  formatCurrency,
  formatDateTime,
} from "../../utils/errorUtils";
import AlertMessage from "../../components/AlertMessage";
import StatusBadge from "../../components/StatusBadge";

export default function AdminCustomerDetail() {
  const { id } = useParams();
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    loadDetails();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const loadDetails = async () => {
    setLoading(true);
    setError(null);
    setNotFound(false);
    try {
      const res = await getCustomerDetails(id);
      setDetails(res.data);
    } catch (err) {
      if (err?.response?.status === 404) {
        setNotFound(true);
      } else {
        setError(extractErrorMessage(err, "Unable to load customer details."));
      }
    } finally {
      setLoading(false);
    }
  };

  const customer = details?.customer || details?.user || null;
  const accounts = details?.accounts || [];
  const recentTransactions = details?.recentTransactions || [];
  const totalTransactionsCount =
    details?.totalTransactionsCount ?? recentTransactions.length;
  const accountRequests =
    details?.accountRequests || details?.closureRequests || [];

  return (
    <div className="page">
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "1rem",
        }}
      >
        <h1 className="page-title" style={{ margin: 0 }}>
          Customer Details
        </h1>
        <Link to="/admin/customers" className="btn btn-secondary btn-sm">
          &larr; Back to Customers
        </Link>
      </div>

      <AlertMessage message={error} />

      {loading && (
        <div className="card">
          <p>Loading customer profile and financial records...</p>
        </div>
      )}

      {!loading && notFound && (
        <div className="card">
          <h2>Customer Not Found</h2>
          <p style={{ color: "var(--text-muted)" }}>
            No customer exists with ID #{id}.
          </p>
          <div style={{ marginTop: "1rem" }}>
            <Link to="/admin/customers" className="btn btn-primary">
              View All Customers
            </Link>
          </div>
        </div>
      )}

      {!loading && !notFound && customer && (
        <>
          {/* Customer Information Card */}
          <div className="card" style={{ marginBottom: "1.5rem" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "1rem",
                borderBottom: "1px solid var(--border-color, #e0e0e0)",
                paddingBottom: "0.5rem",
              }}
            >
              <h2 style={{ margin: 0 }}>Customer Information</h2>
              <div>
                <span className="role-tag" style={{ marginRight: "0.5rem" }}>
                  {customer.role}
                </span>
                <StatusBadge status={customer.status} />
              </div>
            </div>

            <div className="detail-grid">
              <div>
                <div className="detail-label">Customer / User ID</div>
                <div className="detail-value">#{customer.userId}</div>
              </div>
              <div>
                <div className="detail-label">Full Name</div>
                <div className="detail-value">
                  <strong>{customer.fullName}</strong>
                </div>
              </div>
              <div>
                <div className="detail-label">Email Address</div>
                <div className="detail-value">{customer.email}</div>
              </div>
              <div>
                <div className="detail-label">Username</div>
                <div className="detail-value">{customer.username || "—"}</div>
              </div>
              <div>
                <div className="detail-label">Phone Number</div>
                <div className="detail-value">{customer.phoneNumber || "—"}</div>
              </div>
              <div>
                <div className="detail-label">Registration Date</div>
                <div className="detail-value">
                  {formatDateTime(customer.createdAt)}
                </div>
              </div>
              <div>
                <div className="detail-label">Account Status</div>
                <div className="detail-value">
                  <StatusBadge status={customer.status} />
                </div>
              </div>
              <div>
                <div className="detail-label">Active / Inactive Status</div>
                <div className="detail-value">
                  {customer.status === "ACTIVE" ? (
                    <span style={{ color: "var(--teal-700, #0f5c56)", fontWeight: 600 }}>
                      Active
                    </span>
                  ) : (
                    <span style={{ color: "var(--red-700, #b91c1c)", fontWeight: 600 }}>
                      Inactive ({customer.status})
                    </span>
                  )}
                </div>
              </div>
              <div style={{ gridColumn: "span 2" }}>
                <div className="detail-label">Address</div>
                <div className="detail-value">
                  {customer.address || "No address recorded"}
                </div>
              </div>
            </div>
          </div>

          {/* Account Information Card */}
          <div className="card" style={{ marginBottom: "1.5rem" }}>
            <h2>Account Information ({accounts.length})</h2>
            {accounts.length === 0 ? (
              <p style={{ color: "var(--text-muted)" }}>
                No bank accounts opened for this customer.
              </p>
            ) : (
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Account Number</th>
                      <th>Account Type</th>
                      <th>Status</th>
                      <th>Current Balance</th>
                      <th>Created Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {accounts.map((acc) => (
                      <tr key={acc.accountId}>
                        <td>
                          <strong>{acc.accountNumber}</strong>
                        </td>
                        <td>{acc.accountType}</td>
                        <td>
                          <StatusBadge status={acc.status} />
                        </td>
                        <td>
                          <strong>{formatCurrency(acc.balance)}</strong>
                        </td>
                        <td>{formatDateTime(acc.createdAt)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Transaction Summary Card */}
          <div className="card" style={{ marginBottom: "1.5rem" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "1rem",
              }}
            >
              <h2 style={{ margin: 0 }}>Transaction Summary</h2>
              <span
                style={{
                  fontSize: "0.9rem",
                  color: "var(--text-muted)",
                  fontWeight: 600,
                }}
              >
                Total Transactions: {totalTransactionsCount}
              </span>
            </div>

            {recentTransactions.length === 0 ? (
              <p style={{ color: "var(--text-muted)" }}>
                No transactions recorded for this customer.
              </p>
            ) : (
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Reference</th>
                      <th>Type</th>
                      <th>Amount</th>
                      <th>Balance After</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentTransactions.map((tx) => (
                      <tr key={tx.transactionId}>
                        <td>{formatDateTime(tx.createdAt)}</td>
                        <td>{tx.transactionReference}</td>
                        <td>
                          <StatusBadge status={tx.transactionType} />
                        </td>
                        <td>
                          <strong>{formatCurrency(tx.amount)}</strong>
                        </td>
                        <td>{formatCurrency(tx.balanceAfter)}</td>
                        <td>
                          <StatusBadge status={tx.status || "SUCCESS"} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Account Requests History Card */}
          <div className="card">
            <h2>Account Requests History ({accountRequests.length})</h2>
            {accountRequests.length === 0 ? (
              <p style={{ color: "var(--text-muted)" }}>
                No account closure or reopen requests recorded for this customer.
              </p>
            ) : (
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Type</th>
                      <th>Requested Date</th>
                      <th>Account Number</th>
                      <th>Reason</th>
                      <th>Status</th>
                      <th>Admin Notes</th>
                      <th>Reviewed Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {accountRequests.map((req) => (
                      <tr key={req.requestId || req.id}>
                        <td>
                          <span
                            className={`badge ${
                              req.requestType === "REOPEN"
                                ? "badge-primary"
                                : "badge-warning"
                            }`}
                            style={{
                              display: "inline-block",
                              padding: "0.2rem 0.5rem",
                              borderRadius: "4px",
                              fontSize: "0.75rem",
                              fontWeight: 600,
                              backgroundColor:
                                req.requestType === "REOPEN"
                                  ? "var(--teal-100, #ccfbf1)"
                                  : "var(--amber-100, #fef3c7)",
                              color:
                                req.requestType === "REOPEN"
                                  ? "var(--teal-800, #115e59)"
                                  : "var(--amber-800, #92400e)",
                            }}
                          >
                            {req.requestType || "CLOSURE"}
                          </span>
                        </td>
                        <td>{formatDateTime(req.requestedAt)}</td>
                        <td>{req.accountNumber}</td>
                        <td>
                          <div>{req.reason}</div>
                          {req.additionalNotes && (
                            <div
                              style={{
                                fontSize: "0.8rem",
                                color: "var(--text-muted)",
                                marginTop: "0.2rem",
                              }}
                            >
                              Note: {req.additionalNotes}
                            </div>
                          )}
                        </td>
                        <td>
                          <StatusBadge status={req.status} />
                        </td>
                        <td>{req.adminNotes || "—"}</td>
                        <td>
                          {req.reviewedAt
                            ? formatDateTime(req.reviewedAt)
                            : "Pending"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
