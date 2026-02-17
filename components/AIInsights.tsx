
import React from 'react';
import { AIAnalysisResult } from '../types';
import { Brain, ShieldCheck, AlertCircle, ChevronRight, Sparkles, Activity, Wallet } from 'lucide-react';

interface AIInsightsProps {
  analysis: AIAnalysisResult | null;
  loading: boolean;
}

export const AIInsights: React.FC<AIInsightsProps> = ({ analysis, loading }) => {
  if (loading) {
    return (
      <div className="h-[60vh] flex flex-col items-center justify-center space-y-6">
        <div className="relative">
          <div className="w-20 h-20 border-4 border-blue-500/10 border-t-blue-500 rounded-full animate-spin"></div>
          <Brain className="absolute inset-0 m-auto w-8 h-8 text-blue-400 animate-pulse" />
        </div>
        <div className="text-center">
          <p className="text-blue-400 font-black tracking-[0.2em] uppercase text-xs animate-pulse">Neural Engine Processing</p>
          <p className="text-slate-500 text-xs mt-3 font-medium">Fusing SAR backscatter & TRMM precipitation data...</p>
        </div>
      </div>
    );
  }

  if (!analysis) return null;

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-6 duration-1000">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
        <div className="flex items-center gap-5">
          <div className="w-14 h-14 bg-gradient-to-tr from-blue-600 to-indigo-600 rounded-2xl flex items-center justify-center shadow-2xl shadow-blue-500/20">
            <Brain className="text-white w-8 h-8" />
          </div>
          <div>
            <h2 className="text-2xl font-black text-white tracking-tight">Disaster Intelligence</h2>
            <p className="text-slate-400 text-sm font-medium">Dự báo dựa trên mô hình học sâu & dữ liệu viễn thám</p>
          </div>
        </div>
        
        <div className="flex gap-4">
          <div className="bg-slate-800/60 border border-slate-700 px-5 py-3 rounded-2xl backdrop-blur-md">
            <div className="flex items-center gap-2 mb-1">
              <Activity className="w-4 h-4 text-blue-400" />
              <span className="text-[10px] font-bold text-slate-500 uppercase">Độ tin cậy</span>
            </div>
            <div className="text-xl font-black text-white">{analysis.confidenceScore}%</div>
          </div>
          <div className="bg-slate-800/60 border border-slate-700 px-5 py-3 rounded-2xl backdrop-blur-md">
            <div className="flex items-center gap-2 mb-1">
              <Wallet className="text-emerald-400 w-4 h-4" />
              <span className="text-[10px] font-bold text-slate-500 uppercase">Thiệt hại tổng</span>
            </div>
            <div className="text-xl font-black text-emerald-400">{analysis.estimatedTotalLoss} Tỷ</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="group bg-gradient-to-br from-blue-600/10 to-transparent border border-blue-500/20 rounded-[2.5rem] p-10 backdrop-blur-xl hover:border-blue-500/40 transition-all duration-500">
          <h3 className="text-blue-400 font-black text-[11px] uppercase tracking-[0.25em] mb-6 flex items-center gap-3">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-ping"></div>
            Tóm tắt tình trạng
          </h3>
          <p className="text-slate-100 leading-relaxed text-xl font-medium italic">
            "{analysis.summary}"
          </p>
        </div>

        <div className="group bg-gradient-to-br from-red-600/10 to-transparent border border-red-500/20 rounded-[2.5rem] p-10 backdrop-blur-xl hover:border-red-500/40 transition-all duration-500">
          <h3 className="text-red-400 font-black text-[11px] uppercase tracking-[0.25em] mb-6 flex items-center gap-3">
            <AlertCircle className="w-4 h-4" />
            Đánh giá rủi ro 48h
          </h3>
          <p className="text-slate-200 leading-relaxed text-lg font-normal">
            {analysis.riskAssessment}
          </p>
        </div>
      </div>

      <div className="bg-slate-800/40 border border-slate-700 rounded-[2.5rem] p-10 shadow-2xl backdrop-blur-md relative overflow-hidden">
        <div className="absolute top-0 right-0 p-10 opacity-5">
           <ShieldCheck className="w-40 h-40 text-green-400" />
        </div>
        
        <h3 className="text-slate-100 font-black text-xl mb-8 flex items-center gap-4 relative z-10">
          <ShieldCheck className="w-7 h-7 text-green-400" />
          Kế hoạch hành động chiến lược
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 relative z-10">
          {analysis.recommendations.map((rec, idx) => (
            <div 
              key={idx} 
              className="group p-6 bg-slate-900/40 rounded-3xl border border-slate-700/50 hover:border-blue-500/40 transition-all hover:bg-slate-800 hover:-translate-y-1 shadow-lg"
            >
              <div className="flex gap-5 items-start">
                <div className="w-10 h-10 rounded-2xl bg-blue-600/10 flex items-center justify-center text-blue-400 shrink-0 group-hover:bg-blue-600 group-hover:text-white transition-all duration-300">
                  <span className="font-black text-sm">{idx + 1}</span>
                </div>
                <p className="text-slate-300 text-sm leading-relaxed font-semibold">
                  {rec}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-center gap-3 py-4">
        <div className="h-px bg-slate-800 flex-1"></div>
        <p className="text-slate-600 text-[10px] font-black uppercase tracking-[0.3em]">AI Verification System v4.2</p>
        <div className="h-px bg-slate-800 flex-1"></div>
      </div>
    </div>
  );
};
