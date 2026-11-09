import type { AnalyzedRoute, Recommendation } from '@/types';
import RouteCard from './RouteCard';
import RecommendationBanner from './RecommendationBanner';
import './RouteList.css';

interface RouteListProps {
  routes: AnalyzedRoute[];
  recommendation: Recommendation | null;
  warnings: string[];
  selectedRouteId: string | null;
  onSelectRoute: (routeId: string) => void;
}

export default function RouteList({
  routes,
  recommendation,
  warnings,
  selectedRouteId,
  onSelectRoute,
}: RouteListProps) {
  const routeLabels: Record<string, string> = {};
  for (const route of routes) {
    routeLabels[route.id] = route.label;
  }

  return (
    <div className="route-list">
      <RecommendationBanner
        recommendation={recommendation}
        routeLabels={routeLabels}
        warnings={warnings}
      />

      <div className="route-list__cards" role="list" aria-label="Route options">
        {routes.map((route, index) => (
          <div key={route.id} role="listitem">
            <RouteCard
              route={route}
              index={index}
              isSelected={selectedRouteId === route.id}
              isRecommended={recommendation?.route_id === route.id}
              recommendation={recommendation}
              onClick={() => onSelectRoute(route.id)}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
