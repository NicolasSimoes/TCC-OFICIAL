import { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap, ZoomControl } from 'react-leaflet';
import { Maximize2, Star } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Region, GridPoint } from '@/types';
import { HeatmapLayer } from './HeatmapLayer';

import 'leaflet/dist/leaflet.css';

interface MapViewProps {
  regions: Region[];
  focusRegion?: Region | null;
  onRegionClick?: (region: Region) => void;
  gridPoints?: GridPoint[];
}

// Componente para centralizar o mapa em uma região
function FocusRegion({ region }: { region: Region | null }) {
  const map = useMap();

  useEffect(() => {
    if (region) {
      map.flyTo([region.lat, region.lng], 15, {
        duration: 1.5,
      });
    }
  }, [region, map]);

  return null;
}

// Componente para fullscreen
function FullscreenControl() {
  const map = useMap();
  const [isFullscreen, setIsFullscreen] = useState(false);

  const toggleFullscreen = () => {
    const container = map.getContainer();
    if (!document.fullscreenElement) {
      container.requestFullscreen?.();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen?.();
      setIsFullscreen(false);
    }
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  return (
    <div className="leaflet-top leaflet-right" style={{ marginTop: '10px', marginRight: '10px' }}>
      <div className="leaflet-control">
        <Button
          size="icon"
          variant="secondary"
          onClick={toggleFullscreen}
          className="h-8 w-8 shadow-md"
          aria-label={isFullscreen ? 'Sair do fullscreen' : 'Fullscreen'}
        >
          <Maximize2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

// Legenda do mapa
function MapLegend() {
  return (
    <div className="leaflet-bottom leaflet-left" style={{ marginBottom: '20px', marginLeft: '10px' }}>
      <div className="leaflet-control rounded-lg border bg-card/95 p-3 shadow-lg backdrop-blur text-xs">
        <h4 className="font-semibold mb-2 text-foreground">Legenda</h4>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-green-500" />
            <span className="text-muted-foreground">Excelente (85+)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-blue-500" />
            <span className="text-muted-foreground">Bom (70-84)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-yellow-500" />
            <span className="text-muted-foreground">Médio (55-69)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-red-500" />
            <span className="text-muted-foreground">Baixo (&lt;55)</span>
          </div>
          <div className="flex items-center gap-2 mt-2 pt-2 border-t">
            <Star className="h-3 w-3 text-yellow-400 fill-yellow-400" />
            <span className="text-muted-foreground">Top 3 Regiões</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export function MapView({ regions, focusRegion, onRegionClick, gridPoints }: MapViewProps) {
  const mapRef = useRef(null);
  const [viewMode, setViewMode] = useState<'clusters' | 'heatmap'>('clusters');

  // Centro de Fortaleza
  const center: [number, number] = [-3.745, -38.52];

  const getScoreColor = (score: number): string => {
    if (score >= 85) return '#22c55e'; // green-500
    if (score >= 70) return '#3b82f6'; // blue-500
    if (score >= 55) return '#eab308'; // yellow-500
    return '#ef4444'; // red-500
  };

  const getScoreColorName = (score: number): string => {
    if (score >= 85) return 'Excelente';
    if (score >= 70) return 'Bom';
    if (score >= 55) return 'Médio';
    return 'Baixo';
  };

  // Top 3 regiões
  const top3Ids = new Set(regions.slice(0, 3).map((r) => r.id));

  // Prepara dados do heatmap: [lat, lng, intensity (0-1)]
  const heatmapData: Array<[number, number, number]> = gridPoints
    ? gridPoints.map((gp) => [gp.lat, gp.lon, gp.score / 100])
    : [];

  return (
    <div className="relative h-[320px] md:h-[400px] lg:h-[500px] w-full rounded-lg overflow-hidden border">
      {/* Toggle de visualização */}
      {gridPoints && gridPoints.length > 0 && (
        <div className="absolute top-3 left-3 z-[1000] bg-white/95 backdrop-blur rounded-lg shadow-lg border">
          <div className="flex gap-1 p-1">
            <button
              onClick={() => setViewMode('clusters')}
              className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                viewMode === 'clusters'
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-accent text-muted-foreground'
              }`}
            >
              Clusters
            </button>
            <button
              onClick={() => setViewMode('heatmap')}
              className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                viewMode === 'heatmap'
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-accent text-muted-foreground'
              }`}
            >
              Mapa de Calor
            </button>
          </div>
        </div>
      )}

      <MapContainer
        ref={mapRef}
        center={center}
        zoom={12}
        zoomControl={false}
        className="h-full w-full"
        style={{ background: 'hsl(217 33% 17%)' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        />
        <ZoomControl position="topright" />
        <FullscreenControl />
        <MapLegend />
        <FocusRegion region={focusRegion || null} />

        {/* Renderização condicional: heatmap OU clusters */}
        {viewMode === 'heatmap' && heatmapData.length > 0 && (
          <HeatmapLayer points={heatmapData} />
        )}

        {viewMode === 'clusters' && regions.map((region) => {
          const isTop3 = top3Ids.has(region.id);
          const color = getScoreColor(region.score);

          return (
            <CircleMarker
              key={region.id}
              center={[region.lat, region.lng]}
              radius={isTop3 ? 12 : 7}
              pathOptions={{
                color: color,
                fillColor: color,
                fillOpacity: isTop3 ? 0.9 : 0.7,
                weight: isTop3 ? 3 : 2,
              }}
              eventHandlers={{
                click: () => onRegionClick?.(region),
              }}
            >
              <Popup>
                <div className="min-w-[200px] space-y-2">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-foreground">
                      {region.name.split(' - ')[0]}
                    </h3>
                    {isTop3 && (
                      <Star className="h-4 w-4 text-yellow-400 fill-yellow-400" />
                    )}
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <span
                      className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
                      style={{ backgroundColor: `${color}20`, color }}
                    >
                      Score: {region.score.toFixed(1)}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      ({getScoreColorName(region.score)})
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-muted-foreground">Potencial:</span>
                      <span className="ml-1 font-medium text-primary">
                        {region.potential.toFixed(0)}%
                      </span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Classe:</span>
                      <span className="ml-1 font-medium">{region.socialClass}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Tipo:</span>
                      <span className="ml-1 font-medium">{region.commercialType}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">POIs:</span>
                      <span className="ml-1 font-medium">{region.pois}</span>
                    </div>
                  </div>

                  <div className="pt-2 border-t text-xs text-muted-foreground">
                    <span>Pop: {region.population.toLocaleString()}</span>
                    <span className="mx-2">•</span>
                    <span>Concorrentes: {region.competitors}</span>
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}
