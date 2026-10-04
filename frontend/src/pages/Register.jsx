import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { registerUser } from "../api/authApi";
import { extractErrorMessage } from "../utils/errorUtils";
import { validatePhoneNumber, sanitizePhoneInput, PHONE_ERROR_MESSAGE } from "../utils/validation";
import AlertMessage from "../components/AlertMessage";

const initialForm = {
  fullName: "",
  email: "",
  phoneNumber: "",
  password: "",
  address: "",
};

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [phoneError, setPhoneError] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handlePhoneChange = (e) => {
    const sanitized = sanitizePhoneInput(e.target.value);
    setForm((prev) => ({ ...prev, phoneNumber: sanitized }));

    if (sanitized.length > 0 && !["6", "7", "8", "9"].includes(sanitized[0])) {
      setPhoneError(PHONE_ERROR_MESSAGE);
    } else if (sanitized.length === 10) {
      setPhoneError(null);
    } else {
      setPhoneError(null);
    }
  };

  const handlePhoneBlur = () => {
    if (form.phoneNumber) {
      const err = validatePhoneNumber(form.phoneNumber);
      setPhoneError(err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    const phoneValidationErr = validatePhoneNumber(form.phoneNumber);
    if (phoneValidationErr) {
      setPhoneError(phoneValidationErr);
      setError(phoneValidationErr);
      return;
    }

    setSubmitting(true);
    try {
      await registerUser(form);
      setSuccess("Registration successful! Redirecting to login...");
      setTimeout(() => navigate("/login"), 1500);
    } catch (err) {
      setError(extractErrorMessage(err, "Registration failed. Please check your details."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1 className="auth-title">Create your account</h1>
        <p className="auth-subtitle">Join SecureBank in a few seconds</p>

        <AlertMessage message={error} />
        <AlertMessage type="success" message={success} />

        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            Full Name
            <input name="fullName" value={form.fullName} onChange={handleChange} required />
          </label>
          <label>
            Email
            <input type="email" name="email" value={form.email} onChange={handleChange} required />
          </label>
          <label>
            Phone Number
            <input
              type="tel"
              inputMode="numeric"
              name="phoneNumber"
              value={form.phoneNumber}
              onChange={handlePhoneChange}
              onBlur={handlePhoneBlur}
              placeholder="10-digit mobile number (e.g. 9876543210)"
              maxLength={10}
              required
            />
            {phoneError && (
              <span
                style={{
                  color: "#dc2626",
                  fontSize: "0.85rem",
                  marginTop: "0.25rem",
                  display: "block",
                  lineHeight: "1.2",
                }}
              >
                {phoneError}
              </span>
            )}
          </label>
          <label>
            Password
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              required
              minLength={8}
            />
          </label>
          <label>
            Address
            <input name="address" value={form.address} onChange={handleChange} required />
          </label>

          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? "Creating account..." : "Register"}
          </button>
        </form>

        <p className="auth-footer">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </div>
    </div>
  );
}
