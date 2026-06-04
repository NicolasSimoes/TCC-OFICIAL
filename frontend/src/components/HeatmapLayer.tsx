import { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet.heat';

interface HeatmapLayerProps {
  points: Array<[number, number, number]>; // [lat, lng, intensity]
  options?: {
    radius?: number;
    blur?: number;
    maxZoom?: number;
    max?: number;
    minOpacity?: number;
    gradient?: Record<number, string>;
  };
}

export function HeatmapLayer({ points, options = {} }: HeatmapLayerProps) {
  const map = useMap();

  useEffect(() => {
    if (!points || points.length === 0) return;

    const defaultOptions = {
      radius: 15,       // Reduzido de 18 para 15 (menos vazamento)
      blur: 15,         // Reduzido de 20 para 15 (bordas mais definidas)
      maxZoom: 17,
      max: 0.5,         // Reduzido de 0.6 para 0.5 (cores mais intensas)
      minOpacity: 0.6,  // Aumentado de 0.5 para 0.6 (mais visível)
      gradient: {
        0.0: 'rgba(0, 0, 255, 0)',      // Azul transparente
        0.2: 'cyan',
        0.4: 'lime',
        0.6: 'yellow',
        0.8: 'orange',
        1.0: 'red',
      },
      ...options,
    };

    // @ts-ignore - leaflet.heat não tem tipagens completas
    const heatLayer = L.heatLayer(points, defaultOptions).addTo(map);

    return () => {
      map.removeLayer(heatLayer);
    };
  }, [map, points, options]);

  return null;
}
