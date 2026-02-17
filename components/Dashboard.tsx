
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, Cell } from 'recharts';
import { RegionData, WeatherDay, FloodSeverity } from '../types';
// Consolidate lucide-react imports and move to the top
import { Droplets, CloudRain, Users, Waves, TrendingUp, Wallet, BarChart3 } from 'lucide-react';

interface DashboardProps {
  regions: RegionData[];
  weather: WeatherDay[];
}

export const Dashboard: React.FC<DashboardProps> = ({ regions, weather }) => {
  const totalSubmerged = regions.reduce((acc, curr) => acc + curr.submergedArea, 0);
  const totalLoss = regions.reduce((acc, curr) => acc + curr.estimatedLoss, 0);
  const totalAffected = regions.reduce((acc, curr) => acc + curr.affectedPopulation, 0);

  const getSeverityColor = (s: FloodSeverity) => {
    switch (s) {
      case FloodSeverity.CRITICAL: return 'text-red-400 bg-red-400/10 border-red-500/20';
      case FloodSeverity.HIGH: return 'text-orange-400 bg-orange-400/10 border-orange-500/20';
      case FloodSeverity.MEDIUM: return 'text-yellow-400 bg-yellow-400/10 border-yellow-500/20';
      case FloodSeverity.LOW: return 'text-blue-400 bg-blue-400/10 border-blue-500/20';
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Tổng diện tích ngập" 
          value={`${totalSubmerged.toFixed(1)} ha`} 
          icon={<Waves className="text-blue-400" />} 
          trend="+15.2% (SAR)"
          trendUp={true}
        />
        <StatCard 
          title="Thiệt hại kinh tế" 
          value={`${totalLoss.toFixed(1)} tỷ`} 
          icon={<Wallet className="text-emerald-400" />} 
          trend="Ước tính sơ bộ"
        />
        <StatCard 
          title="Dân cư bị ảnh hưởng" 
          value={totalAffected.toLocaleString()} 
          icon={<Users className="text-purple-400" />} 
          trend="Cần hỗ trợ khẩn cấp"
        />
        <StatCard 
          title="Mức độ rủi ro AI" 
          value="Nguy cấp" 
          icon={<TrendingUp className="text-red-400" />} 
          trend="Xu hướng tăng"
          trendUp={true}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-slate-800/40 border border-slate-700 rounded-3xl p-6 shadow-xl backdrop-blur-sm">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-blue-400" />
              Diện tích ngập & Thiệt hại (Tỷ VND)
            </h3>
          </div>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={regions}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px' }}
                  itemStyle={{ color: '#38bdf8' }}
                />
                <Bar dataKey="submergedArea" fill="#3b82f6" radius={[6, 6, 0, 0]} name="Diện tích (ha)">
                  {regions.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.severity === FloodSeverity.CRITICAL ? '#f43f5e' : '#3b82f6'} />
                  ))}
                </Bar>
                <Bar dataKey="estimatedLoss" fill="#10b981" radius={[6, 6, 0, 0]} name="Thiệt hại (Tỷ)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-800/40 border border-slate-700 rounded-3xl p-6 shadow-xl backdrop-blur-sm">
          <h3 className="text-lg font-semibold mb-6 text-slate-100 flex items-center gap-2">
            <CloudRain className="w-5 h-5 text-sky-400" />
            Diễn biến lượng mưa vệ tinh (mm)
          </h3>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={weather}>
                <defs>
                  <linearGradient id="colorRain" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px' }}
                />
                <Area type="monotone" dataKey="rainfall" stroke="#0ea5e9" strokeWidth={3} fillOpacity={1} fill="url(#colorRain)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="bg-slate-800/40 border border-slate-700 rounded-3xl overflow-hidden shadow-xl backdrop-blur-sm">
        <div className="p-6 border-b border-slate-700 flex justify-between items-center bg-slate-900/40">
          <h3 className="text-lg font-semibold text-slate-100">Phân tích tác động chi tiết theo khu vực</h3>
          <div className="text-xs text-slate-400 font-medium">Nguồn dữ liệu: Sentinel-1 & GPM</div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-slate-900/50 text-slate-400 text-[11px] uppercase tracking-[0.15em] font-bold">
                <th className="px-6 py-5">Tên khu vực</th>
                <th className="px-6 py-5">Trạng thái</th>
                <th className="px-6 py-5">Diện tích ngập</th>
                <th className="px-6 py-5">Độ sâu TB</th>
                <th className="px-6 py-5">Thiệt hại ước tính</th>
                <th className="px-6 py-5">Dân cư</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {regions.map((region) => (
                <tr key={region.id} className="hover:bg-slate-700/30 transition-all cursor-default">
                  <td className="px-6 py-5 font-bold text-white">{region.name}</td>
                  <td className="px-6 py-5">
                    <span className={`px-3 py-1 rounded-full text-[10px] font-black tracking-wider uppercase border ${getSeverityColor(region.severity)}`}>
                      {region.severity}
                    </span>
                  </td>
                  <td className="px-6 py-5 text-slate-300 font-mono">{region.submergedArea} ha</td>
                  <td className="px-6 py-5 text-slate-300 font-mono">{region.avgDepth} m</td>
                  <td className="px-6 py-5 text-emerald-400 font-bold">{region.estimatedLoss} tỷ</td>
                  <td className="px-6 py-5 text-slate-300">{region.affectedPopulation.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const StatCard: React.FC<{ title: string, value: string, icon: React.ReactNode, trend?: string, trendUp?: boolean }> = ({ title, value, icon, trend, trendUp }) => (
  <div className="group bg-slate-800/40 border border-slate-700 p-6 rounded-3xl shadow-lg backdrop-blur-sm hover:border-slate-500 transition-all duration-300">
    <div className="flex items-center justify-between mb-4">
      <span className="text-slate-500 text-[11px] font-bold uppercase tracking-[0.1em]">{title}</span>
      <div className="w-10 h-10 rounded-2xl bg-slate-900/50 flex items-center justify-center border border-slate-700/50 group-hover:scale-110 transition-transform">
        {icon}
      </div>
    </div>
    <div className="flex items-baseline gap-2">
      <span className="text-2xl font-black text-white tracking-tight">{value}</span>
      {trend && (
        <span className={`text-[10px] font-black px-2 py-0.5 rounded-full ${trendUp ? 'text-red-400 bg-red-400/10 border border-red-500/20' : 'text-slate-400 bg-slate-400/10 border border-slate-700'}`}>
          {trend}
        </span>
      )}
    </div>
  </div>
);
