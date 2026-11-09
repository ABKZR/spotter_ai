import { useState, useCallback } from 'react';
import { z } from 'zod';
import LocationInput from './LocationInput';
import { RouteIcon } from '@/components/common/Icons';
import type { TripRequest, GeocodeSuggestion } from '@/types';
import { getDefaultDeparture } from '@/utils/format';
import './TripForm.css';

const tripSchema = z.object({
  origin: z.string().min(1, 'Origin is required'),
  destination: z.string().min(1, 'Destination is required'),
  departure_at: z.string().min(1, 'Departure time is required').refine(
    (val) => new Date(val) > new Date(),
    'Departure must be in the future'
  ),
  load_weight_lb: z.number().positive('Load weight must be greater than 0'),
  sampling_interval_miles: z.union([z.literal(10), z.literal(25), z.literal(50)]),
});

interface TripFormProps {
  onSubmit: (request: TripRequest) => void;
  isLoading: boolean;
}

const INTERVALS = [10, 25, 50] as const;

export default function TripForm({ onSubmit, isLoading }: TripFormProps) {
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [departureAt, setDepartureAt] = useState(getDefaultDeparture());
  const [loadWeight, setLoadWeight] = useState<string>('40000');
  const [interval, setInterval] = useState<10 | 25 | 50>(25);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const [, setOriginSuggestion] = useState<GeocodeSuggestion | null>(null);
  const [, setDestSuggestion] = useState<GeocodeSuggestion | null>(null);

  const handleOriginChange = useCallback((value: string, suggestion?: GeocodeSuggestion) => {
    setOrigin(value);
    if (suggestion) setOriginSuggestion(suggestion);
    setErrors((prev) => {
      const next = { ...prev };
      delete next.origin;
      return next;
    });
  }, []);

  const handleDestChange = useCallback((value: string, suggestion?: GeocodeSuggestion) => {
    setDestination(value);
    if (suggestion) setDestSuggestion(suggestion);
    setErrors((prev) => {
      const next = { ...prev };
      delete next.destination;
      return next;
    });
  }, []);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();

      const formData = {
        origin,
        destination,
        departure_at: departureAt ? new Date(departureAt).toISOString() : '',
        load_weight_lb: Number(loadWeight) || 0,
        sampling_interval_miles: interval,
      };

      const result = tripSchema.safeParse(formData);
      if (!result.success) {
        const fieldErrors: Record<string, string> = {};
        for (const issue of result.error.issues) {
          const key = issue.path[0];
          if (typeof key === 'string') fieldErrors[key] = issue.message;
        }
        setErrors(fieldErrors);
        return;
      }

      setErrors({});
      onSubmit(result.data as TripRequest);
    },
    [origin, destination, departureAt, loadWeight, interval, onSubmit]
  );

  return (
    <form className="trip-form" onSubmit={handleSubmit} noValidate>
      <h2 className="trip-form__title">Plan Route</h2>

      <LocationInput
        label="Origin"
        value={origin}
        onChange={handleOriginChange}
        error={errors.origin}
        disabled={isLoading}
        placeholder="e.g., Dallas, TX"
      />

      <LocationInput
        label="Destination"
        value={destination}
        onChange={handleDestChange}
        error={errors.destination}
        disabled={isLoading}
        placeholder="e.g., Chicago, IL"
      />

      <div className="trip-form__field">
        <label htmlFor="departure" className="trip-form__label">
          Departure
        </label>
        <input
          id="departure"
          type="datetime-local"
          className={`trip-form__input ${errors.departure_at ? 'trip-form__input--error' : ''}`}
          value={departureAt}
          onChange={(e) => {
            setDepartureAt(e.target.value);
            setErrors((prev) => {
              const next = { ...prev };
              delete next.departure_at;
              return next;
            });
          }}
          disabled={isLoading}
          aria-describedby={errors.departure_at ? 'departure-error' : undefined}
        />
        {errors.departure_at && (
          <span id="departure-error" className="trip-form__error" role="alert">
            {errors.departure_at}
          </span>
        )}
      </div>

      <div className="trip-form__field">
        <label htmlFor="load-weight" className="trip-form__label">
          Load Weight (lbs)
        </label>
        <input
          id="load-weight"
          type="number"
          className={`trip-form__input ${errors.load_weight_lb ? 'trip-form__input--error' : ''}`}
          value={loadWeight}
          onChange={(e) => {
            setLoadWeight(e.target.value);
            setErrors((prev) => {
              const next = { ...prev };
              delete next.load_weight_lb;
              return next;
            });
          }}
          min={1}
          step={1000}
          disabled={isLoading}
          placeholder="40000"
          aria-describedby={errors.load_weight_lb ? 'weight-error' : undefined}
        />
        {errors.load_weight_lb && (
          <span id="weight-error" className="trip-form__error" role="alert">
            {errors.load_weight_lb}
          </span>
        )}
      </div>

      <fieldset className="trip-form__fieldset" disabled={isLoading}>
        <legend className="trip-form__label">Sampling Interval</legend>
        <div className="trip-form__segments">
          {INTERVALS.map((val) => (
            <label
              key={val}
              className={`trip-form__segment ${interval === val ? 'trip-form__segment--active' : ''}`}
            >
              <input
                type="radio"
                name="interval"
                value={val}
                checked={interval === val}
                onChange={() => setInterval(val)}
                className="trip-form__radio-hidden"
                aria-label={`${val} mile interval`}
              />
              {val} mi
            </label>
          ))}
        </div>
      </fieldset>

      <button
        type="submit"
        className="trip-form__submit"
        disabled={isLoading}
        aria-busy={isLoading}
      >
        {isLoading ? (
          <>
            <span className="trip-form__spinner" aria-hidden="true" />
            Analyzing Route Weather…
          </>
        ) : (
          <>
            <RouteIcon />
            <span>Calculate & Compare Routes</span>
          </>
        )}
      </button>
    </form>
  );
}
