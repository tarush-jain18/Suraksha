"use client";

import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

interface SectionPageProps {
  title: string;
  subtitle: string;
  children?: React.ReactNode;
}

export default function SectionPage({
  title,
  subtitle,
  children,
}: SectionPageProps) {
  return (
    <main className="app">
      <Sidebar />

      <div className="main">
        <Topbar />

        <div className="content">
          <div className="page-heading">
            <div>
              <h1>{title}</h1>
              <p>{subtitle}</p>
            </div>
          </div>

          {children}
        </div>
      </div>
    </main>
  );
}