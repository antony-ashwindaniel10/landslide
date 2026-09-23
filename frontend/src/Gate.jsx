import { useEffect, useState } from "react";
import App from "./App.jsx";
import FieldReport from "./FieldReport.jsx";
import Login from "./Login.jsx";
import { API_BASE, authHeaders, clearSession, saveSession } from "./api";
import "./App.css";

export default function Gate() {
  const [session, setSession] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("ldt-token");
    if (!token) {
      setReady(true);
      return;
    }
    fetch(`${API_BASE}/auth/me`, { headers: authHeaders() })
      .then(async (response) => {
        if (!response.ok) throw new Error("expired");
        return response.json();
      })
      .then((user) => setSession(user))
      .catch(() => clearSession())
      .finally(() => setReady(true));
  }, []);

  function handleLogin(payload) {
    saveSession(payload);
    setSession(payload.user);
  }

  function handleLogout() {
    fetch(`${API_BASE}/auth/logout`, {
      method: "POST",
      headers: authHeaders(),
    }).catch(() => {});
    clearSession();
    setSession(null);
  }

  if (!ready) {
    return (
      <div className="gate-loading">
        <p>Opening the landslide desk…</p>
      </div>
    );
  }

  if (!session) {
    return <Login onSuccess={handleLogin} />;
  }

  if (session.role === "admin") {
    return <App session={session} onLogout={handleLogout} />;
  }

  return <FieldReport session={session} onLogout={handleLogout} />;
}
