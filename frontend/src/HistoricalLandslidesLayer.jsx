import { useEffect, useRef } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";

/**
 * Renders ~10k historical landslide points with Leaflet's canvas renderer.
 * Built once outside React's render tree so pan/zoom/state updates stay fast.
 */
export default function HistoricalLandslidesLayer({ landslides, onSelect }) {
  const map = useMap();
  const groupRef = useRef(null);
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;

  useEffect(() => {
    if (!map || !landslides?.length) return;

    const renderer = L.canvas({ padding: 0.5 });
    const group = L.layerGroup();
    const hoverTip = L.tooltip({
      direction: "top",
      offset: [0, -8],
      opacity: 1,
      className: "historical-hover-tip",
    });

    const detail = (label, value) =>
      `<p><strong>${label}:</strong> ${value || "N/A"}</p>`;

    for (let i = 0; i < landslides.length; i++) {
      const row = landslides[i];
      const lat = Number(row.latitude);
      const lon = Number(row.longitude);

      if (!Number.isFinite(lat) || !Number.isFinite(lon)) continue;

      const marker = L.circleMarker([lat, lon], {
        radius: 4,
        color: "#dc2626",
        fillColor: "#ef4444",
        fillOpacity: 0.85,
        weight: 1,
        renderer,
        bubblingMouseEvents: false,
        className: "historical-landslide-marker",
      });

      const html = `
        <div class="historical-hover-card">
          <h3>Historical Landslide</h3>
          ${detail("State", row.state)}
          ${detail("District", row.district)}
          ${detail("Year", row.event_year)}
          ${detail("Movement", row.movement_type_clean)}
          ${detail("Latitude", lat.toFixed(5))}
          ${detail("Longitude", lon.toFixed(5))}
          <p class="historical-hover-hint">Click for AI risk prediction</p>
        </div>
      `;

      marker.on("mouseover", () => {
        hoverTip.setLatLng([lat, lon]).setContent(html).openOn(map);
      });

      marker.on("mouseout", () => {
        map.closeTooltip(hoverTip);
      });

      marker.on("click", (event) => {
        map.closeTooltip(hoverTip);
        L.DomEvent.stop(event);
        event.originalEvent?.stopPropagation();
        onSelectRef.current?.(lat, lon);
      });

      group.addLayer(marker);
    }

    group.addTo(map);
    groupRef.current = group;

    return () => {
      map.removeLayer(group);
      groupRef.current = null;
    };
  }, [map, landslides]);

  return null;
}
