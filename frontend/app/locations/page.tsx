"use client";

import { useEffect, useRef } from "react";
import "leaflet/dist/leaflet.css";

import Sidebar from "@/app/components/Sidebar";
import Topbar from "@/app/components/Topbar";

export default function LocationsPage() {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<any>(null);

  const latitude = 19.8135;
  const longitude = 85.8312;

  useEffect(() => {
    let cancelled = false;

    async function initializeMap() {
      if (!mapContainerRef.current || mapRef.current) {
        return;
      }

      const L = await import("leaflet");

      if (
        cancelled ||
        !mapContainerRef.current ||
        mapRef.current
      ) {
        return;
      }

      const map = L.map(mapContainerRef.current, {
        center: [latitude, longitude],
        zoom: 10,
        zoomControl: false,
      });

      mapRef.current = map;

      /* =====================================================
         MAP TILES
      ===================================================== */

      L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
          attribution:
            "© OpenStreetMap contributors",
        }
      ).addTo(map);

      /* =====================================================
         ZOOM CONTROL
      ===================================================== */

      L.control
        .zoom({
          position: "topright",
        })
        .addTo(map);

      /* =====================================================
         PURI MARKER
      ===================================================== */

      const targetIcon = L.divIcon({
        className: "location-target-marker",

        html: `
          <div class="location-marker-ring">
            <div class="location-marker-dot"></div>
          </div>
        `,

        iconSize: [42, 42],
        iconAnchor: [21, 21],
      });

      L.marker(
        [latitude, longitude],
        {
          icon: targetIcon,
        }
      )
        .addTo(map)
        .bindPopup(`
          <div style="min-width:180px">
            <strong style="font-size:16px">
              Puri, Odisha
            </strong>

            <br/>

            <span>
              Target Impact Location
            </span>

            <br/><br/>

            <strong>Latitude:</strong>
            ${latitude}°

            <br/>

            <strong>Longitude:</strong>
            ${longitude}°
          </div>
        `)
        .openPopup();

      /* =====================================================
         LOCATION CIRCLE
      ===================================================== */

      L.circle(
        [latitude, longitude],
        {
          radius: 10000,
          color: "#12c7ed",
          weight: 1.5,
          fillColor: "#12c7ed",
          fillOpacity: 0.08,
        }
      ).addTo(map);

      /* =====================================================
         INVALIDATE SIZE
      ===================================================== */

      setTimeout(() => {
        map.invalidateSize();
      }, 150);
    }

    initializeMap();

    return () => {
      cancelled = true;

      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  return (
    <main className="app">

      {/* ===================================================
          SIDEBAR
      =================================================== */}

      <Sidebar />


      {/* ===================================================
          MAIN
      =================================================== */}

      <div className="main">

        <Topbar />

        <div className="content">

          {/* =================================================
              HEADER
          ================================================= */}

          <div className="page-header">

            <div>

              <h1>
                Locations
              </h1>

              <p>
                Manage cyclone impact assessment locations.
              </p>

            </div>

          </div>


          {/* =================================================
              LOCATION DETAILS
          ================================================= */}

          <section className="location-card card">

            <div className="location-card-header">

              <div>

                <span className="location-label">
                  TARGET LOCATION
                </span>

                <h2>
                  Puri, Odisha
                </h2>

              </div>

              <div className="location-status">

                <span className="location-status-dot" />

                ACTIVE TARGET

              </div>

            </div>


            <div className="location-stats">

              <div>

                <span>
                  Latitude
                </span>

                <strong>
                  19.8135°
                </strong>

              </div>


              <div>

                <span>
                  Longitude
                </span>

                <strong>
                  85.8312°
                </strong>

              </div>


              <div>

                <span>
                  Elevation
                </span>

                <strong>
                  10 m
                </strong>

              </div>


              <div>

                <span>
                  Coast Distance
                </span>

                <strong>
                  1.9 km
                </strong>

              </div>

            </div>

          </section>


          {/* =================================================
              MAP
          ================================================= */}

          <section className="location-map-card card">

            <div className="location-map-header">

              <div>

                <span className="location-label">
                  LOCATION MAP
                </span>

                <h2>
                  Puri Impact Assessment Area
                </h2>

              </div>

              <div className="coordinates-badge">

                {latitude.toFixed(4)}°N,
                {" "}
                {longitude.toFixed(4)}°E

              </div>

            </div>


            <div
              ref={mapContainerRef}
              className="location-map"
            />


            {/* MAP LEGEND */}

            <div className="location-map-legend">

              <div className="legend-item">

                <span className="legend-dot target" />

                Target Location

              </div>


              <div className="legend-item">

                <span className="legend-circle" />

                10 km Assessment Radius

              </div>

            </div>

          </section>

        </div>

      </div>

    </main>
  );
}