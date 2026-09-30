"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  Bell,
  Clock3,
  Database,
  FileText,
  Home,
  Map,
  MapPin,
  Radio,
  Sparkle,
  Settings,
  Wind,
} from "lucide-react";

const monitoringItems = [
  {
    label: "Dashboard",
    icon: Home,
    href: "/",
  },
  {
    label: "Live Cyclones",
    icon: Radio,
    href: "/live-cyclones",
  },
  {
    label: "Impact Map",
    icon: Map,
    href: "/impact-map",
  },
];

const analysisItems = [
  {
    label: "Gemini Advisory",
    icon: Sparkle,
    href: "/gemini-advisory",
  },
  {
    label: "Risk Analysis",
    icon: Activity,
    href: "/risk-analysis",
  },
  {
    label: "Historical Data",
    icon: Clock3,
    href: "/historical-data",
  },
  {
    label: "Alerts",
    icon: Bell,
    href: "/alerts",
  },
  {
    label: "Locations",
    icon: MapPin,
    href: "/locations",
  },
];

const systemItems = [
  {
    label: "Data Sources",
    icon: Database,
    href: "/data-sources",
  },
  {
    label: "Settings",
    icon: Settings,
    href: "/settings",
  },
  {
    label: "Documentation",
    icon: FileText,
    href: "/documentation",
  },
];

function NavItem({
  item,
}: {
  item: {
    label: string;
    icon: React.ElementType;
    href: string;
  };
}) {
  const pathname = usePathname();

  const active =
    item.href === "/"
      ? pathname === "/"
      : pathname.startsWith(item.href);

  const Icon = item.icon;

  return (
    <Link
      href={item.href}
      className={`sidebar-item ${
        active ? "sidebar-item-active" : ""
      }`}
    >
      <span className="sidebar-icon">
        <Icon size={19} strokeWidth={2} />
      </span>

      <span className="sidebar-label">
        {item.label}
      </span>

      {active && (
        <span className="sidebar-active-dot" />
      )}
    </Link>
  );
}

function Section({
  title,
  items,
}: {
  title: string;
  items: typeof monitoringItems;
}) {
  return (
    <div className="sidebar-section">
      <div className="sidebar-section-title">
        {title}
      </div>

      <div className="sidebar-items">
        {items.map((item) => (
          <NavItem
            key={item.href}
            item={item}
          />
        ))}
      </div>
    </div>
  );
}

export default function Sidebar() {
  return (
    <aside className="sidebar">

      {/* ================= BRAND ================= */}

      <div className="sidebar-brand">

        <div className="sidebar-logo">
          <Wind
            size={25}
            strokeWidth={2.3}
          />
        </div>

        <div className="sidebar-brand-text">
          <div className="sidebar-brand-name">
            SURAKSHA
          </div>

          <div className="sidebar-brand-subtitle">
            CYCLONE IMPACT FORECASTER
          </div>
        </div>

      </div>


      {/* ================= ACTIVE SYSTEM ================= */}

      <div className="monitor-status">

        <span className="monitor-pulse" />

        <div>
          <strong>Monitoring Active</strong>
          <span>Odisha Region</span>
        </div>

      </div>


      {/* ================= NAVIGATION ================= */}

      <nav className="sidebar-navigation">

        <Section
          title="MONITORING"
          items={monitoringItems}
        />

        <Section
          title="ANALYSIS"
          items={analysisItems}
        />

        <Section
          title="SYSTEM"
          items={systemItems}
        />

      </nav>


      {/* ================= FOOTER ================= */}

      <div className="sidebar-footer">

        <div className="sidebar-footer-top">

          <div className="india-mark">
            🇮🇳
          </div>

          <div>
            <strong>
              Prepared Communities
            </strong>

            <span>
              Safer Tomorrows
            </span>
          </div>

        </div>

        <div className="sidebar-version">
          SURAKSHA <span>v1.0</span>
        </div>

      </div>

    </aside>
  );
}