# Weather-Aware Truck Routing

A web application that helps truck drivers compare three route alternatives using real-time weather conditions, load weight constraints, estimated checkpoint arrival times, and travel duration.

Built as a full-stack assessment for **Spotter AI — Full Stack Developer**.

## Features

- **Three Route Alternatives** — Fetches and compares 3 distinct routes from origin to destination
- **Distance-Based Weather Sampling** — Samples weather every 10, 25, or 50 miles along each route
- **ETA-Aware Forecasts** — Weather is looked up at the estimated time the truck will reach each checkpoint
- **Risk Classification** — Wind, rain, and snow classified into Low / Moderate / High / Severe / No Travel
- **Load-Dependent Rules** — Heavy loads increase wind risk severity per fleet safety specifications
- **Smart Recommendation** — Lexicographic ranking: fewest Severe miles → fewest High miles → lowest average risk → shortest duration
- **Interactive Map** — MapLibre GL JS map showing routes, risk-colored checkpoints, and weather details
- **Weather Corridor Heatmap** — Visualize forecast risk along routes with a 0–48 hour slider
- **No Travel Warnings** — Routes with dangerous conditions are flagged and excluded from recommendation

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite |
| Backend | Python 3.12+, Django, Django REST Framework |
| Map | MapLibre GL JS |
| Routing | OpenRouteService API |
| Weather | Open-Meteo API (free, no key required) |
| API State | TanStack Query |
| Validation | Zod (frontend), DRF Serializers (backend) |

## Architecture

```
React + TypeScript (Vite)
       |
       | HTTPS / JSON
       v
Django REST API
       |
       +-- Input Validation (DRF Serializers)
       +-- Geocoding Adapter (OpenRouteService)
       +-- Routing Adapter (OpenRouteService)
       |       └── 3 Route Alternatives
       +-- Checkpoint Service
       |       ├── Distance-based sampling along polyline
       |       └── Cumulative ETA calculation
       +-- Weather Adapter (Open-Meteo)
       |       ├── Forecast at checkpoint coordinates + ETA
       |       └── Unit normalization (km/h→mph, mm→in)
       +-- Risk Engine
       |       ├── Weather thresholds
       |       ├── Load adjustments
       |       └── Checkpoint risk classification
       +-- Route Scoring & Recommendation
       └── Response Serializer
```

## Prerequisites

- Python 3.12+
- Node.js 18+
- npm 9+
- OpenRouteService API key (free at [openrouteservice.org](https://openrouteservice.org/dev/#/signup))

## Local Setup

### 1. Clone and configure

```bash
git clone <repository-url>
cd weather-aware-routing
```

### 2. Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate    # macOS/Linux
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your ORS_API_KEY
```

### 3. Frontend setup

```bash
cd frontend
npm install
```

### 4. Run the application

**Backend** (terminal 1):
```bash
cd backend
source venv/bin/activate
python manage.py runserver 8000
```

**Frontend** (terminal 2):
```bash
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ORS_API_KEY` | Yes | OpenRouteService API key |
| `DEBUG` | No | Django debug mode (default: True) |
| `SECRET_KEY` | No | Django secret key (auto-generated for dev) |

## Sample Trip

For testing, try:
- **Origin:** Chicago, IL
- **Destination:** Detroit, MI
- **Departure:** Tomorrow at 8:00 AM
- **Load weight:** 32,000 lb
- **Sampling interval:** 25 miles

## Testing

### Backend tests
```bash
cd backend
source venv/bin/activate
pytest routing/tests/ -v
```

### Frontend build check
```bash
cd frontend
npx tsc --noEmit
npm run build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/trips/analyze/` | Analyze trip with 3 route alternatives |
| GET | `/api/v1/geocode/suggest/?q=...` | Geocode autocomplete suggestions |
| POST | `/api/v1/forecast-corridor/` | Get weather along corridor at slider time |

## Provider Configuration & Limitations

### OpenRouteService
- Free tier: 40 requests/minute, 2000 requests/day
- HGV (Heavy Goods Vehicle) profile used for truck routing
- Alternative routes: requests 3, may return fewer for some trips

### Open-Meteo
- Free, no API key required
- Hourly forecast available up to ~7 days ahead
- Weather variables: wind speed (km/h), rain (mm), snowfall (cm)
- All values converted to imperial units on the backend

## Known Limitations

1. **Route alternatives**: Some origin-destination pairs may return fewer than 3 distinct alternatives
2. **Forecast horizon**: Weather data beyond ~7 days may be unavailable
3. **ETA estimation**: Based on routing provider's duration data; does not account for real-time traffic
4. **Missing weather**: Checkpoints with missing forecasts are marked incomplete, not treated as safe
5. **No persistence**: Trip analyses are not stored; each analysis is a fresh computation

## Risk Model

See [docs/risk-model.md](docs/risk-model.md) for detailed documentation of:
- Weather thresholds and boundary conventions
- Load-dependent wind rules
- Multiple condition aggregation
- Missing data handling
- Route mileage estimation methodology

## License

Built for Spotter AI assessment purposes.
