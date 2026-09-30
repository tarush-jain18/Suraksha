import Sidebar from "@/app/components/Sidebar";
import Topbar from "@/app/components/Topbar";

import {
  getDashboardData,
  getPeakForecastPoint,
  getCurrentForecastPoint,
} from "@/app/lib/dashboard";


export default function RiskAnalysisPage() {
  const data = getDashboardData();

  const current = getCurrentForecastPoint(data);
  const peak = getPeakForecastPoint(data);

  const hazards = data.hazards;
  const vulnerability = data.vulnerability;
  const exposure = data.exposure;
  const earlyWarning = data.early_warning;


  /* =========================================================
     HELPERS
  ========================================================= */

  const percentage = (value: number) =>
    `${(value * 100).toFixed(1)}%`;


  const riskColor = (level?: string) => {
    switch (level?.toUpperCase()) {
      case "HIGH":
        return "#ff625d";

      case "MODERATE":
        return "#f4b942";

      case "WATCH":
        return "#12c7ed";

      case "EMERGENCY":
        return "#ff3b30";

      case "LOW":
        return "#5cc8a1";

      default:
        return "#8ca6b8";
    }
  };


  /* =========================================================
     PEAK COMPATIBILITY
  ========================================================= */

const peakRiskPercentage =
  peak?.risk_percentage ?? 0;

const peakRiskLevel =
  peak?.risk_level ?? "UNKNOWN";

const peakRiskScore =
  peak?.risk_score ?? 0;


  const riskLevel =
    data.risk.level?.toUpperCase() ?? "UNKNOWN";


  /* =========================================================
     HAZARDS
  ========================================================= */

  const hazardItems = [
    {
      name: "Wind Intensity",
      value: hazards.wind,
      description:
        "Cyclone wind hazard at the selected location.",
      icon: "🌪️",
    },

    {
      name: "Rainfall",
      value: hazards.rainfall,
      description:
        "Rainfall-related hazard contribution.",
      icon: "🌧️",
    },

    {
      name: "Storm Surge",
      value: hazards.storm_surge,
      description:
        "Coastal surge hazard based on location exposure.",
      icon: "🌊",
    },

    {
      name: "Flooding",
      value: hazards.flood,
      description:
        "Combined rainfall, surge and elevation contribution.",
      icon: "🏞️",
    },
  ];


  /* =========================================================
     VULNERABILITY
  ========================================================= */

  const vulnerabilityItems = [
    {
      name: "Population",
      value: vulnerability.population,
      icon: "👥",
    },

    {
      name: "Infrastructure",
      value: vulnerability.infrastructure,
      icon: "🏗️",
    },

    {
      name: "Agriculture",
      value: vulnerability.agriculture,
      icon: "🌾",
    },

    {
      name: "Healthcare",
      value: vulnerability.healthcare,
      icon: "🏥",
    },
  ];


  /* =========================================================
     FORECAST
  ========================================================= */

  const forecastPoints = [
    ...(data.forecast?.observed ?? []),
    ...(data.forecast?.projected ?? []),
  ];


  return (
    <div className="app">

      {/* =====================================================
          SIDEBAR
      ===================================================== */}

      <Sidebar />


      {/* =====================================================
          MAIN APPLICATION AREA
      ===================================================== */}

      <div className="main">

        <Topbar />

        <div className="content">
        {/* ===================================================
            PAGE
        =================================================== */}

        <main className="risk-analysis-page">

          {/* =================================================
              HEADER
          ================================================= */}

          <div className="risk-page-header">

            <h1>
              Risk Analysis
            </h1>

            <p>
              Analyze hazard, vulnerability, exposure
              and projected cyclone risk.
            </p>

          </div>


          {/* =================================================
              TOP SUMMARY
          ================================================= */}

          <div className="risk-summary-grid">

            {/* CURRENT RISK */}

            <div className="risk-analysis-card">

              <span className="risk-card-label">
                CURRENT RISK
              </span>

              <strong
                style={{
                  color: riskColor(riskLevel),
                }}
              >
                {data.risk.percentage.toFixed(1)}%
              </strong>

              <small>
                {riskLevel}
              </small>

            </div>


            {/* PEAK RISK */}

            <div className="risk-analysis-card">

              <span className="risk-card-label">
                PEAK FORECAST
              </span>

              <strong
                style={{
                  color: riskColor(
                    peakRiskLevel
                  ),
                }}
              >
                {peak
                  ? peakRiskPercentage.toFixed(1)
                  : "—"}
                %
              </strong>

              <small>
                {peakRiskLevel}

                {peak &&
                "forecast_type" in peak &&
                peak.forecast_type
                  ? ` · ${peak.forecast_type.toUpperCase()}`
                  : ""}
              </small>

            </div>


            {/* COMBINED HAZARD */}

            <div className="risk-analysis-card">

              <span className="risk-card-label">
                COMBINED HAZARD
              </span>

              <strong>
                {percentage(
                  hazards.combined
                )}
              </strong>

              <small>
                Physical hazard index
              </small>

            </div>


            {/* TARGET */}

            <div className="risk-analysis-card">

              <span className="risk-card-label">
                IMPACT TARGET
              </span>

              <strong
                className="target-value"
              >
                {data.location.name}
              </strong>

              <small>
                {data.location.region}
              </small>

            </div>

          </div>


          {/* =================================================
              RISK PROGRESSION + EARLY WARNING
          ================================================= */}

          <div className="risk-two-column">

            {/* RISK PROGRESSION */}

            <section className="risk-analysis-panel">

              <div className="panel-heading">

                <div>

                  <h2>
                    Risk Progression
                  </h2>

                  <p>
                    Current and projected risk at the
                    selected impact location.
                  </p>

                </div>

                <span className="panel-badge">
                  BACKEND MODEL
                </span>

              </div>


              <div className="risk-chart">

                {forecastPoints.map(
                  (point, index) => {

                    const value =
                      point.risk.percentage;

                    const height =
                      Math.max(
                        12,
                        Math.min(
                          100,
                          value * 2.1
                        )
                      );

                    const isCurrent =
                      index ===
                      data.forecast.observed.length - 1;


                    return (
                      <div
                        key={`${point.timestamp}-${index}`}
                        className="risk-bar-column"
                      >

                        <span
                          className="risk-bar-value"
                          style={{
                            color: isCurrent
                              ? "#12c7ed"
                              : "#a5b9c6",
                          }}
                        >
                          {value.toFixed(1)}%
                        </span>


                        <div
                          className="risk-bar"
                          style={{
                            height:
                              `${height}%`,

                            background:
                              isCurrent
                                ? "#12c7ed"
                                : value >= 40
                                ? "#ff625d"
                                : "#c99d3d",

                            opacity:
                              isCurrent
                                ? 1
                                : 0.85,
                          }}
                        />


                        <span className="risk-bar-label">

                          {point.hours_ahead === 0
                            ? "Now"
                            : point.hours_ahead !== undefined
                            ? `+${point.hours_ahead}h`
                            : "—"}

                        </span>

                      </div>
                    );
                  }
                )}

              </div>

            </section>


            {/* EARLY WARNING */}

            <section className="risk-analysis-panel">

              <div className="panel-heading">

                <div>

                  <h2>
                    Early Warning
                  </h2>

                  <p>
                    Operational warning state.
                  </p>

                </div>

              </div>


              <div className="warning-box">

                <div className="warning-header">

                  <span>
                    WARNING LEVEL
                  </span>

                  <strong
                    style={{
                      color: riskColor(
                        earlyWarning?.warning_level ??
                        riskLevel
                      ),
                    }}
                  >
                    {earlyWarning?.warning_level ??
                      riskLevel}
                  </strong>

                </div>


                <div className="warning-grid">

                  <div>

                    <small>
                      Current
                    </small>

                    <strong>
                      {(
                        (earlyWarning?.current_risk ??
                          data.risk.score) *
                        100
                      ).toFixed(1)}
                      %
                    </strong>

                  </div>


                  <div>

                    <small>
                      Projected
                    </small>

                    <strong>
                      {(
                        (earlyWarning?.projected_risk ??
                          peakRiskScore ??
                          data.risk.score) *
                        100
                      ).toFixed(1)}
                      %
                    </strong>

                  </div>

                </div>


                {earlyWarning?.lead_time_hours !==
                  undefined && (

                  <div className="lead-time">

                    <small>
                      Lead Time
                    </small>

                    <strong>
                      {earlyWarning.lead_time_hours}
                      {" "}
                      hours
                    </strong>

                  </div>

                )}

              </div>

            </section>

          </div>


          {/* =================================================
              HAZARD + VULNERABILITY
          ================================================= */}

          <div className="risk-two-column">

            {/* HAZARDS */}

            <section className="risk-analysis-panel">

              <div className="panel-heading">

                <div>

                  <h2>
                    Hazard Assessment
                  </h2>

                  <p>
                    Physical hazards contributing to
                    the current risk.
                  </p>

                </div>

                <span className="panel-badge">
                  HAZARDS
                </span>

              </div>


              <div className="hazard-list">

                {hazardItems.map(
                  (item) => {

                    const value =
                      item.value * 100;


                    return (
                      <div
                        key={item.name}
                        className="hazard-item"
                      >

                        <div className="hazard-title">

                          <span>
                            {item.icon}{" "}
                            {item.name}
                          </span>

                          <strong>
                            {value.toFixed(1)}%
                          </strong>

                        </div>


                        <div className="risk-progress-track">

                          <div
                            className="risk-progress-fill"
                            style={{
                              width:
                                `${Math.min(
                                  100,
                                  value
                                )}%`,

                              background:
                                value >= 80
                                  ? "#ff625d"
                                  : value >= 50
                                  ? "#f4b942"
                                  : "#12c7ed",
                            }}
                          />

                        </div>


                        <small>
                          {item.description}
                        </small>

                      </div>
                    );
                  }
                )}

              </div>

            </section>


            {/* VULNERABILITY */}

            <section className="risk-analysis-panel">

              <div className="panel-heading">

                <div>

                  <h2>
                    Vulnerability
                  </h2>

                  <p>
                    Susceptibility of exposed systems
                    and communities.
                  </p>

                </div>

                <span className="panel-badge">
                  EXPOSURE
                </span>

              </div>


              <div className="vulnerability-grid">

                {vulnerabilityItems.map(
                  (item) => (

                    <div
                      key={item.name}
                      className="vulnerability-card"
                    >

                      <span className="vulnerability-icon">
                        {item.icon}
                      </span>

                      <small>
                        {item.name}
                      </small>

                      <strong>
                        {percentage(
                          item.value
                        )}
                      </strong>

                    </div>

                  )
                )}

              </div>


              <div className="combined-vulnerability">

                <small>
                  Combined vulnerability
                </small>

                <strong>
                  {percentage(
                    vulnerability.combined
                  )}
                </strong>

              </div>

            </section>

          </div>


          {/* =================================================
              EXPOSURE + RISK DRIVERS
          ================================================= */}

          <div className="risk-two-column">

            {/* EXPOSURE */}

            <section className="risk-analysis-panel">

              <div className="panel-heading">

                <div>

                  <h2>
                    Exposure
                  </h2>

                  <p>
                    Assets and population located within
                    the selected impact area.
                  </p>

                </div>

              </div>


              <div className="exposure-grid">

                <div className="exposure-stat">

                  <small>
                    Population
                  </small>

                  <strong>
                    {exposure.population_density.toFixed(1)}
                  </strong>

                  <span>
                    / km²
                  </span>

                </div>


                <div className="exposure-stat">

                  <small>
                    Infrastructure
                  </small>

                  <strong>
                    {exposure.infrastructure_density.toFixed(1)}
                  </strong>

                  <span>
                    density
                  </span>

                </div>


                <div className="exposure-stat">

                  <small>
                    Agriculture
                  </small>

                  <strong>
                    {exposure.agriculture_percentage.toFixed(1)}%
                  </strong>

                  <span>
                    area
                  </span>

                </div>

              </div>


              <div className="combined-exposure">

                <small>
                  Combined exposure score
                </small>

                <strong>
                  {percentage(
                    exposure.score
                  )}
                </strong>

              </div>

            </section>


            {/* RISK DRIVERS */}

            <section className="risk-analysis-panel">

              <div className="panel-heading">

                <div>

                  <h2>
                    Risk Drivers
                  </h2>

                  <p>
                    Factors currently contributing to
                    the backend risk assessment.
                  </p>

                </div>

                <span className="panel-badge">
                  {data.risk.drivers.length}
                  {" "}
                  FACTORS
                </span>

              </div>


              <div className="drivers-list">

                {data.risk.drivers.map(
                  (driver, index) => (

                    <div
                      key={`${driver}-${index}`}
                      className="driver-item"
                    >

                      <span>
                        {index + 1}
                      </span>

                      <strong>
                        {driver}
                      </strong>

                    </div>

                  )
                )}

              </div>

            </section>

          </div>

        </main>

      </div>
</div>
    </div>
  );
}