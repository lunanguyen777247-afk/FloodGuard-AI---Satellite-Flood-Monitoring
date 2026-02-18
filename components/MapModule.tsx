
import React, { useState, useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Layers, MapPin, Search, Maximize2, MousePointer2, Radar, ShieldAlert } from 'lucide-react';
// Import FloodSeverity enum to resolve reference errors
import { RegionData, FloodSeverity } from '../types';

interface MapModuleProps {
  regions: RegionData[];
}

export const MapModule: React.FC<MapModuleProps> = ({ regions }) => {
  const [selectedLayer, setSelectedLayer] = useState<'sar' | 'rainfall' | 'dem'>('sar');
  const [scanPos, setScanPos] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setScanPos(prev => (prev + 1) % 100);
    }, 50);
    return () => clearInterval(interval);
  }, []);

  // Fetch map tile URLs and GeoJSON outlines for provided regions
  useEffect(() => {
    async function fetchMapData() {
      const updated = await Promise.all(regions.map(async (r) => {
        try {
          const mapResp = await fetch(`/api/regions/${encodeURIComponent(r.name)}/map`);
          const mapJson = mapResp.ok ? await mapResp.json() : null;
          const geoResp = await fetch(`/api/regions/${encodeURIComponent(r.name)}/geojson`);
          const geoJson = geoResp.ok ? await geoResp.json() : null;

          return {
            ...r,
            tileUrl: mapJson?.map_url,
            mapStats: mapJson?.flood_statistics,
            geojson: geoJson,
          } as RegionData;
        } catch (e) {
          return r;
        }
      }));

      // set local overlay state
      setOverlayRegions(updated);
    }

    fetchMapData();
  }, [regions]);

  const [overlayRegions, setOverlayRegions] = useState<RegionData[]>(regions);
  const mapRef = useRef<L.Map | null>(null);
  const geoLayerRef = useRef<L.GeoJSON | null>(null);

  useEffect(() => {
    // initialize leaflet map once
    if (!mapRef.current) {
      const map = L.map('leaflet-map', { center: [15.5, 107.0], zoom: 7 });
      mapRef.current = map;
    }

    // if there is a tileUrl from first region, set tile layer
    const tileUrl = overlayRegions.find(r => r.tileUrl)?.tileUrl;
    if (tileUrl && mapRef.current) {
      // remove existing tile layers
      mapRef.current.eachLayer((layer: any) => {
        if ((layer as any)._url) mapRef.current?.removeLayer(layer);
      });
      L.tileLayer(tileUrl, { maxZoom: 18, attribution: '© Earth Engine' }).addTo(mapRef.current);
    }

    // draw geojson overlays
    const geo = overlayRegions.find(r => r.geojson)?.geojson;
    if (geo && mapRef.current) {
      if (geoLayerRef.current) {
        geoLayerRef.current.clearLayers();
        geoLayerRef.current.addData(geo);
      } else {
        geoLayerRef.current = L.geoJSON(geo, { style: { color: '#3b82f6', weight: 2, fillOpacity: 0.25 } }).addTo(mapRef.current);
      }
      try {
        mapRef.current.fitBounds(geoLayerRef.current.getBounds(), { maxZoom: 12 });
      } catch {}
    }
  }, [overlayRegions]);

  return (
    <div className="h-[calc(100vh-12rem)] flex gap-6 animate-in slide-in-from-bottom-4 duration-700">
      <div className="flex-1 relative bg-slate-950 rounded-[2.5rem] border border-slate-700 shadow-2xl overflow-hidden group">
        {/* Radar Scanning Line */}
        <div 
          className="absolute inset-0 z-10 pointer-events-none opacity-20 bg-gradient-to-b from-transparent via-blue-500 to-transparent"
          style={{ height: '2px', top: `${scanPos}%` }}
        />
        
        {/* Mock Map Background */}
        <div 
          className="absolute inset-0 opacity-30 bg-cover bg-center transition-transform duration-[3000ms] group-hover:scale-110"
          style={{ backgroundImage: `url('https://images.unsplash.com/photo-1526666923948-b28483953e75?auto=format&fit=crop&q=80&w=2000')` }}
        />
        
        {/* Radar Circles Effect */}
        <div className="absolute inset-0 z-0 pointer-events-none opacity-10 flex items-center justify-center">
            <div className="w-[400px] h-[400px] border border-blue-500 rounded-full animate-ping"></div>
            <div className="absolute w-[600px] h-[600px] border border-blue-500/50 rounded-full"></div>
            <div className="absolute w-[800px] h-[800px] border border-blue-500/20 rounded-full"></div>
        </div>

        {/* Interactive Layers Visualization */}
        <svg className="absolute inset-0 w-full h-full z-10 pointer-events-none" viewBox="0 0 800 600">
          {/* If geojson available, draw outlines scaled into viewBox */}
          {overlayRegions.map((r, idx) => {
            if (!r.geojson || !r.geojson.features || r.geojson.features.length === 0) {
              // fallback: draw a pin at calculated position
              return (
                <g key={r.id} transform={`translate(${200 + idx * 100}, ${150 + idx * 70})`} className="pointer-events-auto cursor-pointer group/pin">
                  <circle r="6" fill="#f43f5e" className="animate-ping opacity-75" />
                  <circle r="4" fill="#f43f5e" />
                </g>
              );
            }

            // compute bbox of features to map to 0..800 x 0..600
            let coords: number[][] = [];
            r.geojson.features.forEach((f: any) => {
              const geom = f.geometry;
              if (geom.type === 'Polygon') {
                geom.coordinates[0].forEach((pt: number[]) => coords.push(pt));
              } else if (geom.type === 'MultiPolygon') {
                geom.coordinates.forEach((poly: any) => poly[0].forEach((pt: number[]) => coords.push(pt)));
              }
            });

            if (coords.length === 0) return null;

            const lons = coords.map(c => c[0]);
            const lats = coords.map(c => c[1]);
            const minLon = Math.min(...lons), maxLon = Math.max(...lons);
            const minLat = Math.min(...lats), maxLat = Math.max(...lats);

            const w = 800, h = 600;
            const lonToX = (lon: number) => ((lon - minLon) / (maxLon - minLon || 1)) * w;
            const latToY = (lat: number) => (1 - (lat - minLat) / (maxLat - minLat || 1)) * h;

            return r.geojson.features.map((f: any, fi: number) => {
              let pathD = '';
              const geom = f.geometry;
              if (geom.type === 'Polygon') {
                pathD = geom.coordinates[0].map((pt: number[], i: number) => `${i===0?'M':'L'} ${lonToX(pt[0])} ${latToY(pt[1])}`).join(' ') + ' Z';
              } else if (geom.type === 'MultiPolygon') {
                pathD = geom.coordinates.map((poly: any) => poly[0].map((pt: number[], i: number) => `${i===0?'M':'L'} ${lonToX(pt[0])} ${latToY(pt[1])}`).join(' ') + ' Z').join(' ');
              }

              return (
                <path key={`${r.id}-${fi}`} d={pathD} fill="rgba(59,130,246,0.25)" stroke="#3b82f6" strokeWidth={1.5} />
              );
            });
          })}
        </svg>

        {/* Floating Map Intelligence UI */}
        <div className="absolute top-8 left-8 z-20 space-y-4">
          <div className="bg-slate-900/80 backdrop-blur-xl p-1.5 rounded-2xl border border-slate-700 flex gap-1 shadow-2xl">
            {(['sar', 'rainfall', 'dem'] as const).map((layer) => (
              <button
                key={layer}
                onClick={() => setSelectedLayer(layer)}
                className={`px-5 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
                  selectedLayer === layer ? 'bg-blue-600 text-white shadow-xl shadow-blue-500/20' : 'text-slate-500 hover:text-white'
                }`}
              >
                {layer}
              </button>
            ))}
          </div>
        </div>

        <div className="absolute bottom-8 left-8 right-8 z-20 flex justify-between items-end">
          <div className="bg-slate-900/90 backdrop-blur-xl p-6 rounded-3xl border border-slate-700 shadow-2xl max-w-sm">
            <div className="flex items-center gap-3 mb-4">
              <Radar className="w-5 h-5 text-blue-400 animate-pulse" />
              <h4 className="text-[11px] font-black text-white uppercase tracking-[0.2em]">SAR Metadata Protocol</h4>
            </div>
            <div className="space-y-3">
              <MetadataRow label="Sensor" value="Sentinel-1 C-Band SAR" />
              <MetadataRow label="Polarization" value="VV + VH" />
              <MetadataRow label="Orbit Info" value="Pass ID: 154-DESC" />
              <MetadataRow label="Algorithm" value="Adaptive Thresholding" />
            </div>
          </div>

          <div className="flex flex-col gap-3 items-end">
             <div className="bg-red-500/20 backdrop-blur-xl px-6 py-3 rounded-2xl border border-red-500/30 shadow-2xl flex items-center gap-4">
              <ShieldAlert className="w-5 h-5 text-red-500 animate-bounce" />
              <div>
                <span className="block text-[10px] font-black text-red-400 uppercase leading-none">Cảnh báo khẩn cấp</span>
                <span className="text-xs text-white font-bold">Vỡ đê bao tại phân khu 04- Huế</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="w-80 flex flex-col gap-6">
        <div className="bg-slate-800/40 border border-slate-700 rounded-3xl p-6 shadow-xl backdrop-blur-sm">
          <h3 className="text-sm font-black mb-6 text-white uppercase tracking-widest flex items-center gap-3">
            <Search className="w-5 h-5 text-blue-400" />
            Phân tích lớp
          </h3>
          <div className="space-y-4">
            <LayerMetric label="Độ phân giải" value="10m/pixel" />
            <LayerMetric label="Độ tin cậy detection" value="96.8%" color="text-green-400" />
            <LayerMetric label="Diện tích trũng (DEM < 2m)" value="2,400 ha" color="text-amber-400" />
          </div>
        </div>

        <div className="bg-slate-800/40 border border-slate-700 rounded-3xl p-6 shadow-xl backdrop-blur-sm flex-1">
          <h3 className="text-sm font-black mb-6 text-white uppercase tracking-widest flex items-center gap-3">
            <MapPin className="w-5 h-5 text-red-500" />
            Vùng trọng điểm
          </h3>
          <div className="space-y-4">
            {[...regions].sort((a,b) => b.submergedArea - a.submergedArea).slice(0, 4).map((r) => (
              <div key={r.id} className="group p-4 bg-slate-900/50 rounded-2xl hover:bg-slate-800 transition-all border border-slate-700/50">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-bold text-sm text-slate-100">{r.name}</span>
                  <span className="text-[10px] font-black text-red-400">-{r.estimatedLoss}T</span>
                </div>
                <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                  <div 
                    // Reference FloodSeverity from the newly added import
                    className={`h-full transition-all duration-1000 ${r.severity === FloodSeverity.CRITICAL ? 'bg-red-500' : 'bg-blue-500'}`} 
                    style={{ width: `${(r.submergedArea / 700) * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const MetadataRow = ({ label, value }: { label: string, value: string }) => (
  <div className="flex justify-between items-center text-[10px]">
    <span className="text-slate-500 font-bold uppercase">{label}</span>
    <span className="text-slate-300 font-mono">{value}</span>
  </div>
);

const LayerMetric = ({ label, value, color = "text-white" }: { label: string, value: string, color?: string }) => (
  <div className="p-4 bg-slate-900/50 rounded-2xl border border-slate-700/50">
    <label className="text-[9px] font-black text-slate-500 uppercase block mb-1">{label}</label>
    <div className={`text-lg font-black tracking-tight ${color}`}>{value}</div>
  </div>
);
