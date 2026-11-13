import React, { useState } from 'react';
import { MessageSquare, Sparkles, Send, AlertCircle, HelpCircle, Table, CheckCircle2 } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { Dataset } from '../types';
import { api } from '../services/api';

interface NLAnalyticsViewProps {
  dataset: Dataset | null;
}

export const NLAnalyticsView: React.FC<NLAnalyticsViewProps> = ({ dataset }) => {
  const [query, setQuery] = useState('What is the average of my dataset?');
  const [queryResult, setQueryResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  React.useEffect(() => {
    setQueryResult(null);
    setErrorMsg(null);
  }, [dataset?.id]);

  const handleQuery = async () => {
    if (!dataset) {
      setErrorMsg('Please upload or select a dataset first.');
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    setQueryResult(null);
    try {
      const res = await api.runNLQuery(dataset.id, query);
      setQueryResult(res);
    } catch (e: any) {
      setErrorMsg(e.message || 'Analytics query failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto p-4">
      {/* Header Banner */}
      <div className="glass-panel p-8 rounded-3xl border border-sky-500/20 space-y-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
            <MessageSquare className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-2xl font-black text-white">Natural Language Analytics Engine</h2>
            <p className="text-xs text-slate-400">
              Active Dataset: <span className="text-sky-300 font-bold">{dataset?.name || 'None Selected'}</span>
              {dataset && <span className="text-slate-500 font-mono ml-2">({dataset.row_count} rows, {dataset.col_count} cols)</span>}
            </p>
          </div>
        </div>

        {/* Input Form */}
        <div className="flex gap-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
            placeholder="Ask a question (e.g., 'What is the average Sales?', 'Show Sales by Region')..."
            className="flex-1 glass-card bg-slate-900 border border-slate-700 text-slate-100 text-sm rounded-xl px-4 py-3.5 focus:outline-none focus:border-sky-500"
          />
          <button
            onClick={handleQuery}
            disabled={loading}
            className="bg-sky-500 hover:bg-sky-400 text-white px-6 rounded-xl text-xs font-bold flex items-center gap-2 transition-all shadow-md disabled:opacity-50"
          >
            {loading ? <Sparkles className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            Ask AI
          </button>
        </div>
      </div>

      {/* Error Alert Banner */}
      {errorMsg && (
        <div className="glass-card p-4 rounded-2xl border border-rose-500/40 bg-rose-950/20 flex items-center gap-3 text-rose-300 text-xs font-semibold">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Query Result Card */}
      {queryResult && (
        <div className="space-y-6">
          {queryResult.status === 'ERROR' ? (
            /* Error / Missing Column Banner */
            <div className="glass-card p-6 rounded-2xl border border-amber-500/40 bg-amber-950/20 space-y-4">
              <div className="flex items-center gap-3 text-amber-300 font-bold text-sm">
                <HelpCircle className="w-5 h-5 text-amber-400 shrink-0" />
                <span>{queryResult.error_message}</span>
              </div>

              {queryResult.suggestions && queryResult.suggestions.length > 0 && (
                <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 text-xs text-amber-200 font-mono">
                  💡 {queryResult.suggestions.join(' ')}
                </div>
              )}

              {queryResult.available_columns && (
                <div className="space-y-2">
                  <p className="text-xs font-bold text-slate-400">Available Columns in '{dataset?.name}':</p>
                  <div className="flex flex-wrap gap-2">
                    {queryResult.available_columns.map((col: string, idx: number) => (
                      <span key={idx} className="bg-slate-900 border border-slate-700 text-slate-300 text-xs px-2.5 py-1 rounded-lg font-mono">
                        {col}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : queryResult.intent === 'STATISTICS' || queryResult.chart_type === 'metric' ? (
            /* Numeric Calculation Card (e.g. "What is the average Sales?") */
            <div className="glass-card p-6 rounded-2xl border border-emerald-500/30 bg-emerald-950/10 space-y-4">
              <div className="flex items-center justify-between border-b border-emerald-500/20 pb-4">
                <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                  <CheckCircle2 className="w-5 h-5" /> Statistical Calculation (Pandas Engine)
                </div>
                <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs px-3 py-1 rounded-full font-mono font-bold uppercase">
                  {queryResult.operation || 'METRIC'}
                </span>
              </div>

              <div className="p-6 bg-slate-950/80 rounded-2xl border border-slate-800 text-center space-y-2">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  {queryResult.operation} of {queryResult.column}
                </p>
                <p className="text-4xl font-extrabold text-sky-400 font-mono">
                  {queryResult.value}
                </p>
              </div>

              <p className="text-xs text-slate-300 bg-slate-900/60 p-3 rounded-xl border border-slate-800 font-mono">
                💡 {queryResult.summary}
              </p>
            </div>
          ) : queryResult.intent === 'SCHEMA' ? (
            /* Schema Info View */
            <div className="glass-card p-6 rounded-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Table className="w-5 h-5 text-sky-400" /> Active Dataset Schema
                </h3>
              </div>
              <p className="text-xs text-slate-300 bg-slate-900/60 p-3 rounded-xl border border-slate-800 font-mono">
                💡 {queryResult.summary}
              </p>
              {queryResult.data && (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-900 text-slate-400 uppercase text-[10px]">
                      <tr>
                        <th className="p-3">Column Name</th>
                        <th className="p-3">Data Type</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 font-mono">
                      {queryResult.data.map((row: any, idx: number) => (
                        <tr key={idx} className="text-slate-300">
                          <td className="p-3 font-bold text-sky-300">{row.column}</td>
                          <td className="p-3">{row.type}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ) : (
            /* Chart Visualization View */
            <div className="glass-card p-6 rounded-2xl space-y-6">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <h3 className="text-lg font-bold text-white">{queryResult.title || 'Analytics Chart'}</h3>
                <span className="bg-sky-500/20 text-sky-300 text-xs px-3 py-1 rounded-full font-bold uppercase">
                  Chart Type: {queryResult.chart_type}
                </span>
              </div>

              <p className="text-xs text-slate-300 bg-slate-900/60 p-3 rounded-xl border border-slate-800 font-mono">
                💡 {queryResult.summary}
              </p>

              {queryResult.data && queryResult.data.length > 0 && (
                <div className="h-80 w-full pt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={queryResult.data}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey={queryResult.x_col || 'range'} stroke="#94a3b8" fontSize={12} />
                      <YAxis stroke="#94a3b8" fontSize={12} />
                      <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }} />
                      <Bar dataKey={queryResult.y_col || 'count'} fill="#38bdf8" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
