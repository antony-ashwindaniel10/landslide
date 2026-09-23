import { useEffect, useState } from "react";
import { API_BASE, authHeaders } from "./api";

export default function ReportInbox() {
  const [reports, setReports] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/reports`, {
        headers: authHeaders(),
      });
      if (!response.ok) {
        throw new Error("Ground reports could not be loaded");
      }
      const data = await response.json();
      setReports(data.reports || []);
      setError("");
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function review(reportId, status) {
    const response = await fetch(`${API_BASE}/reports/${reportId}/review`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ status }),
    });
    if (!response.ok) {
      setError("Could not update that report.");
      return;
    }
    const updated = await response.json();
    setReports((current) =>
      current.map((report) => (report.id === updated.id ? updated : report))
    );
  }

  return (
    <section className="inbox-section">
      <div className="section-title">
        <h2>Ground reports</h2>
        <p>
          Photos from field users. Verify a report before you treat it as
          confirmation of the model.
        </p>
      </div>

      {loading && <p className="command-status">Loading field photos…</p>}
      {error && <p className="login-error">{error}</p>}
      {!loading && reports.length === 0 && (
        <p className="source-note">No field photos have been uploaded yet.</p>
      )}

      <ul className="report-inbox">
        {reports.map((report) => (
          <li key={report.id}>
            {report.image_url ? (
              <img src={`${API_BASE}${report.image_url}`} alt="" />
            ) : (
              <div className="inbox-placeholder">No photo</div>
            )}
            <div>
              <strong>{report.category || "Ground observation"}</strong>
              <p>{report.note || "No note"}</p>
              <em>
                {report.reporter || report.username} ·{" "}
                {Number(report.latitude).toFixed(3)},{" "}
                {Number(report.longitude).toFixed(3)} · {report.status || "pending"}
              </em>
              {report.status !== "verified" && report.status !== "dismissed" && (
                <div className="inbox-actions">
                  <button type="button" onClick={() => review(report.id, "verified")}>
                    Verify
                  </button>
                  <button
                    type="button"
                    className="ghost"
                    onClick={() => review(report.id, "dismissed")}
                  >
                    Dismiss
                  </button>
                </div>
              )}
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
