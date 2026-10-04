export default function AlertMessage({ type = "error", message }) {
  if (!message) return null;
  return <div className={`alert alert-${type}`}>{message}</div>;
}
