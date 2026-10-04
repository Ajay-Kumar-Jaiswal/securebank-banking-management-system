/**
 * Phone Number Validation Rules:
 * - Exactly 10 digits
 * - Digits only
 * - First digit must be 6, 7, 8, or 9
 * - No spaces, letters, or symbols
 */
export const PHONE_REGEX = /^[6-9]\d{9}$/;
export const PHONE_ERROR_MESSAGE =
  "Phone number must be exactly 10 digits and start with 6, 7, 8, or 9.";

/**
 * Validates a 10-digit phone number.
 * Returns an error string if invalid, or null if valid.
 *
 * @param {string} phone
 * @param {boolean} required
 * @returns {string|null}
 */
export function validatePhoneNumber(phone, required = true) {
  if (phone === null || phone === undefined) {
    return required ? PHONE_ERROR_MESSAGE : null;
  }

  const str = String(phone).trim();
  if (!str) {
    return required ? PHONE_ERROR_MESSAGE : null;
  }

  if (!PHONE_REGEX.test(str)) {
    return PHONE_ERROR_MESSAGE;
  }

  return null;
}

/**
 * Sanitizes phone input in real-time by stripping non-digit characters
 * and limiting length to 10 digits.
 *
 * @param {string} value
 * @returns {string}
 */
export function sanitizePhoneInput(value) {
  if (!value) return "";
  return String(value).replace(/\D/g, "").slice(0, 10);
}
