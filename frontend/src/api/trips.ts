import client from './client';
import type {
  TripRequest,
  TripAnalysis,
  GeocodeSuggestion,
  ForecastCorridorRequest,
  ForecastCorridorResponse,
} from '@/types';

export async function analyzeTrip(request: TripRequest): Promise<TripAnalysis> {
  const { data } = await client.post<TripAnalysis>('/trips/analyze/', request);
  return data;
}

export async function geocodeSuggest(query: string): Promise<GeocodeSuggestion[]> {
  if (!query || query.trim().length < 2) return [];
  const { data } = await client.get<GeocodeSuggestion[]>('/geocode/suggest/', {
    params: { q: query.trim() },
  });
  return data;
}

export async function getForecastCorridor(
  request: ForecastCorridorRequest
): Promise<ForecastCorridorResponse> {
  const { data } = await client.post<ForecastCorridorResponse>(
    '/forecast-corridor/',
    request
  );
  return data;
}
