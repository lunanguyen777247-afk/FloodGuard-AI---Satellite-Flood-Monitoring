
import React from 'react';
import { NAVIGATION } from '../constants';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  return (
    <aside className="w-20 md:w-64 bg-[#1e293b] border-r border-slate-800 flex flex-col transition-all duration-300">
      <div className="p-6 flex items-center gap-3">
        <div className="hidden md:block">
          <span className="text-lg font-bold text-blue-400">System Menu</span>
        </div>
      </div>

      <nav className="flex-1 px-3 space-y-2">
        {NAVIGATION.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-all ${
              activeTab === item.id
                ? 'bg-blue-600/10 text-blue-400 border border-blue-500/20 shadow-inner'
                : 'text-slate-400 hover:bg-slate-800 hover:text-white'
            }`}
          >
            {item.icon}
            <span className="hidden md:block font-medium">{item.name}</span>
          </button>
        ))}
      </nav>

      <div className="p-4 mt-auto">
        <div className="hidden md:block bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Satellite Status</h4>
          <div className="space-y-2">
            <div className="flex justify-between text-[10px] text-slate-300">
              <span>Sentinel-1 (SAR)</span>
              <span className="text-green-400">Online</span>
            </div>
            <div className="w-full bg-slate-700 h-1 rounded-full overflow-hidden">
              <div className="bg-blue-500 h-full w-[85%]"></div>
            </div>
            <div className="flex justify-between text-[10px] text-slate-300">
              <span>GPM (Rainfall)</span>
              <span className="text-yellow-400">Syncing</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};
