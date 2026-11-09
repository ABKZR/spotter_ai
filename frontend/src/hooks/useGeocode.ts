import { useState, useEffect, useRef, useCallback } from 'react';
import { geocodeSuggest } from '@/api/trips';
import type { GeocodeSuggestion } from '@/types';

export function useGeocode(query: string) {
  const [suggestions, setSuggestions] = useState<GeocodeSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const search = useCallback((q: string) => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (abortRef.current) abortRef.current.abort();

    if (!q || q.trim().length < 2) {
      setSuggestions([]);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    timerRef.current = setTimeout(async () => {
      const controller = new AbortController();
      abortRef.current = controller;

      try {
        const results = await geocodeSuggest(q);
        if (!controller.signal.aborted) {
          setSuggestions(results);
          setIsLoading(false);
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(err instanceof Error ? err.message : 'Geocode failed');
          setSuggestions([]);
          setIsLoading(false);
        }
      }
    }, 300);
  }, []);

  useEffect(() => {
    search(query);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (abortRef.current) abortRef.current.abort();
    };
  }, [query, search]);

  const clear = useCallback(() => {
    setSuggestions([]);
    setError(null);
  }, []);

  return { suggestions, isLoading, error, clear };
}
