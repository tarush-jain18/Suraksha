import SectionPage from "../components/SectionPage";

export default function Documentation() {
  return (
    <SectionPage
      title="Documentation"
      subtitle="Understand how SURA RAKSHA generates cyclone impact forecasts."
    >
      <div className="source-grid">
        <div className="dashboard-card">
          <span className="eyebrow">PIPELINE</span>
          <h2>Hazard Engine</h2>
          <p>
            Calculates wind, rainfall, storm surge and flooding hazards.
          </p>
        </div>

        <div className="dashboard-card">
          <span className="eyebrow">RISK ENGINE</span>
          <h2>Risk Assessment</h2>
          <p>
            Combines hazard, exposure and vulnerability into a risk score.
          </p>
        </div>

        <div className="dashboard-card">
          <span className="eyebrow">FORECAST</span>
          <h2>Track Projection</h2>
          <p>
            Projects cyclone movement and risk at six-hour intervals.
          </p>
        </div>

        <div className="dashboard-card">
          <span className="eyebrow">WARNING</span>
          <h2>Early Warning</h2>
          <p>
            Detects risk escalation and prepares operational warnings.
          </p>
        </div>
      </div>
    </SectionPage>
  );
}