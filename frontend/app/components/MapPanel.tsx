"use client";

import { useEffect, useRef, useState } from "react";
import "leaflet/dist/leaflet.css";

import type {
  DashboardData,
  InfrastructureAsset,
} from "@/app/lib/dashboard";


/* =========================================================
   LAYER TYPES
========================================================= */

type LayerKey =
  | "observed"
  | "projected"
  | "roads"
  | "bridges"
  | "schools"
  | "healthcare"
  | "critical"
  | "target";


/* =========================================================
   LAYER LABELS
========================================================= */

const labels: Record<LayerKey, string> = {
  observed: "Observed Track",
  projected: "Projected Track",
  roads: "Road Network",
  bridges: "Bridges",
  schools: "Schools",
  healthcare: "Healthcare",
  critical: "Critical Buildings",
  target: "Target Location",
};


/* =========================================================
   INFRASTRUCTURE MARKER CONFIG
========================================================= */

const markerConfig: Record<
  LayerKey,
  {
    emoji: string;
    color: string;
    title: string;
  }
> = {
  observed: {
    emoji: "🌀",
    color: "#ef4444",
    title: "Current Cyclone",
  },

  projected: {
    emoji: "➤",
    color: "#f59e0b",
    title: "Projected Track",
  },

  roads: {
    emoji: "",
    color: "#8ed1fc",
    title: "Road Network",
  },

  bridges: {
    emoji: "🌉",
    color: "#8b5cf6",
    title: "Bridge",
  },

  schools: {
    emoji: "🏫",
    color: "#f59e0b",
    title: "School",
  },

  healthcare: {
    emoji: "🏥",
    color: "#ef4444",
    title: "Healthcare",
  },

  critical: {
    emoji: "🏛️",
    color: "#ec4899",
    title: "Critical Building",
  },

  target: {
    emoji: "📍",
    color: "#12c7ed",
    title: "Target Location",
  },
};


/* =========================================================
   CREATE INFRASTRUCTURE ICON
========================================================= */

function iconFor(
  L: any,
  type: LayerKey
) {
  const config =
    markerConfig[type];

  if (
    type === "roads"
  ) {
    return null;
  }

  return L.divIcon({
    className:
      `infra-marker infra-${type}`,

    html: `
      <div
        style="
          width:30px;
          height:30px;
          border-radius:50%;
          background:${config.color};
          border:2px solid rgba(255,255,255,.95);
          display:flex;
          align-items:center;
          justify-content:center;
          font-size:14px;
          box-shadow:
            0 2px 8px rgba(0,0,0,.35),
            0 0 0 4px ${config.color}33;
        "
      >
        ${config.emoji}
      </div>
    `,

    iconSize: [
      30,
      30,
    ],

    iconAnchor: [
      15,
      15,
    ],

    popupAnchor: [
      0,
      -14,
    ],
  });
}


/* =========================================================
   MAP PANEL
========================================================= */

export default function MapPanel({
  data,
}: {
  data: DashboardData;
}) {

  const container =
    useRef<HTMLDivElement | null>(null);

  const mapRef =
    useRef<any>(null);

  const groupsRef =
    useRef<
      Partial<
        Record<
          LayerKey,
          any
        >
      >
    >({});


  /* =======================================================
     LAYER VISIBILITY
  ======================================================= */

  const [visible, setVisible] =
    useState<
      Record<
        LayerKey,
        boolean
      >
    >({
      observed: true,
      projected: true,
      roads: true,
      bridges: true,
      schools: true,
      healthcare: true,
      critical: true,
      target: true,
    });


  /* =======================================================
     MAP INITIALIZATION
  ======================================================= */

  useEffect(() => {

    let cancelled = false;


    async function init() {

      if (
        !container.current ||
        mapRef.current
      ) {
        return;
      }


      const L =
        await import("leaflet");


      if (
        cancelled ||
        !container.current ||
        mapRef.current
      ) {
        return;
      }


      /* ===================================================
         CREATE MAP
      =================================================== */

      const map =
        L.map(
          container.current,
          {
            center: [
              data.location.latitude,
              data.location.longitude,
            ],

            zoom: 8,

            zoomControl: false,
          }
        );


      mapRef.current =
        map;


      /* ===================================================
         BASE MAP
      =================================================== */

      L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
          attribution:
            "© OpenStreetMap contributors",
        }
      ).addTo(map);


      /* ===================================================
         ZOOM CONTROL
      =================================================== */

      L.control
        .zoom({
          position: "topleft",
        })
        .addTo(map);


      /* ===================================================
         LAYER GROUPS
      =================================================== */

      const observedGroup =
        L.layerGroup();

      const projectedGroup =
        L.layerGroup();

      const roadsGroup =
        L.layerGroup();

      const bridgesGroup =
        L.layerGroup();

      const schoolsGroup =
        L.layerGroup();

      const healthcareGroup =
        L.layerGroup();

      const criticalGroup =
        L.layerGroup();

      const targetGroup =
        L.layerGroup();


      groupsRef.current = {
        observed:
          observedGroup,

        projected:
          projectedGroup,

        roads:
          roadsGroup,

        bridges:
          bridgesGroup,

        schools:
          schoolsGroup,

        healthcare:
          healthcareGroup,

        critical:
          criticalGroup,

        target:
          targetGroup,
      };


      /* ===================================================
         TRACK DATA
      =================================================== */

      const observed =
        data.map?.track?.observed
          ?.coordinates?.length
          ? data.map.track.observed.coordinates
          : (
              data.forecast.observed ??
              []
            ).map(
              (point) => [
                point.cyclone_position.longitude,
                point.cyclone_position.latitude,
              ]
            );


      const projected =
        data.map?.track?.projected
          ?.coordinates?.length
          ? data.map.track.projected.coordinates
          : (
              data.forecast.projected ??
              []
            ).map(
              (point) => [
                point.cyclone_position.longitude,
                point.cyclone_position.latitude,
              ]
            );


      const coords = [
        ...observed,
        ...projected,
      ].map(
        ([lng, lat]) =>
          [
            lat,
            lng,
          ] as [
            number,
            number
          ]
      );


      /* ===================================================
         OBSERVED TRACK
      =================================================== */

      if (
        observed.length
      ) {

        const observedLatLng =
          observed.map(
            ([lng, lat]) =>
              [
                lat,
                lng,
              ] as [
                number,
                number
              ]
          );


        L.polyline(
          observedLatLng,
          {
            color:
              "#ff625d",

            weight:
              4,

            opacity:
              0.95,
          }
        )
          .addTo(
            observedGroup
          );


        observed.forEach(
          (
            [lng, lat],
            index
          ) => {

            const point =
              data.forecast
                .observed?.[
                index
              ];


            const isCurrent =
              index ===
              observed.length - 1;


            L.circleMarker(
              [
                lat,
                lng,
              ],
              {
                radius:
                  isCurrent
                    ? 7
                    : 4,

                color:
                  "#ffffff",

                fillColor:
                  "#ff625d",

                fillOpacity:
                  1,

                weight:
                  2,
              }
            )
              .bindTooltip(
                point
                  ? `
                    <strong>
                      Observed
                    </strong>
                    <br/>
                    Wind:
                    ${point.wind_kmph} km/h
                    <br/>
                    Risk:
                    ${point.risk.percentage.toFixed(1)}%
                  `
                  : "Observed"
              )
              .addTo(
                observedGroup
              );

          }
        );

      }


      /* ===================================================
         PROJECTED TRACK
      =================================================== */

      if (
        projected.length
      ) {

        const projectedLatLng =
          projected.map(
            ([lng, lat]) =>
              [
                lat,
                lng,
              ] as [
                number,
                number
              ]
          );


        /*
         * Connect current observed point
         * to first projected point.
         */

        const latestObserved =
          observed.length
            ? observed[
                observed.length - 1
              ]
            : undefined;


        const projectedTrack =
          latestObserved
            ? [
                [
                  latestObserved[1],
                  latestObserved[0],
                ] as [
                  number,
                  number
                ],

                ...projectedLatLng,
              ]
            : projectedLatLng;


        L.polyline(
          projectedTrack,
          {
            color:
              "#ffb642",

            weight:
              4,

            dashArray:
              "8 7",

            opacity:
              0.95,
          }
        )
          .addTo(
            projectedGroup
          );


        projected.forEach(
          (
            [lng, lat],
            index
          ) => {

            const point =
              data.forecast
                .projected?.[
                index
              ];


            L.circleMarker(
              [
                lat,
                lng,
              ],
              {
                radius:
                  4,

                color:
                  "#ffffff",

                fillColor:
                  "#ffb642",

                fillOpacity:
                  1,

                weight:
                  2,
              }
            )
              .bindTooltip(
                point
                  ? `
                    <strong>
                      Projected
                      ${
                        point.hours_ahead
                          ? `+${point.hours_ahead}h`
                          : ""
                      }
                    </strong>

                    <br/>

                    Wind:
                    ${point.wind_kmph} km/h

                    <br/>

                    Risk:
                    ${point.risk.percentage.toFixed(1)}%
                  `
                  : "Projected"
              )
              .addTo(
                projectedGroup
              );

          }
        );

      }


      /* ===================================================
         INFRASTRUCTURE
      =================================================== */

      const categories =
        data.infrastructure
          ?.categories;


      /* ===================================================
         ROADS
      =================================================== */

      const roads =
        categories?.roads ??
        [];


      const roadFeatures =
        roads
          .filter(
            (
              asset
            ) =>
              asset.geometry
                ?.type ===
              "LineString"
          )
          .map(
            (
              asset
            ) => ({
              type:
                "Feature",

              properties: {
                name:
                  asset.name,

                class:
                  asset.class,
              },

              geometry:
                asset.geometry,
            })
          );


      if (
        roadFeatures.length
      ) {

        L.geoJSON(
          {
            type:
              "FeatureCollection",

            features:
              roadFeatures,
          } as any,
          {
            style:
              (
                feature: any
              ) => {

                const roadClass =
                  feature
                    ?.properties
                    ?.class;


                const majorRoad =
                  [
                    "primary",
                    "trunk",
                    "secondary",
                  ].includes(
                    roadClass
                  );


                return {
                  color:
                    majorRoad
                      ? "#8ed1fc"
                      : "#66808f",

                  weight:
                    majorRoad
                      ? 2.5
                      : 1,

                  opacity:
                    0.75,
                };

              },
          }
        )
          .addTo(
            roadsGroup
          );

      }


      /* ===================================================
         ADD ASSET MARKERS
      =================================================== */

      const addAssets = (
        assets:
          InfrastructureAsset[],

        group:
          any,

        type:
          LayerKey
      ) => {

        const icon =
          iconFor(
            L,
            type
          );


        if (!icon) {
          return;
        }


        assets.forEach(
          (
            asset
          ) => {

            if (
              typeof asset.latitude !==
                "number" ||
              typeof asset.longitude !==
                "number"
            ) {
              return;
            }


            const distance =
              typeof asset.distance_km ===
                "number"
                ? asset.distance_km.toFixed(
                    2
                  )
                : "—";


            const popup =
              `
                <div
                  style="
                    min-width:170px;
                    font-family:Arial,sans-serif;
                  "
                >

                  <div
                    style="
                      font-size:14px;
                      font-weight:700;
                      margin-bottom:5px;
                    "
                  >
                    ${markerConfig[type].emoji}
                    ${markerConfig[type].title}
                  </div>

                  <div
                    style="
                      font-size:13px;
                      font-weight:600;
                      margin-bottom:5px;
                    "
                  >
                    ${
                      asset.name ||
                      "Unnamed"
                    }
                  </div>

                  <div
                    style="
                      font-size:11px;
                      color:#667;
                    "
                  >
                    Type:
                    ${
                      asset.type ||
                      markerConfig[type].title
                    }
                  </div>

                  <div
                    style="
                      font-size:11px;
                      color:#667;
                      margin-top:3px;
                    "
                  >
                    Distance:
                    ${distance} km
                  </div>

                </div>
              `;


            L.marker(
              [
                asset.latitude,
                asset.longitude,
              ],
              {
                icon,
              }
            )
              .bindPopup(
                popup
              )
              .addTo(
                group
              );

          }
        );

      };


      /* ===================================================
         BRIDGES
      =================================================== */

      addAssets(
        categories?.bridges ??
          [],

        bridgesGroup,

        "bridges"
      );


      /* ===================================================
         SCHOOLS
      =================================================== */

      addAssets(
        categories?.schools ??
          [],

        schoolsGroup,

        "schools"
      );


      /* ===================================================
         HEALTHCARE / HOSPITALS
      =================================================== */

      addAssets(
        categories?.healthcare ??
          [],

        healthcareGroup,

        "healthcare"
      );


      /* ===================================================
         CRITICAL BUILDINGS
      =================================================== */

      addAssets(
        categories?.critical_buildings ??
          [],

        criticalGroup,

        "critical"
      );


      /* ===================================================
         CURRENT CYCLONE
      =================================================== */

      const current =
        data.cyclone
          .current_position;


      const cycloneIcon =
        iconFor(
          L,
          "observed"
        );


      if (
        cycloneIcon
      ) {

        L.marker(
          [
            current.latitude,
            current.longitude,
          ],
          {
            icon:
              cycloneIcon,
          }
        )
          .bindPopup(
            `
              <strong>
                ${data.cyclone.id}
              </strong>

              <br/>

              ${data.cyclone.name}

              <br/>

              Wind:
              ${data.current_conditions.wind_kmph}
              km/h

              <br/>

              Pressure:
              ${data.current_conditions.pressure_hpa}
              hPa

              <br/>

              Risk:
              ${data.risk.percentage.toFixed(1)}%

              <br/>

              Status:
              ${data.risk.level}
            `
          )
          .addTo(
            observedGroup
          );

      }


      /* ===================================================
         TARGET LOCATION
      =================================================== */

      const target =
        data.location;


      const targetIcon =
        iconFor(
          L,
          "target"
        );


      if (
        targetIcon
      ) {

        L.marker(
          [
            target.latitude,
            target.longitude,
          ],
          {
            icon:
              targetIcon,
          }
        )
          .bindPopup(
            `
              <strong>
                Target Location
              </strong>

              <br/>

              ${target.name},
              ${target.region}

              <br/>

              Elevation:
              ${target.elevation_m} m

              <br/>

              Coast:
              ${target.distance_from_coast_km} km
            `
          )
          .addTo(
            targetGroup
          );

      }


      /* ===================================================
         ADD VISIBLE GROUPS
      =================================================== */

      Object.entries(
        groupsRef.current
      ).forEach(
        (
          [
            key,
            group,
          ]
        ) => {

          if (
            visible[
              key as LayerKey
            ]
          ) {

            group?.addTo(
              map
            );

          }

        }
      );


      /* ===================================================
         FIT MAP
      =================================================== */

      if (
        coords.length
      ) {

        map.fitBounds(
          L.latLngBounds(
            coords
          ),
          {
            padding: [
              35,
              35,
            ],
          }
        );

      }


      /* ===================================================
         RESIZE
      =================================================== */

      setTimeout(
        () => {

          if (
            !cancelled
          ) {

            map.invalidateSize();

          }

        },
        150
      );

    }


    init();


    /* =====================================================
       CLEANUP
    ===================================================== */

    return () => {

      cancelled =
        true;


      if (
        mapRef.current
      ) {

        mapRef.current.remove();

        mapRef.current =
          null;

      }


      groupsRef.current =
        {};

    };


    // Map is initialized once
    // for the current dashboard payload.
    // eslint-disable-next-line react-hooks/exhaustive-deps

  }, [data]);


  /* =========================================================
     TOGGLE LAYER
  ========================================================= */

  const toggle = (
    key:
      LayerKey,

    checked:
      boolean
  ) => {

    setVisible(
      (
        current
      ) => ({
        ...current,

        [key]:
          checked,
      })
    );


    const group =
      groupsRef.current[
        key
      ];

    const map =
      mapRef.current;


    if (
      !group ||
      !map
    ) {
      return;
    }


    if (
      checked
    ) {

      group.addTo(
        map
      );

    } else {

      map.removeLayer(
        group
      );

    }

  };


  /* =========================================================
     INFRASTRUCTURE SUMMARY
  ========================================================= */

  const infra =
    data.infrastructure
      ?.summary;


  /* =========================================================
     UI
  ========================================================= */

  return (
    <section
      className="map-panel card"
    >

      <div
        ref={container}
        className="leaflet-map"
      />


      {/* ===================================================
          MAP LAYERS PANEL
      =================================================== */}

      <div
        className="map-layers"
      >

        <strong>
          Map Layers
        </strong>


        {(
          [
            "observed",
            "projected",
            "roads",
            "bridges",
            "schools",
            "healthcare",
            "critical",
            "target",
          ] as LayerKey[]
        ).map(
          (
            key
          ) => (

            <label
              key={key}
            >

              <input
                type="checkbox"
                checked={
                  visible[key]
                }
                onChange={
                  (
                    event
                  ) =>
                    toggle(
                      key,
                      event.target.checked
                    )
                }
              />

              <span>
                {labels[key]}
              </span>

            </label>

          )
        )}


        {/* =================================================
            ASSET SUMMARY
        ================================================= */}

        {infra && (

          <div
            style={{
              marginTop:
                10,

              paddingTop:
                9,

              borderTop:
                "1px solid rgba(255,255,255,.12)",
            }}
          >

            <strong
              style={{
                display:
                  "block",

                fontSize:
                  "16px",

                marginBottom:
                  "2px",
              }}
            >
              {infra.total_assets.toLocaleString()}
            </strong>

            <small
              style={{
                display:
                  "block",

                opacity:
                  0.7,

                lineHeight:
                  1.35,
              }}
            >
              infrastructure assets
              <br />
              within 10 km radius
            </small>

          </div>

        )}

      </div>

    </section>
  );
}