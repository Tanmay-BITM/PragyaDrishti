import React from 'react';
import { LayoutDashboard, Database, Brain, FileText, Bell, Sparkles, ArrowRight } from 'lucide-react';
import { Dataset, MLModel } from '../types';

interface PersonalDashboardProps {
  datasets: Dataset[];
  onNavigate: (tab: string) => void;
}

export const PersonalDashboard: React.FC<PersonalDashboardProps> = ({ datasets, onNavigate }) => {
  return (
    <div className="space-y-8 max-w-7xl mx-auto p-4">
      {/* Header Banner */}
      <div className="glass-panel p-8 rounded-3xl border border-sky-500/20 space-y-4">
        <h2 className="text-2xl font-black text-white flex items-center gap-3">
          Personal Command Center
          <span className="bg-emerald-500/20 text-emerald-400 text-xs px-2.5 py-0.5 rounded-full border border-emerald-500/30">System Active</span>
        </h2>
        <p className="text-xs text-slate-400">Overview of active datasets, saved machine learning models, recent predictions, and system alerts.</p>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[
          { label: 'Active Datasets', val: datasets.length, icon: Database, color: 'text-sky-400' },
          { label: 'Trained ML Models', val: '4', icon: Brain, color: 'text-purple-400' },
          { label: 'Generated Reports', val: '12', icon: FileText, color: 'text-emerald-400' },
          { label: 'System Alerts', val: '0 Pending', icon: Bell, color: 'text-amber-400' }
        ].map((m, i) => {
          const Icon = m.icon;
          return (
            <div key={i} className="glass-card p-5 rounded-2xl flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-400 font-semibold">{m.label}</p>
                <p className={`text-2xl font-extrabold mt-1 ${m.color}`}>{m.val}</p>
              </div>
              <div className="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-400">
                <Icon className="w-5 h-5" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Quick Launch Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-card p-6 rounded-2xl space-y-4 hover:border-purple-500/40 cursor-pointer" onClick={() => onNavigate('prompt-ml')}>
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Brain className="w-5 h-5 text-purple-400" /> Prompt-to-ML Flagship Studio
            </h3>
            <ArrowRight className="w-4 h-4 text-purple-400" />
          </div>
          <p className="text-xs text-slate-400">Type natural language prompts to auto-clean, train optimal algorithms, and deploy REST prediction APIs instantly.</p>
        </div>

        <div className="glass-card p-6 rounded-2xl space-y-4 hover:border-sky-500/40 cursor-pointer" onClick={() => onNavigate('analytics')}>
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-sky-400" /> Natural Language Analytics
            </h3>
            <ArrowRight className="w-4 h-4 text-sky-400" />
          </div>
          <p className="text-xs text-slate-400">Ask plain English questions to auto-generate chart aggregations and data storytelling insights.</p>
        </div>
      </div>
    </div>
  );
};
