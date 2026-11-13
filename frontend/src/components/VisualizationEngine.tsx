import React, { useState, useEffect } from 'react';
import { BarChart2, PieChart, LineChart as LineIcon, Grid, Layers, Download, SlidersHorizontal, AlertCircle } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, LineChart, Line, PieChart as RePie, Pie, Cell, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { Dataset } from '../types';
import { api } from '../services/api';

interface VisualizationEngineProps {
  dataset: Dataset | null;
}

export const VisualizationEngine: React.FC<VisualizationEngineProps> = ({ dataset }) => {
  const [activeChart, setActiveChart] = useState('bar');
  const [columns, setColumns] = useState<string[]>([]);
  const [xAxisCol, setXAxisCol] = useState<string>('');
  const [yAxisCol, setYAxisCol] = useState<string>('');
  const [chartData, setChartData] = useState<any[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const chartTypes = [
    { id: 'bar', label: 'Bar Chart' },
    { id: 'line', label: 'Line Chart' },
    { id: 'pie', label: 'Pie Chart' },
    { id: 'area', label: 'Area Chart' }
  ];

  const COLORS = ['#38bdf8', '#818cf8', '#c084fc', '#34d399', '#f43f5e', '#fbbf24'];

  useEffect(() => {
    setColumns([]);
    setChartData([]);
    setXAxisCol('');
    setYAxisCol('');
    setErrorMsg(null);

    if (dataset?.id) {
      api.previewDataset(dataset.id).then((res) => {
        if (res && res.columns && res.rows) {
          setColumns(res.columns);
          setChartData(res.rows);
          if (res.columns.length > 0) setXAxisCol(res.columns[0]);
          if (res.columns.length > 1) {
            const numCol = res.columns_info?.find((c: any) => c.type.includes('int') || c.type.includes('float'))?.name || res.columns[1];
            setYAxisCol(numCol);
          }
        }
      }).catch((err) => {
        setErrorMsg(err.message || 'Failed to load dataset visualization preview');
      });
    }
  }, [dataset?.id]);

  return (
    <div className="space-y-8 max-w-7xl mx-auto p-4">
      {/* Header Banner */}
      <div className="glass-panel p-8 rounded-3xl border border-sky-500/20 space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
              <BarChart2 className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-2xl font-black text-white">Interactive Visualization Studio</h2>
              <p className="text-xs text-slate-400">Active Dataset: <span className="text-sky-300 font-bold">{dataset?.name || 'None Selected'}</span></p>
            </div>
          </div>
        </div>

        {/* Column Selectors */}
        {dataset && columns.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 pt-2">
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-400">X-Axis Column (Category):</label>
              <select
                value={xAxisCol}
                onChange={(e) => setXAxisCol(e.target.value)}
                className="w-full glass-card bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl px-3 py-2.5 focus:outline-none focus:border-sky-500"
              >
                {columns.map((c, i) => (
                  <option key={i} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-400">Y-Axis Column (Metric):</label>
              <select
                value={yAxisCol}
                onChange={(e) => setYAxisCol(e.target.value)}
                className="w-full glass-card bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl px-3 py-2.5 focus:outline-none focus:border-sky-500"
              >
                {columns.map((c, i) => (
                  <option key={i} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-400">Chart Type:</label>
              <div className="flex gap-1">
                {chartTypes.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => setActiveChart(c.id)}
                    className={`flex-1 py-2 rounded-xl text-xs font-semibold transition-all ${
                      activeChart === c.id
                        ? 'bg-sky-500 text-white shadow-md'
                        : 'glass-card text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {c.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {!dataset && (
        <div className="glass-card p-6 rounded-2xl border border-sky-500/20 text-center text-slate-400 text-xs">
          Please upload or select a dataset first to render custom charts.
        </div>
      )}

      {errorMsg && (
        <div className="glass-card p-4 rounded-2xl border border-rose-500/40 bg-rose-950/20 flex items-center gap-3 text-rose-300 text-xs font-semibold">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Main Interactive Studio Grid */}
      {dataset && chartData.length > 0 && (
        <div className="glass-card p-6 rounded-2xl space-y-4">
          <h3 className="text-base font-bold text-white uppercase tracking-wider text-xs">
            Rendered Chart ({xAxisCol} vs {yAxisCol})
          </h3>

          <div className="h-96 w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              {activeChart === 'line' ? (
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey={xAxisCol} stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }} />
                  <Line type="monotone" dataKey={yAxisCol} stroke="#38bdf8" strokeWidth={3} />
                </LineChart>
              ) : activeChart === 'pie' ? (
                <RePie data={chartData.slice(0, 10)} dataKey={yAxisCol} nameKey={xAxisCol} cx="50%" cy="50%" outerRadius={120} label>
                  {chartData.slice(0, 10).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </RePie>
              ) : (
                <BarChart data={chartData.slice(0, 30)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey={xAxisCol} stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }} />
                  <Bar dataKey={yAxisCol} fill="#38bdf8" radius={[6, 6, 0, 0]} />
                </BarChart>
              )}
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};
