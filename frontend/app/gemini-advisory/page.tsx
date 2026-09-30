"use client";

import React from "react";
import Sidebar from "@/app/components/Sidebar";

import {
  Sparkles,
  ShieldAlert,
  AlertTriangle,
  Clock3,
  MapPin,
  Users,
  Building2,
  CheckCircle2,
  Wind,
  Waves,
  CloudRain,
  Activity,
  Copy,
  Check,
  ChevronDown,
} from "lucide-react";

type HazardImpact = {
  hazard?: string;
  severity?: string;
  message?: string;
};

type AdvisoryContent = {
  title?: string;
  severity?: string;
  summary?: string;

  risk_status?: {
    current_risk?: number;
    current_level?: string;
    projected_risk?: number;
    projected_level?: string;
    lead_time_hours?: number;
  };

  hazard_impacts?: HazardImpact[];

  population_impacts?: string;
  infrastructure_impacts?: string;

  authority_actions?: string[];
  priority_actions?: string[];

  flash_message?: string;
};

type AdvisoryResponse = {
  success?: boolean;

  cyclone?: {
    id?: string;
    name?: string;
  };

  target?: {
    latitude?: number;
    longitude?: number;
    location_name?: string;
  };

  forecast?: {
    hours_ahead?: number;
    timestamp?: string;
    forecast_type?: string;
    wind_kmph?: number;
    pressure_hpa?: number;
    distance_to_location_km?: number;
  };

  warning?: {
    trigger?: boolean;
    warning_level?: string;
    current_level?: string;
    projected_level?: string;
    current_risk?: number;
    projected_risk?: number;
    current_percentage?: number;
    projected_percentage?: number;
    lead_time_hours?: number;
  };

  hazards?: {
    wind?: number;
    rainfall?: number;
    storm_surge?: number;
    flood?: number;
  };

  exposure?: {
    population_score?: number;
    infrastructure_score?: number;
  };

  trigger_details?: {
    risk_escalation?: {
      escalation?: boolean;
      threshold_crossed?: boolean;
      current_level?: string;
      projected_level?: string;
      current_risk?: number;
      projected_risk?: number;
      increase?: number;
      hours_ahead?: number;
      reason?: string;
    };

    hazard_escalation?: {
      escalation?: boolean;
      hazard?: string;
      current_score?: number;
      projected_score?: number;
      increase?: number;
      hours_ahead?: number;
      severity?: string;
      reason?: string;
    };

    reasons?: string[];
  };

  advisory?: {
    success?: boolean;
    model?: string;
    authority_type?: string;
    location?: string;
    advisory?: AdvisoryContent;
    fallback?: boolean;
  };
};

type AdvisoryFile = Record<
  string,
  AdvisoryResponse
>;

const HORIZONS = [6, 12, 18, 24, 30, 36];

export default function GeminiAdvisoryPage() {
  const [data, setData] =
    React.useState<AdvisoryFile | null>(null);

  const [hours, setHours] =
    React.useState(36);

  const [loading, setLoading] =
    React.useState(true);

  const [copySuccess, setCopySuccess] =
    React.useState(false);

  const [error, setError] =
    React.useState("");

  React.useEffect(() => {
    loadAdvisoryData();
  }, []);

  async function loadAdvisoryData() {
    try {
      setLoading(true);
      setError("");

      /*
       * IMPORTANT:
       * This is a LOCAL JSON file.
       * No backend/API request.
       */

      const response = await fetch(
        "/data/advisory.json",
        {
          cache: "no-store",
        }
      );

      if (!response.ok) {
        throw new Error(
          `advisory.json returned ${response.status}`
        );
      }

      const json: AdvisoryFile =
        await response.json();

      setData(json);

    } catch (err) {
      console.error(
        "Advisory JSON error:",
        err
      );

      setError(
        "Unable to load advisory JSON."
      );

    } finally {
      setLoading(false);
    }
  }

  /*
   * Select advisory directly from JSON.
   * No API call when horizon changes.
   */

  const advisory =
    data?.[String(hours)];

  async function copyFlashMessage() {
    const message =
      advisory?.advisory?.advisory
        ?.flash_message;

    if (!message) return;

    try {
      await navigator.clipboard.writeText(
        message
      );

      setCopySuccess(true);

      setTimeout(() => {
        setCopySuccess(false);
      }, 1800);

    } catch {
      console.error(
        "Unable to copy message"
      );
    }
  }

  if (loading) {
    return (
      <main className="app">
        <Sidebar />

        <div className="main">

          <div className="gemini-page-loading">

            <div className="gemini-spinner" />

            <p>
              Loading advisory data...
            </p>

          </div>

        </div>
      </main>
    );
  }

  if (error || !data) {
    return (
      <main className="app">
        <Sidebar />

        <div className="main">

          <div className="gemini-error">

            <Sparkles size={32} />

            <h2>
              Advisory unavailable
            </h2>

            <p>
              {error ||
                "Unable to load advisory.json"}
            </p>

            <button
              onClick={loadAdvisoryData}
            >
              Retry
            </button>

          </div>

        </div>
      </main>
    );
  }

  if (!advisory) {
    return (
      <main className="app">
        <Sidebar />

        <div className="main">

          <div className="gemini-error">

            <AlertTriangle size={32} />

            <h2>
              Advisory not available
            </h2>

            <p>
              No JSON data exists for +
              {hours} hours.
            </p>

          </div>

        </div>
      </main>
    );
  }

  const cyclone =
    advisory.cyclone;

  const target =
    advisory.target;

  const forecast =
    advisory.forecast;

  const warning =
    advisory.warning;

  const hazards =
    advisory.hazards;

  const exposure =
    advisory.exposure;

  const triggerDetails =
    advisory.trigger_details;

  const ai =
    advisory.advisory;

  const aiContent =
    ai?.advisory;

  const severity =
    warning?.warning_level ??
    aiContent?.severity ??
    "WATCH";

  const riskCurrent =
    Number(
      warning?.current_percentage ??
      (warning?.current_risk ?? 0) * 100
    );

  const riskProjected =
    Number(
      warning?.projected_percentage ??
      (warning?.projected_risk ?? 0) * 100
    );

  const riskChange =
    riskProjected - riskCurrent;

  return (
    <main className="app">

      <Sidebar />

      <div className="main">

        <div className="content gemini-content">

          {/* =================================================
              HEADER
          ================================================= */}

          <section className="gemini-page-header">

            <div>

              <div className="gemini-eyebrow">

                <Sparkles size={14} />

                AI CYCLONE ADVISORY

              </div>

              <h1>
                AI Cyclone Advisory
              </h1>

              <p>
                Gemini-powered operational
                intelligence for disaster
                management authorities
              </p>

            </div>

            <div className="gemini-header-status">

              <span className="system-dot" />

              SYSTEM ACTIVE

              <span className="header-divider" />

              <strong>
                {cyclone?.id ?? "CY001"}
              </strong>

              <span className="header-divider" />

              <strong>
                {ai?.model ??
                  "gemini-3.8-flash"}
              </strong>

            </div>

          </section>


          {/* =================================================
              CYCLONE SUMMARY
          ================================================= */}

          <section className="cyclone-summary-grid">

            <div className="summary-main-card">

              <div className="summary-storm-icon">
                <Wind size={25} />
              </div>

              <div>

                <span>
                  ACTIVE CYCLONE
                </span>

                <h2>
                  {cyclone?.name ??
                    "Demo Cyclone"}
                </h2>

                <p>
                  {target?.location_name ??
                    ai?.location ??
                    "Puri"}
                  , Odisha
                </p>

              </div>

            </div>


            <InfoBox
              label="COORDINATES"
              value={`${target?.latitude ?? "—"}° N`}
              subValue={`${target?.longitude ?? "—"}° E`}
            />

            <InfoBox
              label="AUTHORITY"
              value={
                ai?.authority_type
                  ?.replaceAll("_", " ") ??
                "DISTRICT DISASTER MANAGEMENT"
              }
            />

            <InfoBox
              label="LEAD TIME"
              value={`${forecast?.hours_ahead ?? hours} HOURS`}
            />

          </section>


          {/* =================================================
              HORIZON
          ================================================= */}

          <section className="horizon-section">

            <div className="horizon-heading">

              <div>

                <span>
                  FORECAST HORIZON
                </span>

                <h2>
                  Advisory for +{hours} hours
                </h2>

              </div>

              <div className="horizon-current">
                +{hours}H SELECTED
              </div>

            </div>

            <div className="horizon-selector">

              {HORIZONS.map(
                (value) => (

                  <button
                    key={value}
                    className={
                      value === hours
                        ? "active"
                        : ""
                    }
                    onClick={() =>
                      setHours(value)
                    }
                  >
                    +{value}h
                  </button>

                )
              )}

            </div>

          </section>


          {/* =================================================
              WARNING
          ================================================= */}

          <section
            className={`warning-banner ${severity.toLowerCase()}`}
          >

            <div className="warning-left">

              <div className="warning-icon">
                <ShieldAlert size={24} />
              </div>

              <div>

                <span>
                  {severity}
                </span>

                <h2>
                  {warning?.trigger
                    ? "Early warning trigger active"
                    : "Monitoring advisory"}
                </h2>

                <p>
                  {warning?.lead_time_hours ??
                    forecast?.hours_ahead ??
                    hours}{" "}
                  hours lead time
                </p>

              </div>

            </div>


            <div className="warning-risk">

              <div>

                <span>
                  CURRENT RISK
                </span>

                <strong>
                  {riskCurrent.toFixed(2)}%
                </strong>

                <small>
                  {warning?.current_level ??
                    "—"}
                </small>

              </div>

              <div className="risk-arrow">
                →
              </div>

              <div>

                <span>
                  PROJECTED RISK
                </span>

                <strong>
                  {riskProjected.toFixed(2)}%
                </strong>

                <small>
                  {warning?.projected_level ??
                    "—"}
                </small>

              </div>

            </div>

          </section>


          {/* =================================================
              AI ADVISORY
          ================================================= */}

          <section className="ai-advisory-card">

            <div className="ai-card-header">

              <div className="ai-card-title">

                <div className="ai-icon">
                  <Sparkles size={22} />
                </div>

                <div>

                  <span>
                    GEMINI OPERATIONAL INTELLIGENCE
                  </span>

                  <h2>
                    AI Operational Advisory
                  </h2>

                </div>

              </div>

              <div className="ai-meta">

                <span>
                  {ai?.model ??
                    "gemini-3.8-flash"}
                </span>

                <span>
                  {ai?.location ??
                    target?.location_name ??
                    "Puri"}
                </span>

              </div>

            </div>


            <div className="generated-label">

              <CheckCircle2 size={13} />

              GENERATED FROM CURRENT
              FORECAST DATA

            </div>


            <h2 className="advisory-title">

              {aiContent?.title ??
                "Operational Cyclone Advisory"}

            </h2>


            <p className="advisory-summary">

              {aiContent?.summary ??
                "No advisory summary available."}

            </p>

          </section>


          {/* =================================================
              FLASH MESSAGE
          ================================================= */}

          <section className="flash-message-card">

            <div className="flash-message-icon">
              <AlertTriangle size={21} />
            </div>

            <div className="flash-message-content">

              <span>
                FLASH MESSAGE
              </span>

              <p>
                {aiContent?.flash_message ??
                  "No flash message available."}
              </p>

            </div>

            <button
              onClick={copyFlashMessage}
              className="copy-button"
            >

              {copySuccess ? (
                <>
                  <Check size={15} />
                  COPIED
                </>
              ) : (
                <>
                  <Copy size={15} />
                  COPY
                </>
              )}

            </button>

          </section>


          {/* =================================================
              RISK STATUS
          ================================================= */}

          <section className="dashboard-section">

            <SectionHeading
              eyebrow="RISK STATUS"
              title="Current vs Projected Risk"
              icon={<Activity size={19} />}
            />

            <div className="risk-status-grid">

              <MetricCard
                label="CURRENT RISK"
                value={`${riskCurrent.toFixed(2)}%`}
                sub={
                  warning?.current_level
                }
              />

              <MetricCard
                label="CURRENT LEVEL"
                value={
                  warning?.current_level ??
                  "—"
                }
                sub="Backend classification"
              />

              <MetricCard
                label="PROJECTED RISK"
                value={`${riskProjected.toFixed(2)}%`}
                sub={
                  warning?.projected_level
                }
              />

              <MetricCard
                label="PROJECTED LEVEL"
                value={
                  warning?.projected_level ??
                  "—"
                }
                sub="Backend classification"
              />

            </div>

            <div className="risk-change-row">

              <span>
                Risk change
              </span>

              <strong>
                {riskChange >= 0
                  ? "+"
                  : ""}
                {riskChange.toFixed(2)}
                percentage points
              </strong>

              <span>
                Lead time
              </span>

              <strong>
                {forecast?.hours_ahead ??
                  hours} hours
              </strong>

            </div>

          </section>


          {/* =================================================
              FORECAST CONDITIONS
          ================================================= */}

          <section className="dashboard-section">

            <SectionHeading
              eyebrow="FORECAST CONDITIONS"
              title={`Projected Conditions +${hours}h`}
              icon={<Wind size={19} />}
            />

            <div className="forecast-condition-grid">

              <MetricCard
                label="WIND"
                value={`${forecast?.wind_kmph ?? "—"} km/h`}
              />

              <MetricCard
                label="PRESSURE"
                value={`${forecast?.pressure_hpa ?? "—"} hPa`}
              />

              <MetricCard
                label="DISTANCE"
                value={`${forecast?.distance_to_location_km ?? "—"} km`}
              />

              <MetricCard
                label="FORECAST"
                value={`+${forecast?.hours_ahead ?? hours} hours`}
              />

            </div>

            <div className="timestamp-row">

              Timestamp:

              <strong>
                {formatTimestamp(
                  forecast?.timestamp
                )}
              </strong>

            </div>

          </section>


          {/* =================================================
              HAZARDS
          ================================================= */}

          <section className="dashboard-section">

            <SectionHeading
              eyebrow="HAZARD IMPACTS"
              title="Hazard Assessment"
              icon={<ShieldAlert size={19} />}
            />

            <div className="hazard-score-grid">

              <HazardCard
                name="WIND"
                score={hazards?.wind}
                icon={<Wind size={19} />}
                impact={findHazardImpact(
                  aiContent?.hazard_impacts,
                  "wind"
                )}
              />

              <HazardCard
                name="RAINFALL"
                score={hazards?.rainfall}
                icon={<CloudRain size={19} />}
                impact={findHazardImpact(
                  aiContent?.hazard_impacts,
                  "rain"
                )}
              />

              <HazardCard
                name="STORM SURGE"
                score={hazards?.storm_surge}
                icon={<Waves size={19} />}
                impact={findHazardImpact(
                  aiContent?.hazard_impacts,
                  "surge"
                )}
              />

              <HazardCard
                name="FLOOD"
                score={hazards?.flood}
                icon={<CloudRain size={19} />}
                impact={findHazardImpact(
                  aiContent?.hazard_impacts,
                  "flood"
                )}
              />

            </div>

          </section>


          {/* =================================================
              HAZARD ESCALATION
          ================================================= */}

          <section className="escalation-section">

            <SectionHeading
              eyebrow="TRIGGER ANALYSIS"
              title="Projected Hazard Escalation"
              icon={<AlertTriangle size={19} />}
            />

            {triggerDetails?.hazard_escalation
              ?.escalation ? (

              <div className="escalation-content">

                <div className="escalation-main">

                  <span>
                    HAZARD
                  </span>

                  <strong>
                    {
                      triggerDetails
                        .hazard_escalation
                        .hazard
                    }
                  </strong>

                </div>

                <EscalationMetric
                  label="CURRENT"
                  value={
                    triggerDetails
                      .hazard_escalation
                      .current_score
                  }
                />

                <EscalationMetric
                  label="PROJECTED"
                  value={
                    triggerDetails
                      .hazard_escalation
                      .projected_score
                  }
                />

                <EscalationMetric
                  label="INCREASE"
                  value={
                    triggerDetails
                      .hazard_escalation
                      .increase
                  }
                  plus
                />

                <div>

                  <span>
                    SEVERITY
                  </span>

                  <strong>
                    {
                      triggerDetails
                        .hazard_escalation
                        .severity
                    }
                  </strong>

                </div>

                <div>

                  <span>
                    TIME
                  </span>

                  <strong>
                    {
                      triggerDetails
                        .hazard_escalation
                        .hours_ahead
                    }{" "}
                    hours
                  </strong>

                </div>

              </div>

            ) : (

              <div className="no-escalation">

                <CheckCircle2 size={19} />

                No significant hazard
                escalation detected.

              </div>

            )}

            {triggerDetails?.hazard_escalation
              ?.reason && (

              <div className="reason-box">

                <span>
                  REASON
                </span>

                <p>
                  {
                    triggerDetails
                      .hazard_escalation
                      .reason
                  }
                </p>

              </div>

            )}

          </section>


          {/* =================================================
              EXPOSURE
          ================================================= */}

          <section className="exposure-grid">

            <div className="exposure-card">

              <div className="exposure-title">

                <Users size={20} />

                <div>

                  <span>
                    POPULATION EXPOSURE
                  </span>

                  <h3>
                    {(
                      (exposure
                        ?.population_score ??
                        0) * 100
                    ).toFixed(1)}
                    %
                  </h3>

                </div>

              </div>

              <p>
                {aiContent
                  ?.population_impacts ??
                  "No population impact information available."}
              </p>

            </div>


            <div className="exposure-card">

              <div className="exposure-title">

                <Building2 size={20} />

                <div>

                  <span>
                    INFRASTRUCTURE EXPOSURE
                  </span>

                  <h3>
                    {(
                      (exposure
                        ?.infrastructure_score ??
                        0) * 100
                    ).toFixed(1)}
                    %
                  </h3>

                </div>

              </div>

              <p>
                {aiContent
                  ?.infrastructure_impacts ??
                  "No infrastructure impact information available."}
              </p>

            </div>

          </section>


          {/* =================================================
              AUTHORITY ACTIONS
          ================================================= */}

          <section className="dashboard-section">

            <SectionHeading
              eyebrow="OPERATIONAL RESPONSE"
              title="Recommended Authority Actions"
              icon={<CheckCircle2 size={19} />}
            />

            <div className="action-list">

              {(
                aiContent
                  ?.authority_actions ?? []
              ).map(
                (action, index) => (

                  <div
                    className="action-card"
                    key={index}
                  >

                    <div className="action-number">

                      {String(
                        index + 1
                      ).padStart(2, "0")}

                    </div>

                    <p>
                      {action}
                    </p>

                  </div>

                )
              )}

            </div>

          </section>


          {/* =================================================
              PRIORITY ACTIONS
          ================================================= */}

          <section className="priority-section">

            <SectionHeading
              eyebrow="HIGH PRIORITY"
              title="Priority Actions"
              icon={<AlertTriangle size={19} />}
            />

            <div className="priority-list">

              {(
                aiContent
                  ?.priority_actions ?? []
              ).map(
                (action, index) => (

                  <div
                    className="priority-item"
                    key={index}
                  >

                    <span>
                      PRIORITY
                    </span>

                    <p>
                      {action}
                    </p>

                  </div>

                )
              )}

            </div>

          </section>


          {/* =================================================
              WHY TRIGGERED
          ================================================= */}

          <details className="trigger-details">

            <summary>

              <div>

                <span>
                  TECHNICAL ANALYSIS
                </span>

                <h2>
                  Why Was This Advisory Triggered?
                </h2>

              </div>

              <ChevronDown size={20} />

            </summary>


            <div className="trigger-body">

              <div className="trigger-block">

                <h3>
                  Risk Escalation
                </h3>

                <div className="trigger-grid">

                  <TriggerValue
                    label="Escalation"
                    value={
                      triggerDetails
                        ?.risk_escalation
                        ?.escalation
                        ? "YES"
                        : "NO"
                    }
                  />

                  <TriggerValue
                    label="Threshold Crossed"
                    value={
                      triggerDetails
                        ?.risk_escalation
                        ?.threshold_crossed
                        ? "YES"
                        : "NO"
                    }
                  />

                  <TriggerValue
                    label="Current Risk"
                    value={
                      triggerDetails
                        ?.risk_escalation
                        ?.current_risk
                    }
                  />

                  <TriggerValue
                    label="Projected Risk"
                    value={
                      triggerDetails
                        ?.risk_escalation
                        ?.projected_risk
                    }
                  />

                  <TriggerValue
                    label="Increase"
                    value={
                      triggerDetails
                        ?.risk_escalation
                        ?.increase
                    }
                  />

                </div>

                <p className="trigger-reason">

                  {
                    triggerDetails
                      ?.risk_escalation
                      ?.reason ??
                    "No reason provided."
                  }

                </p>

              </div>


              <div className="trigger-block">

                <h3>
                  Hazard Escalation
                </h3>

                <div className="trigger-grid">

                  <TriggerValue
                    label="Hazard"
                    value={
                      triggerDetails
                        ?.hazard_escalation
                        ?.hazard
                    }
                  />

                  <TriggerValue
                    label="Current Score"
                    value={
                      triggerDetails
                        ?.hazard_escalation
                        ?.current_score
                    }
                  />

                  <TriggerValue
                    label="Projected Score"
                    value={
                      triggerDetails
                        ?.hazard_escalation
                        ?.projected_score
                    }
                  />

                  <TriggerValue
                    label="Increase"
                    value={
                      triggerDetails
                        ?.hazard_escalation
                        ?.increase
                    }
                  />

                  <TriggerValue
                    label="Severity"
                    value={
                      triggerDetails
                        ?.hazard_escalation
                        ?.severity
                    }
                  />

                  <TriggerValue
                    label="Hours Ahead"
                    value={
                      triggerDetails
                        ?.hazard_escalation
                        ?.hours_ahead
                    }
                  />

                </div>

                <p className="trigger-reason">

                  {
                    triggerDetails
                      ?.hazard_escalation
                      ?.reason ??
                    "No reason provided."
                  }

                </p>

              </div>


              <div className="trigger-block">

                <h3>
                  Trigger Reasons
                </h3>

                <ul>

                  {(
                    triggerDetails?.reasons ??
                    []
                  ).map(
                    (reason, index) => (

                      <li key={index}>
                        {reason}
                      </li>

                    )
                  )}

                </ul>

              </div>

            </div>

          </details>


          {/* =================================================
              METADATA
          ================================================= */}

          <section className="metadata-section">

            <SectionHeading
              eyebrow="ADVISORY METADATA"
              title="Generation Information"
              icon={<Sparkles size={19} />}
            />

            <div className="metadata-grid">

              <MetaItem
                label="Cyclone"
                value={
                  cyclone?.name ??
                  "Demo Cyclone"
                }
              />

              <MetaItem
                label="Cyclone ID"
                value={
                  cyclone?.id ??
                  "CY001"
                }
              />

              <MetaItem
                label="Location"
                value={
                  target?.location_name ??
                  ai?.location ??
                  "Puri"
                }
              />

              <MetaItem
                label="Authority"
                value={
                  ai?.authority_type ??
                  "DISTRICT_DISASTER_MANAGEMENT"
                }
              />

              <MetaItem
                label="AI Model"
                value={
                  ai?.model ??
                  "gemini-3.8-flash"
                }
              />

              <MetaItem
                label="Forecast Horizon"
                value={`${hours} hours`}
              />

              <MetaItem
                label="Generated from Backend"
                value="YES"
              />

              <MetaItem
                label="Fallback"
                value={
                  ai?.fallback
                    ? "YES"
                    : "NO"
                }
              />

            </div>

            <div
              className={
                ai?.fallback
                  ? "generation-status fallback"
                  : "generation-status"
              }
            >

              {ai?.fallback ? (
                <>
                  <AlertTriangle size={17} />

                  Gemini unavailable —
                  deterministic backend
                  fallback advisory is being used.

                </>
              ) : (
                <>
                  <CheckCircle2 size={17} />

                  Gemini advisory generated
                  successfully.

                </>
              )}

            </div>

          </section>

        </div>

      </div>

    </main>
  );
}


/* ============================================================
   COMPONENTS
============================================================ */

function InfoBox({
  label,
  value,
  subValue,
}: {
  label: string;
  value: string;
  subValue?: string;
}) {
  return (
    <div className="info-box">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

      {subValue && (
        <small>
          {subValue}
        </small>
      )}

    </div>
  );
}


function SectionHeading({
  eyebrow,
  title,
  icon,
}: {
  eyebrow: string;
  title: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="section-heading">

      <div>

        <span>
          {eyebrow}
        </span>

        <h2>
          {title}
        </h2>

      </div>

      {icon}

    </div>
  );
}


function MetricCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="metric-card">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

      {sub && (
        <small>
          {sub}
        </small>
      )}

    </div>
  );
}


function HazardCard({
  name,
  score,
  icon,
  impact,
}: {
  name: string;
  score?: number;
  icon: React.ReactNode;
  impact?: HazardImpact;
}) {
  const numericScore =
    Number(score ?? 0);

  return (
    <div className="hazard-score-card">

      <div className="hazard-top">

        <div className="hazard-name">

          <div className="hazard-score-icon">
            {icon}
          </div>

          <strong>
            {name}
          </strong>

        </div>

        {impact?.severity && (
          <span
            className={`severity-badge ${impact.severity.toLowerCase()}`}
          >
            {impact.severity}
          </span>
        )}

      </div>


      <div className="hazard-score">

        <strong>
          {numericScore.toFixed(3)}
        </strong>

        <span>
          {(numericScore * 100).toFixed(1)}%
        </span>

      </div>


      <p>
        {impact?.message ??
          "No hazard message available."}
      </p>

    </div>
  );
}


function EscalationMetric({
  label,
  value,
  plus = false,
}: {
  label: string;
  value?: number;
  plus?: boolean;
}) {
  return (
    <div>

      <span>
        {label}
      </span>

      <strong>
        {value != null
          ? `${plus && value >= 0 ? "+" : ""}${value.toFixed(3)}`
          : "—"}
      </strong>

    </div>
  );
}


function TriggerValue({
  label,
  value,
}: {
  label: string;
  value?: string | number | boolean;
}) {
  return (
    <div>

      <span>
        {label}
      </span>

      <strong>
        {value == null
          ? "—"
          : typeof value === "number"
          ? value.toFixed(3)
          : String(value)}
      </strong>

    </div>
  );
}


function MetaItem({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div>

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>
  );
}


/* ============================================================
   HELPERS
============================================================ */

function findHazardImpact(
  impacts: HazardImpact[] | undefined,
  keyword: string
) {
  if (!impacts) return undefined;

  return impacts.find(
    (item) =>
      String(
        item.hazard ?? ""
      )
        .toLowerCase()
        .includes(keyword)
  );
}


function formatTimestamp(
  timestamp?: string
) {
  if (!timestamp) return "—";

  return timestamp
    .replace("T", " ")
    .slice(0, 16);
}