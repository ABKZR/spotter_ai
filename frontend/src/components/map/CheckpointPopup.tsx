import type { Checkpoint } from '@/types';
import { formatDateTime, formatDistance, formatWeatherValue } from '@/utils/format';
import { RISK_CONFIGS } from '@/utils/risk';
import { AlertTriangleIcon } from '@/components/common/Icons';
import './CheckpointPopup.css';

interface CheckpointPopupProps {
  checkpoint: Checkpoint;
  onClose: () => void;
}

export default function CheckpointPopup({ checkpoint, onClose }: CheckpointPopupProps) {
  const { weather, risk } = checkpoint;
  const overallRisk = risk?.overall ?? 'low';
  const cfg = RISK_CONFIGS[overallRisk];

  return (
    <div className="checkpoint-popup">
      <div className="checkpoint-popup__header">
        <div>
          <span className="checkpoint-popup__sequence">Checkpoint #{checkpoint.sequence}</span>
          <span className="checkpoint-popup__dist">
            ({formatDistance(checkpoint.distance_from_origin_miles)} from origin)
          </span>
        </div>
        <button
          type="button"
          className="checkpoint-popup__close"
          onClick={onClose}
          aria-label="Close popup"
        >
          ×
        </button>
      </div>

      <div className="checkpoint-popup__eta">
        <span className="checkpoint-popup__label">Estimated Arrival (ETA):</span>
        <span className="checkpoint-popup__val">
          {checkpoint.estimated_arrival_at
            ? formatDateTime(checkpoint.estimated_arrival_at)
            : 'Pending'}
        </span>
      </div>

      <div
        className="checkpoint-popup__badge"
        style={{ backgroundColor: `${cfg.color}18`, color: cfg.color, borderColor: cfg.color }}
      >
        Overall Risk: <strong>{cfg.label}</strong>
      </div>

      {risk?.load_adjustments && risk.load_adjustments.length > 0 && (
        <div className="checkpoint-popup__adjustments">
          {risk.load_adjustments.map((adj, i) => (
            <div key={i} className="checkpoint-popup__adjustment">
              <AlertTriangleIcon /> {adj}
            </div>
          ))}
        </div>
      )}

      <div className="checkpoint-popup__grid">
        <div className="checkpoint-popup__cell">
          <span className="checkpoint-popup__cell-title">Wind</span>
          <span className="checkpoint-popup__cell-val">
            {formatWeatherValue(weather?.wind_mph ?? null, 'mph')}
          </span>
          <span
            className="checkpoint-popup__pill"
            style={{
              backgroundColor: RISK_CONFIGS[risk?.conditions.wind ?? 'low'].color,
            }}
          >
            {RISK_CONFIGS[risk?.conditions.wind ?? 'low'].label}
          </span>
        </div>

        <div className="checkpoint-popup__cell">
          <span className="checkpoint-popup__cell-title">Rain</span>
          <span className="checkpoint-popup__cell-val">
            {formatWeatherValue(weather?.rain_in_per_hour ?? null, 'in/hr')}
          </span>
          <span
            className="checkpoint-popup__pill"
            style={{
              backgroundColor: RISK_CONFIGS[risk?.conditions.rain ?? 'low'].color,
            }}
          >
            {RISK_CONFIGS[risk?.conditions.rain ?? 'low'].label}
          </span>
        </div>

        <div className="checkpoint-popup__cell">
          <span className="checkpoint-popup__cell-title">Snow</span>
          <span className="checkpoint-popup__cell-val">
            {formatWeatherValue(weather?.snow_in_per_hour ?? null, 'in/hr')}
          </span>
          <span
            className="checkpoint-popup__pill"
            style={{
              backgroundColor: RISK_CONFIGS[risk?.conditions.snow ?? 'low'].color,
            }}
          >
            {RISK_CONFIGS[risk?.conditions.snow ?? 'low'].label}
          </span>
        </div>
      </div>

      {weather && !weather.available && (
        <p className="checkpoint-popup__warning">
          Forecast unavailable at target ETA; marked incomplete.
        </p>
      )}
    </div>
  );
}
