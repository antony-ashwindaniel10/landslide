import { useEffect, useRef } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";

const API_BASE = "http://127.0.0.1:8000";

function colorFor(score) {
  if (score >= 75) return "#dc2626";
  if (score >= 50) return "#ea580c";
  if (score >= 25) return "#ca8a04";
  return "#16a34a";
}

export default function RiskHeatmapLayer({ active }) {
  const map = useMap();
  const groupRef = useRef(null);

  useEffect(() => {
    if (!map || !active) {
      if (groupRef.current) {
        map.removeLayer(groupRef.current);
        groupRef.current = null;
      }
      return undefined;
    }

    const controller = new AbortController();
    const group = L.layerGroup();

    fetch(`${API_BASE}/heatmap`, { signal: controller.signal })
      .then((response) => response.json())
      .then((data) => {
        (data.cells || []).forEach((cell) => {
          const color = colorFor(cell.risk_score);
          const marker = L.circleMarker([cell.latitude, cell.longitude], {
            radius: 10,
            color,
            fillColor: color,
            fillOpacity: 0.35,
            weight: 1,
            bubblingMouseEvents: false,
          });
          marker.bindPopup(
            `<strong>${cell.risk_level} susceptibility</strong><br/>` +
              `Score ${cell.risk_score}/100<br/>` +
              `${cell.landslide_count} historical events<br/>` +
              `Mean slope ${cell.mean_slope}°`
          );
          group.addLayer(marker);
        });
        group.addTo(map);
        groupRef.current = group;
      })
      .catch(() => {});

    return () => {
      controller.abort();
      if (groupRef.current) {
        map.removeLayer(groupRef.current);
        groupRef.current = null;
      }
    };
  }, [map, active]);

  return null;
}
