import { useEffect, useState } from "react";
import { getAuditLogs } from "../../api/adminApi";
import { extractErrorMessage, formatDateTime } from "../../utils/errorUtils";
import AlertMessage from "../../components/AlertMessage";

export default function AdminAuditLogs() {
  const [logs, setLogs] = useState([]);
  const [actionFilter, setActionFilter] = useState("");
  const [entityFilter, setEntityFilter] = useState("");
  const [limit, setLimit] = useState(50);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [actionFilter, entityFilter, limit]);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = { limit };
      if (actionFilter) params.action = actionFilter;
      if (entityFilter) params.entity_type = entityFilter;
      const res = await getAuditLogs(params);
      setLogs(res.data);
    } catch (err) {
      setError(extractErrorMessage(err, "Could not load audit log records."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
        <h1 className="page-title" style={{ margin: 0 }}>System Audit Logs</h1>
        <button className="btn btn-sm btn-secondary" onClick={load}>
          Refresh Logs
        </button>
      </div>

      <div className="card">
        <AlertMessage message={error} />

        <div className="filter-form">
          <label>
            Filter by Action
            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
            >
              <option value="">All Actions</option>
              <option value="LOGIN">LOGIN</option>
              <option value="REGISTER">REGISTER</option>
              <option value="PROFILE_UPDATE">PROFILE_UPDATE</option>
              <option value="PASSWORD_CHANGE">PASSWORD_CHANGE</option>
              <option value="ACCOUNT_OPEN">ACCOUNT_OPEN</option>
              <option value="DEPOSIT">DEPOSIT</option>
              <option value="WITHDRAWAL">WITHDRAWAL</option>
              <option value="TRANSFER">TRANSFER</option>
              <option value="BENEFICIARY_ADD">BENEFICIARY_ADD</option>
              <option value="BENEFICIARY_DELETE">BENEFICIARY_DELETE</option>
              <option value="CLOSURE_REQUEST_SUBMIT">CLOSURE_REQUEST_SUBMIT</option>
              <option value="CLOSURE_REQUEST_APPROVE">CLOSURE_REQUEST_APPROVE</option>
              <option value="CLOSURE_REQUEST_REJECT">CLOSURE_REQUEST_REJECT</option>
              <option value="CUSTOMER_STATUS_UPDATE">CUSTOMER_STATUS_UPDATE</option>
              <option value="ACCOUNT_STATUS_UPDATE">ACCOUNT_STATUS_UPDATE</option>
            </select>
          </label>

          <label>
            Entity Type
            <select
              value={entityFilter}
              onChange={(e) => setEntityFilter(e.target.value)}
            >
              <option value="">All Entities</option>
              <option value="USER">USER</option>
              <option value="ACCOUNT">ACCOUNT</option>
              <option value="TRANSACTION">TRANSACTION</option>
              <option value="BENEFICIARY">BENEFICIARY</option>
              <option value="ACCOUNT_REQUEST">ACCOUNT_REQUEST</option>
            </select>
          </label>

          <label>
            Show Records
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
            >
              <option value={25}>Latest 25</option>
              <option value={50}>Latest 50</option>
              <option value={100}>Latest 100</option>
            </select>
          </label>
        </div>
      </div>

      <div className="card">
        {loading ? (
          <p>Loading audit trail...</p>
        ) : logs.length === 0 ? (
          <p>No audit log events recorded matching the selection.</p>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Log ID</th>
                  <th>Timestamp</th>
                  <th>Actor ID</th>
                  <th>Action</th>
                  <th>Entity Type</th>
                  <th>Entity ID</th>
                  <th>IP Address</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.logId}>
                    <td>#{log.logId}</td>
                    <td>{formatDateTime(log.createdAt)}</td>
                    <td>{log.actorId ? `User #${log.actorId}` : "System"}</td>
                    <td>
                      <span style={{ fontWeight: 600, color: "var(--teal-700)", fontFamily: "monospace" }}>
                        {log.action}
                      </span>
                    </td>
                    <td>{log.entityType}</td>
                    <td>{log.entityId != null ? `#${log.entityId}` : "—"}</td>
                    <td>
                      <code style={{ fontSize: "0.82rem" }}>{log.ipAddress || "—"}</code>
                    </td>
                    <td>
                      <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                        {log.details || "—"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
