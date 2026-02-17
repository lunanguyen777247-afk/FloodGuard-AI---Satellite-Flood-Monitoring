
import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './components/Dashboard';
import { MapModule } from './components/MapModule';
import { WeatherModule } from './components/WeatherModule';
import { AIInsights } from './components/AIInsights';
import { InformationModule } from './components/InformationModule';
import { MOCK_REGIONS, MOCK_WEATHER_HISTORY } from './constants';
import { generateFloodAnalysis } from './services/geminiService';
import { AIAnalysisResult } from './types';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [analysis, setAnalysis] = useState<AIAnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalysis = async () => {
      setLoading(true);
      const result = await generateFloodAnalysis(MOCK_REGIONS, MOCK_WEATHER_HISTORY);
      setAnalysis(result);
      setLoading(false);
    };

    fetchAnalysis();
  }, []);

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard regions={MOCK_REGIONS} weather={MOCK_WEATHER_HISTORY} />;
      case 'map':
        return <MapModule regions={MOCK_REGIONS} />;
      case 'weather':
        return <WeatherModule weather={MOCK_WEATHER_HISTORY} />;
      case 'risk':
        return <AIInsights analysis={analysis} loading={loading} />;
      case 'info':
        return <InformationModule />;
      default:
        return <Dashboard regions={MOCK_REGIONS} weather={MOCK_WEATHER_HISTORY} />;
    }
  };

  return (
    <div className="flex h-screen bg-[#0f172a] overflow-hidden">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="flex-1 overflow-y-auto relative">
        <header className="sticky top-0 z-30 bg-[#0f172a]/80 backdrop-blur-md border-b border-slate-800 p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight">FloodGuard AI</h1>
              <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Satellite & Meteorological Intel</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="hidden md:flex flex-col items-end">
              <span className="text-xs text-slate-500 font-medium">Status: Live Monitor</span>
              <span className="text-sm text-green-400 flex items-center gap-1.5">
                <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                SAR Processing Active
              </span>
            </div>
            <button className="bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-lg text-sm transition-colors border border-slate-700">
              Export Report
            </button>
          </div>
        </header>

        <div className="p-6 md:p-8">
          {renderContent()}
        </div>
      </main>
    </div>
  );
};

export default App;
