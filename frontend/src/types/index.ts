export type RiskLevel = 'low' | 'moderate' | 'high' | 'severe' | 'no_travel';

export interface Coordinate {
  latitude: number;
  longitude: number;
}

export interface Location {
  label: string;
  latitude: number;
  longitude: number;
}

export interface TripRequest {
  origin: string;
  destination: string;
  departure_at: string;
  load_weight_lb: number;
  sampling_interval_miles: 10 | 25 | 50;
}

export interface WeatherData {
  forecast_at: string;
  wind_mph: number | null;
  rain_in_per_hour: number | null;
  snow_in_per_hour: number | null;
  source: string;
  available: boolean;
}

export interface ConditionRisk {
  wind: RiskLevel | null;
  rain: RiskLevel | null;
  snow: RiskLevel | null;
}

export interface CheckpointRisk {
  overall: RiskLevel;
  conditions: ConditionRisk;
  load_adjustments: string[];
  complete: boolean;
}

export interface Checkpoint {
  id: string;
  sequence: number;
  distance_from_origin_miles: number;
  latitude: number;
  longitude: number;
  estimated_arrival_at: string;
  weather: WeatherData | null;
  risk: CheckpointRisk | null;
}

export interface RouteGeometry {
  type: 'LineString';
  coordinates: [number, number][]; // [lng, lat]
}

export interface RouteMetrics {
  severe_miles: number;
  high_miles: number;
  average_risk: number;
  no_travel_checkpoints: number;
  forecast_coverage_percent: number;
  complete: boolean;
}

export interface AnalyzedRoute {
  id: string;
  label: string;
  geometry: RouteGeometry;
  distance_miles: number;
  duration_seconds: number;
  arrival_at: string;
  summary: string;
  metrics: RouteMetrics;
  checkpoints: Checkpoint[];
}

export interface Recommendation {
  route_id: string;
  status: 'recommended' | 'no_suitable_route' | 'partial';
  reason: string[];
}

export interface TripInfo {
  origin: Location;
  destination: Location;
  departure_at: string;
  load_weight_lb: number;
  sampling_interval_miles: number;
}

export interface TripAnalysis {
  trip: TripInfo;
  recommendation: Recommendation | null;
  routes: AnalyzedRoute[];
  warnings: string[];
  generated_at: string;
}

export interface GeocodeSuggestion {
  label: string;
  latitude: number;
  longitude: number;
}

export interface ForecastCorridorRequest {
  checkpoints: { id?: string; sequence?: number; latitude: number; longitude: number }[];
  departure_at: string;
  hours: number;
  load_weight_lb: number;
}

export interface CorridorPoint {
  id: string;
  sequence: number;
  latitude: number;
  longitude: number;
  target_time: string;
  overall_risk: RiskLevel;
  wind_risk: RiskLevel | null;
  rain_risk: RiskLevel | null;
  snow_risk: RiskLevel | null;
  wind_mph: number | null;
  rain_in_per_hour: number | null;
  snow_in_per_hour: number | null;
  load_adjustments: string[];
  complete: boolean;
}

export interface ForecastCorridorResponse {
  hours_offset: number;
  target_time: string;
  points: CorridorPoint[];
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
}
