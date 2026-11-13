import React, { useState, useEffect } from 'react';
import { TrendingUp, Cpu, Play, AlertCircle, Database, CheckCircle2, Sparkles, Activity, ArrowRight, Info } from 'lucide-react';
import { Dataset, MLModel } from '../types';
import { api } from '../services/api';

interface PredictiveAnalyticsViewProps {
  dataset: Dataset | null;
  onNavigate?: (tab: string) => void;
}

export const PredictiveAnalyticsView: React.FC<PredictiveAnalyticsViewProps> = ({ dataset, onNavigate }) => {
  const [columns, setColumns] = useState<string[]>([]);
  const [selectedTarget, setSelectedTarget] = useState<string>('');
  const [models, setModels] = useState<MLModel[]>([]);
  const [activeModel, setActiveModel] = useState<MLModel | null>(null);
  
  // Interactive Feature Inputs for Live Model Inference
  const [featureInputs, setFeatureInputs] = useState<Record<string, any>>({});
  const [requiredFeatures, setRequiredFeatures] = useState<string[]>([]);
  const [predResult, setPredResult] = useState<any>(null);
  const [predicting, setPredicting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    setColumns([]);
    setSelectedTarget('');
    setModels([]);
    setActiveModel(null);
    setPredResult(null);
    setErrorMsg(null);
    setRequiredFeatures([]);
    setFeatureInputs({});

    if (dataset?.id) {
      // 1. Fetch Dataset Columns
      api.previewDataset(dataset.id).then((res) => {
        if (res && res.columns) {
          setColumns(res.columns);
          if (res.columns.length > 0) {
            setSelectedTarget(res.columns[res.columns.length - 1]);
          }
        }
      }).catch(() => {});

      // 2. Fetch Trained Models for Active Dataset
      api.getDatasetModels(dataset.id).then((mList) => {
        setModels(mList);
      }).catch(() => {});
    }
  }, [dataset?.id]);

  // Update Active Model strictly by dataset_id + target_column lookup
  useEffect(() => {
    setPredResult(null);
    setErrorMsg(null);

    if (models.length > 0 && selectedTarget) {
      const match = models.find(
        (m) => m.target_column?.toLowerCase() === selectedTarget.toLowerCase()
      );
      
      if (match) {
        setActiveModel(match);

        // 1. Extract exact saved feature columns from model metadata
        let featCols: string[] = [];
        if (match.feature_columns && match.feature_columns.length > 0) {
          featCols = match.feature_columns;
        } else if (match.explanation_text) {
          try {
            const exp = JSON.parse(match.explanation_text);
            if (exp.used_features && Array.isArray(exp.used_features)) {
              featCols = exp.used_features;
            }
          } catch (e) {}
        }

        if (featCols.length === 0 && match.feature_importance_json) {
          try {
            const fi = JSON.parse(match.feature_importance_json);
            featCols = Object.keys(fi);
          } catch (e) {}
        }

        // Exclude target column from features if present
        const tgtLower = (match.target_column || '').toLowerCase();
        const cleanFeats = featCols.filter((f) => f.toLowerCase() !== tgtLower);
        setRequiredFeatures(cleanFeats);

        // Pre-fill default inputs for all required features
        const initialInputs: Record<string, any> = {};
        cleanFeats.forEach((feat) => {
          const featLower = feat.toLowerCase();
          if (featLower.includes('region')) initialInputs[feat] = 'North';
          else if (featLower.includes('product')) initialInputs[feat] = 'Laptops';
          else if (featLower.includes('discount')) initialInputs[feat] = 0.05;
          else if (featLower.includes('unit_price') || featLower.includes('price')) initialInputs[feat] = 500.0;
          else if (featLower.includes('quantity') || featLower.includes('qty')) initialInputs[feat] = 10;
          else initialInputs[feat] = 10;
        });
        setFeatureInputs(initialInputs);
      } else {
        setActiveModel(null);
        setRequiredFeatures([]);
        setFeatureInputs({});
      }
    } else {
      setActiveModel(null);
      setRequiredFeatures([]);
      setFeatureInputs({});
    }
  }, [selectedTarget, models]);

  const handlePredict = async () => {
    if (!activeModel) return;

    // Validate all required feature fields before sending API request
    const missing = requiredFeatures.filter(
      (f) => featureInputs[f] === undefined || featureInputs[f] === '' || featureInputs[f] === null
    );

    if (missing.length > 0) {
      setErrorMsg(`Missing required feature: ${missing.join(', ')}`);
      return;
    }

    setPredicting(true);
    setPredResult(null);
    setErrorMsg(null);

    try {
      const res = await api.predictModel(activeModel.id, featureInputs);
      setPredResult(res);
    } catch (e: any) {
      setErrorMsg(e.message || 'Model prediction execution failed.');
    } finally {
      setPredicting(false);
    }
  };

  if (!dataset) {
    return (
      <div className="space-y-8 max-w-7xl mx-auto p-4">
        <div className="glass-panel p-8 rounded-3xl border border-sky-500/20 text-center space-y-4">
          <Database className="w-12 h-12 text-slate-500 mx-auto" />
          <h2 className="text-xl font-bold text-white">No Dataset Selected</h2>
          <p className="text-xs text-slate-400">Please upload or select an active dataset first to perform predictive analytics and model inference.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto p-4">
      {/* Header Banner */}
      <div className="glass-panel p-8 rounded-3xl border border-sky-500/20 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
              <TrendingUp className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-2xl font-black text-white">Predictive Analytics & Model Inference Portal</h2>
              <p className="text-xs text-slate-400">
                Active Dataset: <span className="text-sky-300 font-bold">{dataset.name}</span> ({dataset.row_count} rows × {dataset.col_count} columns)
              </p>
            </div>
          </div>

          {/* Target Column Selector */}
          {columns.length > 0 && (
            <div className="space-y-1">
              <label className="text-[11px] font-bold text-slate-400 block">Select Target Column for Prediction:</label>
              <select
                value={selectedTarget}
                onChange={(e) => setSelectedTarget(e.target.value)}
                className="glass-card bg-slate-900 border border-slate-700 text-sky-300 text-xs font-bold rounded-xl px-4 py-2.5 focus:outline-none focus:border-sky-500"
              >
                {columns.map((col, idx) => (
                  <option key={idx} value={col}>🎯 Target: {col}</option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Model Inference Section */}
      {activeModel ? (
        <div className="glass-card p-6 rounded-2xl space-y-6 border border-emerald-500/30">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-slate-800 pb-4">
            <div className="flex items-center gap-3">
              <Cpu className="w-5 h-5 text-emerald-400" />
              <div>
                <h3 className="text-base font-bold text-white">
                  Trained ML Pipeline: {activeModel.name}
                </h3>
                <p className="text-xs text-slate-400 font-mono">
                  Algorithm: <span className="text-emerald-300 font-bold">{activeModel.best_algorithm}</span> • Task: <span className="text-purple-400 uppercase font-bold">{activeModel.task_type}</span> • Target: <span className="text-sky-300 font-bold">{activeModel.target_column}</span>
                </p>
              </div>
            </div>
            <span className="bg-emerald-500/20 text-emerald-300 text-xs px-3 py-1 rounded-full font-bold font-mono border border-emerald-500/30">
              Model ID #{activeModel.id} Active
            </span>
          </div>

          {/* Dynamic Feature Inputs */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Model Feature Inputs ({requiredFeatures.length} features required):
              </h4>
              <span className="text-[11px] text-slate-400 font-mono">Target '{activeModel.target_column}' excluded from features</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {requiredFeatures.map((feat, idx) => (
                <div key={idx} className="space-y-1">
                  <label className="text-xs font-bold text-slate-400 flex items-center justify-between">
                    <span>{feat}:</span>
                  </label>
                  <input
                    type={typeof featureInputs[feat] === 'number' ? 'number' : 'text'}
                    value={featureInputs[feat] ?? ''}
                    onChange={(e) => {
                      const val = e.target.value;
                      const parsedVal = !isNaN(Number(val)) && val !== '' ? Number(val) : val;
                      setFeatureInputs({ ...featureInputs, [feat]: parsedVal });
                    }}
                    placeholder={`Enter ${feat}`}
                    className="w-full glass-card bg-slate-950 border border-slate-700 text-slate-100 text-xs font-mono rounded-xl px-3 py-2.5 focus:outline-none focus:border-emerald-500"
                  />
                </div>
              ))}
            </div>

            <button
              onClick={handlePredict}
              disabled={predicting}
              className="bg-gradient-to-r from-emerald-600 to-sky-600 hover:from-emerald-500 hover:to-sky-500 text-white px-6 py-3 rounded-xl text-xs font-bold flex items-center gap-2 transition-all shadow-glow disabled:opacity-50"
            >
              {predicting ? <Activity className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
              {predicting ? 'Computing Inference...' : 'Execute Model Prediction'}
            </button>
          </div>

          {/* Error Alert */}
          {errorMsg && (
            <div className="glass-card p-4 rounded-xl border border-rose-500/40 bg-rose-950/20 flex items-center gap-3 text-rose-300 text-xs font-semibold font-mono">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Live Prediction Output Display */}
          {predResult && (
            <div className="glass-card bg-slate-950 p-6 rounded-xl border border-emerald-500/40 space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between">
                <span className="text-emerald-400 font-bold flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4" /> Real Model Prediction Complete
                </span>
                <span className="text-slate-400">Target: {predResult.target_column}</span>
              </div>
              <div className="pt-2">
                <p className="text-slate-400 text-[11px] uppercase tracking-wider font-sans font-bold">Predicted Output Value:</p>
                <p className="text-3xl font-black text-sky-400 mt-1">{String(predResult.prediction)}</p>
              </div>
              {predResult.probabilities && (
                <p className="text-slate-400 text-[11px] pt-1">Class Probabilities: {JSON.stringify(predResult.probabilities)}</p>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="glass-card p-8 rounded-2xl border border-amber-500/30 bg-amber-950/10 text-center space-y-4">
          <AlertCircle className="w-10 h-10 text-amber-400 mx-auto" />
          <h3 className="text-base font-bold text-white">No Trained Model Available for Target '{selectedTarget}'</h3>
          <p className="text-xs text-slate-300 max-w-lg mx-auto leading-relaxed">
            No machine learning model is currently available for dataset <span className="text-amber-300 font-bold">'{dataset.name}'</span> and target column <span className="text-sky-300 font-bold">'{selectedTarget}'</span>. Please train a model first using the Prompt-to-ML or AutoML engine.
          </p>
          {onNavigate && (
            <button
              onClick={() => onNavigate('prompt-ml')}
              className="bg-amber-600 hover:bg-amber-500 text-white px-5 py-2.5 rounded-xl text-xs font-bold transition-all shadow-md inline-flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4" /> Train Model via Prompt-to-ML <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>
      )}

      {/* Time-Series Forecast Status Panel */}
      <div className="glass-card p-6 rounded-2xl space-y-2 border border-slate-800">
        <h3 className="text-sm font-bold text-slate-300 flex items-center gap-2">
          <Info className="w-4 h-4 text-sky-400" /> Time-Series Forecasting Status
        </h3>
        <p className="text-xs text-slate-400 leading-relaxed font-mono">
          Time-series projection is unavailable because the selected model ({activeModel ? activeModel.best_algorithm : 'None'}) is a supervised ML pipeline, not a time-series forecasting model.
        </p>
      </div>
    </div>
  );
};
