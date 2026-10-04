import React from "react";

export default function ConfirmModal({
  isOpen,
  title,
  message,
  children,
  confirmText = "Confirm",
  cancelText = "Cancel",
  confirmVariant = "primary",
  onConfirm,
  onCancel,
  loading = false,
}) {
  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={loading ? null : onCancel}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">{title}</h3>
          {!loading && (
            <button className="modal-close" onClick={onCancel} aria-label="Close">
              &times;
            </button>
          )}
        </div>
        <div className="modal-body">
          {message && <p className="modal-message">{message}</p>}
          {children}
        </div>
        <div className="modal-footer">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onCancel}
            disabled={loading}
          >
            {cancelText}
          </button>
          <button
            type="button"
            className={`btn btn-${confirmVariant}`}
            onClick={onConfirm}
            disabled={loading}
          >
            {loading ? "Processing..." : confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
