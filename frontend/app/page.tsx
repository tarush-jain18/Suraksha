"use client";

import { useEffect, useRef, useState } from "react";
import Sidebar from "@/app/components/Sidebar";
import Topbar from "@/app/components/Topbar";
import CycloneHeader from "@/app/components/CycloneHeader";
import CurrentConditions from "@/app/components/CurrentConditions";
import RiskCard from "@/app/components/RiskCard";
import ForecastTimeline from "@/app/components/ForecastTimeline";
import ImpactOverview from "@/app/components/ImpactOverview";
import RiskDrivers from "@/app/components/RiskDrivers";
import RecentAlerts from "@/app/components/RecentAlerts";
import MapPanel from "@/app/components/MapPanel";
import type { DashboardData } from "@/app/lib/dashboard";

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Automatic dispatch state
  const dispatchStarted = useRef(false);
  const [dispatchSuccess, setDispatchSuccess] = useState(false);
  const [dispatchError, setDispatchError] = useState(false);

  // ============================================================
  // AUTOMATIC WARNING DISPATCH
  // ============================================================
  useEffect(() => {
    // Prevent duplicate API calls during React development re-renders
    if (dispatchStarted.current) return;

    dispatchStarted.current = true;

    async function dispatchWarning() {
      try {
        const API_BASE_URL =
          process.env.NEXT_PUBLIC_API_BASE_URL ||
          "http://127.0.0.1:8000";

        const response = await fetch(
          `${API_BASE_URL}/api/cyclones/CY001/dispatch?hours=36`,
          {
            method: "POST"
          }
        );

        if (!response.ok) {
          throw new Error(
            "Automatic warning dispatch successful:",
          );
        }

        const result = await response.json();

        console.log(
          "Automatic warning dispatch successful:",
          result
        );

        // Show website notification
        setDispatchSuccess(true);

        // Automatically hide after 5 seconds
        setTimeout(() => {
          setDispatchSuccess(false);
        }, 5000);
      } catch (err) {
        console.error(
          "Automatic warning dispatch failed:",
          err
        );

        // Show failure notification
        setDispatchError(true);

        // Automatically hide after 6 seconds
        setTimeout(() => {
          setDispatchError(false);
        }, 6000);
      }
    }

    dispatchWarning();
  }, []);

  // ============================================================
  // LOAD DASHBOARD DATA
  // ============================================================
  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      try {
        const response = await fetch("/data/dashboard.json", {
          cache: "no-store",
        });

        if (!response.ok) {
          throw new Error(
            `Dashboard JSON returned ${response.status}`
          );
        }

        const json = (await response.json()) as DashboardData;

        if (!cancelled) {
          setData(json);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load dashboard data."
          );
        }
      }
    }

    loadDashboard();

    return () => {
      cancelled = true;
    };
  }, []);

  // ============================================================
  // ERROR SCREEN
  // ============================================================
  if (error) {
    return (
      <main className="app">
        <Sidebar />

        <div className="main">
          <Topbar />

          <div className="content">
            <section
              className="card"
              style={{ padding: 32 }}
            >
              <h2>Dashboard data could not be loaded</h2>

              <p>{error}</p>

              <p>
                Confirm that{" "}
                <code>public/data/dashboard.json</code>{" "}
                exists and that{" "}
                <code>/data/dashboard.json</code>{" "}
                opens in the browser.
              </p>
            </section>
          </div>
        </div>
      </main>
    );
  }

  // ============================================================
  // LOADING SCREEN
  // ============================================================
  if (!data) {
    return (
      <main className="app">
        <Sidebar />

        <div className="main">
          <Topbar />

          <div className="content">
            <section
              className="card"
              style={{ padding: 32 }}
            >
              <h2>Loading cyclone dashboard…</h2>

              <p>
                Reading the latest processed dashboard
                data.
              </p>
            </section>
          </div>
        </div>
      </main>
    );
  }

  // ============================================================
  // FORECAST DATA
  // ============================================================
  const forecastPoints = [
    ...(data.forecast?.observed ?? []),
    ...(data.forecast?.projected ?? []),
  ];

  // Prevent unused variable warning if forecastPoints
  // is not currently needed by another component.
  void forecastPoints;

  // ============================================================
  // MAIN DASHBOARD
  // ============================================================
  return (
    <main className="app">

      {/* ======================================================
          AUTOMATIC DISPATCH SUCCESS NOTIFICATION
          ====================================================== */}
      {dispatchSuccess && (
        <div className="dispatch-notification success">

          <div className="dispatch-icon">
            ✓
          </div>

          <div className="dispatch-content">
            <strong>Warning Dispatched</strong>

            <p>
              Automatic mail and SMS notifications
              have been sent successfully.
            </p>
          </div>

          <button
            className="dispatch-close"
            onClick={() => setDispatchSuccess(false)}
            aria-label="Close notification"
          >
            ×
          </button>

        </div>
      )}

      {/* ======================================================
          AUTOMATIC DISPATCH ERROR NOTIFICATION
          ====================================================== */}
      {dispatchError && (
        <div className="dispatch-notification error">

          <div className="dispatch-icon">
            !
          </div>

          <div className="dispatch-content">
            <strong>Warning Dispatch Failed</strong>

            <p>
              The automatic warning could not be
              dispatched. Please check the backend.
            </p>
          </div>

          <button
            className="dispatch-close"
            onClick={() => setDispatchError(false)}
            aria-label="Close notification"
          >
            ×
          </button>

        </div>
      )}

      {/* ======================================================
          SIDEBAR
          ====================================================== */}
      <Sidebar />

      {/* ======================================================
          MAIN CONTENT
          ====================================================== */}
      <div className="main">

        <Topbar />

        <div className="content">

          {/* Cyclone Header */}
          <CycloneHeader data={data} />

          {/* ==================================================
              MAP + CURRENT CONDITIONS + RISK
              ================================================== */}
          <div className="main-grid">

            <div className="left-column">
              <MapPanel data={data} />
            </div>

            <div className="right-column">
              <CurrentConditions data={data} />
              <RiskCard data={data} />
            </div>

          </div>

          {/* ==================================================
              FORECAST
              ================================================== */}
          <ForecastTimeline data={data} />

          {/* ==================================================
              IMPACT + RISK + ALERTS
              ================================================== */}
          <div className="bottom-grid">

            <ImpactOverview data={data} />

            <RiskDrivers data={data} />

            <RecentAlerts data={data} />

          </div>

        </div>
      </div>
    </main>
  );
}