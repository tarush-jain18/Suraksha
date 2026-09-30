import type { DashboardData } from "@/app/lib/dashboard";

interface Props {
  data: DashboardData;
}

function level(value: number): [string, string] {
  if (value >= 0.8) return ["High", "high"];
  if (value >= 0.5) return ["Medium", "medium"];
  return ["Low", "low"];
}

export default function RiskDrivers({ data }: Props) {
  const hazards = data.hazards;

  const drivers = [
    ["Wind Intensity", hazards.wind],
    ["Rainfall", hazards.rainfall],
    ["Storm Surge", hazards.storm_surge],
    ["Flooding", hazards.flood],
  ] as const;

  return (
    <section className="card bottom-card">
      <div className="section-title-row">
        <h2>Risk Drivers</h2>
        <span className="risk-subtitle">Backend hazard assessment</span>
      </div>

      <div className="drivers">
        {drivers.map(([label, raw]) => {
          const value = Math.max(0, Math.min(1, Number(raw)));
          const [name, type] = level(value);

          return (
            <div className="driver" key={label}>
              <span>{label}</span>
              <div className="driver-bar">
                <i
                  className={type}
                  style={{ width: `${Math.round(value * 100)}%` }}
                />
              </div>
              <strong className={type}>
                {name}
              </strong>
            </div>
          );
        })}
      </div>
    </section>
  );
}
