import SectionPage from "../components/SectionPage";

export default function DataSources() {
  return (
    <SectionPage
      title="Data Sources"
      subtitle="View the datasets and services powering SURA RAKSHA."
    >
      <div className="source-grid">
        <div className="dashboard-card">
          <h2>Earth Engine</h2>
          <p>Rainfall, elevation and geospatial context.</p>
        </div>

        <div className="dashboard-card">
          <h2>OpenStreetMap</h2>
          <p>Infrastructure and geographic exposure data.</p>
        </div>

        <div className="dashboard-card">
          <h2>Historical Cyclones</h2>
          <p>Historical Odisha cyclone catalog and comparisons.</p>
        </div>

        <div className="dashboard-card">
          <h2>Cyclone Forecast Engine</h2>
          <p>Hazard, vulnerability and risk calculations.</p>
        </div>
      </div>
    </SectionPage>
  );
}