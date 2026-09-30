import { AlertTriangle, Info } from "lucide-react";
import type { DashboardData } from "@/app/lib/dashboard";

interface Props {
  data: DashboardData;
}

export default function RecentAlerts({ data }: Props) {
  const alerts = Array.isArray(data.alerts) ? data.alerts : [];

  return (
    <section className="card bottom-card alerts-card">
      <div className="section-title-row">
        <h2>Recent Alerts</h2>
        <span className="risk-subtitle">{alerts.length} active</span>
      </div>

      {alerts.length === 0 ? (
        <div className="alert-item info">
          <Info size={22} />
          <div>
            <div className="alert-head">
              <strong>System Status</strong>
            </div>
            <p>
              Current risk: {data.risk.level} (
              {data.risk.percentage.toFixed(1)}%). Monitor official updates.
            </p>
          </div>
        </div>
      ) : (
        alerts.slice(0, 4).map((alert) => (
          <div
            className={`alert-item ${
              alert.level === "EMERGENCY" || alert.level === "HIGH"
                ? "warning"
                : "info"
            }`}
            key={alert.id}
          >
            {alert.level === "EMERGENCY" || alert.level === "HIGH" ? (
              <AlertTriangle size={22} />
            ) : (
              <Info size={22} />
            )}

            <div>
              <div className="alert-head">
                <strong>
                  {alert.level}: {alert.title}
                </strong>
              </div>
              <p>{alert.message}</p>
              {alert.action && (
                <span className="location-tag">{alert.action}</span>
              )}
            </div>
          </div>
        ))
      )}
    </section>
  );
}
