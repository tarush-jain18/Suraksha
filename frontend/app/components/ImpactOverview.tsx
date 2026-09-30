import { Building2, HeartPulse, Leaf, Users } from "lucide-react";
import type { DashboardData } from "@/app/lib/dashboard";

export default function ImpactOverview({ data }: { data: DashboardData }) {
  const exposure = data.exposure;
  const summary = data.infrastructure?.summary;
  const stats = [
    [Users, "Population Density", `${Number(exposure.population_density).toFixed(1)} / km²`],
    [Building2, "Infrastructure Assets", `${Number(summary?.total_assets ?? 0).toLocaleString()}`],
    [Leaf, "Agriculture Area", `${Number(exposure.agriculture_percentage).toFixed(1)}%`],
    [HeartPulse, "Healthcare Facilities", `${Number(summary?.healthcare ?? 0)}`],
  ] as const;
  return (
    <section className="card bottom-card">
      <h2>Impact Overview <span>({data.location.region})</span></h2>
      <div className="impact-grid">
        {stats.map(([Icon, label, value]) => <div className="impact-stat" key={label}><Icon /><div><span>{label}</span><strong>{value}</strong></div></div>)}
      </div>
    </section>
  );
}
