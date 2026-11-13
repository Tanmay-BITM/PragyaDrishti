import React, { useState } from 'react';
import { Upload, FileSpreadsheet, CheckCircle2, AlertCircle, Sparkles, Wand2 } from 'lucide-react';
import { Dataset } from '../types';
import { api } from '../services/api';

interface DatasetUploadProps {
  datasets: Dataset[];
  onUploadSuccess: (ds: Dataset) => void;
  onNavigateToClean: (ds: Dataset) => void;
  selectedDataset?: Dataset | null;
  onSelectDataset?: (ds: Dataset) => void;
}

export const DatasetUpload: React.FC<DatasetUploadProps> = ({
  datasets,
  onUploadSuccess,
  onNavigateToClean,
  selectedDataset,
  onSelectDataset
}) => {
  const [selectedDs, setSelectedDs] = useState<Dataset | null>(selectedDataset || datasets[0] || null);
  const [previewData, setPreviewData] = useState<any>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  React.useEffect(() => {
    if (selectedDataset) {
      setSelectedDs(selectedDataset);
    } else if (datasets.length > 0 && !selectedDs) {
      setSelectedDs(datasets[0]);
    }
  }, [selectedDataset, datasets]);

  const handleFileDrop = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setIsUploading(true);
      setUploadError(null);
      try {
        const ds = await api.uploadDataset(file);
        onUploadSuccess(ds);
        setSelectedDs(ds);
        if (onSelectDataset) onSelectDataset(ds);
        loadPreview(ds.id);
      } catch (err: any) {
        setUploadError(err.message || 'Failed to upload dataset.');
      } finally {
        setIsUploading(false);
      }
    }
  };

  const loadPreview = async (id: number) => {
    try {
      const data = await api.previewDataset(id);
      setPreviewData(data);
    } catch (err: any) {
      console.error(err);
    }
  };

  React.useEffect(() => {
    if (selectedDs) loadPreview(selectedDs.id);
  }, [selectedDs]);

  return (
    <div className="space-y-8 max-w-7xl mx-auto p-4">
      {/* Upload Header / Drop Area */}
      <div className="glass-panel p-8 rounded-3xl border border-sky-500/20 text-center space-y-6">
        <div className="w-16 h-16 rounded-2xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 mx-auto">
          <Upload className="w-8 h-8 animate-bounce" />
        </div>

        <div>
          <h2 className="text-2xl font-black text-white">Upload Dataset & Schema Inspector</h2>
          <p className="text-xs text-slate-400 mt-1">Supports CSV, Excel (.xlsx, .xls) up to 250MB with instant type & quality detection.</p>
        </div>

        <div className="max-w-xl mx-auto">
          <label className="glass-card hover:bg-slate-800/80 border-2 border-dashed border-sky-500/40 p-8 rounded-2xl cursor-pointer block space-y-3 transition-all group">
            <FileSpreadsheet className="w-10 h-10 text-sky-400 mx-auto group-hover:scale-110 transition-transform" />
            <p className="text-sm font-bold text-slate-200">
              {isUploading ? 'Parsing Dataset Metadata...' : 'Drag & drop CSV/Excel here or click to browse'}
            </p>
            <p className="text-[11px] text-slate-400">Automatic null count, datatypes, and quality scoring initialized on ingestion</p>
            <input type="file" accept=".csv, .xlsx, .xls" onChange={handleFileDrop} className="hidden" />
          </label>
        </div>

        {uploadError && (
          <div className="glass-card p-4 rounded-2xl border border-rose-500/40 bg-rose-950/20 flex items-center justify-center gap-3 text-rose-300 text-xs font-semibold max-w-xl mx-auto">
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
            <span>{uploadError}</span>
          </div>
        )}
      </div>

      {/* Dataset History & Preview Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Dataset History List */}
        <div className="glass-card p-6 rounded-2xl space-y-4">
          <h3 className="text-base font-bold text-white flex items-center justify-between">
            <span>Dataset Repository</span>
            <span className="text-xs text-slate-400 font-mono">{datasets.length} files</span>
          </h3>

          <div className="space-y-2">
            {datasets.map((ds) => (
              <div
                key={ds.id}
                onClick={() => {
                  setSelectedDs(ds);
                  if (onSelectDataset) onSelectDataset(ds);
                }}
                className={`p-3.5 rounded-xl cursor-pointer transition-all border ${
                  selectedDs?.id === ds.id
                    ? 'bg-sky-500/15 border-sky-500/40 text-white shadow-sm'
                    : 'glass-card hover:bg-slate-800/40 border-slate-800 text-slate-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <p className="font-bold text-xs truncate max-w-[160px]">{ds.name}</p>
                  <span className="bg-emerald-500/20 text-emerald-300 text-[10px] px-2 py-0.5 rounded font-mono font-bold">
                    Score: {ds.quality_score}%
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2">
                  <span>{ds.row_count} rows • {ds.col_count} cols</span>
                  <span>v{ds.version}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Schema & Data Preview Grid */}
        <div className="lg:col-span-2 glass-card p-6 rounded-2xl space-y-4">
          {selectedDs && (
            <>
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                  <h3 className="text-lg font-bold text-white">{selectedDs.name} Preview</h3>
                  <p className="text-xs text-slate-400">File: {selectedDs.filename} • Quality: <span className="text-emerald-400 font-bold">{selectedDs.quality_score}%</span></p>
                </div>

                <button
                  onClick={() => onNavigateToClean(selectedDs)}
                  className="bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all shadow-md"
                >
                  <Wand2 className="w-4 h-4" /> Run Auto-Clean
                </button>
              </div>

              {previewData ? (
                <div className="overflow-x-auto max-h-[350px]">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-900 sticky top-0 text-slate-400 uppercase text-[10px]">
                      <tr>
                        {previewData.columns.map((col: string, i: number) => (
                          <th key={i} className="p-3 border-b border-slate-800">{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono">
                      {previewData.rows.map((row: any, rIdx: number) => (
                        <tr key={rIdx} className="hover:bg-slate-800/30 text-slate-300">
                          {previewData.columns.map((col: string, cIdx: number) => (
                            <td key={cIdx} className="p-3 text-[11px] whitespace-nowrap">{String(row[col] ?? '')}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-xs text-slate-500 text-center py-12">Loading dataset grid preview...</p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
