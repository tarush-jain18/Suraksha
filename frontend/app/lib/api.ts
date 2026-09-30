export interface CycloneTrackPoint {
  timestamp: string;
  latitude: number;
  longitude: number;
  wind_kmph: number;
  pressure_hpa: number;
}

export interface Cyclone {
  id: string;
  name: string;
  category: string;
  max_wind_kmph: number;
  min_pressure_hpa: number;
  track: CycloneTrackPoint[];
}

export interface MonitorStatus {
  running: boolean;
  last_run: string | null;
  last_warning_level: string | null;
  last_risk_score: number | null;
  dispatch_count: number;
}

export async function getCyclone(
  cycloneId: string
): Promise<Cyclone> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/api/cyclones/${cycloneId}`,
    {
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch cyclone: ${response.status}`
    );
  }

  return response.json();
}

export async function getMonitorStatus(
  cycloneId: string
): Promise<MonitorStatus> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/api/cyclones/${cycloneId}/monitor?action=status`,
    {
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch monitor status: ${response.status}`
    );
  }

  const data = await response.json();

  return data.monitor;
}

export interface ImpactData {
  success: boolean;
  cyclone_id: string;
  cyclone_name: string;

  target: {
    latitude: number;
    longitude: number;
  };

  forecast_hour: number;

  impact: {
    location: {
      latitude: number;
      longitude: number;
    };

    cyclone: {
      latitude: number;
      longitude: number;
      distance_km: number;
      wind_kmph: number;
      pressure_hpa: number;
    };

    hazards: {
      wind: number;
      rainfall: number;
      storm_surge: number;
      flood: number;
      combined: number;
    };

    vulnerability: {
      population: number;
      infrastructure: number;
      agriculture: number;
      healthcare: number;
      combined: number;
    };

    exposure: {
      population_density: number;
      infrastructure_density: number;
      agriculture_percentage: number;
      score: number;
    };

    risk: {
      score: number;
      percentage: number;
      level: string;
      drivers: string[];
    };

    location_context: {
      latitude: number;
      longitude: number;
      rainfall_mm: number;
      elevation_m: number;
      distance_from_coast_km: number;
      population_density: number;
      agriculture_percentage: number;
      infrastructure_density: number;
      healthcare_access: number;
      healthcare_facilities: number;
      nearest_healthcare_km: number;
    };

    forecast: {
      hours_ahead: number;
      timestamp: string;
      forecast_type: string;
    };
  };
}

export async function getImpact(
  cycloneId: string,
  hours: number
): Promise<ImpactData> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/api/cyclones/${cycloneId}/impact/${hours}`,
    {
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch ${hours}h impact: ${response.status}`
    );
  }

  return response.json();
}