/** Extracts a human-readable message from an Axios error thrown by our API. */
export function extractErrorMessage(err, fallback = "Something went wrong. Please try again.") {
  if (err?.response?.data) {
    const data = err.response.data;
    if (data.details && data.details.length > 0) {
      return data.details.join(" | ");
    }
    if (data.message) {
      return data.message;
    }
  }
  return fallback;
}

export function formatCurrency(amount) {
  const value = Number(amount || 0);
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatDateTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
