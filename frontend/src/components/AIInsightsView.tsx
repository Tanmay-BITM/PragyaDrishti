import React, { useState, useEffect } from 'react';
import { Lightbulb, TrendingUp, ShieldAlert, Sparkles, CheckCircle2, Database, RefreshCw } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { Dataset } from '../types';
import { api } from '../services/api';

interface AIInsightsViewProps {
  dataset?: Dataset | null;
}

export const AIInsightsView: React.FC<AIInsightsViewProps> = ({ dataset }) => {
  const [insights, setInsights] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (dataset?.id) {
      setLoading(true);
      setError(null);
      api.getInsights(dataset.id)
        .then((data) => {
          setInsights(data);
        })
        .catch((err) => {
          setError(err.message || 'Failed to load executive insights.');
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setInsights(null);
    }
  }, [dataset?.id]);

  if (!dataset) {
    return (
      <div className="space-y-8 max-w-7xl mx-auto p-4">
        <div className="glass-panel p-8 rounded-3xl border border-sky-500/20 text-center space-y-4">
          <Database className="w-12 h-12 text-slate-500 mx-auto" />
          <h2 className="text-xl font-bold text-white">No Dataset Selected</h2>
          <p className="text-xs text-slate-400">Please upload or select an active dataset to view AI Executive Insights & Data Storytelling.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto p-4">
      <div className="glass-panel p-8 rounded-3xl border border-sky-500/20 space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <Lightbulb className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-2xl font-black text-white">AI Executive Insights & Data Storytelling</h2>
              <p className="text-xs text-slate-400">
                Active Dataset: <span className="text-amber-400 font-bold">{dataset.name}</span> ({dataset.row_count} rows × {dataset.col_count} columns)
              </p>
            </div>
          </div>
          {insights && (
            <div className="bg-emerald-500/10 border border-emerald-500/30 px-4 py-2 rounded-xl text-right">
              <p className="text-[10px] text-slate-400 font-medium">Quality Score</p>
              <p className="text-lg font-black text-emerald-400">{insights.quality_score}%</p>
            </div>
          )}
        </div>
      </div>

      {loading ? (
        <div className="glass-panel p-12 text-center text-slate-400 font-mono text-xs flex items-center justify-center gap-2">
          <RefreshCw className="w-4 h-4 animate-spin text-amber-400" />
          Analyzing dataset schema, calculating correlations & generating factual AI insights...
        </div>
      ) : error ? (
        <div className="glass-panel p-6 border border-rose-500/30 text-rose-300 text-xs font-mono">
          {error}
        </div>
      ) : insights ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="glass-card p-6 rounded-2xl space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-sky-400" /> Executive Summary
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/60 p-4 rounded-xl border border-slate-800 font-mono">
              {insights.executive_summary}
            </p>
          </div>

          <div className="glass-card p-6 rounded-2xl space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-400" /> Key Trends & Anomaly Detection
            </h3>
            <ul className="space-y-3 text-xs text-slate-300">
              {insights.key_trends?.map((trend: string, i: number) => (
                <li key={i} className="flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span className="font-mono leading-relaxed">{trend}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export const PredictiveForecastingView: React.FC<AIInsightsViewProps> = ({ dataset }) => {
  const [forecastResult, setForecastResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (dataset?.id) {
      setLoading(true);
      setError(null);
      api.getForecast(dataset.id)
        .then((data) => {
          setForecastResult(data);
        })
        .catch((err) => {
          setError(err.message || 'Failed to load predictive forecast.');
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setForecastResult(null);
    }
  }, [dataset?.id]);

  if (!dataset) {
    return (
      <div className="space-y-8 max-w-7xl mx-auto p-4">
        <div className="glass-panel p-8 rounded-3xl border border-sky-500/20 text-center space-y-4">
          <Database className="w-12 h-12 text-slate-500 mx-auto" />
          <h2 className="text-xl font-bold text-white">No Dataset Selected</h2>
          <p className="text-xs text-slate-400">Please upload or select an active dataset to view Predictive Analytics & Time-Series Forecasting.</p>
        </div>
      </div>
    );
  }

  const chartData = [
    ...(forecastResult?.historical?.map((h: any) => ({ period: h.period, actual: h.actual, forecast: h.actual })) || []),
    ...(forecastResult?.forecast?.map((f: any) => ({ period: f.period, forecast: f.forecast, lower: f.lower_bound, upper: f.upper_bound })) || [])
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto p-4">
      <div className="glass-panel p-8 rounded-3xl border border-sky-500/20 space-y-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-2xl font-black text-white">Predictive Analytics & Time-Series Forecasting</h2>
            <p className="text-xs text-slate-400">
              Target Column: <span className="text-sky-400 font-bold">{forecastResult?.target_column || 'Automated Feature'}</span> • Dataset: <span className="text-slate-200 font-bold">{dataset.name}</span>
            </p>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="glass-panel p-12 text-center text-slate-400 font-mono text-xs flex items-center justify-center gap-2">
          <RefreshCw className="w-4 h-4 animate-spin text-sky-400" />
          Calculating time series trend & confidence bounds for dataset...
        </div>
      ) : error ? (
        <div className="glass-panel p-6 border border-rose-500/30 text-rose-300 text-xs font-mono">
          {error}
        </div>
      ) : forecastResult ? (
        <div className="glass-card p-6 rounded-2xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white">
              Growth Projection Trend ({forecastResult.growth_rate_pct >= 0 ? '+' : ''}{forecastResult.growth_rate_pct}%)
            </h3>
            <span className="text-xs font-mono text-slate-400">Periods: {forecastResult.periods} ahead</span>
          </div>
          <div className="h-80 w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="period" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }} />
                <Area type="monotone" dataKey="forecast" stroke="#38bdf8" fill="#38bdf8" fillOpacity={0.3} name="Forecast Value" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : null}
    </div>
  );
};
