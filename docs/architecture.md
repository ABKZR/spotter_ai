# Architecture Documentation

## System Overview

The Weather-Aware Truck Routing application follows a client-server architecture with a React frontend communicating with a Django REST API backend. All external service communication happens through the backend.

## Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (React)                     │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ TripForm │  │RouteList │  │ RouteMap │  │ Heatmap │ │
│  │          │  │& Cards   │  │(MapLibre)│  │ Slider  │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │
│       │              │             │              │      │
│       └──────────────┴─────────────┴──────────────┘      │
│                          │                                │
│                   TanStack Query                          │
│                          │                                │
└──────────────────────────┼────────────────────────────────┘
                           │ HTTPS / JSON
                           ▼
┌──────────────────────────────────────────────────────────┐
│                  Backend (Django REST)                     │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                    API Layer                         │ │
│  │  POST /api/v1/trips/analyze/                        │ │
│  │  GET  /api/v1/geocode/suggest/                      │ │
│  │  POST /api/v1/forecast-corridor/                    │ │
│  └────────────────────┬────────────────────────────────┘ │
│                       │                                   │
│  ┌────────────────────▼────────────────────────────────┐ │
│  │              Route Planner (Orchestrator)            │ │
│  │  1. Geocode → 2. Route → 3. Checkpoint → 4. ETA    │ │
│  │  → 5. Weather → 6. Risk → 7. Score → 8. Recommend  │ │
│  └───┬────────────┬───────────────┬────────────────────┘ │
│      │            │               │                       │
│  ┌───▼──┐    ┌────▼────┐    ┌─────▼─────┐               │
│  │Domain│    │Services │    │ Providers │               │
│  │      │    │         │    │           │               │
│  │risk  │    │checkpoint│   │geocoding  │               │
│  │units │    │eta_calc │    │routing    │               │
│  │models│    │weather  │    │weather    │               │
│  │      │    │recommend│    │           │               │
│  └──────┘    └─────────┘    └─────┬─────┘               │
│                                    │                      │
└────────────────────────────────────┼──────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
              ┌─────▼─────┐  ┌──────▼──────┐  ┌─────▼─────┐
              │OpenRoute   │  │  Open-Meteo │  │OSM Tiles  │
              │Service API │  │ Weather API │  │(MapLibre) │
              └────────────┘  └─────────────┘  └───────────┘
```

## Frontend Responsibilities

- **Trip Input Form**: Collect origin, destination, departure time, load weight, sampling interval
- **Geocode Autocomplete**: Suggest locations as the user types
- **Route Display**: Show route comparison cards with risk metrics
- **Recommendation**: Display which route is recommended and why
- **Map Visualization**: Render routes, checkpoints, and risk markers using MapLibre GL JS
- **Weather Corridor**: Visualize risk along routes at different forecast times
- **State Management**: Handle loading, error, partial, and success states

The frontend does NOT perform risk calculations or weather processing.

## Backend Responsibilities

### API Layer (`routing/api/`)
- Request validation via DRF serializers
- Response serialization
- Error formatting (never exposes secrets or stack traces)

### Services Layer (`routing/services/`)
- **route_planner.py**: Orchestrates the full analysis pipeline
- **checkpoint_generator.py**: Generates distance-based checkpoints along polyline geometry
- **eta_calculator.py**: Calculates estimated arrival time at each checkpoint using cumulative duration
- **weather_enricher.py**: Fetches and attaches weather forecasts to checkpoints
- **recommendation.py**: Scores routes and produces lexicographic recommendation

### Domain Layer (`routing/domain/`)
- **risk.py**: Weather threshold classification + load-dependent adjustments
- **units.py**: Unit conversions (km/h→mph, mm→in, cm→in)
- **models.py**: Data classes for the domain (no database ORM)

### Provider Layer (`routing/providers/`)
- **geocoding_provider.py**: OpenRouteService geocoding
- **routing_provider.py**: OpenRouteService directions with alternatives
- **weather_provider.py**: Open-Meteo hourly forecast

## API Contract

### POST /api/v1/trips/analyze/

**Request:**
```json
{
  "origin": "Chicago, IL",
  "destination": "Detroit, MI",
  "departure_at": "2026-11-10T08:00:00-06:00",
  "load_weight_lb": 32000,
  "sampling_interval_miles": 25
}
```

**Response:** Complete trip analysis with recommendation, 3 analyzed routes (each with checkpoints, weather, risk, metrics), and warnings.

### GET /api/v1/geocode/suggest/?q=Chicago

Returns geocoding suggestions for autocomplete.

### POST /api/v1/forecast-corridor/

Returns weather risk data along route checkpoints at a specific forecast time (for the 0-48h slider).

## ETA Pipeline

```
Departure Time
     │
     ▼
Route Segments (from routing provider)
  [seg1: 15mi, 900s] [seg2: 20mi, 1200s] [seg3: 10mi, 600s]
     │
     ▼
Cumulative Duration at Segment Boundaries
  [0s → 900s → 2100s → 2700s]
     │
     ▼
Checkpoint at Distance d
  → Find containing segment
  → Interpolate duration within segment
  → Add to departure time
     │
     ▼
Checkpoint ETA (UTC)
```

## Forecast Caching & Failure Handling

- Weather requests are deduplicated by coordinate + forecast hour
- Bounded concurrency (max 5 parallel requests)
- Connection and read timeouts on all external calls
- Rate limit errors trigger bounded retries with backoff
- Missing forecasts are recorded as unavailable (never treated as safe)
- Partial results are distinguishable from complete results

## Map & Heatmap Data Flow

1. Backend returns GeoJSON geometry and checkpoint data
2. Frontend adds route geometries as MapLibre GeoJSON sources
3. Checkpoint markers are rendered as circle layers with risk-driven colors
4. Weather corridor uses line layers with data-driven width/color
5. Slider changes trigger corridor forecast API → update line layer data
6. Map instance is created once and updated via `setData()` calls
