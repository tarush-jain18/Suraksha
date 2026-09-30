import type { DashboardData } from "@/app/lib/dashboard";

interface Props {
  data: DashboardData;
}

export default function CurrentConditions({ data }: Props) {
  const { cyclone, current_conditions, location } = data;

  return (
    <section className="conditions-card card">
      <div className="section-heading">
        <h2>Current Conditions</h2>
        <p>
          {location.name}, {location.region} ·{" "}
          {cyclone.current_position.latitude.toFixed(2)}°N,{" "}
          {cyclone.current_position.longitude.toFixed(2)}°E
        </p>
      </div>

      <div className="condition-grid">
        <div className="condition">
          <span className="condition-icon">💨</span>
          <div>
            <span>Wind Speed</span>
            <strong>{current_conditions.wind_kmph} km/h</strong>
          </div>
        </div>

        <div className="condition">
          <span className="condition-icon">🌧</span>
          <div>
            <span>Rainfall</span>
            <strong>{current_conditions.rainfall_mm.toFixed(0)} mm</strong>
          </div>
        </div>

        <div className="condition">
          <span className="condition-icon">◉</span>
          <div>
            <span>Central Pressure</span>
            <strong>{current_conditions.pressure_hpa} hPa</strong>
          </div>
        </div>

        <div className="condition">
          <span className="condition-icon">➤</span>
          <div>
            <span>Distance from Coast</span>
            <strong>{location.distance_from_coast_km.toFixed(1)} km</strong>
          </div>
        </div>

        <div className="condition">
          <span className="condition-icon">⌁</span>
          <div>
            <span>Elevation</span>
            <strong>{location.elevation_m} m</strong>
          </div>
        </div>

        <div className="condition">
          <span className="condition-icon">📍</span>
          <div>
            <span>Target Location</span>
            <strong>{location.name}</strong>
          </div>
        </div>
      </div>
    </section>
  );
}
