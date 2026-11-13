import React, { useState } from 'react';
import { Wand2, CheckCircle2, ShieldAlert, Sparkles, RefreshCw } from 'lucide-react';
import { Dataset } from '../types';
import { api } from '../services/api';

interface AutoCleanViewProps {
  dataset: Dataset | null;
  onCleaningComplete: () => void;
}

export const AutoCleanView: React.FC<AutoCleanViewProps> = ({ dataset, onCleaningComplete }) => {
  const [isCleaning, setIsCleaning] = useState(false);
  const [cleanedResult, setCleanedResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  React.useEffect(() => {
    setCleanedResult(null);
    setError(null);
  }, [dataset?.id]);

  const handleClean = async () => {
    if (!dataset?.id) return;
    setIsCleaning(true);
    setError(null);
    try {
      const res = await api.autoCleanDataset(dataset.id);
      setCleanedResult({
        original_score: dataset.quality_score,
        new_score: res.report?.new_quality_score ?? 100,
        duplicates_removed: res.report?.duplicates_removed ?? 0,
        operations: res.report?.operations || res.report?.operations_performed || [],
        version: res.version
      });
      onCleaningComplete();
    } catch (err: any) {
      setError(err.message || 'Auto-clean execution failed.');
    } finally {
      setIsCleaning(false);
    }
  };

  if (!dataset) {
    return (
      <div className="space-y-8 max-w-7xl mx-auto p-4">
        <div className="glass-panel p-8 rounded-3xl border border-sky-500/20 text-center space-y-4">
          <Wand2 className="w-12 h-12 text-slate-500 mx-auto" />
          <h2 className="text-xl font-bold text-white">No Dataset Selected</h2>
          <p className="text-xs text-slate-400">Please upload or select an active dataset to perform automated cleaning.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto p-4">
      <div className="glass-panel p-8 rounded-3xl border border-sky-500/20 space-y-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
            <Wand2 className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-2xl font-black text-white">Automated Data Cleaning Engine</h2>
            <p className="text-xs text-slate-400">Target Dataset: <span className="text-sky-300 font-bold">{dataset.name}</span> ({dataset.row_count} rows × {dataset.col_count} columns)</p>
          </div>
        </div>

        {/* Action Controls & Settings */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-4">
          {[
            { label: 'Fill Missing Values', desc: 'Median for numeric, Mode for strings', checked: true },
            { label: 'Remove Duplicates', desc: 'De-duplicates identical rows', checked: true },
            { label: 'Clip Outliers (IQR)', desc: 'Caps values beyond 1.5x IQR', checked: true },
            { label: 'Normalize Data Types', desc: 'Auto type casting & scaling', checked: true },
          ].map((item, i) => (
            <div key={i} className="glass-card p-4 rounded-xl border border-slate-800 space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                {item.label}
              </div>
              <p className="text-[11px] text-slate-400">{item.desc}</p>
            </div>
          ))}
        </div>

        {error && (
          <div className="glass-card p-4 rounded-xl border border-rose-500/30 text-rose-300 text-xs font-mono">
            {error}
          </div>
        )}

        <div className="pt-2">
          <button
            onClick={handleClean}
            disabled={isCleaning}
            className="w-full bg-gradient-to-r from-sky-500 via-indigo-500 to-purple-600 hover:from-sky-400 hover:to-purple-500 text-white py-4 rounded-2xl text-sm font-extrabold shadow-glow flex items-center justify-center gap-2 transition-all disabled:opacity-50"
          >
            {isCleaning ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            {isCleaning ? 'Cleaning Dataset...' : 'Execute One-Click Auto-Clean Pipeline'}
          </button>
        </div>
      </div>

      {/* Cleaning Quality Comparison Report */}
      {cleanedResult && (
        <div className="glass-card p-6 rounded-2xl border border-emerald-500/30 bg-emerald-950/10 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" /> Quality Improvement Summary
            </h3>
            <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs px-3 py-1 rounded-full font-bold">
              Dataset Version v{cleanedResult.version} Created
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="glass-card p-4 rounded-xl text-center">
              <p className="text-xs text-slate-400">Previous Quality Score</p>
              <p className="text-3xl font-extrabold text-amber-400 mt-1">{cleanedResult.original_score}%</p>
            </div>
            <div className="glass-card p-4 rounded-xl text-center">
              <p className="text-xs text-slate-400">New Quality Score</p>
              <p className="text-3xl font-extrabold text-emerald-400 mt-1">{cleanedResult.new_score}%</p>
            </div>
            <div className="glass-card p-4 rounded-xl text-center">
              <p className="text-xs text-slate-400">Duplicates Removed</p>
              <p className="text-3xl font-extrabold text-sky-400 mt-1">{cleanedResult.duplicates_removed} rows</p>
            </div>
          </div>

          {cleanedResult.operations && cleanedResult.operations.length > 0 && (
            <div className="glass-card p-4 rounded-xl space-y-2">
              <h4 className="text-xs font-bold text-slate-300">Operations Executed:</h4>
              <ul className="space-y-1 text-xs text-slate-400 font-mono">
                {cleanedResult.operations.map((op: string, idx: number) => (
                  <li key={idx} className="flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    {op}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
