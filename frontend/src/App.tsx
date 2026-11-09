import { useState, useCallback, useEffect, useRef } from 'react';
import TripForm from '@/components/form/TripForm';
import RouteList from '@/components/routes/RouteList';
import RouteMap from '@/components/map/RouteMap';
import HeatmapSlider from '@/components/weather/HeatmapSlider';
import LoadingOverlay from '@/components/common/LoadingOverlay';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import { TruckIcon } from '@/components/common/Icons';
import { useTrip } from '@/hooks/useTrip';
import { getForecastCorridor } from '@/api/trips';
import type { TripRequest, TripAnalysis, CorridorPoint } from '@/types';
import './App.css';

export default function App() {
  const [analysis, setAnalysis] = useState<TripAnalysis | null>(null);
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(null);
  const [sliderHour, setSliderHour] = useState<number>(0);
  const [corridorPoints, setCorridorPoints] = useState<CorridorPoint[]>([]);
  const [isCorridorLoading, setIsCorridorLoading] = useState<boolean>(false);
  const [lastSubmittedRequest, setLastSubmittedRequest] = useState<TripRequest | null>(null);

  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const { mutate: runAnalysis, isPending: isLoading, error: apiError } = useTrip();

  const handleFormSubmit = useCallback(
    (request: TripRequest) => {
      setLastSubmittedRequest(request);
      setSliderHour(0);
      setCorridorPoints([]);

      runAnalysis(request, {
        onSuccess: (data) => {
          setAnalysis(data);
          const recId = data.recommendation?.route_id || data.routes[0]?.id || null;
          setSelectedRouteId(recId);
        },
      });
    },
    [runAnalysis]
  );

  const handleRetry = useCallback(() => {
    if (lastSubmittedRequest) {
      handleFormSubmit(lastSubmittedRequest);
    }
  }, [lastSubmittedRequest, handleFormSubmit]);

  const handleSliderChange = useCallback(
    (hour: number) => {
      setSliderHour(hour);

      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }

      if (hour === 0 || !analysis || !selectedRouteId) {
        setCorridorPoints([]);
        setIsCorridorLoading(false);
        return;
      }

      const activeRoute = analysis.routes.find((r) => r.id === selectedRouteId);
      if (!activeRoute) return;

      setIsCorridorLoading(true);

      debounceTimerRef.current = setTimeout(async () => {
        try {
          const resp = await getForecastCorridor({
            checkpoints: activeRoute.checkpoints.map((cp) => ({
              id: cp.id,
              sequence: cp.sequence,
              latitude: cp.latitude,
              longitude: cp.longitude,
            })),
            departure_at: analysis.trip.departure_at,
            hours: hour,
            load_weight_lb: analysis.trip.load_weight_lb,
          });
          setCorridorPoints(resp.points);
        } catch (err) {
          console.error('Failed to update corridor forecast:', err);
        } finally {
          setIsCorridorLoading(false);
        }
      }, 400);
    },
    [analysis, selectedRouteId]
  );

  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  const errorMessage = apiError
    ? (apiError as any)?.response?.data?.error?.message ||
      (apiError as Error).message ||
      'Failed to calculate routes. Please check your locations and try again.'
    : null;

  return (
    <div className="app-container">
      {isLoading && <LoadingOverlay />}

      <aside className="app-sidebar">
        <header className="app-header">
          <div className="app-logo">
            <div className="app-logo__icon-wrapper">
              <TruckIcon />
            </div>
            <div>
              <h1 className="app-logo__title">Spotter Routing</h1>
              <p className="app-logo__subtitle">Weather-Aware Truck Navigation</p>
            </div>
          </div>
        </header>

        <div className="app-sidebar__content">
          <TripForm onSubmit={handleFormSubmit} isLoading={isLoading} />

          {errorMessage && (
            <ErrorDisplay
              title="Analysis Error"
              message={errorMessage}
              onRetry={lastSubmittedRequest ? handleRetry : undefined}
            />
          )}

          {analysis && (
            <RouteList
              routes={analysis.routes}
              recommendation={analysis.recommendation}
              warnings={analysis.warnings}
              selectedRouteId={selectedRouteId}
              onSelectRoute={setSelectedRouteId}
            />
          )}
        </div>
      </aside>

      <main className="app-main">
        <div className="app-map-area">
          <RouteMap
            routes={analysis ? analysis.routes : []}
            selectedRouteId={selectedRouteId}
            onSelectRoute={setSelectedRouteId}
            corridorPoints={sliderHour > 0 ? corridorPoints : undefined}
            sliderHour={sliderHour}
            origin={analysis?.trip.origin}
            destination={analysis?.trip.destination}
          />
        </div>

        {analysis && (
          <HeatmapSlider
            departureAt={analysis.trip.departure_at}
            hours={sliderHour}
            onChange={handleSliderChange}
            isLoading={isCorridorLoading}
          />
        )}
      </main>
    </div>
  );
}
