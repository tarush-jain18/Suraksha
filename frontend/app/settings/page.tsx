import SectionPage from "../components/SectionPage";

export default function Settings() {
  return (
    <SectionPage
      title="Settings"
      subtitle="Configure dashboard and monitoring preferences."
    >
      <div className="dashboard-card settings-list">
        <div>
          <div>
            <strong>Auto Refresh</strong>
            <p>Refresh cyclone monitoring data automatically.</p>
          </div>

          <input type="checkbox" defaultChecked />
        </div>

        <div>
          <div>
            <strong>Early Warning Notifications</strong>
            <p>Display operational warning notifications.</p>
          </div>

          <input type="checkbox" defaultChecked />
        </div>

        <div>
          <div>
            <strong>Infrastructure Layer</strong>
            <p>Show exposed infrastructure on the impact map.</p>
          </div>

          <input type="checkbox" defaultChecked />
        </div>
      </div>
    </SectionPage>
  );
}