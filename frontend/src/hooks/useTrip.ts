import { useMutation } from '@tanstack/react-query';
import { analyzeTrip } from '@/api/trips';

export function useTrip() {
  return useMutation({
    mutationFn: analyzeTrip,
  });
}
