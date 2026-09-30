import Sidebar from "@/app/components/Sidebar";
import Topbar from "@/app/components/Topbar";
import MapPanel from "@/app/components/MapPanel";

import { getDashboardData } from "@/app/lib/dashboard";

export default function ImpactMapPage() {
  const data = getDashboardData();

  const infrastructure = data.infrastructure?.summary;

  const map = data.map;

  return (
    <main className="app">
      <Sidebar />

      <div className="main">
        <Topbar />

        <div className="content impact-page">

          {/* HEADER */}
          <div className="impact-page-header">

            <div>
              <div className="eyebrow">
                GEOSPATIAL IMPACT ANALYSIS
              </div>

              <h1>Impact Map</h1>

              <p>
                Track cyclone movement, projected impact and
                exposed infrastructure around {data.location.name}.
              </p>
            </div>

            <div className="impact-status">
              <span className="status-dot" />

              <div>
                <strong>{data.cyclone.id}</strong>
                <span>
                  {data.risk.level} RISK
                </span>
              </div>
            </div>

          </div>


          {/* QUICK STATS */}
          <div className="impact-stats">

            <div className="impact-stat-card">
              <span className="impact-stat-icon">🌀</span>

              <div>
                <small>Current Wind</small>
                <strong>
                  {data.current_conditions.wind_kmph} km/h
                </strong>
              </div>
            </div>


            <div className="impact-stat-card">
              <span className="impact-stat-icon">⚠</span>

              <div>
                <small>Current Risk</small>
                <strong>
                  {data.risk.percentage.toFixed(1)}%
                </strong>
              </div>
            </div>


            <div className="impact-stat-card">
              <span className="impact-stat-icon">📍</span>

              <div>
                <small>Target</small>
                <strong>
                  {data.location.name}
                </strong>
              </div>
            </div>


            <div className="impact-stat-card">
              <span className="impact-stat-icon">🏗</span>

              <div>
                <small>Exposed Assets</small>
                <strong>
                  {infrastructure?.total_assets?.toLocaleString() ?? "—"}
                </strong>
              </div>
            </div>

          </div>


          {/* MAP */}
          <div className="impact-map-container">

            <MapPanel
              data={data}
            />

{/* MAP INFORMATION PANEL */}
<div
  className="impact-map-overlay"
  style={{
    top: "72px",
    left: "16px",
    right: "auto",
    zIndex: 1000,
  }}
>

  <div className="overlay-title">
    <span>MAP LAYERS</span>
  </div>

  <label>
    <span className="legend observed" />
    Observed Track
  </label>

  <label>
    <span className="legend projected" />
    Projected Track
  </label>

  <label>
    <span className="legend cyclone" />
    Current Cyclone
  </label>

  <label>
    <span className="legend target" />
    Target Location
  </label>

  <div className="overlay-divider" />

  <div className="map-location">

    <span>IMPACT TARGET</span>

    <strong>
      {data.location.name}
    </strong>

    <small>
      {data.location.latitude.toFixed(4)}°N,{" "}
      {data.location.longitude.toFixed(4)}°E
    </small>

  </div>

</div>

          </div>


          {/* BOTTOM ANALYSIS */}
          <div className="impact-analysis-grid">

            {/* INFRASTRUCTURE */}
            <section className="card impact-analysis-card">

              <div className="analysis-heading">
                <div>
                  <span className="eyebrow">
                    INFRASTRUCTURE EXPOSURE
                  </span>

                  <h2>
                    Exposed Assets
                  </h2>
                </div>

                <strong className="analysis-total">
                  {infrastructure?.total_assets?.toLocaleString() ?? "—"}
                </strong>
              </div>


              <div className="asset-grid">

                <div>
                  <span>Roads</span>
                  <strong>
                    {infrastructure?.roads ?? 0}
                  </strong>
                </div>

                <div>
                  <span>Bridges</span>
                  <strong>
                    {infrastructure?.bridges ?? 0}
                  </strong>
                </div>

                <div>
                  <span>Schools</span>
                  <strong>
                    {infrastructure?.schools ?? 0}
                  </strong>
                </div>

                <div>
                  <span>Healthcare</span>
                  <strong>
                    {infrastructure?.healthcare ?? 0}
                  </strong>
                </div>

                <div>
                  <span>Critical Buildings</span>
                  <strong>
                    {infrastructure?.critical_buildings ?? 0}
                  </strong>
                </div>

              </div>

            </section>


            {/* FORECAST */}
            <section className="card impact-analysis-card">

              <div className="analysis-heading">

                <div>
                  <span className="eyebrow">
                    PROJECTED IMPACT
                  </span>

                  <h2>
                    Cyclone Approach
                  </h2>
                </div>

                <span className="forecast-badge">
                  +36 HOURS
                </span>

              </div>


              {data.forecast?.peak && (

                <div className="peak-impact">

                  <div>
                    <span>Peak Risk</span>

                    <strong>
                      {data.forecast.peak.risk_percentage.toFixed(1)}%
                    </strong>
                  </div>


                  <div>
                    <span>Wind</span>

                    <strong>
                      {data.forecast.peak.wind_kmph} km/h
                    </strong>
                  </div>


                  <div>
                    <span>Pressure</span>

                    <strong>
                      {data.forecast.peak.pressure_hpa} hPa
                    </strong>
                  </div>

                </div>

              )}


              <div className="approach-message">

                <span>→</span>

                <p>
                  The projected cyclone track approaches{" "}
                  <strong>
                    {data.location.name}
                  </strong>{" "}
                  during the forecast period.
                </p>

              </div>

            </section>

          </div>

        </div>
      </div>
    </main>
  );
}