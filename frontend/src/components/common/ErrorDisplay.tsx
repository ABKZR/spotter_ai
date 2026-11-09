import { AlertTriangleIcon } from './Icons';
import './ErrorDisplay.css';

interface ErrorDisplayProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export default function ErrorDisplay({
  title = 'Route Analysis Error',
  message,
  onRetry,
}: ErrorDisplayProps) {
  return (
    <div className="error-display" role="alert">
      <div className="error-display__icon">
        <AlertTriangleIcon />
      </div>
      <div className="error-display__content">
        <h4 className="error-display__title">{title}</h4>
        <p className="error-display__message">{message}</p>
        {onRetry && (
          <button type="button" className="error-display__button" onClick={onRetry}>
            Try Again
          </button>
        )}
      </div>
    </div>
  );
}
