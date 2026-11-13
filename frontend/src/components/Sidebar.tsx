import React from 'react';
import { 
  Home, Database, Wand2, Brain, Cpu, MessageSquare, BarChart2, 
  Lightbulb, TrendingUp, LayoutDashboard, FileSpreadsheet, 
  ShieldAlert, Settings 
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  const menuItems = [
    { id: 'landing', label: 'Landing Page', icon: Home, module: 'M1' },
    { id: 'dashboard', label: 'Personal Dashboard', icon: LayoutDashboard, module: 'M12' },
    { id: 'datasets', label: 'Dataset Upload', icon: Database, module: 'M3' },
    { id: 'auto-clean', label: 'Auto Data Cleaning', icon: Wand2, module: 'M4' },
    { id: 'prompt-ml', label: 'Prompt-to-ML Engine', icon: Brain, module: 'M5', flagship: true },
    { id: 'automl', label: 'AutoML Leaderboard', icon: Cpu, module: 'M6' },
    { id: 'analytics', label: 'NL Analytics', icon: MessageSquare, module: 'M7' },
    { id: 'visualization', label: 'Chart & Dashboards', icon: BarChart2, module: 'M8' },
    { id: 'insights', label: 'AI Insights', icon: Lightbulb, module: 'M9' },
    { id: 'forecasting', label: 'Predictive Analytics', icon: TrendingUp, module: 'M10' },
    { id: 'reports', label: 'Report Generator', icon: FileSpreadsheet, module: 'M11' },
    { id: 'admin', label: 'Admin Dashboard', icon: ShieldAlert, module: 'M13' },
  ];

  return (
    <aside className="w-64 glass-panel border-r border-slate-800/80 min-h-[calc(100vh-65px)] p-4 flex flex-col justify-between hidden lg:flex">
      <div className="space-y-1.5">
        <p className="px-3 text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-3">System Modules</p>
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                isActive
                  ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-sky-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>
              <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${
                item.flagship 
                  ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' 
                  : 'bg-slate-800 text-slate-400'
              }`}>
                {item.module}
              </span>
            </button>
          );
        })}
      </div>

      <div className="pt-4 border-t border-slate-800/60">
        <div className="glass-card p-3 rounded-xl flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold text-xs">
            PD
          </div>
          <div>
            <p className="text-xs font-bold text-slate-200">Production Mode</p>
            <p className="text-[10px] text-slate-400">PostgreSQL • Gemini AI</p>
          </div>
        </div>
      </div>
    </aside>
  );
};
