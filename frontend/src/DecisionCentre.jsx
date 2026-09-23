import { useEffect, useState } from "react";
import { API_BASE, authHeaders } from "./api";

const QUEUE_KEY = "ldt-report-queue";

function readQueue() {
  try {
    return JSON.parse(localStorage.getItem(QUEUE_KEY) || "[]");
  } catch {
    return [];
  }
}

function writeQueue(items) {
  localStorage.setItem(QUEUE_KEY, JSON.stringify(items));
}

async function postReport(report) {
  const response = await fetch(`${API_BASE}/reports`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(report),
  });
  if (!response.ok) {
    throw new Error("Report sync failed");
  }
  return response.json();
}

export default function DecisionCentre({
  latitude,
  longitude,
  riskResult,
  forecastData,
  placeName,
  onDecision,
}) {
  const [decision, setDecision] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [language, setLanguage] = useState("en");
  const [note, setNote] = useState("");
  const [reporter, setReporter] = useState("Field officer");
  const [reportStatus, setReportStatus] = useState("");
  const [alerts, setAlerts] = useState([]);
  const [queued, setQueued] = useState(readQueue().length);
  const [refreshKey, setRefreshKey] = useState(0);

  const score = Number(riskResult?.prediction?.risk_score ?? 0);
  const soil = Number(
    riskResult?.environment?.soil_wetness_gwet_top ?? 0
  );
  const slope = Number(riskResult?.environment?.slope_degrees ?? 0);
  const rainfall = Number(riskResult?.environment?.rainfall_mm_day ?? 0);

  const forecast72 = (forecastData?.hourly?.precipitation_mm || [])
    .slice(0, 72)
    .reduce((sum, value) => sum + Number(value || 0), 0);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError("");
      const params = new URLSearchParams({
        latitude: String(latitude),
        longitude: String(longitude),
        ml_score: String(score),
        rainfall_mm: String(rainfall),
        soil_wetness: String(soil),
        slope: String(slope),
        forecast_rain_72h: String(forecast72),
        place_name: placeName || "",
      });

      try {
        const response = await fetch(`${API_BASE}/decision?${params}`);
        if (!response.ok) {
          throw new Error("Decision support could not be loaded");
        }
        const data = await response.json();
        if (!cancelled) {
          setDecision(data);
          onDecision?.(data);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError.message);
          setDecision(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    if (Number.isFinite(latitude) && Number.isFinite(longitude) && riskResult) {
      load();
    }

    return () => {
      cancelled = true;
    };
  }, [
    latitude,
    longitude,
    score,
    rainfall,
    soil,
    slope,
    forecast72,
    placeName,
    riskResult,
    refreshKey,
  ]);

  useEffect(() => {
    fetch(`${API_BASE}/alerts`)
      .then((response) => (response.ok ? response.json() : { alerts: [] }))
      .then((data) => setAlerts(data.alerts || []))
      .catch(() => {});
  }, [decision]);

  async function syncQueue() {
    const pending = readQueue();
    if (!pending.length || !navigator.onLine) return;
    const remaining = [];
    for (const item of pending) {
      try {
        await postReport(item);
      } catch {
        remaining.push(item);
      }
    }
    writeQueue(remaining);
    setQueued(remaining.length);
  }

  useEffect(() => {
    syncQueue();
    window.addEventListener("online", syncQueue);
    return () => window.removeEventListener("online", syncQueue);
  }, []);

  async function submitReport(event) {
    event.preventDefault();
    const report = {
      latitude,
      longitude,
      note,
      reporter,
    };

    try {
      await postReport(report);
      setReportStatus("Report synced and fused into the next risk update.");
      setNote("");
      setRefreshKey((current) => current + 1);
    } catch {
      const pending = readQueue();
      pending.push(report);
      writeQueue(pending);
      setQueued(pending.length);
      setReportStatus("Offline. Report saved on this device and will sync later.");
    }
  }

  async function sendAlert() {
    if (!decision) return;
    const response = await fetch(`${API_BASE}/alerts`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        latitude,
        longitude,
        place: placeName || "Selected slope",
        risk_level: decision.risk_level,
        risk_score: decision.dynamic_score,
        language,
        channel: "SMS",
      }),
    });
    if (response.ok) {
      const created = await response.json();
      setAlerts((current) => [created, ...current]);
    }
  }

  if (!riskResult) return null;

  const level = decision?.risk_level || "Green";

  return (
    <section className={`decision-centre level-${level.toLowerCase()}`}>
      <header className="command-hero">
        <div>
          <p className="command-kicker">Operations command centre</p>
          <h2>{placeName || "Selected slope"}</h2>
          <p>
            Slope stability, threatened infrastructure, and who to warn first.
          </p>
        </div>
        <div className="command-score">
          <span>Dynamic score</span>
          <strong>{decision ? decision.dynamic_score : "—"}</strong>
          <em>/ 100</em>
          <b className="level-pill">{decision ? decision.risk_level : "…"}</b>
        </div>
      </header>

      {loading && (
        <p className="command-status">
          Mapping roads, villages, and warning priority…
        </p>
      )}
      {error && <p className="decision-error">{error}</p>}

      {decision && (
        <>
          <div className="priority-banner">{decision.priority_action}</div>

          <div className="answer-grid">
            <article>
              <h3>Slope</h3>
              <p>{decision.answers.which_slope}</p>
            </article>
            <article>
              <h3>Severity</h3>
              <p>{decision.answers.how_severe}</p>
            </article>
            <article>
              <h3>Affected</h3>
              <p>{decision.answers.what_is_affected}</p>
            </article>
            <article>
              <h3>Warn first</h3>
              <p>{decision.answers.who_first}</p>
            </article>
          </div>

          <h3 className="command-heading">Precursor signals</h3>
          <div className="precursor-list">
            {decision.precursors.map((item) => (
              <div key={item.name}>
                <div className="precursor-top">
                  <strong>{item.name}</strong>
                  <span>
                    {item.value} {item.unit}
                  </span>
                </div>
                <div className="signal-track">
                  <div
                    className="signal-fill"
                    style={{ width: `${Math.min(100, item.signal * 3.2)}%` }}
                  />
                </div>
                <small>{item.source}</small>
              </div>
            ))}
          </div>

          <h3 className="command-heading">Threatened infrastructure</h3>
          <div className="infra-grid">
            <InfraList title="Roads" items={decision.infrastructure.roads} />
            <InfraList title="Bridges" items={decision.infrastructure.bridges} />
            <InfraList title="Settlements" items={decision.infrastructure.villages} />
            <InfraList
              title="Hospitals and schools"
              items={decision.infrastructure.critical}
            />
          </div>
          <p className="source-note">{decision.infrastructure.source}</p>

          <h3 className="command-heading">Connectivity and evacuation</h3>
          <div className="connect-grid">
            <article>
              <span>Threatened segment</span>
              <strong>
                {decision.connectivity.threatened_segment?.name || "None mapped"}
              </strong>
            </article>
            <article>
              <span>Could be isolated</span>
              <strong>
                {decision.connectivity.villages_at_risk_of_isolation.join(", ") ||
                  "None identified"}
              </strong>
            </article>
            <article>
              <span>Alternate routes</span>
              <strong>
                {decision.connectivity.alternate_routes.join(", ") || "None mapped"}
              </strong>
            </article>
            <article>
              <span>Evacuation order</span>
              <strong>
                {decision.connectivity.evacuation_priority.join(" → ") || "None"}
              </strong>
            </article>
          </div>

          <div>
            <h3 className="command-heading">Who must be warned</h3>
            <ol className="warn-list">
              {decision.who_to_warn.map((item) => (
                <li key={item.priority}>
                  <b>{item.priority}</b>
                  <div>
                    <strong>{item.who}</strong>
                    <span>
                      {item.why} · {item.channel}
                    </span>
                  </div>
                </li>
              ))}
            </ol>
            {decision.iot && (
              <p className="iot-chip">
                {decision.iot.sensor.name} · {decision.iot.distance_km} km
                {decision.iot.fused ? " · fused into score" : ""}
              </p>
            )}
          </div>

          <div className="alert-card">
            <h3 className="command-heading">Dispatch alert</h3>
            <div className="alert-row">
              <select
                value={language}
                onChange={(event) => setLanguage(event.target.value)}
              >
                <option value="en">English</option>
                <option value="hi">Hindi</option>
                <option value="as">Assamese</option>
              </select>
              <button type="button" onClick={sendAlert}>
                Queue SMS
              </button>
            </div>
            <p className="alert-text">{decision.alerts[language]}</p>
          </div>
        </>
      )}

      <div className="report-card">
        <div>
          <h3 className="command-heading">Ground evidence</h3>
          <p className="source-note">
            Stored on this device if the network drops, then synced automatically.
            {queued > 0 ? ` ${queued} waiting to sync.` : ""}
          </p>
        </div>
        <form className="report-form" onSubmit={submitReport}>
          <input
            value={reporter}
            onChange={(event) => setReporter(event.target.value)}
            placeholder="Reporter"
          />
          <textarea
            value={note}
            onChange={(event) => setNote(event.target.value)}
            placeholder="Cracks, debris, seepage, or slope movement"
            required
          />
          <button type="submit">Submit report</button>
        </form>
        {reportStatus && <p className="report-status">{reportStatus}</p>}
      </div>

      {alerts.length > 0 && (
        <ul className="alert-log">
          {alerts.slice(0, 4).map((alert) => (
            <li key={alert.id}>
              <b className={`mini-level level-${(alert.risk_level || "green").toLowerCase()}`}>
                {alert.risk_level}
              </b>
              <span>
                {alert.place} · {alert.language.toUpperCase()} · {alert.channel} ·{" "}
                {alert.status}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function InfraList({ title, items }) {
  return (
    <div>
      <h4>{title}</h4>
      {items?.length ? (
        <ul>
          {items.slice(0, 4).map((item) => (
            <li key={`${item.name}-${item.distance_km}`}>
              {item.name}
              {item.kind ? ` (${item.kind})` : ""} · {item.distance_km} km
            </li>
          ))}
        </ul>
      ) : (
        <p>None within range</p>
      )}
    </div>
  );
}
