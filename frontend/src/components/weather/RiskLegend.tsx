import { RISK_CONFIGS } from '@/utils/risk';
import './RiskLegend.css';

const LEVELS = ['low', 'moderate', 'high', 'severe', 'no_travel'] as const;

export default function RiskLegend() {
  return (
    <div className="risk-legend" aria-label="Weather risk severity legend">
      <div className="risk-legend__header">
        <span className="risk-legend__title">Risk Classification</span>
      </div>
      <div className="risk-legend__items">
        {LEVELS.map((level) => {
          const cfg = RISK_CONFIGS[level];
          return (
            <div key={level} className="risk-legend__item">
              <span
                className="risk-legend__swatch"
                style={{ backgroundColor: cfg.color }}
                aria-hidden="true"
              />
              <span className="risk-legend__label">{cfg.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
