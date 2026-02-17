
import React from 'react';
import { WeatherDay } from '../types';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Thermometer, CloudRain, Wind, Droplets } from 'lucide-react';

interface WeatherModuleProps {
  weather: WeatherDay[];
}

export const WeatherModule: React.FC<WeatherModuleProps> = ({ weather }) => {
  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white">Meteorological Intelligence</h2>
          <p className="text-slate-400">Sourced from GPM Satellite & TRMM Mission Datasets</p>
        </div>
        <div className="flex gap-2">
          <div className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl flex items-center gap-2">
            <Droplets className="w-4 h-4 text-blue-400" />
            <span className="text-sm font-bold">Relative Humidity: 94%</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 bg-slate-800/40 border border-slate-700 rounded-3xl p-6 shadow-xl backdrop-blur-sm">
          <h3 className="text-lg font-semibold mb-6 text-white">Precipitation vs. Temperature Profile</h3>
          <div className="h-96 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={weather}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="date" stroke="#94a3b8" />
                <YAxis yAxisId="left" stroke="#38bdf8" />
                <YAxis yAxisId="right" orientation="right" stroke="#f43f5e" />
                <Tooltip 
                   contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px' }}
                />
                <Legend />
                <Line yAxisId="left" type="monotone" dataKey="rainfall" stroke="#38bdf8" strokeWidth={3} dot={{ r: 6 }} activeDot={{ r: 8 }} name="Rainfall (mm)" />
                <Line yAxisId="right" type="monotone" dataKey="temperature" stroke="#f43f5e" strokeWidth={3} dot={{ r: 6 }} activeDot={{ r: 8 }} name="Temp (°C)" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="space-y-6">
          <WeatherFeatureCard 
            title="Max Precip" 
            value="350 mm" 
            desc="Recorded on Nov 04" 
            icon={<CloudRain className="w-6 h-6 text-sky-400" />} 
          />
          <WeatherFeatureCard 
            title="Wind Gust" 
            value="45 km/h" 
            desc="North-East Direction" 
            icon={<Wind className="w-6 h-6 text-slate-400" />} 
          />
          <WeatherFeatureCard 
            title="Saturation" 
            value="98.2%" 
            desc="Soil Moisture Level" 
            icon={<Droplets className="w-6 h-6 text-blue-400" />} 
          />
          <WeatherFeatureCard 
            title="Pressure" 
            value="1004 hPa" 
            desc="Atmospheric Low" 
            icon={<Thermometer className="w-6 h-6 text-orange-400" />} 
          />
        </div>
      </div>
    </div>
  );
};

const WeatherFeatureCard = ({ title, value, desc, icon }: { title: string, value: string, desc: string, icon: React.ReactNode }) => (
  <div className="bg-slate-800/40 border border-slate-700 p-6 rounded-3xl shadow-lg backdrop-blur-sm flex items-center gap-5">
    <div className="w-12 h-12 bg-slate-900 rounded-2xl flex items-center justify-center border border-slate-700/50">
      {icon}
    </div>
    <div>
      <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest">{title}</h4>
      <div className="text-xl font-bold text-white">{value}</div>
      <p className="text-[10px] text-slate-400">{desc}</p>
    </div>
  </div>
);
