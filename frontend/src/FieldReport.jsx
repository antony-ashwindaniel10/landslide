import { useEffect, useState } from "react";
import { CircleMarker, MapContainer, TileLayer, useMapEvents } from "react-leaflet";
import { API_BASE, authHeaders } from "./api";
import "leaflet/dist/leaflet.css";

const CATEGORIES = [
  "Crack",
  "Slope movement",
  "Blocked road",
  "Seepage",
  "Debris",
];

function LocationPicker({ onPick }) {
  useMapEvents({
    click(event) {
      onPick(event.latlng.lat, event.latlng.lng);
    },
  });
  return null;
}

export default function FieldReport({ session, onLogout }) {
  const [latitude, setLatitude] = useState(null);
  const [longitude, setLongitude] = useState(null);
  const [placeName, setPlaceName] = useState("");
  const [risk, setRisk] = useState(null);
  const [locating, setLocating] = useState(false);
  const [scoring, setScoring] = useState(false);
  const [category, setCategory] = useState(CATEGORIES[0]);
  const [note, setNote] = useState("");
  const [photoName, setPhotoName] = useState("");
  const [photoData, setPhotoData] = useState("");
  const [preview, setPreview] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [reports, setReports] = useState([]);

  async function loadMine() {
    const response = await fetch(`${API_BASE}/reports/mine`, {
      headers: authHeaders(),
    });
    if (!response.ok) return;
    const data = await response.json();
    setReports(data.reports || []);
  }

  useEffect(() => {
    loadMine().catch(() => {});
  }, []);

  async function describePoint(lat, lon) {
    setLatitude(lat);
    setLongitude(lon);
    setScoring(true);
    setRisk(null);
    setPlaceName("");
    try {
      const [placeResponse, riskResponse] = await Promise.all([
        fetch(
          `${API_BASE}/place-name?latitude=${lat}&longitude=${lon}`
        ),
        fetch(`${API_BASE}/predict-at`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ latitude: lat, longitude: lon }),
        }),
      ]);
      if (placeResponse.ok) {
        const place = await placeResponse.json();
        setPlaceName(place.place_name || "");
      }
      if (riskResponse.ok) {
        setRisk(await riskResponse.json());
      }
    } catch {
      setError("Could not score this point. You can still send the photo.");
    } finally {
      setScoring(false);
    }
  }

  function useMyLocation() {
    if (!navigator.geolocation) {
      setError("This browser cannot read a GPS location. Tap the map instead.");
      return;
    }
    setLocating(true);
    setError("");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocating(false);
        describePoint(position.coords.latitude, position.coords.longitude);
      },
      () => {
        setLocating(false);
        setError("Location permission was denied. Tap the map to mark the slope.");
      },
      { enableHighAccuracy: true, timeout: 12000 }
    );
  }

  function onPhoto(event) {
    const file = event.target.files?.[0];
    setError("");
    setStatus("");
    if (!file) {
      setPhotoName("");
      setPhotoData("");
      setPreview("");
      return;
    }
    if (!file.type.startsWith("image/")) {
      setError("Choose a photo of the slope, crack, or blocked road.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError("Photo must be under 5 MB.");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || "");
      setPhotoData(result);
      setPreview(result);
      setPhotoName(file.name);
    };
    reader.readAsDataURL(file);
  }

  async function submit(event) {
    event.preventDefault();
    setError("");
    setStatus("");
    if (latitude == null || longitude == null) {
      setError("Mark the location with GPS or by tapping the map.");
      return;
    }
    if (!photoData) {
      setError("Add a photo from the site before sending.");
      return;
    }
    setBusy(true);
    try {
      const response = await fetch(`${API_BASE}/reports`, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          latitude,
          longitude,
          note,
          reporter: session.display_name,
          category,
          image_base64: photoData,
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || "Upload failed");
      }
      setStatus("Photo sent. An admin will review it before any alert goes out.");
      setNote("");
      setPhotoName("");
      setPhotoData("");
      setPreview("");
      await loadMine();
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setBusy(false);
    }
  }

  const level = risk?.prediction?.risk_level || "";

  return (
    <div className="app field-app">
      <header className="header">
        <div>
          <h1>Field report</h1>
          <p>Geo-tagged ground evidence for the NER landslide desk</p>
        </div>
        <div className="header-actions">
          <div className="session-chip">
            <div>
              <strong>{session.display_name}</strong>
              <span>Field user</span>
            </div>
            <button type="button" onClick={onLogout}>
              Sign out
            </button>
          </div>
        </div>
      </header>

      <section className="field-layout">
        <form className="field-card" onSubmit={submit}>
          <h2>Send what you see</h2>
          <p className="source-note">
            Tap the map or use GPS, then photograph the crack, moving slope, or
            blocked road.
          </p>

          <div className="field-map">
            <MapContainer
              center={[26.2, 92.9]}
              zoom={6}
              scrollWheelZoom
              style={{ height: "280px", width: "100%" }}
            >
              <TileLayer
                attribution="&copy; OpenStreetMap contributors"
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <LocationPicker onPick={describePoint} />
              {latitude != null && (
                <CircleMarker
                  center={[latitude, longitude]}
                  radius={9}
                  pathOptions={{ color: "#1d4ed8", fillColor: "#38bdf8", fillOpacity: 0.9 }}
                />
              )}
            </MapContainer>
          </div>

          <div className="field-actions">
            <button type="button" onClick={useMyLocation} disabled={locating}>
              {locating ? "Reading GPS…" : "Use my location"}
            </button>
            {latitude != null && (
              <span>
                {latitude.toFixed(5)}, {longitude.toFixed(5)}
                {placeName ? ` · ${placeName}` : ""}
              </span>
            )}
          </div>

          {scoring && <p className="command-status">Scoring this slope…</p>}
          {risk && (
            <div className={`field-risk level-${level.toLowerCase()}`}>
              <b>{level}</b>
              <span>
                Score {risk.prediction.risk_score}/100 · rain{" "}
                {risk.environment.rainfall_mm_day} mm · slope{" "}
                {risk.environment.slope_degrees}°
              </span>
            </div>
          )}

          <label>
            What are you seeing?
            <select
              value={category}
              onChange={(event) => setCategory(event.target.value)}
            >
              {CATEGORIES.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </label>

          <label>
            Note from the site
            <textarea
              value={note}
              onChange={(event) => setNote(event.target.value)}
              placeholder="How wide is the crack, is the road blocked, is the slope moving?"
              required
            />
          </label>

          <label className="photo-drop">
            Site photo
            <input
              type="file"
              accept="image/*"
              capture="environment"
              onChange={onPhoto}
            />
            {photoName && <span>{photoName}</span>}
          </label>
          {preview && <img className="photo-preview" src={preview} alt="Selected site" />}

          {error && <p className="login-error">{error}</p>}
          {status && <p className="report-status">{status}</p>}

          <button type="submit" className="login-submit" disabled={busy}>
            {busy ? "Sending…" : "Upload ground report"}
          </button>
        </form>

        <aside className="field-card">
          <h2>Your reports</h2>
          {reports.length === 0 ? (
            <p className="source-note">No photos sent from this account yet.</p>
          ) : (
            <ul className="report-inbox">
              {reports.map((report) => (
                <li key={report.id}>
                  {report.image_url && (
                    <img
                      src={`${API_BASE}${report.image_url}`}
                      alt=""
                    />
                  )}
                  <div>
                    <strong>{report.category || "Ground observation"}</strong>
                    <p>{report.note}</p>
                    <em>
                      {report.status || "pending"} ·{" "}
                      {Number(report.latitude).toFixed(3)},{" "}
                      {Number(report.longitude).toFixed(3)}
                    </em>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </aside>
      </section>
    </div>
  );
}
