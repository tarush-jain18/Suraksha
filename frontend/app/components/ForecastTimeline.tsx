"use client";

import type { DashboardData, ForecastPoint } from "@/app/lib/dashboard";

interface Props {
  data: DashboardData;
}

export default function ForecastTimeline({ data }: Props) {
  // Safety check so the dashboard doesn't crash while data is loading.
  if (!data) {
    return (
      <section className="forecast-section card">
        <div className="forecast-title">
          <span>◷</span>

          <div>
            <h2>Forecast Timeline</h2>
            <p>Loading forecast data...</p>
          </div>
        </div>
      </section>
    );
  }

  const observed: ForecastPoint[] =
    data.forecast?.observed ?? [];

  const projected: ForecastPoint[] =
    data.forecast?.projected ?? [];

  /*
   * We don't want all 10 points displayed as a huge timeline.
   *
   * The dashboard should show:
   *
   * Current
   * +6 hours
   * +12 hours
   * +18 hours
   * +24 hours
   * +30 hours
   * +36 hours
   *
   * The latest observed point represents the current cyclone state.
   */
  const current =
    observed.length > 0
      ? observed[observed.length - 1]
      : null;

  const points: ForecastPoint[] = current
    ? [current, ...projected]
    : projected;

  return (
    <section className="forecast-section card">
      {/* Header */}
      <div className="forecast-title">
        <span>◷</span>

        <div>
          <h2>Forecast Timeline</h2>

          <p>
            Observed and projected cyclone impact at the selected
            location
          </p>
        </div>
      </div>

      {/* Timeline line */}
      {points.length > 0 && (
        <div className="timeline-line">
          {points.map((point, index) => (
            <span
              key={`${point.timestamp}-${index}`}
              className={index === 0 ? "current-dot" : ""}
            />
          ))}
        </div>
      )}

      {/* Forecast cards */}
      <div
        className="forecast-grid"
        style={{
          gridTemplateColumns: `repeat(
            ${Math.max(points.length, 1)},
            minmax(150px, 1fr)
          )`,
        }}
      >
        {points.map((point, index) => {
          const isCurrent = index === 0;

          const hoursAhead = Number(
            point.hours_ahead ?? 0
          );

          const wind = Number(
            point.wind_kmph ?? 0
          );

          const pressure = Number(
            point.pressure_hpa ?? 0
          );

          const riskPercentage = Number(
            point.risk?.percentage ?? 0
          );

          return (
            <div
              className={`forecast-card ${
                isCurrent ? "selected" : ""
              }`}
              key={`${point.timestamp}-${index}`}
            >
              {/* Time */}
              <strong>
                {isCurrent
                  ? "Current"
                  : `+${hoursAhead} hours`}
              </strong>

              {/* Timestamp */}
              <small>
                {new Date(
                  point.timestamp
                ).toLocaleString([], {
                  day: "2-digit",
                  month: "short",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </small>

              {/* Status */}
              <div className="forecast-status">
                <span>
                  {isCurrent
                    ? "OBSERVED"
                    : "PROJECTED"}
                </span>
              </div>

              {/* Wind */}
              <div>
                <span>💨</span>
                <b>{wind.toFixed(0)} km/h</b>
              </div>

              {/* Pressure */}
              <div>
                <span>◉</span>
                <b>{pressure.toFixed(0)} hPa</b>
              </div>

              {/* Risk */}
              <div>
                <span>⚠</span>
                <b>{riskPercentage.toFixed(1)}%</b>
              </div>
            </div>
          );
        })}
      </div>

      {/* Empty state */}
      {points.length === 0 && (
        <div className="forecast-empty">
          No forecast data available.
        </div>
      )}
    </section>
  );
}