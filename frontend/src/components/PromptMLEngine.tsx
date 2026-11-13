import React, { useState, useEffect } from 'react';
import { Brain, Sparkles, Cpu, Download, Play, CheckCircle2, AlertCircle, Activity, Terminal, FileCode, Layers, Info, ShieldAlert } from 'lucide-react';
import { Dataset, MLModel } from '../types';
import { api } from '../services/api';

interface PromptMLEngineProps {
  datasets: Dataset[];
  selectedDataset?: Dataset | null;
  onSelectDataset?: (ds: Dataset) => void;
}

export const PromptMLEngine: React.FC<PromptMLEngineProps> = ({ datasets, selectedDataset, onSelectDataset }) => {
  const [prompt, setPrompt] = useState('Predict Sales using Quantity, Unit_Price, Discount, Region and Product');
  const [selectedDatasetId, setSelectedDatasetId] = useState<number>(selectedDataset?.id || datasets[0]?.id || 1);
  const [targetColumn, setTargetColumn] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [trainedModel, setTrainedModel] = useState<MLModel | null>(null);
  const [previewColumns, setPreviewColumns] = useState<string[]>([]);
  
  // Prediction REST API tester state
  const [testPayload, setTestPayload] = useState('{}');
  const [predictionResult, setPredictionResult] = useState<any>(null);
  const [predLoading, setPredLoading] = useState(false);

  useEffect(() => {
    if (selectedDataset) {
      setSelectedDatasetId(selectedDataset.id);
    } else if (datasets.length > 0) {
      setSelectedDatasetId(datasets[0].id);
    }
  }, [selectedDataset, datasets]);

  useEffect(() => {
    if (selectedDatasetId) {
      api.previewDataset(selectedDatasetId).then((data) => {
        if (data && data.columns) {
          setPreviewColumns(data.columns);
          const payloadTemplate: Record<string, any> = {};
          data.columns.slice(0, 4).forEach((col: string) => {
            payloadTemplate[col] = data.rows[0]?.[col] ?? 0;
          });
          setTestPayload(JSON.stringify(payloadTemplate, null, 2));
        }
      }).catch(() => {});
    }
  }, [selectedDatasetId]);

  const samplePrompts = [
    'Predict Sales using Quantity, Unit_Price, Discount, Region and Product',
    'Predict Profit using Quantity, Unit_Price, Discount, Region and Product',
    'Predict CGPA using Attendance, Study_Hours, Previous_Score and Assignments',
    'Predict Placement using Attendance, Study_Hours, Previous_Score and Assignments'
  ];

  const handleTrain = async () => {
    if (!selectedDatasetId) {
      setErrorMsg('Please upload or select a dataset first.');
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    setTrainedModel(null);
    setPredictionResult(null);
    try {
      const model = await api.trainFromPrompt(prompt, selectedDatasetId, targetColumn || undefined);
      setTrainedModel(model);
      
      // Update test payload with feature keys if available
      if (model.feature_importance_json) {
        const featMap = JSON.parse(model.feature_importance_json);
        const featKeys = Object.keys(featMap);
        if (featKeys.length > 0) {
          const template: Record<string, any> = {};
          featKeys.forEach(k => { template[k] = 10; });
          setTestPayload(JSON.stringify(template, null, 2));
        }
      }
    } catch (e: any) {
      setErrorMsg(e.message || 'Model training failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleTestPrediction = async () => {
    if (!trainedModel) return;
    try {
      const parsed = JSON.parse(testPayload);
      setPredLoading(true);
      setErrorMsg(null);
      const res = await api.predictModel(trainedModel.id, parsed);
      setPredictionResult(res);
    } catch (e: any) {
      alert(e.message || 'Invalid JSON payload structure or prediction failure');
    } finally {
      setPredLoading(false);
    }
  };

  const leaderboard = trainedModel?.leaderboard_json ? JSON.parse(trainedModel.leaderboard_json) : [];
  const featureImportance = trainedModel?.feature_importance_json ? JSON.parse(trainedModel.feature_importance_json) : {};
  
  let explanationDict: any = null;
  if (trainedModel?.explanation_text) {
    try {
      explanationDict = JSON.parse(trainedModel.explanation_text);
    } catch (e) {
      explanationDict = { raw_text: trainedModel.explanation_text };
    }
  }

  const primaryMetricLabel = explanationDict?.primary_metric_label || (trainedModel?.task_type === 'classification' ? 'Cross-Validated F1-Score' : 'Cross-Validated R²');
  const targetSource = explanationDict?.target_selection_source || (targetColumn ? 'Selected by user' : 'Inferred from prompt');

  return (
    <div className="space-y-8 max-w-7xl mx-auto p-4">
      {/* Header Banner */}
      <div className="glass-panel p-8 rounded-3xl border border-purple-500/20 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl" />
        <div className="flex items-center gap-4 mb-2">
          <div className="w-12 h-12 rounded-2xl bg-purple-500/20 border border-purple-500/40 flex items-center justify-center text-purple-400">
            <Brain className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-2xl font-black text-white flex items-center gap-3">
              Prompt-to-ML Flagship Engine
              <span className="bg-purple-500/20 text-purple-300 border border-purple-500/30 text-xs px-2.5 py-0.5 rounded-full font-bold">
                Dataset-Agnostic AutoML
              </span>
            </h2>
            <p className="text-xs text-slate-400">Train, evaluate, explain, and deploy ML models on arbitrary uploaded datasets using natural language prompts.</p>
          </div>
        </div>

        {/* Prompt Input Form */}
        <div className="mt-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Dataset Selector */}
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-400">Select Dataset:</label>
              <select
                value={selectedDatasetId}
                onChange={(e) => {
                  const newId = Number(e.target.value);
                  setSelectedDatasetId(newId);
                  const found = datasets.find(d => d.id === newId);
                  if (found && onSelectDataset) onSelectDataset(found);
                }}
                className="w-full glass-card bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl px-4 py-3 focus:outline-none focus:border-sky-500"
              >
                {datasets.map((ds) => (
                  <option key={ds.id} value={ds.id}>
                    📊 {ds.name} ({ds.row_count} rows, {ds.col_count} cols)
                  </option>
                ))}
              </select>
            </div>

            {/* Target Column Override (Optional) */}
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-400">Target Column (Optional Override):</label>
              <select
                value={targetColumn}
                onChange={(e) => setTargetColumn(e.target.value)}
                className="w-full glass-card bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-xl px-4 py-3 focus:outline-none focus:border-sky-500"
              >
                <option value="">✨ Priority 2: Auto-Infer from Prompt / Schema</option>
                {previewColumns.map((col, idx) => (
                  <option key={idx} value={col}>🎯 Priority 1: Override to {col}</option>
                ))}
              </select>
            </div>

            {/* Natural Language Prompt */}
            <div className="space-y-1">
              <label className="text-xs font-bold text-slate-400">Prompt / Goal:</label>
              <div className="relative">
                <input
                  type="text"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="e.g. Predict Sales using Quantity, Unit_Price..."
                  className="w-full glass-card bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-xl px-4 py-3 pr-28 focus:outline-none focus:border-purple-500"
                />
                <button
                  onClick={handleTrain}
                  disabled={loading}
                  className="absolute right-1 top-1 bottom-1 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white px-4 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all disabled:opacity-50"
                >
                  {loading ? <Activity className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                  {loading ? 'Training...' : 'Train'}
                </button>
              </div>
            </div>
          </div>

          {/* Quick Prompt Chips */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-[11px] font-bold text-slate-500">Quick Prompt Chips:</span>
            {samplePrompts.map((p, i) => (
              <button
                key={i}
                onClick={() => setPrompt(p)}
                className="glass-card hover:bg-purple-500/20 text-slate-300 text-[11px] px-2.5 py-1 rounded-lg transition-all"
              >
                {p}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error Alert Banner */}
      {errorMsg && (
        <div className="glass-card p-4 rounded-2xl border border-rose-500/40 bg-rose-950/20 flex items-center gap-3 text-rose-300 text-xs font-semibold">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Model Training Results */}
      {trainedModel && (
        <div className="space-y-6">
          {/* Executive Summary Card & Target Selection Transparency */}
          <div className="glass-card p-6 rounded-2xl border border-emerald-500/30 bg-emerald-950/10 space-y-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-emerald-500/20 pb-4">
              <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                <CheckCircle2 className="w-5 h-5" /> Model Trained Successfully on Uploaded Dataset
              </div>
              <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs px-3 py-1 rounded-full font-mono font-bold self-start md:self-auto">
                Top Model: {trainedModel.best_algorithm}
              </span>
            </div>

            {/* Target Selection & Task Badge Banner */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-mono">
              <div className="glass-card bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-400 block text-[11px] font-sans font-bold">Target Column:</span>
                <span className="text-sky-400 font-extrabold text-sm">{trainedModel.target_column}</span>
              </div>
              <div className="glass-card bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-400 block text-[11px] font-sans font-bold">Task Type:</span>
                <span className="text-purple-400 font-extrabold text-sm uppercase">{trainedModel.task_type}</span>
              </div>
              <div className="glass-card bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-400 block text-[11px] font-sans font-bold">Target Selection Source:</span>
                <span className="text-amber-400 font-extrabold text-xs">{targetSource}</span>
              </div>
            </div>

            {/* Warnings Alert Banner (if any) */}
            {explanationDict?.warnings && explanationDict.warnings.length > 0 && (
              <div className="glass-card p-3.5 rounded-xl border border-amber-500/40 bg-amber-950/20 flex items-center gap-3 text-amber-300 text-xs">
                <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
                <span>{explanationDict.warnings.join(' ')}</span>
              </div>
            )}
          </div>

          {/* Leaderboard & Feature Importance Split */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* AutoML Leaderboard Table */}
            <div className="glass-card p-6 rounded-2xl space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-sky-400" /> Top Model by Cross-Validated Score ({leaderboard.length} Algorithms)
                </h3>
                <span className="text-[11px] text-slate-400 font-mono">{primaryMetricLabel}</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px]">
                    <tr>
                      <th className="p-3">Rank</th>
                      <th className="p-3">Algorithm</th>
                      <th className="p-3">{primaryMetricLabel}</th>
                      <th className="p-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {leaderboard.map((item: any, idx: number) => (
                      <tr key={idx} className={item.rank === 1 ? 'bg-sky-500/10 font-bold text-sky-300' : 'text-slate-300'}>
                        <td className="p-3">#{item.rank || idx + 1}</td>
                        <td className="p-3">{item.algorithm}</td>
                        <td className="p-3 text-emerald-400 font-bold">{item.primary_score ?? item.f1_score ?? item.r2_score ?? 'N/A'}</td>
                        <td className="p-3">
                          {item.status === 'SUCCESS' ? (
                            <span className="bg-emerald-500/20 text-emerald-400 text-[10px] px-2 py-0.5 rounded font-bold">Passed</span>
                          ) : (
                            <span className="bg-rose-500/20 text-rose-400 text-[10px] px-2 py-0.5 rounded font-bold">Failed</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Feature Importance Breakdown */}
            <div className="glass-card p-6 rounded-2xl space-y-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-purple-400" /> Feature Importance Breakdown
              </h3>
              
              {Object.keys(featureImportance).length > 0 ? (
                <div className="space-y-3 pt-2">
                  {Object.entries(featureImportance).map(([feat, val]: [string, any], i: number) => {
                    const pct = Math.round(Number(val) * 100);
                    return (
                      <div key={i} className="space-y-1">
                        <div className="flex justify-between text-xs font-semibold text-slate-300">
                          <span>{feat}</span>
                          <span className="font-mono text-purple-400">{pct}%</span>
                        </div>
                        <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden">
                          <div className="h-full bg-gradient-to-r from-purple-500 to-sky-400 rounded-full" style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-xs text-slate-400 py-8 text-center italic">Feature importance unavailable for this model</p>
              )}
            </div>
          </div>

          {/* Detailed Audit & Explanation Panel */}
          {explanationDict && (
            <div className="glass-card p-6 rounded-2xl space-y-4 border border-slate-800">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Info className="w-4 h-4 text-sky-400" /> Pipeline Audit & Explanation Panel
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                <div className="space-y-2 glass-card bg-slate-950/60 p-4 rounded-xl border border-slate-800">
                  <p className="text-sky-400 font-bold font-sans">Features Used ({explanationDict.used_features?.length || 0}):</p>
                  <p className="text-slate-300">{explanationDict.used_features?.join(', ') || 'None'}</p>
                </div>

                <div className="space-y-2 glass-card bg-slate-950/60 p-4 rounded-xl border border-slate-800">
                  <p className="text-rose-400 font-bold font-sans">Excluded Features & Identifiers ({explanationDict.excluded_features?.length || 0}):</p>
                  {explanationDict.excluded_features && explanationDict.excluded_features.length > 0 ? (
                    <ul className="space-y-1 text-slate-300 text-[11px]">
                      {explanationDict.excluded_features.map((ex: any, idx: number) => (
                        <li key={idx}>🚫 <span className="font-bold text-slate-200">{ex.column}</span>: {ex.reason}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-slate-400 text-[11px]">No features excluded.</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Model Deployment & Instant REST API Endpoint Tester */}
          <div className="glass-card p-6 rounded-2xl space-y-4 border border-sky-500/20">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-emerald-400" /> Standalone Model REST API Endpoint
                </h3>
                <p className="text-xs text-slate-400">Model pipeline packaged as `.joblib` and deployed to: <span className="font-mono text-sky-400">{trainedModel.endpoint_url}/{trainedModel.id}</span></p>
              </div>

              <a
                href={`/api/v1/prompt-ml/download-model/${trainedModel.id}`}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-2 glass-card hover:bg-slate-800 text-sky-400 border border-sky-500/30 px-4 py-2 rounded-xl text-xs font-bold transition-all"
              >
                <Download className="w-4 h-4" /> Download Trained .joblib Model
              </a>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-400 flex items-center gap-2">
                  <FileCode className="w-3.5 h-3.5" /> Feature Payload (JSON):
                </label>
                <textarea
                  value={testPayload}
                  onChange={(e) => setTestPayload(e.target.value)}
                  rows={4}
                  className="w-full glass-card bg-slate-950 font-mono text-xs text-sky-300 p-3 rounded-xl border border-slate-800 focus:outline-none focus:border-sky-500"
                />
                <button
                  onClick={handleTestPrediction}
                  disabled={predLoading}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all shadow-md disabled:opacity-50"
                >
                  {predLoading ? <Activity className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                  {predLoading ? 'Executing...' : 'Execute Live Prediction REST API Call'}
                </button>
              </div>

              {predictionResult && (
                <div className="glass-card bg-slate-950 p-4 rounded-xl border border-emerald-500/30 space-y-2 font-mono text-xs">
                  <p className="text-emerald-400 font-bold">{predictionResult.status || 'SUCCESS 200 OK'}</p>
                  <p className="text-slate-300">Model: <span className="text-white">{predictionResult.algorithm || trainedModel.best_algorithm}</span></p>
                  <p className="text-slate-300">Target Column: <span className="text-white">{predictionResult.target_column || trainedModel.target_column}</span></p>
                  <p className="text-slate-300">Predicted Output: <span className="text-2xl font-extrabold text-sky-400 block mt-1">{String(predictionResult.prediction)}</span></p>
                  {predictionResult.probabilities && (
                    <p className="text-slate-400 text-[11px] truncate">Class Probabilities: {JSON.stringify(predictionResult.probabilities)}</p>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
