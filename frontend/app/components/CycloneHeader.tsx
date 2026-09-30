import type { DashboardData } from "@/app/lib/dashboard";

interface Props {
  data: DashboardData;
}

export default function CycloneHeader({ data }: Props) {
  const { cyclone, current_conditions, risk, location } = data;

  return (
    <section className="cyclone-header card">
      <div className="cyclone-symbol">🌪️</div>

      <div className="cyclone-title">
        <span className="active-badge">ACTIVE CYCLONE</span>
        <h1>{cyclone.id}</h1>
        <p>
          {cyclone.name} · {location.name}, {location.region}
        </p>
      </div>

      <div className="cyclone-stats">
        <div>
          <span>Current Status</span>
          <strong className="watch">
            <i />
            {risk.level}
          </strong>
        </div>

        <div>
          <span>Category</span>
          <strong>{cyclone.category}</strong>
        </div>

        <div>
          <span>Current Wind</span>
          <strong>{current_conditions.wind_kmph} km/h</strong>
        </div>

        <div>
          <span>Pressure</span>
          <strong>{current_conditions.pressure_hpa} hPa</strong>
        </div>

        <div>
          <span>Peak Wind</span>
          <strong>{cyclone.max_wind_kmph} km/h</strong>
        </div>
      </div>
    </section>
  );
}
