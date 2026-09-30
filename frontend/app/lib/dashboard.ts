import fs from "fs";
import path from "path";

/* =========================================================
   FORECAST POINT
========================================================= */

export interface ForecastPoint {
  timestamp: string;

  hours_from_start?: number;

  hours_ahead?: number;

  forecast_type?: "observed" | "projected" | string;

  cyclone_position: {
    latitude: number;
    longitude: number;
  };

  distance_to_location_km?: number;

  wind_kmph: number;

  pressure_hpa: number;

  hazards?: {
    wind: number;
    rainfall: number;
    storm_surge: number;
    flood: number;
    combined: number;
  };

  risk: {
    score: number;
    percentage: number;
    level: string;
  };
}


/* =========================================================
   FORECAST PEAK
   NOTE:
   Backend peak is a summary object, NOT a ForecastPoint.
========================================================= */

export interface ForecastPeak {
  timestamp: string;

  risk_score: number;

  risk_percentage: number;

  risk_level: string;

  wind_kmph: number;

  pressure_hpa: number;

  distance_to_location_km: number;

  cyclone_latitude: number;

  cyclone_longitude: number;

  forecast_type?: string;
}


/* =========================================================
   CLOSEST APPROACH
========================================================= */

export interface ClosestApproach {
  timestamp: string;

  distance_to_location_km: number;

  wind_kmph: number;

  pressure_hpa: number;

  risk_percentage: number;

  risk_level: string;

  forecast_type?: string;
}


/* =========================================================
   INFRASTRUCTURE ASSET
========================================================= */

export interface InfrastructureAsset {
  id: string | null;

  name: string;

  type: string;

  class: string;

  latitude: number;

  longitude: number;

  distance_km: number;

  geometry: {
    type: string;
    coordinates: any;
  };

  properties?: Record<string, any>;
}


/* =========================================================
   INFRASTRUCTURE SUMMARY
========================================================= */

export interface InfrastructureSummary {
  roads: number;

  bridges: number;

  schools: number;

  healthcare: number;

  critical_buildings: number;

  total_assets: number;
}


/* =========================================================
   INFRASTRUCTURE EXPOSURE
========================================================= */

export interface InfrastructureExposure {
  asset_count: number;

  asset_density_per_km2: number;

  infrastructure_exposure_score: number;
}


/* =========================================================
   INFRASTRUCTURE
========================================================= */

export interface InfrastructureData {
  success: boolean;

  location: {
    latitude: number;
    longitude: number;
  };

  radius_km: number;

  summary: InfrastructureSummary;

  exposure: InfrastructureExposure;

  categories?: {
    roads?: InfrastructureAsset[];

    bridges?: InfrastructureAsset[];

    schools?: InfrastructureAsset[];

    healthcare?: InfrastructureAsset[];

    critical_buildings?: InfrastructureAsset[];
  };

  assets?: InfrastructureAsset[];
}


/* =========================================================
   ALERT
========================================================= */

export interface DashboardAlert {
  id: string;

  category?: string;

  level: string;

  title: string;

  message: string;

  action?: string;

  severity?: number;
}


/* =========================================================
   HISTORICAL DATA
========================================================= */

export interface HistoricalCyclone {
  name: string;

  year: number;

  max_wind_kmph: number;

  min_pressure_hpa: number;

  minimum_distance_to_odisha_km: number;

  track_intersects_odisha: boolean;

  similarity_percentage: number;
}


/* =========================================================
   DASHBOARD DATA
========================================================= */

export interface DashboardData {
  success: boolean;


  /* -------------------------------------------------------
     CYCLONE
  ------------------------------------------------------- */

  cyclone: {
    id: string;

    name: string;

    category: string;

    max_wind_kmph: number;

    min_pressure_hpa: number;

    current_position: {
      latitude: number;

      longitude: number;
    };
  };


  /* -------------------------------------------------------
     LOCATION
  ------------------------------------------------------- */

  location: {
    name: string;

    region: string;

    latitude: number;

    longitude: number;

    elevation_m: number;

    distance_from_coast_km: number;
  };


  /* -------------------------------------------------------
     CURRENT CONDITIONS
  ------------------------------------------------------- */

  current_conditions: {
    wind_kmph: number;

    pressure_hpa: number;

    rainfall_mm: number;
  };


  /* -------------------------------------------------------
     RISK
  ------------------------------------------------------- */

  risk: {
    score: number;

    percentage: number;

    level: string;

    drivers: string[];
  };


  /* -------------------------------------------------------
     HAZARDS
  ------------------------------------------------------- */

  hazards: {
    wind: number;

    rainfall: number;

    storm_surge: number;

    flood: number;

    combined: number;
  };


  /* -------------------------------------------------------
     VULNERABILITY
  ------------------------------------------------------- */

  vulnerability: {
    population: number;

    infrastructure: number;

    agriculture: number;

    healthcare: number;

    combined: number;
  };


  /* -------------------------------------------------------
     EXPOSURE
  ------------------------------------------------------- */

  exposure: {
    population_density: number;

    infrastructure_density: number;

    agriculture_percentage: number;

    score: number;
  };


  /* -------------------------------------------------------
     FORECAST
  ------------------------------------------------------- */

  forecast: {
    observed: ForecastPoint[];

    projected: ForecastPoint[];

    peak?: ForecastPeak;

    closest_approach?: ClosestApproach;
  };


  /* -------------------------------------------------------
     FORECAST TIMELINE
  ------------------------------------------------------- */

  forecast_timeline?: ForecastPoint[];


  /* -------------------------------------------------------
     ALERTS
  ------------------------------------------------------- */

  alerts?: DashboardAlert[];

  track_alerts?: any[];


  /* -------------------------------------------------------
     IMPACT
  ------------------------------------------------------- */

  impact?: any;


  /* -------------------------------------------------------
     INFRASTRUCTURE
  ------------------------------------------------------- */

  infrastructure?: InfrastructureData;


  /* -------------------------------------------------------
     EARLY WARNING
  ------------------------------------------------------- */

  early_warning?: {
    trigger?: boolean;

    warning_level?: string;

    priority?: string;

    current_risk?: number;

    current_level?: string;

    projected_risk?: number;

    projected_level?: string;

    lead_time_hours?: number;

    risk_forecast?: any[];

    hazard_forecast?: any[];

    reasons?: string[];

    trigger_details?: any;

    [key: string]: any;
  };


  /* -------------------------------------------------------
     ADVISORY
  ------------------------------------------------------- */

  advisory?: {
    available?: boolean;

    hours_ahead?: number;

    result?: any;

    [key: string]: any;
  };


  /* -------------------------------------------------------
     HISTORICAL
  ------------------------------------------------------- */

  historical?: {
    statistics: {
      total_cyclones: number;

      cyclones_entering_odisha: number;

      average_max_wind_kmph: number;

      maximum_wind_kmph: number;

      average_min_pressure_hpa: number;

      lowest_pressure_hpa: number;
    };

    similar_cyclones: HistoricalCyclone[];
  };


  /* -------------------------------------------------------
     MAP
  ------------------------------------------------------- */

  map?: {
    center: {
      latitude: number;

      longitude: number;
    };

    track: {
      observed: {
        type: string;

        coordinates: number[][];
      };

      projected: {
        type: string;

        coordinates: number[][];
      };

      all_points: any[];
    };

    target_marker: {
      type: string;

      coordinates: number[];
    };

    peak_risk?: any;

    infrastructure?: any;

    alerts?: any[];

    layers?: Record<string, boolean>;
  };


  /* -------------------------------------------------------
     SUMMARY
  ------------------------------------------------------- */

  summary?: {
    risk_level?: string;

    alert_count?: number;

    historical_summary?: any;

    [key: string]: any;
  };
}


/* =========================================================
   LOAD DASHBOARD JSON
========================================================= */

export function getDashboardData(): DashboardData {

  const filePath = path.join(
    process.cwd(),
    "public",
    "data",
    "dashboard-ui.json"
  );


  if (!fs.existsSync(filePath)) {

    throw new Error(
      `Dashboard data file not found: ${filePath}`
    );

  }


  const file = fs.readFileSync(
    filePath,
    "utf-8"
  );


  return JSON.parse(
    file
  ) as DashboardData;
}


/* =========================================================
   ALL FORECAST POINTS
========================================================= */

export function getAllForecastPoints(
  data: DashboardData
): ForecastPoint[] {

  return [
    ...(data.forecast?.observed ?? []),

    ...(data.forecast?.projected ?? []),
  ];
}


/* =========================================================
   FUTURE FORECAST POINTS
   Current observed point + projected points
========================================================= */

export function getFutureForecastPoints(
  data: DashboardData
): ForecastPoint[] {

  const projected =
    data.forecast?.projected ?? [];


  const observed =
    data.forecast?.observed ?? [];


  const current =
    observed.length > 0
      ? observed[observed.length - 1]
      : undefined;


  return current
    ? [current, ...projected]
    : projected;
}


/* =========================================================
   CURRENT FORECAST POINT
========================================================= */

export function getCurrentForecastPoint(
  data: DashboardData
): ForecastPoint | undefined {

  const observed =
    data.forecast?.observed ?? [];


  if (observed.length === 0) {

    return undefined;

  }


  return observed[
    observed.length - 1
  ];
}


/* =========================================================
   PEAK FORECAST
   Returns the backend peak summary when available.
   Otherwise calculates the peak from timeline points.
========================================================= */

export function getPeakForecastPoint(
  data: DashboardData
): ForecastPeak | undefined {

  /* -------------------------------------------------------
     BACKEND PROVIDED PEAK
  ------------------------------------------------------- */

  if (data.forecast?.peak) {

    return data.forecast.peak;

  }


  /* -------------------------------------------------------
     FALLBACK
  ------------------------------------------------------- */

  const points =
    getAllForecastPoints(data);


  if (points.length === 0) {

    return undefined;

  }


  const highest =
    points.reduce(
      (
        currentHighest,
        point
      ) => {

        return point.risk.percentage >
          currentHighest.risk.percentage
          ? point
          : currentHighest;

      }
    );


  return {
    timestamp:
      highest.timestamp,

    risk_score:
      highest.risk.score,

    risk_percentage:
      highest.risk.percentage,

    risk_level:
      highest.risk.level,

    wind_kmph:
      highest.wind_kmph,

    pressure_hpa:
      highest.pressure_hpa,

    distance_to_location_km:
      highest.distance_to_location_km ?? 0,

    cyclone_latitude:
      highest.cyclone_position.latitude,

    cyclone_longitude:
      highest.cyclone_position.longitude,

    forecast_type:
      highest.forecast_type,
  };
}


/* =========================================================
   TARGET LOCATION
========================================================= */

export function getTargetLocation(
  data: DashboardData
) {

  return {
    name:
      data.location.name,

    region:
      data.location.region,

    latitude:
      data.location.latitude,

    longitude:
      data.location.longitude,
  };
}


/* =========================================================
   MAP TRACK
========================================================= */

export function getMapTrack(
  data: DashboardData
) {

  return data.map?.track ?? {

    observed: {
      type: "LineString",

      coordinates: [],
    },

    projected: {
      type: "LineString",

      coordinates: [],
    },

    all_points: [],
  };
}


/* =========================================================
   CURRENT LOCATION
========================================================= */

export function getCurrentLocation(
  data: DashboardData
) {

  const current =
    getCurrentForecastPoint(data);


  if (current) {

    return {
      latitude:
        current.cyclone_position.latitude,

      longitude:
        current.cyclone_position.longitude,
    };

  }


  return {
    latitude:
      data.cyclone.current_position.latitude,

    longitude:
      data.cyclone.current_position.longitude,
  };
}


/* =========================================================
   PEAK LOCATION
========================================================= */

export function getPeakLocation(
  data: DashboardData
) {

  const peak =
    getPeakForecastPoint(data);


  if (!peak) {

    return undefined;

  }


  return {
    latitude:
      peak.cyclone_latitude,

    longitude:
      peak.cyclone_longitude,
  };
}


/* =========================================================
   RISK HELPERS
========================================================= */

export function getCurrentRisk(
  data: DashboardData
) {

  const current =
    getCurrentForecastPoint(data);


  return current?.risk ?? data.risk;
}


export function getPeakRisk(
  data: DashboardData
) {

  const peak =
    getPeakForecastPoint(data);


  if (!peak) {

    return data.risk;

  }


  return {
    score:
      peak.risk_score,

    percentage:
      peak.risk_percentage,

    level:
      peak.risk_level,
  };
}


/* =========================================================
   INFRASTRUCTURE HELPERS
========================================================= */

export function getInfrastructureSummary(
  data: DashboardData
): InfrastructureSummary | undefined {

  return data.infrastructure?.summary;
}


export function getInfrastructureExposure(
  data: DashboardData
): InfrastructureExposure | undefined {

  return data.infrastructure?.exposure;
}


/* =========================================================
   ALERT HELPERS
========================================================= */

export function getDashboardAlerts(
  data: DashboardData
): DashboardAlert[] {

  return data.alerts ?? [];
}


/* =========================================================
   LOCATION LABEL
========================================================= */

export function getLocationLabel(
  data: DashboardData
): string {

  return `${data.location.name}, ${data.location.region}`;
}


/* =========================================================
   FORECAST COUNT
========================================================= */

export function getForecastCount(
  data: DashboardData
): number {

  return getAllForecastPoints(data).length;
}


/* =========================================================
   PROJECTED FORECAST COUNT
========================================================= */

export function getProjectedForecastCount(
  data: DashboardData
): number {

  return data.forecast?.projected?.length ?? 0;
}


/* =========================================================
   OBSERVED FORECAST COUNT
========================================================= */

export function getObservedForecastCount(
  data: DashboardData
): number {

  return data.forecast?.observed?.length ?? 0;
}