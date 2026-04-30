import { useEffect } from "react";
import { MapContainer, TileLayer, Polyline, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { SimulationResult } from "../../api/client";

interface FitBoundsProps {
  positions: [number, number][];
}

function FitBounds({ positions }: FitBoundsProps) {
  const map = useMap();
  useEffect(() => {
    if (positions.length > 1) {
      map.fitBounds(positions, { padding: [40, 40] });
    }
  }, [map, positions]);
  return null;
}

interface RouteMapProps {
  baseline?: SimulationResult;
  optimized?: SimulationResult;
}

export function RouteMap({ baseline, optimized }: RouteMapProps) {
  const defaultCenter: [number, number] = [39.5, -98.35];
  const defaultZoom = 4;

  const baselinePositions: [number, number][] = baseline
    ? baseline.lat.map((lat, i) => [lat, baseline.lon[i]])
    : [];

  const optimizedPositions: [number, number][] = optimized
    ? optimized.lat.map((lat, i) => [lat, optimized.lon[i]])
    : [];

  return (
    <MapContainer
      center={defaultCenter}
      zoom={defaultZoom}
      style={{ height: "100%", width: "100%" }}
      zoomControl={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {/* Baseline route — stone grey */}
      {baselinePositions.length > 0 && (
        <Polyline
          positions={baselinePositions}
          pathOptions={{ color: "#a09a8e", weight: 4, opacity: 0.7 }}
        />
      )}

      {/* Optimized route — forest green, overlaid */}
      {optimizedPositions.length > 0 && (
        <>
          <Polyline
            positions={optimizedPositions}
            pathOptions={{ color: "#1c5228", weight: 3, opacity: 0.9 }}
          />
          <FitBounds positions={optimizedPositions} />
        </>
      )}

      {!baseline && (
        <div className="leaflet-top leaflet-left" style={{ pointerEvents: "none" }}>
          <div style={{ margin: "16px", background: "white", padding: "10px 14px", borderRadius: "8px", border: "1px solid #e5e7eb", fontSize: "13px", color: "#6b7280" }}>
            Submit a route to see it here
          </div>
        </div>
      )}
    </MapContainer>
  );
}
