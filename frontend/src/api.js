export const API_BASE = import.meta.env.VITE_API_BASE ?? "";

const TOKEN_KEY = "ldt-token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

export function saveSession(payload) {
  localStorage.setItem(TOKEN_KEY, payload.token);
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
}

export function authHeaders(extra = {}) {
  const token = getToken();
  return {
    ...extra,
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}
