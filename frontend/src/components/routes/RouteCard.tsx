import type { AnalyzedRoute, Recommendation } from '@/types';
import { riskColor, riskLabel, getRouteColor } from '@/utils/risk';
import { formatDuration, formatDistance, formatDateTime } from '@/utils/format';
import { CheckIcon, AlertTriangleIcon } from '@/components/common/Icons';
import './RouteCard.css';

interface RouteCardProps {
  route: AnalyzedRoute;
  index: number;
  isSelected: boolean;
  isRecommended: boolean;
  recommendation: Recommendation | null;
  onClick: () => void;
}

export default function RouteCard({
  route,
  index,
  isSelected,
  isRecommended,
  recommendation,
  onClick,
}: RouteCardProps) {
  const color = getRouteColor(route.label, index);
  const { metrics } = route;
  const hasNoTravel = metrics.no_travel_checkpoints > 0;

  return (
    <button
      type="button"
      className={`route-card ${isSelected ? 'route-card--selected' : ''}`}
      onClick={onClick}
      style={{ borderLeftColor: color }}
      aria-pressed={isSelected}
      aria-label={`${route.label}: ${formatDistance(route.distance_miles)}, ${formatDuration(route.duration_seconds)}`}
    >
      <div className="route-card__header">
        <div className="route-card__title-row">
          <span className="route-card__label" style={{ color }}>
            {route.label}
          </span>
          <div className="route-card__badges">
            {isRecommended && recommendation?.status === 'recommended' && (
              <span className="route-card__badge route-card__badge--recommended">
                <CheckIcon /> Recommended
              </span>
            )}
            {hasNoTravel && (
              <span className="route-card__badge route-card__badge--no-travel">
                <AlertTriangleIcon /> No Travel
              </span>
            )}
          </div>
        </div>
        <div className="route-card__metrics-row">
          <span className="route-card__metric">
            {formatDistance(route.distance_miles)}
          </span>
          <span className="route-card__metric-sep" aria-hidden="true">·</span>
          <span className="route-card__metric">
            {formatDuration(route.duration_seconds)}
          </span>
          <span className="route-card__metric-sep" aria-hidden="true">·</span>
          <span className="route-card__metric">
            ETA {formatDateTime(route.arrival_at)}
          </span>
        </div>
      </div>

      <div className="route-card__risk-summary">
        <div className="route-card__risk-bar" aria-label="Risk distribution">
          {metrics.severe_miles > 0 && (
            <div
              className="route-card__risk-segment"
              style={{
                backgroundColor: riskColor('severe'),
                width: `${Math.max((metrics.severe_miles / route.distance_miles) * 100, 4)}%`,
              }}
              title={`Severe: ${formatDistance(metrics.severe_miles)}`}
            />
          )}
          {metrics.high_miles > 0 && (
            <div
              className="route-card__risk-segment"
              style={{
                backgroundColor: riskColor('high'),
                width: `${Math.max((metrics.high_miles / route.distance_miles) * 100, 4)}%`,
              }}
              title={`High: ${formatDistance(metrics.high_miles)}`}
            />
          )}
          <div
            className="route-card__risk-segment"
            style={{
              backgroundColor: riskColor('low'),
              flex: 1,
            }}
          />
        </div>

        <div className="route-card__risk-details">
          {metrics.severe_miles > 0 && (
            <span className="route-card__risk-tag" style={{ color: riskColor('severe') }}>
              {formatDistance(metrics.severe_miles)} {riskLabel('severe')}
            </span>
          )}
          {metrics.high_miles > 0 && (
            <span className="route-card__risk-tag" style={{ color: riskColor('high') }}>
              {formatDistance(metrics.high_miles)} {riskLabel('high')}
            </span>
          )}
          <span className="route-card__risk-avg">
            Avg Risk: {(metrics.average_risk * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {metrics.forecast_coverage_percent < 100 && (
        <div className="route-card__coverage">
          <span className="route-card__coverage-bar">
            <span
              className="route-card__coverage-fill"
              style={{ width: `${metrics.forecast_coverage_percent}%` }}
            />
          </span>
          <span className="route-card__coverage-label">
            {metrics.forecast_coverage_percent.toFixed(0)}% forecast coverage
          </span>
        </div>
      )}
    </button>
  );
}
