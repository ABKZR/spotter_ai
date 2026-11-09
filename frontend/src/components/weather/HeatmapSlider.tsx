import { useId } from 'react';
import { formatSliderHour } from '@/utils/format';
import './HeatmapSlider.css';

interface HeatmapSliderProps {
  departureAt: string;
  hours: number;
  onChange: (hours: number) => void;
  isLoading?: boolean;
}

export default function HeatmapSlider({
  departureAt,
  hours,
  onChange,
  isLoading = false,
}: HeatmapSliderProps) {
  const sliderId = useId();

  return (
    <div className="heatmap-slider">
      <div className="heatmap-slider__header">
        <label htmlFor={sliderId} className="heatmap-slider__label">
          Corridor Forecast Timeline
        </label>
        <span className="heatmap-slider__value">
          {formatSliderHour(hours, departureAt)}
          {isLoading && <span className="heatmap-slider__loading"> (updating…)</span>}
        </span>
      </div>

      <div className="heatmap-slider__track-container">
        <input
          id={sliderId}
          type="range"
          min={0}
          max={48}
          step={1}
          value={hours}
          onChange={(e) => onChange(Number(e.target.value))}
          className="heatmap-slider__input"
          aria-label="Corridor weather forecast hour slider"
        />
        <div className="heatmap-slider__ticks" aria-hidden="true">
          <span>0h (Depart)</span>
          <span>+12h</span>
          <span>+24h</span>
          <span>+36h</span>
          <span>+48h</span>
        </div>
      </div>
    </div>
  );
}
