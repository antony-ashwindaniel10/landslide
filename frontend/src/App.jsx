import { useEffect, useRef, useState } from "react";
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  CircleMarker,
  Popup,
  useMapEvents,
} from "react-leaflet";

import Papa from "papaparse";

import "leaflet/dist/leaflet.css";
import "./App.css";
import HistoricalLandslidesLayer from "./HistoricalLandslidesLayer";
import DecisionCentre from "./DecisionCentre";
import RiskHeatmapLayer from "./RiskHeatmapLayer";

const API_BASE = "http://127.0.0.1:8000";

function buildPlaceNameFromAddress(address = {}, displayName) {
  const localName = [
    address.village,
    address.town,
    address.city,
    address.suburb,
    address.neighbourhood,
    address.hamlet,
    address.locality,
    address.county,
    address.state_district,
    address.state,
  ].find(Boolean);

  const regionParts = [
    address.state_district,
    address.state,
    address.country,
  ].filter(
    (part) => part && part !== localName
  );

  const uniqueRegion = [...new Set(regionParts)];

  if (localName && uniqueRegion.length > 0) {
    return `${localName}, ${uniqueRegion.join(", ")}`;
  }

  if (localName) {
    return localName;
  }

  return displayName || null;
}

async function resolvePlaceName(latitude, longitude, signal) {
  // Nominatim only — avoid a slow/failed backend round-trip first
  const nominatimResponse = await fetch(
    `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json&zoom=14&addressdetails=1`,
    {
      signal,
      headers: {
        Accept: "application/json",
      },
    }
  );

  if (!nominatimResponse.ok) {
    return null;
  }

  const data = await nominatimResponse.json();
  return buildPlaceNameFromAddress(
    data.address || {},
    data.display_name
  );
}

async function readErrorDetail(response) {
  try {
    const body = await response.json();
    if (typeof body?.detail === "string" && body.detail) {
      return body.detail;
    }
  } catch {
    // ignore non-JSON errors
  }
  return "";
}

async function predictAtLocation({
  latitude,
  longitude,
  historical_landslide = false,
  signal,
}) {
  const response = await fetch(`${API_BASE}/predict-at`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    signal,
    body: JSON.stringify({
      latitude,
      longitude,
      historical_landslide,
    }),
  });

  // Missing DEM is a location problem, not a missing API route
  if (response.status === 422 || response.status === 404) {
    const detail = await readErrorDetail(response);
    if (
      response.status === 422 ||
      detail.includes("DEM") ||
      detail.includes("elevation")
    ) {
      throw new Error(
        detail ||
          "No elevation data for this location. Select a place in North Eastern India."
      );
    }
  }

  // Fallback for older backend without /predict-at
  if (response.status === 404) {
    const elevationResponse = await fetch(
      `${API_BASE}/elevation?latitude=${latitude}&longitude=${longitude}`,
      { signal }
    );
    if (!elevationResponse.ok) {
      const detail = await readErrorDetail(elevationResponse);
      throw new Error(
        detail.includes("DEM") || detail.includes("not found")
          ? "No elevation data for this location. Select a place in North Eastern India."
          : "Terrain information could not be obtained"
      );
    }
    const terrain = await elevationResponse.json();
    const elevation = terrain.elevation_m ?? 0;
    const slope = terrain.slope_degrees ?? 1.8;

    const riskResponse = await fetch(`${API_BASE}/risk`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal,
      body: JSON.stringify({
        latitude,
        longitude,
        slope,
        elevation,
        historical_landslide,
      }),
    });
    if (!riskResponse.ok) {
      throw new Error("Risk prediction failed");
    }
    const riskData = await riskResponse.json();
    return {
      ...riskData,
      environment: {
        ...riskData.environment,
        elevation_m: elevation,
        slope_degrees: slope,
      },
      forecast_rainfall: null,
      forecast_risk: null,
    };
  }

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new Error(detail || "Risk prediction failed");
  }

  return response.json();
}

// ============================================================
// MAP CLICK HANDLER (parallel fetches + cancel stale clicks)
// ============================================================

function MapClickHandler({ onPredict }) {
  useMapEvents({
    click: (e) => {
      const target = e.originalEvent?.target;

      if (
        target?.closest?.(".historical-landslide-marker") ||
        target?.closest?.(".leaflet-interactive")?.classList?.contains(
          "historical-landslide-marker"
        )
      ) {
        return;
      }

      if (
        target?.tagName === "path" &&
        target?.getAttribute?.("class")?.includes("historical-landslide-marker")
      ) {
        return;
      }

      onPredict(e.latlng.lat, e.latlng.lng);
    },
  });

  return null;
}


// ============================================================
// AI RISK MARKER
// ============================================================

function AIRiskMarker({
  formData,
  riskResult,
  placeName,
}) {
  const markerRef = useRef(null);

  useEffect(() => {
    if (riskResult && markerRef.current) {
      markerRef.current.openPopup();
    }
  }, [riskResult, placeName]);

  if (!riskResult) return null;

  const latitude = Number(formData.latitude);
  const longitude = Number(formData.longitude);

  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
    return null;
  }

  const score = Number(riskResult.prediction?.risk_score ?? 0);
  const level = riskResult.prediction?.risk_level || "Green";

  let color = "#16a34a";
  let fillColor = "#22c55e";

  if (score >= 75) {
    color = "#dc2626";
    fillColor = "#ef4444";
  } else if (score >= 50) {
    color = "#ea580c";
    fillColor = "#f97316";
  } else if (score >= 25) {
    color = "#ca8a04";
    fillColor = "#eab308";
  }

  return (
    <CircleMarker
      ref={markerRef}
      center={[latitude, longitude]}
      radius={10}
      bubblingMouseEvents={false}
      className="ai-risk-marker"
      pathOptions={{
        color,
        fillColor,
        fillOpacity: 0.9,
        weight: 3,
      }}
    >
      <Popup>
        <div
          style={{
            minWidth: "220px",
            fontSize: "14px",
            lineHeight: "1.5",
          }}
        >
          <h3
            style={{
              margin: "0 0 8px 0",
              color,
              fontSize: "17px",
            }}
          >
            🤖 AI Risk Prediction
          </h3>

          {placeName && (
            <p style={{ margin: "0 0 12px 0" }}>
              <strong>📍 Place:</strong> {placeName}
            </p>
          )}

          <p>
            <strong>Risk Score:</strong> {score.toFixed(2)}/100
          </p>

          <p>
            <strong>Risk Level:</strong> {level}
          </p>

          <p>
            <strong>Landslide Probability:</strong>{" "}
            {(
              Number(riskResult.prediction?.landslide_probability ?? 0) * 100
            ).toFixed(2)}
            %
          </p>

          <p>
            <strong>Latitude:</strong> {latitude}
          </p>

          <p>
            <strong>Longitude:</strong> {longitude}
          </p>
        </div>
      </Popup>
    </CircleMarker>
  );
}


// ============================================================
// 3-DAY AI RISK TREND CHART
// ============================================================

function RiskTrendChart({
  forecastRiskData
}) {

  if (
    !forecastRiskData ||
    !forecastRiskData.forecast_days ||
    forecastRiskData.forecast_days.length === 0
  ) {
    return null;
  }


  const getRiskColor = (score) => {

    const numericScore =
      Number(score || 0);


    if (numericScore >= 75) {
      return "#dc2626";
    }

    if (numericScore >= 50) {
      return "#ea580c";
    }

    if (numericScore >= 25) {
      return "#ca8a04";
    }

    return "#16a34a";

  };


  const getRiskBackground = (score) => {

    const numericScore =
      Number(score || 0);


    if (numericScore >= 75) {
      return "#fee2e2";
    }

    if (numericScore >= 50) {
      return "#ffedd5";
    }

    if (numericScore >= 25) {
      return "#fef9c3";
    }

    return "#dcfce7";

  };


  const maxScore = Math.max(
    ...forecastRiskData.forecast_days.map(
      (day) =>
        Number(day.risk_score || 0)
    ),
    25
  );


  return (

    <div
      style={{
        marginBottom: "20px",
        padding: "20px",
        borderRadius: "12px",
        background: "#f8fafc",
        border: "1px solid #e2e8f0",
      }}
    >

      <h4
        className="forecast-section-title"
        style={{
          marginTop: 0,
        }}
      >

        📈 3-Day AI Risk Trend

      </h4>


      <p
        style={{
          fontSize: "13px",
          color: "#64748b",
          marginTop: "-8px",
          marginBottom: "20px",
        }}
      >

        Predicted landslide risk score for each
        upcoming day.

      </p>


      <div
        style={{
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "space-around",
          gap: "20px",
          height: "230px",
          padding:
            "10px 10px 0 10px",
          borderBottom:
            "2px solid #cbd5e1",
        }}
      >

        {forecastRiskData.forecast_days.map(
          (day) => {

            const score =
              Number(
                day.risk_score || 0
              );


            const riskColor =
              getRiskColor(score);


            const riskBackground =
              getRiskBackground(score);


            const barHeight =
              Math.max(
                (score / maxScore) * 170,
                12
              );


            return (

              <div
                key={day.date}
                style={{
                  flex: 1,
                  height: "100%",
                  display: "flex",
                  flexDirection:
                    "column",
                  alignItems:
                    "center",
                  justifyContent:
                    "flex-end",
                  minWidth: 0,
                }}
              >

                <div
                  style={{
                    background:
                      riskBackground,
                    color:
                      riskColor,
                    border:
                      `1px solid ${riskColor}`,
                    borderRadius:
                      "8px",
                    padding:
                      "4px 8px",
                    fontSize:
                      "13px",
                    fontWeight:
                      "700",
                    marginBottom:
                      "6px",
                  }}
                >

                  {score.toFixed(2)}

                </div>


                <div
                  style={{
                    width: "55px",
                    maxWidth: "75%",
                    height:
                      `${barHeight}px`,
                    background:
                      riskColor,
                    borderRadius:
                      "8px 8px 0 0",
                    transition:
                      "height 0.4s ease",
                    boxShadow:
                      "0 2px 5px rgba(0,0,0,0.12)",
                  }}
                />


                <div
                  style={{
                    marginTop:
                      "8px",
                    textAlign:
                      "center",
                    fontSize:
                      "12px",
                    color:
                      "#475569",
                  }}
                >

                  📅 {day.date}

                </div>


                <div
                  style={{
                    marginTop:
                      "3px",
                    fontSize:
                      "11px",
                    fontWeight:
                      "700",
                    color:
                      riskColor,
                  }}
                >

                  {day.risk_level}

                </div>

              </div>

            );

          }
        )}

      </div>


      {/* ==================================================
          RISK LEVEL GUIDE
      ================================================== */}

      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "12px",
          marginTop: "16px",
          fontSize: "12px",
        }}
      >

        <span>
          🟢 Green: 0–24.99
        </span>

        <span>
          🟡 Yellow: 25–49.99
        </span>

        <span>
          🟠 Orange: 50–74.99
        </span>

        <span>
          🔴 Red: 75–100
        </span>

      </div>


      <p
        style={{
          marginBottom: 0,
          marginTop: "12px",
          fontSize: "12px",
          color: "#64748b",
        }}
      >

        Higher bars indicate higher predicted
        landslide risk.

      </p>

    </div>

  );

}


// ============================================================
// FUTURE RAINFALL + RISK FORECAST COMPONENT
// ============================================================

function RainfallForecast({
  forecastData,
  forecastLoading,
  forecastRiskData,
  forecastRiskLoading
}) {

  // ==========================================================
  // RAINFALL LOADING
  // ==========================================================

  if (forecastLoading) {

    return (

      <div className="forecast-card">

        <h3>
          🌧️ Future Rainfall Forecast
        </h3>

        <p>
          Fetching 3-day rainfall forecast...
        </p>

      </div>

    );

  }


  // ==========================================================
  // NO FORECAST
  // ==========================================================

  if (!forecastData) {

    return (

      <div className="forecast-card">

        <h3>
          🌧️ Future Rainfall & Landslide Risk Forecast
        </h3>

        <p>
          Click a location on the map to view
          the place name, 3-day rainfall and AI risk forecast.
        </p>

      </div>

    );

  }


  const times =
    forecastData.hourly?.time || [];


  const precipitation =
    forecastData.hourly?.precipitation_mm || [];


  // ==========================================================
  // CALCULATE DAILY TOTALS
  // ==========================================================

  const dailyTotals = {};


  times.forEach((time, index) => {

    const date =
      time.substring(0, 10);


    const rainfall =
      Number(
        precipitation[index] ?? 0
      );


    if (!dailyTotals[date]) {

      dailyTotals[date] = 0;

    }


    dailyTotals[date] += rainfall;

  });


  const dailyForecast =
    Object.entries(dailyTotals);


  // ==========================================================
  // NEXT 24 / 48 / 72 HOURS
  // ==========================================================

  const next24 =
    precipitation
      .slice(0, 24)
      .reduce(
        (sum, value) =>
          sum + Number(value || 0),
        0
      );


  const next48 =
    precipitation
      .slice(0, 48)
      .reduce(
        (sum, value) =>
          sum + Number(value || 0),
        0
      );


  const next72 =
    precipitation
      .slice(0, 72)
      .reduce(
        (sum, value) =>
          sum + Number(value || 0),
        0
      );


  const maxHourly =
    precipitation.length > 0
      ? Math.max(
          ...precipitation.map(
            (value) =>
              Number(value || 0)
          )
        )
      : 0;


  // ==========================================================
  // RISK COLOR HELPER
  // ==========================================================

  const getRiskColor = (score) => {

    const numericScore =
      Number(score || 0);


    if (numericScore >= 75) {
      return "#dc2626";
    }

    if (numericScore >= 50) {
      return "#ea580c";
    }

    if (numericScore >= 25) {
      return "#ca8a04";
    }

    return "#16a34a";

  };


  const getRiskBackground = (score) => {

    const numericScore =
      Number(score || 0);


    if (numericScore >= 75) {
      return "#fee2e2";
    }

    if (numericScore >= 50) {
      return "#ffedd5";
    }

    if (numericScore >= 25) {
      return "#fef9c3";
    }

    return "#dcfce7";

  };


  return (

    <div className="forecast-card">

      {/* ====================================================
          HEADER
      ==================================================== */}

      <div className="forecast-header">

        <div>

          <h3>
            🌧️ Future Rainfall & Landslide Risk Forecast
          </h3>

          <p>
            3-day rainfall forecast + Random Forest
            landslide risk prediction
          </p>

        </div>

        <span className="forecast-source">
          {forecastData.source}
        </span>

      </div>


      {/* ====================================================
          RAINFALL SUMMARY
      ==================================================== */}

      <div className="forecast-summary">

        <div className="forecast-summary-item">

          <span>
            Next 24 Hours
          </span>

          <strong>
            {next24.toFixed(1)} mm
          </strong>

        </div>


        <div className="forecast-summary-item">

          <span>
            Next 48 Hours
          </span>

          <strong>
            {next48.toFixed(1)} mm
          </strong>

        </div>


        <div className="forecast-summary-item">

          <span>
            Next 72 Hours
          </span>

          <strong>
            {next72.toFixed(1)} mm
          </strong>

        </div>


        <div className="forecast-summary-item">

          <span>
            Max / Hour
          </span>

          <strong>
            {maxHourly.toFixed(1)} mm
          </strong>

        </div>

      </div>


      {/* ====================================================
          AI 3-DAY RISK FORECAST
      ==================================================== */}

      <h4 className="forecast-section-title">

        🤖 3-Day AI Landslide Risk Forecast

      </h4>


      {forecastRiskLoading && (

        <div
          style={{
            padding: "18px",
            textAlign: "center",
            background: "#f8fafc",
            borderRadius: "10px",
            marginBottom: "20px",
          }}
        >

          <p>
            🤖 Calculating future landslide risk...
          </p>

        </div>

      )}


      {!forecastRiskLoading &&
        forecastRiskData &&
        forecastRiskData.forecast_days && (

          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(180px, 1fr))",
              gap: "14px",
              marginBottom: "20px",
            }}
          >

            {forecastRiskData.forecast_days.map(
              (day) => {

                const score =
                  Number(
                    day.risk_score || 0
                  );


                const riskColor =
                  getRiskColor(score);


                const riskBackground =
                  getRiskBackground(score);


                return (

                  <div
                    key={day.date}
                    style={{
                      padding: "18px",
                      borderRadius: "12px",
                      border:
                        `2px solid ${riskColor}`,
                      background:
                        riskBackground,
                    }}
                  >

                    <div
                      style={{
                        fontWeight: "700",
                        fontSize: "16px",
                        marginBottom: "10px",
                      }}
                    >

                      📅 {day.date}

                    </div>


                    <div
                      style={{
                        marginBottom: "8px",
                      }}
                    >

                      🌧️ Rainfall

                      <strong
                        style={{
                          display: "block",
                          fontSize: "18px",
                          marginTop: "3px",
                        }}
                      >

                        {Number(
                          day.rainfall_mm || 0
                        ).toFixed(1)}{" "}
                        mm

                      </strong>

                    </div>


                    <div
                      style={{
                        marginBottom: "8px",
                      }}
                    >

                      🎯 Risk Score

                      <strong
                        style={{
                          display: "block",
                          fontSize: "22px",
                          color: riskColor,
                          marginTop: "3px",
                        }}
                      >

                        {score.toFixed(2)}/100

                      </strong>

                    </div>


                    <div
                      style={{
                        fontWeight: "700",
                        color: riskColor,
                        marginBottom: "8px",
                      }}
                    >

                      {day.risk_level === "Green" &&
                        "🟢 "}

                      {day.risk_level === "Yellow" &&
                        "🟡 "}

                      {day.risk_level === "Orange" &&
                        "🟠 "}

                      {day.risk_level === "Red" &&
                        "🔴 "}

                      {day.risk_level}

                    </div>


                    <div
                      style={{
                        fontSize: "13px",
                      }}
                    >

                      Landslide Probability:
                      {" "}

                      {(
                        Number(
                          day.landslide_probability || 0
                        ) * 100
                      ).toFixed(2)}%

                    </div>

                  </div>

                );

              }

            )}

          </div>

        )}


      {/* ====================================================
          3-DAY AI RISK TREND
      ==================================================== */}

      {!forecastRiskLoading &&
        forecastRiskData && (

          <RiskTrendChart
            forecastRiskData={
              forecastRiskData
            }
          />

        )}


      {/* ====================================================
          FORECAST MODEL SOURCE
      ==================================================== */}

      {forecastRiskData && (

        <p
          style={{
            fontSize: "12px",
            color: "#64748b",
            marginBottom: "20px",
          }}
        >

          🤖 Model:
          {" "}
          {forecastRiskData.source}

        </p>

      )}


      {/* ====================================================
          DAILY RAINFALL FORECAST
      ==================================================== */}

      <h4 className="forecast-section-title">

        Daily Rainfall Forecast

      </h4>


      <div className="daily-forecast">

        {dailyForecast.map(
          ([date, total]) => (

            <div
              className="daily-forecast-item"
              key={date}
            >

              <span>
                📅 {date}
              </span>

              <strong>
                {Number(total).toFixed(1)} mm
              </strong>

            </div>

          )
        )}

      </div>


      {/* ====================================================
          HOURLY FORECAST
      ==================================================== */}

      <h4 className="forecast-section-title">

        Hourly Rainfall Forecast

      </h4>


      <div className="hourly-forecast">

        {times.map(
          (time, index) => {

            const rainfall =
              Number(
                precipitation[index] || 0
              );


            return (

              <div
                className="hourly-forecast-item"
                key={time}
              >

                <span>
                  {time.replace("T", " ")}
                </span>

                <strong>
                  {rainfall.toFixed(1)} mm
                </strong>

              </div>

            );

          }
        )}

      </div>


      <p className="forecast-footer">

        📡 Source: Open-Meteo
        {" | "}
        Timezone: {forecastData.timezone}

      </p>

    </div>

  );

}


// ============================================================
// MAIN APP
// ============================================================

function App() {


  // ==========================================================
  // STATE
  // ==========================================================

  const [nerStates, setNerStates] =
    useState(null);


  const [landslides, setLandslides] =
    useState([]);


  const [loading, setLoading] =
    useState(true);


  const [formData, setFormData] =
    useState({

      latitude: "27.4728",

      longitude: "94.912",

      rainfall: "",

      soil_moisture: "",

      slope: "1.8",

      elevation: "110",

      historical_landslide: false,

    });


  const [riskResult, setRiskResult] =
    useState(null);


  const [placeName, setPlaceName] =
    useState(null);


  const [predictionLoading, setPredictionLoading] =
    useState(false);


  const [predictionError, setPredictionError] =
    useState(null);


  const [showHeatmap, setShowHeatmap] =
    useState(false);


  const predictAbortRef = useRef(null);


  const predictAtPoint = async (latitude, longitude, historical = false) => {
    predictAbortRef.current?.abort();
    const controller = new AbortController();
    predictAbortRef.current = controller;
    const { signal } = controller;

    setForecastData(null);
    setForecastRiskData(null);
    setRiskResult(null);
    setPlaceName(null);
    setPredictionError(null);
    setPredictionLoading(true);
    setForecastLoading(true);
    setForecastRiskLoading(true);

    setFormData((previous) => ({
      ...previous,
      latitude: Number(latitude).toFixed(6),
      longitude: Number(longitude).toFixed(6),
      historical_landslide: historical,
    }));

    try {
      resolvePlaceName(latitude, longitude, signal)
        .then((name) => {
          if (!signal.aborted && name) {
            setPlaceName(name);
          }
        })
        .catch(() => {});

      const data = await predictAtLocation({
        latitude,
        longitude,
        historical_landslide: historical,
        signal,
      });

      if (signal.aborted) return;

      const soilWetness = Number(
        data.environment?.soil_wetness_gwet_top ?? 0.95
      );

      setFormData((previous) => ({
        ...previous,
        elevation: data.environment?.elevation_m ?? 0,
        slope: data.environment?.slope_degrees ?? 1.8,
        rainfall: data.environment?.rainfall_mm_day ?? "",
        soil_moisture: soilWetness,
      }));

      setRiskResult(data);
      setForecastData(data.forecast_rainfall || null);
      setForecastRiskData(data.forecast_risk || null);
    } catch (error) {
      if (error?.name === "AbortError") return;
      console.error("Prediction error:", error);
      setForecastData(null);
      setForecastRiskData(null);
      setRiskResult(null);
      setPredictionError(
        error?.message ||
          "Prediction failed. Select a place in North Eastern India."
      );
    } finally {
      if (!signal.aborted) {
        setPredictionLoading(false);
        setForecastLoading(false);
        setForecastRiskLoading(false);
      }
    }
  };


  // ==========================================================
  // FORECAST STATE
  // ==========================================================

  const [forecastData, setForecastData] =
    useState(null);


  const [forecastLoading, setForecastLoading] =
    useState(false);


  // ==========================================================
  // FORECAST RISK STATE
  // ==========================================================

  const [forecastRiskData, setForecastRiskData] =
    useState(null);


  const [forecastRiskLoading, setForecastRiskLoading] =
    useState(false);


  const resultPanelRef = useRef(null);


  useEffect(() => {
    if (riskResult && resultPanelRef.current) {
      resultPanelRef.current.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    }
  }, [riskResult]);


  // ==========================================================
  // LOAD NER GEOJSON
  // ==========================================================

  useEffect(() => {

    fetch(
      "/NER_states.geojson"
    )

      .then((response) => {

        if (!response.ok) {

          throw new Error(
            "NER boundary file not found"
          );

        }

        return response.json();

      })

      .then((data) => {

        setNerStates(data);

      })

      .catch((error) => {

        console.error(
          "Failed to load NER boundary:",
          error
        );

      });

  }, []);


  // ==========================================================
  // LOAD HISTORICAL LANDSLIDES
  // ==========================================================

  useEffect(() => {

    Papa.parse(

      "/GSI_NER_landslide_clean.csv",

      {

        download: true,

        header: true,

        skipEmptyLines: true,


        complete: (results) => {
          const cleaned = results.data.filter((row) => {
            const lat = Number(row.latitude);
            const lon = Number(row.longitude);
            return Number.isFinite(lat) && Number.isFinite(lon);
          });

          console.log("Historical landslides loaded:", cleaned.length);
          setLandslides(cleaned);
          setLoading(false);
        },


        error: (error) => {

          console.error(
            "Failed to load landslide CSV:",
            error
          );


          setLoading(false);

        },

      }

    );

  }, []);


  // ==========================================================
  // FORM INPUT HANDLER
  // ==========================================================

  const handleChange = (event) => {

    const {
      name,
      value,
      type,
      checked,
    } = event.target;


    setFormData((previous) => ({

      ...previous,

      [name]:
        type === "checkbox"
          ? checked
          : value,

    }));

  };


  // ==========================================================
  // CALCULATE RISK (manual lat/lon entry)
  // ==========================================================

  const calculateRisk = async () => {

    const latitude = Number(formData.latitude);
    const longitude = Number(formData.longitude);

    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
      alert("Please enter a valid latitude and longitude.");
      return;
    }

    setPredictionLoading(true);
    setRiskResult(null);
    setPlaceName(null);
    setPredictionError(null);
    setForecastData(null);
    setForecastRiskData(null);
    setForecastLoading(true);
    setForecastRiskLoading(true);

    try {

      resolvePlaceName(latitude, longitude)
        .then((name) => {
          if (name) setPlaceName(name);
        })
        .catch(() => {});

      const data = await predictAtLocation({
        latitude,
        longitude,
        historical_landslide: formData.historical_landslide,
      });

      setFormData((previous) => ({
        ...previous,
        elevation: data.environment.elevation_m,
        slope: data.environment.slope_degrees,
        rainfall: data.environment.rainfall_mm_day,
        soil_moisture: data.environment.soil_wetness_gwet_top,
      }));

      setRiskResult(data);
      setForecastData(data.forecast_rainfall || null);
      setForecastRiskData(data.forecast_risk || null);

    } catch (error) {

      console.error("Risk calculation error:", error);
      const message =
        error?.message || "Unable to connect to the AI backend.";
      setPredictionError(message);
      setForecastData(null);
      setForecastRiskData(null);

    } finally {

      setPredictionLoading(false);
      setForecastLoading(false);
      setForecastRiskLoading(false);

    }

  };


  // ==========================================================
  // STATE BOUNDARY STYLE
  // ==========================================================

  const stateStyle = {
    color: "#2563eb",
    weight: 2,
    fillColor: "#60a5fa",
    fillOpacity: 0.12,
  };


  // ==========================================================
  // UI
  // ==========================================================

  return (

    <div className="app">


      {/* ====================================================
          HEADER
      ==================================================== */}

      <header className="header">

        <div>

          <h1>
            🌍 Landslide Digital Twin
          </h1>

          <p>
            AI-Based Landslide Risk Monitoring System
          </p>

        </div>


        <div className="status">

          <span className="status-dot"></span>

          System Online

        </div>

      </header>


      {/* ====================================================
          INTRO
      ==================================================== */}

      <section className="intro">

        <h2>
          North Eastern India
        </h2>

        <p>
          Intelligent landslide prediction,
          risk monitoring and early-warning platform.
        </p>

      </section>


      {/* ====================================================
          STATISTICS
      ==================================================== */}

      <section className="stats">


        <div className="stat-card">

          <h3>
            8
          </h3>

          <p>
            NER States
          </p>

        </div>


        <div className="stat-card">

          <h3>
            10,326
          </h3>

          <p>
            Historical Landslides
          </p>

        </div>


        <div className="stat-card">

          <h3>
            0–100
          </h3>

          <p>
            Risk Score
          </p>

        </div>


        <div className="stat-card">

          <h3>
            🤖
          </h3>

          <p>
            AI Prediction Engine
          </p>

        </div>


      </section>


      {/* ====================================================
          AI PREDICTION
      ==================================================== */}

      <section className="prediction-section">


        <div className="section-title">

          <h2>
            🤖 AI Risk Prediction
          </h2>

          <p>
            Enter latitude/longitude and calculate risk,
            or tap a place on the map for instant AI prediction.
          </p>

        </div>


        <div className="prediction-container">


          {/* ==================================================
              FORM
          ================================================== */}

          <div className="prediction-form">


            <div className="form-group">

              <label>
                Latitude
              </label>

              <input
                type="number"
                name="latitude"
                value={formData.latitude}
                onChange={handleChange}
                step="any"
              />

            </div>


            <div className="form-group">

              <label>
                Longitude
              </label>

              <input
                type="number"
                name="longitude"
                value={formData.longitude}
                onChange={handleChange}
                step="any"
              />

            </div>


            <div className="form-group">

              <label>
                Rainfall (mm/day) — Automatic
              </label>

              <input
                type="number"
                value={formData.rainfall}
                readOnly
                placeholder="Select location"
              />

            </div>


            <div className="form-group">

              <label>
                Soil Wetness (0–1) — Automatic
              </label>

              <input
                type="number"
                value={formData.soil_moisture}
                readOnly
                placeholder="Select location"
                step="0.01"
              />

            </div>


            <div className="form-group">

              <label>
                Slope (degrees) — Automatic
              </label>

              <input
                type="number"
                name="slope"
                value={formData.slope}
                readOnly
                step="any"
              />

            </div>


            <div className="form-group">

              <label>
                Elevation (meters) — Automatic
              </label>

              <input
                type="number"
                name="elevation"
                value={formData.elevation}
                readOnly
                step="any"
              />

            </div>


            <div className="checkbox-group">

              <input
                type="checkbox"
                name="historical_landslide"
                checked={
                  formData.historical_landslide
                }
                onChange={handleChange}
              />

              <label>
                Historical landslide nearby
              </label>

            </div>


            <p className="map-tap-hint">
              Enter latitude and longitude then click
              Calculate the Risk, or tap a place on the
              map below for instant AI prediction.
            </p>

            <button
              className="predict-button"
              onClick={calculateRisk}
              disabled={predictionLoading}
            >

              {predictionLoading

                ? "Fetching Data & Calculating..."

                : "Calculate the Risk"

              }

            </button>


          </div>


          {/* ==================================================
              RESULT
          ================================================== */}

          <div className="prediction-result" ref={resultPanelRef}>


            {predictionLoading && (

              <div className="result-placeholder">

                <div className="result-icon is-analyzing" aria-hidden="true">
                  🤖
                </div>

                <h3>
                  Analyzing Location...
                </h3>

                <p>
                  {placeName
                    ? `Getting AI risk for ${placeName}`
                    : "Resolving place name and predicting landslide risk..."}
                </p>

              </div>

            )}


            {!predictionLoading && !riskResult && (

              <div className="result-placeholder">

                <div className="result-icon">
                  🤖
                </div>

                <h3>
                  {predictionError
                    ? "Prediction unavailable"
                    : "AI Prediction Result"}
                </h3>

                <p>
                  {predictionError ||
                    "Enter lat/lon and click Calculate the Risk, or tap a place on the map."}
                </p>

              </div>

            )}


            {!predictionLoading && riskResult && (

              <div className="result-content">


                <h3>
                  AI Prediction Result
                </h3>


                {placeName && (

                  <div className="place-name-banner">

                    <span>
                      📍 Place
                    </span>

                    <strong>
                      {placeName}
                    </strong>

                  </div>

                )}


                <div className="risk-score">

                  <span>
                    Risk Score
                  </span>

                  <strong>

                    {
                      riskResult.prediction
                        .risk_score
                    }

                    /100

                  </strong>

                </div>


                <div className="risk-level">

                  <span>
                    Risk Level
                  </span>

                  <strong>

                    {
                      riskResult.prediction
                        .risk_level
                    }

                  </strong>

                </div>


                <div className="probability">

                  <span>
                    Landslide Probability
                  </span>

                  <strong>

                    {(
                      riskResult.prediction
                        .landslide_probability
                      * 100
                    ).toFixed(2)}%

                  </strong>

                </div>


                <div className="prediction-status">

                  <span>
                    AI Prediction
                  </span>

                  <strong>

                    {
                      riskResult.prediction
                        .ml_prediction === 1

                        ? "Landslide Risk"

                        : "No Landslide"

                    }

                  </strong>

                </div>


                <div className="environment-summary">

                  <h4>
                    Environmental Data
                  </h4>


                  <p>

                    🌧️ Rainfall:
                    {" "}

                    {
                      riskResult.environment
                        .rainfall_mm_day
                    }

                    {" "}mm/day

                  </p>


                  <p>

                    💧 Soil Wetness:
                    {" "}

                    {
                      riskResult.environment
                        .soil_wetness_gwet_top
                    }

                  </p>


                  <p>

                    ⛰️ Slope:
                    {" "}

                    {
                      riskResult.environment
                        .slope_degrees
                    }°

                  </p>


                  <p>

                    📏 Elevation:
                    {" "}

                    {
                      riskResult.environment
                        .elevation_m
                    } m

                  </p>

                  {riskResult.environment?.terrain_source &&
                    riskResult.environment.terrain_source !== "SRTM DEM" && (
                    <p>
                      Terrain used the nearest known slope because this map tile has no elevation file.
                    </p>
                  )}

                </div>


              </div>

            )}

          </div>

        </div>


        {/* ==================================================
            FUTURE RAINFALL + RISK FORECAST
        ================================================== */}

        <RainfallForecast
          forecastData={forecastData}
          forecastLoading={forecastLoading}
          forecastRiskData={forecastRiskData}
          forecastRiskLoading={forecastRiskLoading}
        />

        <DecisionCentre
          latitude={Number(formData.latitude)}
          longitude={Number(formData.longitude)}
          riskResult={riskResult}
          forecastData={forecastData}
          placeName={placeName}
        />

      </section>


      {/* ====================================================
          MAP
      ==================================================== */}

      <section className="map-section">


        <div className="section-title">

          <h2>
            📍 NER Risk Monitoring Map
          </h2>

          <p>
            Tap anywhere on the map to instantly see
            the place name and AI landslide risk.
          </p>

        </div>


        <div className="map-container">


          <MapContainer
            bounds={[
              [6.5, 68.0],
              [37.2, 97.5],
            ]}
            minZoom={5}
            maxZoom={12}
            maxBounds={[
              [5.8, 67.0],
              [37.8, 98.2],
            ]}
            maxBoundsViscosity={1}
            scrollWheelZoom={true}
            preferCanvas={true}
            style={{
              height: "600px",
              width: "100%",
            }}
          >
            <TileLayer
              attribution='&copy; OpenStreetMap contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              updateWhenZooming={false}
              updateWhenIdle={true}
              keepBuffer={2}
            />

            <MapClickHandler onPredict={predictAtPoint} />

            {nerStates && (
              <GeoJSON
                data={nerStates}
                style={stateStyle}
                interactive={false}
              />
            )}

            <AIRiskMarker
              formData={formData}
              riskResult={riskResult}
              placeName={placeName}
            />

            {!loading && (
              <HistoricalLandslidesLayer
                landslides={landslides}
                onSelect={(latitude, longitude) =>
                  predictAtPoint(latitude, longitude, true)
                }
              />
            )}

            <RiskHeatmapLayer active={showHeatmap} />
          </MapContainer>

        </div>


        {/* ====================================================
            MAP LEGEND
        ==================================================== */}

        <div className="map-legend">

          <span>
            🔴 Historical Landslide
          </span>

          <span>
            🔵 NER State Boundary
          </span>

          <span>
            🤖 AI Marker → Dynamic Risk Level
          </span>

          <span>
            🟠 Heatmap → Inventory susceptibility
          </span>

          <button
            type="button"
            className="heatmap-toggle"
            onClick={() => setShowHeatmap((current) => !current)}
          >
            {showHeatmap ? "Hide risk heatmap" : "Show risk heatmap"}
          </button>

        </div>


      </section>


      {/* ====================================================
          FOOTER
      ==================================================== */}

      <footer>

        <p>

          Intelligent Landslide Digital Twin
          | North Eastern India

        </p>

      </footer>


    </div>

  );

}


export default App;