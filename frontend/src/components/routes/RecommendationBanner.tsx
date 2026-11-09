import type { Recommendation } from '@/types';
import { CheckIcon, AlertTriangleIcon, InfoIcon } from '@/components/common/Icons';
import './RecommendationBanner.css';

interface RecommendationBannerProps {
  recommendation: Recommendation | null;
  routeLabels: Record<string, string>;
  warnings: string[];
}

export default function RecommendationBanner({
  recommendation,
  routeLabels,
  warnings,
}: RecommendationBannerProps) {
  if (!recommendation && warnings.length === 0) return null;

  const status = recommendation?.status;
  const routeLabel = recommendation ? routeLabels[recommendation.route_id] || 'a route' : '';

  return (
    <div className="recommendation-banner" role="status" aria-live="polite">
      {status === 'recommended' && (
        <div className="recommendation-banner__box recommendation-banner__box--recommended">
          <span className="recommendation-banner__icon">
            <CheckIcon />
          </span>
          <div>
            <strong>{routeLabel}</strong> is recommended
            {recommendation?.reason && recommendation.reason.length > 0 && (
              <ul className="recommendation-banner__reasons">
                {recommendation.reason.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {status === 'no_suitable_route' && (
        <div className="recommendation-banner__box recommendation-banner__box--danger">
          <span className="recommendation-banner__icon">
            <AlertTriangleIcon />
          </span>
          <div>
            <strong>No suitable route found</strong>
            {recommendation?.reason && recommendation.reason.length > 0 && (
              <ul className="recommendation-banner__reasons">
                {recommendation.reason.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {status === 'partial' && (
        <div className="recommendation-banner__box recommendation-banner__box--warning">
          <span className="recommendation-banner__icon">
            <InfoIcon />
          </span>
          <div>
            <strong>Partial data — {routeLabel}</strong> is the best available option
            {recommendation?.reason && recommendation.reason.length > 0 && (
              <ul className="recommendation-banner__reasons">
                {recommendation.reason.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {warnings.length > 0 && (
        <div className="recommendation-banner__warnings">
          {warnings.map((w, i) => (
            <div key={i} className="recommendation-banner__warning-item">
              <span className="recommendation-banner__warning-icon">
                <AlertTriangleIcon />
              </span>{' '}
              {w}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
