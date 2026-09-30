"use client";

import React from "react";

import Sidebar from "@/app/components/Sidebar";
import Topbar from "@/app/components/Topbar";

import {
  AlertTriangle,
  ShieldAlert,
  CheckCircle2,
  MapPin,
  Mail,
  Phone,
  Radio,
  Send,
} from "lucide-react";

import type { DashboardData } from "@/app/lib/dashboard";


/* =========================================================
   AUTHORITY
========================================================= */

interface Authority {
  authority_id: string;
  authority_type: string;
  name: string;
  district: string;
  email: string;
  phone: string;
  channels: string[];
  active: boolean;
}


/* =========================================================
   ALERT PAGE
========================================================= */

export default function AlertsPage() {

  const [data, setData] =
    React.useState<DashboardData | null>(null);

  const [authorities, setAuthorities] =
    React.useState<Authority[]>([]);

  const [loading, setLoading] =
    React.useState(true);


  /* =======================================================
     LOAD DATA
  ======================================================= */

  React.useEffect(() => {

    Promise.all([
      fetch("/data/dashboard.json").then((res) => {
        if (!res.ok) {
          throw new Error("Failed to load dashboard");
        }

        return res.json();
      }),

      fetch("/data/authorities.json").then((res) => {
        if (!res.ok) {
          throw new Error("Failed to load authorities");
        }

        return res.json();
      }),
    ])
      .then(([dashboardData, authorityData]) => {

        setData(dashboardData);

        setAuthorities(
          Array.isArray(authorityData)
            ? authorityData
            : []
        );

        setLoading(false);

      })
      .catch((error) => {

        console.error(
          "Alert data loading error:",
          error
        );

        setLoading(false);

      });

  }, []);


  /* =======================================================
     LOADING
  ======================================================= */

  if (loading) {

    return (
      <main className="app">

        <Sidebar />

        <div className="main">

          <Topbar />

          <div className="content">

            <div className="page-loading">
              Loading alerts...
            </div>

          </div>

        </div>

      </main>
    );
  }


  /* =======================================================
     ERROR
  ======================================================= */

  if (!data) {

    return (
      <main className="app">

        <Sidebar />

        <div className="main">

          <Topbar />

          <div className="content">

            <div className="card">
              Unable to load dashboard data.
            </div>

          </div>

        </div>

      </main>
    );
  }


  /* =======================================================
     ALERT DATA
  ======================================================= */

  const alerts = Array.isArray(data.alerts)
    ? data.alerts.slice(0, 4)
    : [];


  /* =======================================================
     AUTHORITY HELPERS
  ======================================================= */

  const formatAuthorityType = (
    type: string
  ) => {

    return type
      .replaceAll("_", " ")
      .replace(/\b\w/g, (char) =>
        char.toUpperCase()
      );
  };


  /* =======================================================
     SEND EMAIL
  ======================================================= */

  const sendEmail = async (
    authority: Authority
  ) => {
    try {
      const API_BASE_URL =
        process.env.NEXT_PUBLIC_API_BASE_URL ||
        "http://127.0.0.1:8000";

      const response = await fetch(
        `${API_BASE_URL}/api/cyclones/CY001/dispatch?hours=36`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        throw new Error(
          `Dispatch failed with status ${response.status}`
        );
      }

      const result = await response.json();

      console.log(
        `Warning dispatched to ${authority.name}:`,
        result
      );

      alert(
        `Warning dispatched successfully to ${authority.name}.\\n\\nMail and SMS notifications have been sent.`
      );
    } catch (error) {
      console.error(
        "Warning dispatch failed:",
        error
      );

      alert(
        "Unable to dispatch warning. Please check the backend."
      );
    }
  };


  /* =======================================================
     SEND SMS
  ======================================================= */

  const sendSMS = (
    authority: Authority
  ) => {

    const message =
      `SURA RAKSHA ALERT: Cyclone risk for ${
        data.location?.name ?? "Puri"
      } is ${
        data.risk?.level ?? "WATCH"
      } (${Number(
        data.risk?.percentage ?? 0
      ).toFixed(1)}%). Please take necessary action.`;

    window.location.href =
      `sms:${authority.phone}?body=${encodeURIComponent(
        message
      )}`;
  };


  return (

    <main className="app">

      {/* =================================================
          SIDEBAR
      ================================================= */}

      <Sidebar />


      {/* =================================================
          MAIN
      ================================================= */}

      <div className="main">

        <Topbar />


        <div className="content">


          {/* =================================================
              HEADER
          ================================================= */}

          <div className="alerts-page-header">

            <div>

              <h1>
                Alerts
              </h1>

              <p>
                View cyclone warnings and operational alerts.
              </p>

            </div>


            <div className="alerts-status">

              <span className="status-dot" />

              {alerts.length} active alerts

            </div>

          </div>


          {/* =================================================
              NORMAL ALERTS
          ================================================= */}

          <section className="system-alerts">


            {alerts.length === 0 ? (

              <div className="no-alerts card">

                <CheckCircle2 size={24} />

                <div>

                  <strong>
                    No active alerts
                  </strong>

                  <p>
                    No operational alerts are currently
                    being generated.
                  </p>

                </div>

              </div>

            ) : (

              <div className="alert-list">

                {alerts.map(
                  (alert: any, index: number) => {

                    const level =
                      String(
                        alert.level ??
                        alert.severity ??
                        "WATCH"
                      ).toUpperCase();


                    const isHigh =
                      level === "HIGH" ||
                      level === "EMERGENCY";


                    return (

                      <article
                        className={`system-alert card ${level.toLowerCase()}`}
                        key={
                          alert.id ??
                          `${alert.title}-${index}`
                        }
                      >

                        {/* ALERT ICON */}

                        <div className="alert-icon">

                          {isHigh ? (

                            <AlertTriangle
                              size={21}
                            />

                          ) : (

                            <ShieldAlert
                              size={21}
                            />

                          )}

                        </div>


                        {/* ALERT CONTENT */}

                        <div className="alert-body">

                          <div className="alert-top">

                            <span
                              className={`alert-level ${level.toLowerCase()}`}
                            >
                              {level}
                            </span>


                            <span className="alert-time">

                              {alert.hours_ahead != null
                                ? `+${alert.hours_ahead}h`
                                : alert.status ??
                                  "ACTIVE"}

                            </span>

                          </div>


                          <h3>

                            {alert.title ??
                              "Cyclone Alert"}

                          </h3>


                          <p>

                            {alert.message ?? ""}

                          </p>


                          {alert.action && (

                            <div className="alert-action">

                              {alert.action}

                            </div>

                          )}

                        </div>

                      </article>

                    );

                  }
                )}

              </div>

            )}

          </section>


          {/* =================================================
              SEPARATOR
          ================================================= */}

          <div
            className="alerts-divider"
            style={{
              marginTop: "32px",
              marginBottom: "28px",
            }}
          >

            <div className="divider-line" />

            <span>
              AUTHORITY CONTACTS
            </span>

            <div className="divider-line" />

          </div>


          {/* =================================================
              AUTHORITY DETAILS
          ================================================= */}

          <section>

            {authorities.length > 0 && (

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns:
                    "repeat(2, minmax(0, 1fr))",
                  gap: "18px",
                }}
              >

                {authorities.map(
                  (authority) => (

                    <article
                      key={authority.authority_id}
                      className="card"
                      style={{
                        padding: "22px",
                      }}
                    >

                      {/* ==============================
                          AUTHORITY HEADER
                      ============================== */}

                      <div
                        style={{
                          display: "flex",
                          justifyContent:
                            "space-between",
                          alignItems: "flex-start",
                          gap: "16px",
                          marginBottom: "20px",
                        }}
                      >

                        <div>

                          <div
                            style={{
                              fontSize: "11px",
                              fontWeight: 700,
                              letterSpacing:
                                "0.12em",
                              textTransform:
                                "uppercase",
                              color:
                                "#6f92a3",
                              marginBottom:
                                "7px",
                            }}
                          >
                            {formatAuthorityType(
                              authority.authority_type
                            )}
                          </div>


                          <h3
                            style={{
                              margin: 0,
                              fontSize:
                                "19px",
                              color:
                                "#e9f4f8",
                            }}
                          >
                            {authority.name}
                          </h3>

                        </div>


                        {/* ACTIVE */}

                        <span
                          style={{
                            display: "inline-flex",
                            alignItems:
                              "center",
                            gap: "6px",
                            padding:
                              "6px 10px",
                            borderRadius:
                              "999px",
                            fontSize:
                              "11px",
                            fontWeight: 700,
                            color:
                              authority.active
                                ? "#28e0a5"
                                : "#ff625d",
                            background:
                              authority.active
                                ? "rgba(40,224,165,.10)"
                                : "rgba(255,98,93,.10)",
                            whiteSpace:
                              "nowrap",
                          }}
                        >

                          <span>
                            ●
                          </span>

                          {authority.active
                            ? "ACTIVE"
                            : "INACTIVE"}

                        </span>

                      </div>


                      {/* ==============================
                          DETAILS
                      ============================== */}

                      <div
                        style={{
                          display: "grid",
                          gridTemplateColumns:
                            "1fr 1fr",
                          gap: "12px",
                        }}
                      >

                        {/* DISTRICT */}

                        <div
                          style={{
                            padding:
                              "13px",
                            borderRadius:
                              "10px",
                            background:
                              "rgba(255,255,255,.025)",
                            border:
                              "1px solid rgba(255,255,255,.06)",
                          }}
                        >

                          <div
                            style={{
                              display:
                                "flex",
                              alignItems:
                                "center",
                              gap: "8px",
                              color:
                                "#7f9dab",
                              fontSize:
                                "12px",
                              marginBottom:
                                "6px",
                            }}
                          >

                            <MapPin
                              size={14}
                            />

                            District

                          </div>

                          <strong>
                            {authority.district}
                          </strong>

                        </div>


                        {/* EMAIL */}

                        <div
                          style={{
                            padding:
                              "13px",
                            borderRadius:
                              "10px",
                            background:
                              "rgba(255,255,255,.025)",
                            border:
                              "1px solid rgba(255,255,255,.06)",
                          }}
                        >

                          <div
                            style={{
                              display:
                                "flex",
                              alignItems:
                                "center",
                              gap: "8px",
                              color:
                                "#7f9dab",
                              fontSize:
                                "12px",
                              marginBottom:
                                "6px",
                            }}
                          >

                            <Mail
                              size={14}
                            />

                            Email

                          </div>

                          <strong
                            style={{
                              fontSize:
                                "12px",
                              wordBreak:
                                "break-all",
                            }}
                          >
                            {authority.email}
                          </strong>

                        </div>


                        {/* PHONE */}

                        <div
                          style={{
                            padding:
                              "13px",
                            borderRadius:
                              "10px",
                            background:
                              "rgba(255,255,255,.025)",
                            border:
                              "1px solid rgba(255,255,255,.06)",
                          }}
                        >

                          <div
                            style={{
                              display:
                                "flex",
                              alignItems:
                                "center",
                              gap: "8px",
                              color:
                                "#7f9dab",
                              fontSize:
                                "12px",
                              marginBottom:
                                "6px",
                            }}
                          >

                            <Phone
                              size={14}
                            />

                            Phone

                          </div>

                          <strong>
                            {authority.phone}
                          </strong>

                        </div>


                        {/* CHANNELS */}

                        <div
                          style={{
                            padding:
                              "13px",
                            borderRadius:
                              "10px",
                            background:
                              "rgba(255,255,255,.025)",
                            border:
                              "1px solid rgba(255,255,255,.06)",
                          }}
                        >

                          <div
                            style={{
                              display:
                                "flex",
                              alignItems:
                                "center",
                              gap: "8px",
                              color:
                                "#7f9dab",
                              fontSize:
                                "12px",
                              marginBottom:
                                "6px",
                            }}
                          >

                            <Radio
                              size={14}
                            />

                            Channels

                          </div>

                          <strong>
                            {authority.channels
                              .map(
                                (channel) =>
                                  channel.toUpperCase()
                              )
                              .join(" • ")}
                          </strong>

                        </div>

                      </div>


                      {/* ==============================
                          SEND BUTTONS
                      ============================== */}

                      <div
                        style={{
                          display:
                            "flex",
                          gap: "10px",
                          marginTop:
                            "16px",
                        }}
                      >

                        {/* EMAIL */}

                        {authority.channels.includes(
                          "email"
                        ) && (

                          <button
                            type="button"
                            onClick={() =>
                              sendEmail(
                                authority
                              )
                            }
                            style={{
                              flex: 1,
                              display:
                                "flex",
                              alignItems:
                                "center",
                              justifyContent:
                                "center",
                              gap: "8px",
                              padding:
                                "11px 14px",
                              borderRadius:
                                "9px",
                              border:
                                "1px solid rgba(18,199,237,.30)",
                              background:
                                "rgba(18,199,237,.08)",
                              color:
                                "#12c7ed",
                              fontWeight:
                                700,
                              fontSize:
                                "13px",
                              cursor:
                                "pointer",
                            }}
                          >

                            <Send
                              size={15}
                            />

                            Send Email

                          </button>

                        )}


                        {/* SMS */}

                        {authority.channels.includes(
                          "sms"
                        ) && (

                          <button
                            type="button"
                            onClick={() =>
                              sendSMS(
                                authority
                              )
                            }
                            style={{
                              flex: 1,
                              display:
                                "flex",
                              alignItems:
                                "center",
                              justifyContent:
                                "center",
                              gap: "8px",
                              padding:
                                "11px 14px",
                              borderRadius:
                                "9px",
                              border:
                                "1px solid rgba(40,224,165,.30)",
                              background:
                                "rgba(40,224,165,.08)",
                              color:
                                "#28e0a5",
                              fontWeight:
                                700,
                              fontSize:
                                "13px",
                              cursor:
                                "pointer",
                            }}
                          >

                            <Send
                              size={15}
                            />

                            Send SMS

                          </button>

                        )}

                      </div>

                    </article>

                  )
                )}

              </div>

            )}

          </section>

        </div>

      </div>

    </main>
  );
}