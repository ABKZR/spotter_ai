import type { RiskLevel } from '@/types';

export const RISK_COLORS: Record<RiskLevel, string> = {
  low: '#22c55e',
  moderate: '#eab308',
  high: '#f97316',
  severe: '#ef4444',
  no_travel: '#7c3aed',
};

export const RISK_LABELS: Record<RiskLevel, string> = {
  low: 'Low',
  moderate: 'Moderate',
  high: 'High',
  severe: 'Severe',
  no_travel: 'No Travel',
};

export const RISK_CONFIGS: Record<RiskLevel, { color: string; label: string }> = {
  low: { color: '#22c55e', label: 'Low' },
  moderate: { color: '#eab308', label: 'Moderate' },
  high: { color: '#f97316', label: 'High' },
  severe: { color: '#ef4444', label: 'Severe' },
  no_travel: { color: '#7c3aed', label: 'No Travel' },
};

export function riskColor(level: RiskLevel): string {
  return RISK_COLORS[level] || '#22c55e';
}

export function riskLabel(level: RiskLevel): string {
  return RISK_LABELS[level] || 'Low';
}

export const RISK_LEVELS: RiskLevel[] = ['low', 'moderate', 'high', 'severe', 'no_travel'];

export const ROUTE_COLORS: Record<string, string> = {
  'Route A': '#3b82f6',
  'Route B': '#10b981',
  'Route C': '#f59e0b',
};

export function getRouteColor(label: string, index: number): string {
  return ROUTE_COLORS[label] ?? ['#3b82f6', '#10b981', '#f59e0b'][index % 3];
}
