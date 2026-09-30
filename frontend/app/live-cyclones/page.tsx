import SectionPage from "../components/SectionPage";

export default function LiveCyclones() {
  return (
    <SectionPage
      title="Live Cyclones"
      subtitle="Monitor active cyclone systems and their latest conditions."
    >
      <div className="dashboard-card">
        <div className="card-header">
          <div>
            <span className="eyebrow">ACTIVE SYSTEM</span>
            <h2>CY001 — Demo Cyclone</h2>
          </div>

          <span className="status-badge">ACTIVE</span>
        </div>

        <div className="stats-grid">
          <div>
            <span>Category</span>
            <strong>Very Severe Cyclonic Storm</strong>
          </div>

          <div>
            <span>Wind</span>
            <strong>150 km/h</strong>
          </div>

          <div>
            <span>Pressure</span>
            <strong>950 hPa</strong>
          </div>

          <div>
            <span>Target</span>
            <strong>Puri, Odisha</strong>
          </div>
        </div>
      </div>
    </SectionPage>
  );
}