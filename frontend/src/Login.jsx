import { useState } from "react";
import { API_BASE } from "./api";

const DEMOS = [
  {
    role: "Admin",
    detail: "Verify risk and queue SMS alerts",
    username: "admin",
    password: "admin123",
  },
  {
    role: "Field user",
    detail: "Upload a geo-tagged ground photo",
    username: "user",
    password: "user123",
  },
];

export default function Login({ onSuccess }) {
  const [mode, setMode] = useState("signin");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event, credentials) {
    event?.preventDefault();
    setBusy(true);
    setError("");
    const body =
      mode === "register" && !credentials
        ? {
            username,
            password,
            display_name: displayName,
          }
        : {
            username: credentials?.username ?? username,
            password: credentials?.password ?? password,
          };
    const path = mode === "register" && !credentials ? "/auth/register" : "/auth/login";

    try {
      const response = await fetch(`${API_BASE}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || "Sign-in failed");
      }
      onSuccess(data);
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-screen">
      <div className="login-card">
        <p className="command-kicker">North Eastern Region</p>
        <h1>Landslide Digital Twin</h1>
        <p className="login-lead">
          Admins verify a high-risk zone before any SMS goes out. Field users
          send geo-tagged photos of cracks, slope movement, and blocked roads.
        </p>

        <div className="login-switch">
          <button
            type="button"
            className={mode === "signin" ? "active" : ""}
            onClick={() => {
              setMode("signin");
              setError("");
            }}
          >
            Sign in
          </button>
          <button
            type="button"
            className={mode === "register" ? "active" : ""}
            onClick={() => {
              setMode("register");
              setError("");
            }}
          >
            Create field account
          </button>
        </div>

        <form className="login-form" onSubmit={(event) => submit(event)}>
          {mode === "register" && (
            <label>
              Name
              <input
                value={displayName}
                onChange={(event) => setDisplayName(event.target.value)}
                placeholder="Your name"
                autoComplete="name"
                required
              />
            </label>
          )}
          <label>
            Username
            <input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="Username"
              autoComplete="username"
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Password"
              autoComplete={mode === "register" ? "new-password" : "current-password"}
              required
            />
          </label>
          {error && <p className="login-error">{error}</p>}
          <button type="submit" className="login-submit" disabled={busy}>
            {busy
              ? "Please wait…"
              : mode === "register"
                ? "Create account"
                : "Enter the portal"}
          </button>
        </form>

        <div className="demo-grid">
          {DEMOS.map((demo) => (
            <button
              key={demo.username}
              type="button"
              className="demo-account"
              disabled={busy}
              onClick={(event) => {
                setMode("signin");
                setUsername(demo.username);
                setPassword(demo.password);
                submit(event, demo);
              }}
            >
              <strong>{demo.role}</strong>
              <span>{demo.detail}</span>
              <em>
                {demo.username} / {demo.password}
              </em>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
