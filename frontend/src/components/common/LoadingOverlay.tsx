import './LoadingOverlay.css';

interface LoadingOverlayProps {
  message?: string;
}

export default function LoadingOverlay({ message }: LoadingOverlayProps) {
  return (
    <div className="loading-overlay" role="status" aria-live="polite">
      <div className="loading-overlay__content">
        <div className="loading-overlay__spinner" aria-hidden="true" />
        <h3 className="loading-overlay__title">Calculating Route Analysis</h3>
        <p className="loading-overlay__status">
          {message || 'Sampling weather forecasts along corridor and applying load limits…'}
        </p>
      </div>
    </div>
  );
}
