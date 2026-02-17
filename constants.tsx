
import React from 'react';
import { CloudRain, Droplets, Map as MapIcon, ShieldAlert, BarChart3, Info } from 'lucide-react';
import { FloodSeverity, RegionData, WeatherDay } from './types';

export const MOCK_REGIONS: RegionData[] = [
  { id: '1', name: 'Quảng Trị', submergedArea: 450.5, rainfall: 320, avgDepth: 1.2, severity: FloodSeverity.HIGH, affectedPopulation: 12500, estimatedLoss: 125.5 },
  { id: '2', name: 'Thừa Thiên Huế', submergedArea: 680.2, rainfall: 410, avgDepth: 1.8, severity: FloodSeverity.CRITICAL, affectedPopulation: 45000, estimatedLoss: 310.2 },
  { id: '3', name: 'Quảng Bình', submergedArea: 210.3, rainfall: 150, avgDepth: 0.8, severity: FloodSeverity.MEDIUM, affectedPopulation: 5400, estimatedLoss: 45.8 },
  { id: '4', name: 'Hà Tĩnh', submergedArea: 95.8, rainfall: 85, avgDepth: 0.3, severity: FloodSeverity.LOW, affectedPopulation: 1200, estimatedLoss: 12.4 },
];

export const MOCK_WEATHER_HISTORY: WeatherDay[] = [
  { date: '2023-11-01', rainfall: 45, temperature: 24 },
  { date: '2023-11-02', rainfall: 120, temperature: 22 },
  { date: '2023-11-03', rainfall: 210, temperature: 21 },
  { date: '2023-11-04', rainfall: 350, temperature: 19 },
  { date: '2023-11-05', rainfall: 180, temperature: 20 },
  { date: '2023-11-06', rainfall: 60, temperature: 23 },
  { date: '2023-11-07', rainfall: 20, temperature: 25 },
];

export const NAVIGATION = [
  { name: 'Dashboard', icon: <BarChart3 className="w-5 h-5" />, id: 'dashboard' },
  { name: 'Satellite Map', icon: <MapIcon className="w-5 h-5" />, id: 'map' },
  { name: 'Weather Data', icon: <CloudRain className="w-5 h-5" />, id: 'weather' },
  { name: 'Risk Assessment', icon: <ShieldAlert className="w-5 h-5" />, id: 'risk' },
  { name: 'Information', icon: <Info className="w-5 h-5" />, id: 'info' },
];
