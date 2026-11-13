import React from 'react';
import { Sparkles, Database, Brain, BarChart3, FileText, Bot, LogOut, User, ChevronDown } from 'lucide-react';
import { Dataset } from '../types';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onOpenChat: () => void;
  user: any;
  onLogout: () => void;
  datasets?: Dataset[];
  activeDataset?: Dataset | null;
  onSelectDataset?: (ds: Dataset) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  onOpenChat,
  user,
  onLogout,
  datasets = [],
  activeDataset,
  onSelectDataset
}) => {
  return (
    <header className="sticky top-0 z-40 w-full glass-panel border-b border-slate-800/80 px-4 md:px-6 py-3 flex items-center justify-between gap-4">
      {/* Brand Logo */}
      <div 
        onClick={() => setActiveTab('landing')} 
        className="flex items-center gap-3 cursor-pointer group shrink-0"
      >
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 via-indigo-500 to-purple-500 p-0.5 shadow-glow">
          <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-sky-400 group-hover:scale-110 transition-transform" />
          </div>
        </div>
        <div>
          <h1 className="text-xl font-extrabold tracking-tight text-white flex items-center gap-2">
            Pragya<span className="text-gradient">Drishti</span>
            <span className="text-[10px] font-semibold tracking-wider uppercase bg-sky-500/10 text-sky-400 border border-sky-500/20 px-2 py-0.5 rounded-full">v1.0 AI</span>
          </h1>
          <p className="text-xs text-slate-400 font-medium hidden sm:block">Prompt-to-ML & Data Analytics Engine</p>
        </div>
      </div>

      {/* Global Active Dataset Selector Switcher */}
      {datasets.length > 0 && (
        <div className="flex items-center gap-2 bg-slate-900/80 border border-sky-500/30 px-3 py-1.5 rounded-xl shadow-inner max-w-[280px] sm:max-w-xs">
          <Database className="w-4 h-4 text-sky-400 shrink-0" />
          <div className="flex flex-col min-w-0 flex-1">
            <span className="text-[9px] font-bold uppercase tracking-wider text-slate-400">Active Dataset</span>
            <select
              value={activeDataset?.id || datasets[0]?.id || ''}
              onChange={(e) => {
                const targetId = Number(e.target.value);
                const found = datasets.find(d => d.id === targetId);
                if (found && onSelectDataset) onSelectDataset(found);
              }}
              className="bg-transparent text-xs font-bold text-sky-200 focus:outline-none cursor-pointer truncate pr-1"
            >
              {datasets.map((ds) => (
                <option key={ds.id} value={ds.id} className="bg-slate-900 text-slate-200">
                  {ds.name} ({ds.row_count}r × {ds.col_count}c)
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* Quick Navigation Pills */}
      <nav className="hidden xl:flex items-center gap-1.5 bg-slate-900/60 p-1.5 rounded-2xl border border-slate-800">
        {[
          { id: 'prompt-ml', label: 'Prompt-to-ML', icon: Brain, badge: 'Flagship' },
          { id: 'analytics', label: 'NL Analytics', icon: BarChart3 },
          { id: 'visualization', label: 'Charts & Dashboards', icon: Database },
          { id: 'forecasting', label: 'Predictive', icon: Sparkles },
          { id: 'reports', label: 'Reports', icon: FileText },
        ].map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                isActive
                  ? 'bg-gradient-to-r from-sky-500 to-indigo-600 text-white shadow-md shadow-sky-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {item.label}
              {item.badge && (
                <span className="bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[9px] px-1.5 py-0.2 rounded-full font-bold">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Action CTA Buttons */}
      <div className="flex items-center gap-2.5 shrink-0">
        <button
          onClick={onOpenChat}
          className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white px-3.5 py-2 rounded-xl text-xs font-bold shadow-glow-purple transition-all transform hover:scale-105"
        >
          <Bot className="w-4 h-4" />
          <span className="hidden sm:inline">AI Data Scientist</span>
        </button>

        {user && (
          <div className="hidden md:flex items-center gap-2 glass-card bg-slate-900/80 border border-slate-700 px-3 py-1.5 rounded-xl">
            <User className="w-3.5 h-3.5 text-sky-400" />
            <span className="text-xs font-bold text-slate-200 truncate max-w-[100px]">
              {user.full_name || user.email?.split('@')[0]}
            </span>
          </div>
        )}

        <button
          onClick={onLogout}
          title="Sign Out"
          className="flex items-center gap-2 glass-card hover:bg-rose-950/40 text-slate-300 hover:text-rose-400 border border-slate-700 hover:border-rose-500/40 px-3 py-2 rounded-xl text-xs font-semibold transition-all"
        >
          <LogOut className="w-4 h-4 text-rose-400" />
          <span className="hidden sm:inline">Logout</span>
        </button>
      </div>
    </header>
  );
};
