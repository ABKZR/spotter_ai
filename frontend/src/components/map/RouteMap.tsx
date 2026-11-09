import { useEffect, useRef, useState, useCallback } from 'react';
import * as maplibregl from 'maplibre-gl';
import type { Map, StyleSpecification } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type { AnalyzedRoute, Checkpoint, CorridorPoint, Location } from '@/types';
import { RISK_CONFIGS } from '@/utils/risk';
import CheckpointPopup from './CheckpointPopup';
import RiskLegend from '@/components/weather/RiskLegend';
import './RouteMap.css';

if (typeof window !== 'undefined' && maplibregl.setWorkerUrl) {
  maplibregl.setWorkerUrl('/maplibre-gl-worker.mjs');
}

interface RouteMapProps {
  routes: AnalyzedRoute[];
  selectedRouteId: string | null;
  onSelectRoute: (routeId: string) => void;
  corridorPoints?: CorridorPoint[];
  sliderHour?: number;
  origin?: Location;
  destination?: Location;
}

const ROUTE_COLORS = ['#2563eb', '#10b981', '#f59e0b', '#8b5cf6'];

const MAP_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    },
  },
  layers: [
    {
      id: 'osm-tiles',
      type: 'raster',
      source: 'osm',
      minzoom: 0,
      maxzoom: 19,
    },
  ],
};

export default function RouteMap({
  routes,
  selectedRouteId,
  onSelectRoute,
  corridorPoints,
  sliderHour = 0,
  origin,
  destination,
}: RouteMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<Map | null>(null);
  const markerARef = useRef<maplibregl.Marker | null>(null);
  const markerBRef = useRef<maplibregl.Marker | null>(null);

  const [mapLoaded, setMapLoaded] = useState(false);
  const [activeCheckpoint, setActiveCheckpoint] = useState<Checkpoint | null>(null);
  const [popupLngLat, setPopupLngLat] = useState<[number, number] | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: MAP_STYLE,
      center: [-98.5795, 39.8283],
      zoom: 4,
    });
    mapRef.current = map;

    map.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'top-right');

    const handleLoad = () => {
      setMapLoaded(true);
    };

    if (map.isStyleLoaded()) {
      setMapLoaded(true);
    } else {
      map.once('load', handleLoad);
    }

    return () => {
      if (markerARef.current) {
        markerARef.current.remove();
        markerARef.current = null;
      }
      if (markerBRef.current) {
        markerBRef.current.remove();
        markerBRef.current = null;
      }
      map.remove();
      mapRef.current = null;
      setMapLoaded(false);
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    if (!map.isStyleLoaded()) {
      const retry = () => setMapLoaded((prev) => !prev);
      map.once('load', retry);
      return;
    }

    const routeFeatures = routes.map((r, idx) => {
      const isSelected = selectedRouteId ? r.id === selectedRouteId : idx === 0;
      return {
        type: 'Feature' as const,
        properties: {
          id: r.id,
          label: r.label,
          isSelected,
          color: ROUTE_COLORS[idx % ROUTE_COLORS.length],
          lineWidth: isSelected ? 6 : 3.5,
          casingWidth: isSelected ? 9 : 5.5,
          lineOpacity: isSelected ? 1.0 : 0.45,
          casingOpacity: isSelected ? 0.85 : 0.3,
        },
        geometry: r.geometry,
      };
    });

    routeFeatures.sort((a, b) => (a.properties.isSelected ? 1 : 0) - (b.properties.isSelected ? 1 : 0));

    const routesGeoJSON: GeoJSON.FeatureCollection = {
      type: 'FeatureCollection',
      features: routeFeatures,
    };

    const routesSource = map.getSource('spotter-routes') as maplibregl.GeoJSONSource | undefined;
    if (routesSource) {
      routesSource.setData(routesGeoJSON);
    } else if (routes.length > 0) {
      map.addSource('spotter-routes', {
        type: 'geojson',
        data: routesGeoJSON,
      });

      map.addLayer({
        id: 'spotter-routes-casing',
        type: 'line',
        source: 'spotter-routes',
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-color': '#0f172a',
          'line-width': ['get', 'casingWidth'],
          'line-opacity': ['get', 'casingOpacity'],
        },
      });

      map.addLayer({
        id: 'spotter-routes-line',
        type: 'line',
        source: 'spotter-routes',
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-color': ['get', 'color'],
          'line-width': ['get', 'lineWidth'],
          'line-opacity': ['get', 'lineOpacity'],
        },
      });

      map.on('click', 'spotter-routes-line', (e: any) => {
        if (!e.features || !e.features[0]) return;
        const clickedId = e.features[0].properties?.id;
        if (clickedId) onSelectRoute(clickedId);
      });

      map.on('mouseenter', 'spotter-routes-line', () => {
        map.getCanvas().style.cursor = 'pointer';
      });
      map.on('mouseleave', 'spotter-routes-line', () => {
        map.getCanvas().style.cursor = '';
      });
    }

    const selectedRoute = routes.find((r) => r.id === selectedRouteId) || routes[0];
    const cpFeatures = (selectedRoute?.checkpoints || []).map((cp, cpIdx) => {
      const corrPt = corridorPoints?.find((p) => p.sequence === cp.sequence);
      const riskLevel = corrPt?.overall_risk || cp.risk?.overall || 'low';
      const color = RISK_CONFIGS[riskLevel]?.color || '#22c55e';
      const isEndpoint = cpIdx === 0 || cpIdx === (selectedRoute?.checkpoints.length || 1) - 1;

      return {
        type: 'Feature' as const,
        properties: {
          id: cp.id,
          sequence: cp.sequence,
          riskColor: color,
          riskLabel: RISK_CONFIGS[riskLevel]?.label || 'Low',
          radius: isEndpoint ? 8 : 6,
        },
        geometry: {
          type: 'Point' as const,
          coordinates: [cp.longitude, cp.latitude],
        },
      };
    });

    const cpGeoJSON: GeoJSON.FeatureCollection = {
      type: 'FeatureCollection',
      features: cpFeatures,
    };

    const cpSource = map.getSource('spotter-checkpoints') as maplibregl.GeoJSONSource | undefined;
    if (cpSource) {
      cpSource.setData(cpGeoJSON);
    } else if (cpFeatures.length > 0) {
      map.addSource('spotter-checkpoints', {
        type: 'geojson',
        data: cpGeoJSON,
      });

      map.addLayer({
        id: 'spotter-checkpoints-layer',
        type: 'circle',
        source: 'spotter-checkpoints',
        paint: {
          'circle-radius': ['get', 'radius'],
          'circle-color': ['get', 'riskColor'],
          'circle-stroke-width': 2.5,
          'circle-stroke-color': '#ffffff',
          'circle-opacity': 0.95,
        },
      });

      map.on('click', 'spotter-checkpoints-layer', (e: any) => {
        if (!e.features || !e.features[0]) return;
        const clickedSeq = e.features[0].properties?.sequence;
        const activeR = routes.find((r) => r.id === selectedRouteId) || routes[0];
        const cp = activeR?.checkpoints.find((c) => c.sequence === clickedSeq);
        if (cp) {
          setActiveCheckpoint(cp);
          setPopupLngLat([cp.longitude, cp.latitude]);
        }
      });

      map.on('mouseenter', 'spotter-checkpoints-layer', () => {
        map.getCanvas().style.cursor = 'pointer';
      });
      map.on('mouseleave', 'spotter-checkpoints-layer', () => {
        map.getCanvas().style.cursor = '';
      });
    }

    if (routes.length > 0 && selectedRoute && selectedRoute.checkpoints.length > 0) {
      const firstCp = selectedRoute.checkpoints[0];
      const lastCp = selectedRoute.checkpoints[selectedRoute.checkpoints.length - 1];

      const originCoord: [number, number] = origin
        ? [origin.longitude, origin.latitude]
        : [firstCp.longitude, firstCp.latitude];

      const destCoord: [number, number] = destination
        ? [destination.longitude, destination.latitude]
        : [lastCp.longitude, lastCp.latitude];

      if (markerARef.current) {
        markerARef.current.remove();
        markerARef.current = null;
      }
      if (markerBRef.current) {
        markerBRef.current.remove();
        markerBRef.current = null;
      }

      const elA = document.createElement('div');
      elA.className = 'spotter-pin spotter-pin--origin';
      elA.innerHTML = `
        <div class="spotter-pin__badge">
          <span class="spotter-pin__letter">A</span>
        </div>
        <div class="spotter-pin__label">Point A: Origin</div>
      `;

      const popupA = new maplibregl.Popup({ offset: [0, -32], closeButton: false }).setHTML(
        `<div style="font-family: inherit; padding: 4px 6px;">
          <div style="font-weight: 700; color: #10b981; font-size: 0.8125rem;">Point A (Origin)</div>
          <div style="font-size: 0.75rem; color: #334155; margin-top: 2px;">${origin?.label || 'Trip Origin'}</div>
        </div>`
      );

      markerARef.current = new maplibregl.Marker({ element: elA, anchor: 'bottom' })
        .setLngLat(originCoord)
        .setPopup(popupA)
        .addTo(map);

      const elB = document.createElement('div');
      elB.className = 'spotter-pin spotter-pin--destination';
      elB.innerHTML = `
        <div class="spotter-pin__badge">
          <span class="spotter-pin__letter">B</span>
        </div>
        <div class="spotter-pin__label">Point B: Destination</div>
      `;

      const popupB = new maplibregl.Popup({ offset: [0, -32], closeButton: false }).setHTML(
        `<div style="font-family: inherit; padding: 4px 6px;">
          <div style="font-weight: 700; color: #ef4444; font-size: 0.8125rem;">Point B (Destination)</div>
          <div style="font-size: 0.75rem; color: #334155; margin-top: 2px;">${destination?.label || 'Trip Destination'}</div>
        </div>`
      );

      markerBRef.current = new maplibregl.Marker({ element: elB, anchor: 'bottom' })
        .setLngLat(destCoord)
        .setPopup(popupB)
        .addTo(map);
    }

    if (routes.length > 0) {
      const bounds = new maplibregl.LngLatBounds();
      routes.forEach((r) => {
        const coords = r.geometry.coordinates;
        if (!coords || coords.length === 0) return;

        const step = Math.max(1, Math.floor(coords.length / 80));
        for (let i = 0; i < coords.length; i += step) {
          bounds.extend(coords[i]);
        }
        bounds.extend(coords[0]);
        bounds.extend(coords[coords.length - 1]);
      });

      if (!bounds.isEmpty()) {
        map.fitBounds(bounds, {
          padding: { top: 90, bottom: 90, left: 70, right: 70 },
          maxZoom: 12,
          duration: 900,
        });
      }
    }
  }, [routes, selectedRouteId, corridorPoints, sliderHour, onSelectRoute, mapLoaded, origin, destination]);

  const handleClosePopup = useCallback(() => {
    setActiveCheckpoint(null);
    setPopupLngLat(null);
  }, []);

  return (
    <div className="route-map-wrapper">
      <div ref={mapContainerRef} className="route-map-container" />
      <div className="route-map__legend-overlay">
        <RiskLegend />
      </div>

      {activeCheckpoint && popupLngLat && (
        <div className="route-map__popup-container">
          <CheckpointPopup checkpoint={activeCheckpoint} onClose={handleClosePopup} />
        </div>
      )}
    </div>
  );
}
