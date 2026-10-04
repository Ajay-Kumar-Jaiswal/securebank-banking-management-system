import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { updateProfile, changePassword } from "../api/authApi";
import { extractErrorMessage, formatDateTime } from "../utils/errorUtils";
import { validatePhoneNumber, sanitizePhoneInput, PHONE_ERROR_MESSAGE } from "../utils/validation";
import AlertMessage from "../components/AlertMessage";
import StatusBadge from "../components/StatusBadge";

export default function Profile() {
  const { user, updateUser, refreshProfile, isAdmin } = useAuth();

  // Profile Form state
  const [fullName, setFullName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [address, setAddress] = useState("");
  const [phoneError, setPhoneError] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileSuccess, setProfileSuccess] = useState(null);
  const [profileError, setProfileError] = useState(null);

  // Password Form state
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [pwdLoading, setPwdLoading] = useState(false);
  const [pwdSuccess, setPwdSuccess] = useState(null);
  const [pwdError, setPwdError] = useState(null);

  useEffect(() => {
    if (user) {
      setFullName(user.fullName || "");
      setPhoneNumber(user.phoneNumber || "");
      setAddress(user.address || "");
    }
  }, [user]);

  const handlePhoneChange = (e) => {
    const sanitized = sanitizePhoneInput(e.target.value);
    setPhoneNumber(sanitized);

    if (sanitized.length > 0 && !["6", "7", "8", "9"].includes(sanitized[0])) {
      setPhoneError(PHONE_ERROR_MESSAGE);
    } else if (sanitized.length === 10) {
      setPhoneError(null);
    } else {
      setPhoneError(null);
    }
  };

  const handlePhoneBlur = () => {
    if (phoneNumber) {
      const err = validatePhoneNumber(phoneNumber);
      setPhoneError(err);
    }
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setProfileError(null);
    setProfileSuccess(null);

    const phoneValidationErr = validatePhoneNumber(phoneNumber);
    if (phoneValidationErr) {
      setPhoneError(phoneValidationErr);
      setProfileError(phoneValidationErr);
      return;
    }

    setProfileLoading(true);

    try {
      const res = await updateProfile({
        fullName: fullName.trim(),
        phoneNumber: phoneNumber.trim(),
        address: address.trim(),
      });
      updateUser(res.data);
      setProfileSuccess("Profile updated successfully.");
    } catch (err) {
      setProfileError(extractErrorMessage(err, "Failed to update profile."));
    } finally {
      setProfileLoading(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPwdError(null);
    setPwdSuccess(null);

    if (newPassword.length < 6) {
      setPwdError("New password must be at least 6 characters long.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setPwdError("New passwords do not match.");
      return;
    }

    setPwdLoading(true);
    try {
      await changePassword({
        currentPassword,
        newPassword,
      });
      setPwdSuccess("Password updated successfully.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setPwdError(extractErrorMessage(err, "Failed to change password."));
    } finally {
      setPwdLoading(false);
    }
  };

  return (
    <div className="page">
      <h1 className="page-title">User Profile</h1>

      <div className="profile-grid">
        {/* Profile Card */}
        <div className="card">
          <h2>Account Details</h2>
          <AlertMessage message={profileError} />
          <AlertMessage type="success" message={profileSuccess} />

          <div className="detail-grid" style={{ marginBottom: "1.5rem" }}>
            <div>
              <div className="detail-label">Email Address</div>
              <div className="detail-value" style={{ fontSize: "1rem" }}>{user?.email}</div>
            </div>
            <div>
              <div className="detail-label">Role</div>
              <div className="detail-value">
                <span className="role-tag" style={{ marginLeft: 0 }}>{user?.role}</span>
              </div>
            </div>
            <div>
              <div className="detail-label">Account Status</div>
              <div className="detail-value">
                <StatusBadge status={user?.status} />
              </div>
            </div>
            <div>
              <div className="detail-label">Member Since</div>
              <div className="detail-value" style={{ fontSize: "0.95rem" }}>
                {user?.createdAt ? formatDateTime(user.createdAt) : "—"}
              </div>
            </div>
          </div>

          {isAdmin && (
            <div className="warning-callout" style={{ marginBottom: "1.25rem" }}>
              <strong>Administrator Protection Active:</strong> You cannot deactivate your own administrator account. To view or manage other administrators, visit <Link to="/admin/administrators" style={{ fontWeight: 600 }}>Administrator Management</Link>.
            </div>
          )}

          <h3>Edit Profile Information</h3>
          <form onSubmit={handleUpdateProfile} className="auth-form" style={{ marginTop: "1rem" }}>
            <label>
              Full Name
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                minLength={2}
              />
            </label>

            <label>
              Phone Number
              <input
                type="tel"
                inputMode="numeric"
                value={phoneNumber}
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
              Residential Address
              <input
                type="text"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="Street address, City, Postal code"
              />
            </label>

            <button type="submit" className="btn btn-primary" disabled={profileLoading}>
              {profileLoading ? "Saving Changes..." : "Save Profile"}
            </button>
          </form>
        </div>

        {/* Change Password Card */}
        <div className="card">
          <h2>Security & Password</h2>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: "1.25rem" }}>
            Ensure your account is using a strong, unique password to prevent unauthorized access.
          </p>

          <AlertMessage message={pwdError} />
          <AlertMessage type="success" message={pwdSuccess} />

          <form onSubmit={handleChangePassword} className="auth-form">
            <label>
              Current Password
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
                placeholder="Enter current password"
              />
            </label>

            <label>
              New Password
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={6}
                placeholder="Minimum 6 characters"
              />
            </label>

            <label>
              Confirm New Password
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                minLength={6}
                placeholder="Re-enter new password"
              />
            </label>

            <button type="submit" className="btn btn-secondary" disabled={pwdLoading}>
              {pwdLoading ? "Updating Password..." : "Update Password"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
