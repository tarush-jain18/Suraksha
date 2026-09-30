import type { DashboardData } from "@/app/lib/dashboard";

interface Props {
  data: DashboardData;
}

export default function RiskCard({ data }: Props) {
  const { risk } = data;
  const percentage = Number(risk.percentage ?? 0);

  return (
    <section className="risk-card card">
      <div className="section-title-row">
        <div>
          <h2>Risk Assessment</h2>
          <span className="risk-subtitle">
            Backend risk at selected location
          </span>
        </div>
      </div>

      <div className="risk-content">
        <div
          className="risk-ring"
          style={{
            background: `conic-gradient(
              #e6a92e ${percentage}%,
              #1a3444 ${percentage}%
            )`,
          }}
        >
          <div>
            <strong>{percentage.toFixed(1)}%</strong>
          </div>
        </div>

        <div>
          <div className="risk-badge">
            <i />
            {risk.level}
          </div>

          <p>{risk.drivers?.join(", ") || "No drivers reported."}.</p>
        </div>
      </div>
    </section>
  );
}
