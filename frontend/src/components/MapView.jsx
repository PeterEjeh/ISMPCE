import { useState, useEffect } from "react";
import { MapContainer, TileLayer, CircleMarker, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import nigeriaStates from "../data/nigeriaStates";

function getColor(share) {
  if (share < 1.5) return "#22c55e";
  if (share < 3.0) return "#eab308";
  if (share < 5.0) return "#f97316";
  return "#ef4444";
}

function getRadius(share) {
  // share is a % of national; scale radius between 8 and 28
  return 8 + Math.min((share / 8) * 20, 20);
}

export default function MapView({ stateContributions }) {
  const [stateData, setStateData] = useState([]);

  useEffect(() => {
    if (!stateContributions || stateContributions.length === 0) return;

    // Merge map coordinates with contribution data
    const merged = nigeriaStates.map((s) => {
      const contrib = stateContributions.find(
        (c) => c.name.toLowerCase() === s.name.toLowerCase()
      );
      return {
        ...s,
        estimated_share: contrib ? contrib.estimated_share : 0,
        estimated_co2: contrib ? contrib.estimated_co2 : null,
        industrial_multiplier: contrib ? contrib.industrial_multiplier : 1.0,
      };
    });
    setStateData(merged);
  }, [stateContributions]);

  // Top 10 states by estimated share for the bar chart
  const top10 = [...(stateContributions || [])]
    .sort((a, b) => b.estimated_share - a.estimated_share)
    .slice(0, 10);

  const maxShare = top10.length > 0 ? top10[0].estimated_share : 1;

  return (
    <div className="card">
      <h2 className="card-title">Nigeria CO2 Emissions by State</h2>
      <p className="card-subtitle">
        Sub-national emission distribution based on empirical Climate TRACE satellite observations and industrial activity.
      </p>

      <div className="map-and-bar">
        {/* Leaflet Map */}
        <div className="map-container">
          <MapContainer
            center={[9.05, 7.49]}
            zoom={6}
            scrollWheelZoom={true}
            style={{ height: "100%", width: "100%", borderRadius: "8px" }}
          >
            {/* Watermark-free, clean dark map tiles */}
            <TileLayer
              attribution='&copy; <a href="https://www.esri.com/">Esri</a> &mdash; Esri, DeLorme, NAVTEQ'
              url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
              maxZoom={16}
            />
            <TileLayer
              attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
              url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}"
              maxZoom={16}
            />
            {stateData.map((state) => (
              <CircleMarker
                key={state.name}
                center={[state.lat, state.lng]}
                radius={getRadius(state.estimated_share)}
                pathOptions={{
                  color: getColor(state.estimated_share),
                  fillColor: getColor(state.estimated_share),
                  fillOpacity: 0.75,
                  weight: 1.5,
                }}
              >
                <Tooltip direction="top" opacity={1} className="custom-tooltip">
                  <div>
                    <strong>{state.name}</strong>
                    <br />
                    Est. Share: {state.estimated_share}%
                    {state.estimated_co2 != null && (
                      <>
                        <br />
                        Est. CO2: {state.estimated_co2} Mt
                      </>
                    )}
                    <br />
                    Zone: {state.zone}
                    <br />
                    Industrial factor: x{state.industrial_multiplier}
                  </div>
                </Tooltip>
              </CircleMarker>
            ))}
          </MapContainer>
        </div>

        {/* Bar Chart: Top 10 contributing states */}
        <div className="contribution-panel">
          <h3 className="contribution-title">Top 10 Contributing States</h3>
          <p className="contribution-note">Estimated share of national CO2</p>
          <div className="contribution-bars">
            {top10.map((state) => (
              <div key={state.name} className="contribution-bar-row">
                <span className="contribution-state-name">{state.name}</span>
                <div className="contribution-bar-track">
                  <div
                    className="contribution-bar-fill"
                    style={{
                      width: `${(state.estimated_share / maxShare) * 100}%`,
                      background: getColor(state.estimated_share),
                    }}
                  />
                </div>
                <span className="contribution-share-value">
                  {state.estimated_share}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="legend">
        <span className="legend-item">
          <span className="legend-dot" style={{ background: "#22c55e" }}></span>
          Low (&lt;1.5%)
        </span>
        <span className="legend-item">
          <span className="legend-dot" style={{ background: "#eab308" }}></span>
          Medium (1.5–3%)
        </span>
        <span className="legend-item">
          <span className="legend-dot" style={{ background: "#f97316" }}></span>
          High (3–5%)
        </span>
        <span className="legend-item">
          <span className="legend-dot" style={{ background: "#ef4444" }}></span>
          Very High (&gt;5%)
        </span>
      </div>
    </div>
  );
}
