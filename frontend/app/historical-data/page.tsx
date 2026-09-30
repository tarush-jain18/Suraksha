"use client";

import { useEffect, useMemo, useState } from "react";
import Sidebar from "@/app/components/Sidebar";
/* ============================================================
   TYPES
============================================================ */

type HistoricalCyclone = {
  sid?: string;
  name: string;
  year: number;
  max_wind_kmph?: number;
  min_pressure_hpa?: number;
  minimum_distance_to_odisha_km?: number;
  track_intersects_odisha?: boolean;
  similarity_percentage?: number;
};

type HistoricalStatistics = {
  total_cyclones: number;
  cyclones_entering_odisha: number;
  average_max_wind_kmph: number;
  maximum_wind_kmph: number;
  average_min_pressure_hpa: number;
  lowest_pressure_hpa: number;
};

type HistoryResponse = {
  success: boolean;
  region: string;
  statistics: HistoricalStatistics;
  cyclones: HistoricalCyclone[];
  similar_cyclones?: HistoricalCyclone[];
};

type CompareResponse = {
  success?: boolean;
  region?: string;
  current_cyclone?: HistoricalCyclone;
  similar_cyclones?: HistoricalCyclone[];
  error?: string;
};

/* ============================================================
   PAGE
============================================================ */

export default function HistoricalPage() {
  const [data, setData] =
    useState<HistoryResponse | null>(null);

  const [search, setSearch] = useState("");

  const [selected, setSelected] =
    useState<HistoricalCyclone | null>(null);

  const [comparison, setComparison] =
    useState<CompareResponse | null>(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  /* ==========================================================
     LOAD LOCAL JSON
  ========================================================== */

  useEffect(() => {
    async function loadHistory() {
      try {
        setLoading(true);
        setError("");

        /*
         * IMPORTANT:
         * This does NOT call FastAPI.
         *
         * It loads:
         *
         * public/data/historical.json
         */

        const response = await fetch(
          "/data/historical.json",
          {
            cache: "no-store",
          }
        );

        if (!response.ok) {
          throw new Error(
            `Historical JSON returned ${response.status}`
          );
        }

        const result: HistoryResponse =
          await response.json();

        setData(result);
      } catch (err) {
        console.error(
          "Historical JSON loading error:",
          err
        );

        setError(
          "Unable to load historical cyclone data."
        );
      } finally {
        setLoading(false);
      }
    }

    loadHistory();
  }, []);

  /* ==========================================================
     SEARCH
  ========================================================== */

  const filteredCyclones = useMemo(() => {
    if (!data?.cyclones) {
      return [];
    }

    const query = search
      .trim()
      .toLowerCase();

    if (!query) {
      return data.cyclones;
    }

    return data.cyclones.filter(
      (cyclone) => {
        return (
          cyclone.name
            ?.toLowerCase()
            .includes(query) ||

          String(cyclone.year)
            .toLowerCase()
            .includes(query) ||

          cyclone.sid
            ?.toLowerCase()
            .includes(query)
        );
      }
    );
  }, [data, search]);

  /* ==========================================================
     SELECT CYCLONE
  ========================================================== */

  function openCyclone(
    cyclone: HistoricalCyclone
  ) {
    setSelected(cyclone);

    /*
     * No backend request.
     *
     * Similar cyclone data comes directly
     * from historical.json.
     */

    const similar =
      data?.similar_cyclones ?? [];

    const filteredSimilar =
      similar.filter(
        (item) =>
          !(
            item.name === cyclone.name &&
            item.year === cyclone.year
          )
      );

    setComparison({
      success: true,
      region: data?.region ?? "Odisha",
      current_cyclone: cyclone,
      similar_cyclones: filteredSimilar,
    });
  }

  /* ==========================================================
     LOADING
  ========================================================== */

  if (loading) {
    return (
      <main className="history-page">
        <Sidebar />
        <div className="history-loading">

          <div className="loading-spinner" />

          <p>
            Loading historical cyclone archive...
          </p>

        </div>

      </main>
    );
  }

  /* ==========================================================
     ERROR
  ========================================================== */

  if (error || !data) {
    return (
      <main className="history-page">

        <Sidebar />

        <div className="history-error">

          <div className="error-icon">
            ⚠
          </div>

          <h2>
            Historical data unavailable
          </h2>

          <p>
            {error ||
              "Historical cyclone JSON could not be loaded."}
          </p>

          <button
            onClick={() =>
              window.location.reload()
            }
            className="retry-button"
          >
            Retry
          </button>

        </div>

      </main>
    );
  }

  const stats =
    data.statistics;

  /* ==========================================================
     PAGE
  ========================================================== */

  return (
    <main className="history-page">

      {/* ======================================================
          HEADER
      ====================================================== */}
<Sidebar />
      <section className="page-header">

        <div>

          <div className="eyebrow">
            ODISHA CYCLONE ARCHIVE
          </div>

          <h1>
            Historical Cyclones
          </h1>

          <p>
            Explore historical cyclone activity
            across Odisha and compare past storms
            with the selected cyclone.
          </p>

        </div>

        <div className="archive-badge">

          <span className="archive-dot" />

          HISTORICAL DATA

        </div>

      </section>

      {/* ======================================================
          STATISTICS
      ====================================================== */}

      <section className="statistics-grid">

        <StatCard
          label="Total Cyclones"
          value={stats.total_cyclones}
          suffix=""
        />

        <StatCard
          label="Entered Odisha"
          value={
            stats.cyclones_entering_odisha
          }
          suffix=""
        />

        <StatCard
          label="Average Maximum Wind"
          value={
            stats.average_max_wind_kmph
          }
          suffix=" km/h"
        />

        <StatCard
          label="Maximum Wind Recorded"
          value={
            stats.maximum_wind_kmph
          }
          suffix=" km/h"
        />

        <StatCard
          label="Average Minimum Pressure"
          value={
            stats.average_min_pressure_hpa
          }
          suffix=" hPa"
        />

        <StatCard
          label="Lowest Pressure Recorded"
          value={
            stats.lowest_pressure_hpa
          }
          suffix=" hPa"
        />

      </section>

      {/* ======================================================
          MAIN CONTENT
      ====================================================== */}

      <section className="history-content">

        {/* ====================================================
            ARCHIVE
        ==================================================== */}

        <div className="archive-panel">

          <div className="panel-header">

            <div>

              <h2>
                Historical Cyclone Archive
              </h2>

              <span>
                {filteredCyclones.length} cyclones
              </span>

            </div>

            {/* SEARCH */}

            <div className="search-wrapper">

              <span className="search-icon">
                🔍
              </span>

              <input
                type="text"
                placeholder="Search name, year or SID..."
                value={search}
                onChange={(event) =>
                  setSearch(
                    event.target.value
                  )
                }
              />

              {search && (
                <button
                  className="clear-search"
                  onClick={() =>
                    setSearch("")
                  }
                  aria-label="Clear search"
                >
                  ×
                </button>
              )}

            </div>

          </div>

          {/* ==================================================
              TABLE
          ================================================== */}

          <div className="table-wrapper">

            <table className="cyclone-table">

              <thead>

                <tr>

                  <th>
                    Cyclone
                  </th>

                  <th>
                    Year
                  </th>

                  <th>
                    Maximum Wind
                  </th>

                  <th>
                    Minimum Pressure
                  </th>

                  <th>
                    Distance to Odisha
                  </th>

                  <th>
                    Odisha Track
                  </th>

                </tr>

              </thead>

              <tbody>

                {filteredCyclones.length === 0 ? (

                  <tr>

                    <td
                      colSpan={6}
                      className="empty-state"
                    >

                      <div>

                        <span>
                          🔎
                        </span>

                        <strong>
                          No cyclones found
                        </strong>

                        <p>
                          Try searching for another
                          name or year.
                        </p>

                      </div>

                    </td>

                  </tr>

                ) : (

                  filteredCyclones.map(
                    (
                      cyclone,
                      index
                    ) => {

                      const isSelected =
                        selected?.name ===
                          cyclone.name &&
                        selected?.year ===
                          cyclone.year;

                      return (

                        <tr
                          key={
                            cyclone.sid ||
                            `${cyclone.name}-${cyclone.year}-${index}`
                          }
                          className={
                            isSelected
                              ? "selected-row"
                              : ""
                          }
                          onClick={() =>
                            openCyclone(
                              cyclone
                            )
                          }
                        >

                          {/* CYCLONE */}

                          <td>

                            <div className="cyclone-name">

                              <span className="storm-icon">
                                🌀
                              </span>

                              <div>

                                <strong>
                                  {cyclone.name}
                                </strong>

                                {cyclone.sid && (
                                  <small>
                                    {cyclone.sid}
                                  </small>
                                )}

                              </div>

                            </div>

                          </td>

                          {/* YEAR */}

                          <td>

                            <span className="year">
                              {cyclone.year}
                            </span>

                          </td>

                          {/* WIND */}

                          <td>

                            <strong>
                              {formatNumber(
                                cyclone.max_wind_kmph
                              )}
                            </strong>

                            <span className="unit">
                              km/h
                            </span>

                          </td>

                          {/* PRESSURE */}

                          <td>

                            <strong>
                              {formatNumber(
                                cyclone.min_pressure_hpa
                              )}
                            </strong>

                            <span className="unit">
                              hPa
                            </span>

                          </td>

                          {/* DISTANCE */}

                          <td>

                            {cyclone.minimum_distance_to_odisha_km !=
                            null
                              ? `${cyclone.minimum_distance_to_odisha_km} km`
                              : "—"}

                          </td>

                          {/* ODISHA TRACK */}

                          <td>

                            {cyclone.track_intersects_odisha ? (

                              <span className="odisha-yes">

                                <i />

                                YES

                              </span>

                            ) : (

                              <span className="odisha-no">

                                <i />

                                NO

                              </span>

                            )}

                          </td>

                        </tr>

                      );

                    }
                  )

                )}

              </tbody>

            </table>

          </div>

        </div>

        {/* ====================================================
            DETAILS
        ==================================================== */}

        <aside className="details-panel">

          {!selected ? (

            <div className="details-empty">

              <div className="details-empty-icon">
                🌀
              </div>

              <h3>
                Select a cyclone
              </h3>

              <p>
                Select any cyclone from the archive
                to view its historical details and
                comparison data.
              </p>

            </div>

          ) : (

            <>

              {/* ==============================================
                  SELECTED HEADER
              ============================================== */}

              <div className="selected-header">

                <div className="selected-storm-icon">
                  🌀
                </div>

                <div>

                  <span className="selected-label">
                    SELECTED CYCLONE
                  </span>

                  <h2>
                    {selected.name}
                  </h2>

                  <p>
                    {selected.year}
                  </p>

                </div>

              </div>

              {/* ==============================================
                  DETAILS
              ============================================== */}

              <div className="detail-stats">

                <DetailItem
                  label="Maximum Wind"
                  value={
                    selected.max_wind_kmph != null
                      ? `${selected.max_wind_kmph} km/h`
                      : "—"
                  }
                />

                <DetailItem
                  label="Minimum Pressure"
                  value={
                    selected.min_pressure_hpa != null
                      ? `${selected.min_pressure_hpa} hPa`
                      : "—"
                  }
                />

                <DetailItem
                  label="Minimum Distance"
                  value={
                    selected.minimum_distance_to_odisha_km !=
                    null
                      ? `${selected.minimum_distance_to_odisha_km} km`
                      : "—"
                  }
                />

                <DetailItem
                  label="Entered Odisha"
                  value={
                    selected.track_intersects_odisha
                      ? "Yes"
                      : "No"
                  }
                />

              </div>

              {/* ==============================================
                  COMPARISON
              ============================================== */}

              <div className="comparison-section">

                <div className="section-title">

                  <div>

                    <h3>
                      Similar Historical Cyclones
                    </h3>

                    <p>
                      Based on wind and pressure
                    </p>

                  </div>

                </div>

                {comparison?.error ? (

                  <div className="comparison-error">

                    {comparison.error}

                  </div>

                ) : comparison?.similar_cyclones &&
                  comparison.similar_cyclones.length >
                    0 ? (

                  <div className="similar-list">

                    {comparison.similar_cyclones.map(
                      (
                        cyclone,
                        index
                      ) => (

                        <div
                          className="similar-item"
                          key={`${cyclone.name}-${cyclone.year}-${index}`}
                        >

                          {/* LEFT */}

                          <div className="similar-info">

                            <div className="similar-rank">
                              {index + 1}
                            </div>

                            <div>

                              <strong>
                                {cyclone.name}
                              </strong>

                              <span>
                                {cyclone.year}
                              </span>

                            </div>

                          </div>

                          {/* RIGHT */}

                          <div className="similar-metrics">

                            <span>
                              {formatNumber(
                                cyclone.max_wind_kmph
                              )}{" "}
                              km/h
                            </span>

                            <span>
                              {formatNumber(
                                cyclone.min_pressure_hpa
                              )}{" "}
                              hPa
                            </span>

                            {cyclone.similarity_percentage !=
                              null && (
                              <span className="similarity">
                                {cyclone.similarity_percentage.toFixed(
                                  2
                                )}
                                %
                              </span>
                            )}

                          </div>

                        </div>

                      )
                    )}

                  </div>

                ) : (

                  <div className="no-comparison">

                    No comparison data available.

                  </div>

                )}

              </div>

            </>

          )}

        </aside>

      </section>

    </main>
  );
}

/* ============================================================
   STAT CARD
============================================================ */

function StatCard({
  label,
  value,
  suffix,
}: {
  label: string;
  value: number;
  suffix: string;
}) {
  return (
    <div className="stat-card">

      <span className="stat-label">
        {label}
      </span>

      <div className="stat-value">

        {formatNumber(value)}

        <small>
          {suffix}
        </small>

      </div>

    </div>
  );
}

/* ============================================================
   DETAIL ITEM
============================================================ */

function DetailItem({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="detail-item">

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
   NUMBER FORMAT
============================================================ */

function formatNumber(
  value?: number
) {
  if (value == null) {
    return "—";
  }

  return Number.isInteger(value)
    ? value.toString()
    : value.toFixed(1);
}