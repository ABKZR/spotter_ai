import { useState, useRef, useEffect, useCallback } from 'react';
import { useGeocode } from '@/hooks/useGeocode';
import { MapPinIcon } from '@/components/common/Icons';
import type { GeocodeSuggestion } from '@/types';
import './LocationInput.css';

interface LocationInputProps {
  label: string;
  value: string;
  onChange: (value: string, suggestion?: GeocodeSuggestion) => void;
  error?: string;
  disabled?: boolean;
  placeholder?: string;
}

export default function LocationInput({
  label,
  value,
  onChange,
  error,
  disabled,
  placeholder,
}: LocationInputProps) {
  const [query, setQuery] = useState(value);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedLabel, setSelectedLabel] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { suggestions, isLoading } = useGeocode(
    selectedLabel === query ? '' : query
  );

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  useEffect(() => {
    if (suggestions.length > 0 && query !== selectedLabel) {
      setIsOpen(true);
    }
  }, [suggestions, query, selectedLabel]);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const v = e.target.value;
      setQuery(v);
      setSelectedLabel('');
      onChange(v);
    },
    [onChange]
  );

  const handleSelect = useCallback(
    (suggestion: GeocodeSuggestion) => {
      setQuery(suggestion.label);
      setSelectedLabel(suggestion.label);
      setIsOpen(false);
      onChange(suggestion.label, suggestion);
    },
    [onChange]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
      if (e.key === 'ArrowDown' && suggestions.length > 0) {
        e.preventDefault();
        setIsOpen(true);
      }
    },
    [suggestions]
  );

  const id = `location-${label.toLowerCase().replace(/\s+/g, '-')}`;

  return (
    <div className="location-input" ref={containerRef}>
      <label htmlFor={id} className="location-input__label">
        {label}
      </label>
      <input
        ref={inputRef}
        id={id}
        type="text"
        className={`location-input__field ${error ? 'location-input__field--error' : ''}`}
        value={query}
        onChange={handleInputChange}
        onFocus={() => {
          if (suggestions.length > 0 && query !== selectedLabel) setIsOpen(true);
        }}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={placeholder}
        autoComplete="off"
        role="combobox"
        aria-expanded={isOpen}
        aria-autocomplete="list"
        aria-controls={`${id}-listbox`}
        aria-describedby={error ? `${id}-error` : undefined}
      />
      {error && (
        <span id={`${id}-error`} className="location-input__error" role="alert">
          {error}
        </span>
      )}

      {isOpen && (
        <ul
          id={`${id}-listbox`}
          className="location-input__dropdown"
          role="listbox"
          aria-label={`${label} suggestions`}
        >
          {isLoading && (
            <li className="location-input__item location-input__item--status">
              Searching…
            </li>
          )}
          {!isLoading && suggestions.length === 0 && query.length >= 2 && (
            <li className="location-input__item location-input__item--status">
              No results found
            </li>
          )}
          {suggestions.map((s, i) => (
            <li
              key={`${s.latitude}-${s.longitude}-${i}`}
              className="location-input__item"
              role="option"
              aria-selected={false}
              onClick={() => handleSelect(s)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSelect(s);
              }}
              tabIndex={0}
            >
              <span className="location-input__item-icon" aria-hidden="true">
                <MapPinIcon />
              </span>
              <span className="location-input__item-label">{s.label}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
