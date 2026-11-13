import React, { useState } from 'react';
import { FileText, Download, FileSpreadsheet, Presentation, Globe, CheckCircle2, Sparkles, AlertCircle, RefreshCw } from 'lucide-react';
import { Dataset } from '../types';
import { api } from '../services/api';

interface ReportGeneratorViewProps {
  dataset?: Dataset | null;
}

export const ReportGeneratorView: React.FC<ReportGeneratorViewProps> = ({ dataset }) => {
  const [reportTitle, setReportTitle] = useState('PragyaDrishti Data Analytics Report');
  const [selectedFormat, setSelectedFormat] = useState('PDF');
  const [generating, setGenerating] = useState(false);
  const [downloadReport, setDownloadReport] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState(false);
  const [downloadedFileName, setDownloadedFileName] = useState('');

  const formats = [
    { id: 'PDF', label: 'PDF Document', icon: FileText, desc: 'Professional vector graphics & AI summary' },
    { id: 'EXCEL', label: 'Excel Workbook', icon: FileSpreadsheet, desc: 'Multi-sheet data & raw model metrics' },
    { id: 'PPTX', label: 'PowerPoint Deck', icon: Presentation, desc: 'Executive slide deck with key trends' },
    { id: 'HTML', label: 'Interactive HTML', icon: Globe, desc: 'Standalone web dashboard package' }
  ];

  const handleGenerate = async () => {
    setGenerating(true);
    setDownloadReport(null);
    setErrorMsg(null);
    setDownloadSuccess(false);
    setDownloadedFileName('');
    try {
      const summaryText = dataset
        ? `Executive report generated for dataset '${dataset.name}' (ID #${dataset.id}, ${dataset.row_count} rows, ${dataset.col_count} columns). Data quality score: ${dataset.quality_score}%.`
        : 'Executive AI summary generated across platform analytics.';
        
      const res = await api.generateReport(reportTitle, selectedFormat, summaryText, dataset?.id);
      setDownloadReport(res);
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to generate report');
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = async () => {
    if (!downloadReport?.id) return;
    setDownloading(true);
    setErrorMsg(null);
    setDownloadSuccess(false);
    try {
      const { blob, contentType } = await api.downloadReport(downloadReport.id);

      // Ensure blob is not empty or truncated
      if (blob.size < 200) {
        throw new Error(`Downloaded report is invalid or empty (${blob.size} bytes).`);
      }

      // Map Content-Type to appropriate file extension
      const extMap: Record<string, string> = {
        'application/pdf': '.pdf',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
        'text/html': '.html',
      };
      const ext = extMap[contentType] || (selectedFormat === 'EXCEL' ? '.xlsx' : selectedFormat === 'HTML' ? '.html' : '.pdf');
      const safeTitle = (reportTitle || 'Report').replace(/[^a-zA-Z0-9_\- ]/g, '').trim().replace(/\s+/g, '_');
      const downloadName = `PragyaDrishti_${safeTitle}${ext}`;

      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = downloadName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      // Only show success after download is verified and object URL triggered
      setDownloadSuccess(true);
      setDownloadedFileName(downloadName);
    } catch (e: any) {
      setErrorMsg(e.message || 'Download failed');
      setDownloadSuccess(false);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto p-4">
      {/* Header Banner */}
      <div className="glass-panel p-8 rounded-3xl border border-sky-500/20 space-y-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-2xl font-black text-white">Multi-Format Analytical Report Generator</h2>
            <p className="text-xs text-slate-400">
              Active Dataset: <span className="text-emerald-400 font-bold">{dataset?.name || 'All Datasets Summary'}</span>
              {dataset && <span className="text-slate-500 font-mono ml-2">(#{dataset.id} • {dataset.row_count} rows × {dataset.col_count} cols)</span>}
            </p>
          </div>
        </div>

        <div className="space-y-4 pt-2">
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-400">Report Title:</label>
            <input
              type="text"
              value={reportTitle}
              onChange={(e) => setReportTitle(e.target.value)}
              className="w-full glass-card bg-slate-900 border border-slate-700 text-slate-100 text-sm rounded-xl px-4 py-3 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-2">
            {formats.map((f) => {
              const Icon = f.icon;
              const isSelected = selectedFormat === f.id;
              return (
                <div
                  key={f.id}
                  onClick={() => setSelectedFormat(f.id)}
                  className={`p-4 rounded-xl cursor-pointer transition-all border ${
                    isSelected
                      ? 'bg-emerald-500/15 border-emerald-500/40 text-white shadow-md'
                      : 'glass-card hover:bg-slate-800 text-slate-400'
                  }`}
                >
                  <Icon className={`w-6 h-6 mb-2 ${isSelected ? 'text-emerald-400' : 'text-slate-400'}`} />
                  <p className="font-bold text-xs">{f.label}</p>
                  <p className="text-[10px] text-slate-400 mt-1">{f.desc}</p>
                </div>
              );
            })}
          </div>

          <button
            onClick={handleGenerate}
            disabled={generating}
            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white py-4 rounded-2xl text-sm font-extrabold shadow-glow flex items-center justify-center gap-2 transition-all disabled:opacity-50"
          >
            {generating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            {generating ? 'Compiling Dataset Report...' : `Generate ${selectedFormat} Report`}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {errorMsg && (
        <div className="glass-card p-4 rounded-2xl border border-rose-500/40 bg-rose-950/20 flex items-center gap-3 text-rose-300 text-xs font-semibold">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Download Action Card */}
      {downloadReport && (
        <div className="glass-card p-6 rounded-2xl border border-emerald-500/30 bg-emerald-950/10 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-3 text-emerald-400 font-bold text-xs">
                <CheckCircle2 className="w-5 h-5" /> Report compiled successfully ({downloadReport.report_type || selectedFormat})
              </div>
              <p className="text-[11px] text-slate-400 font-mono">
                Title: "{downloadReport.title}" • File: {downloadReport.file_path ? downloadReport.file_path.split(/[\\/]/).pop() : 'Ready'}
              </p>
            </div>
            <button
              onClick={handleDownload}
              disabled={downloading}
              className="bg-emerald-500 text-slate-950 px-6 py-2.5 rounded-xl text-xs font-bold shadow-md hover:bg-emerald-400 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <Download className="w-4 h-4" />
              {downloading ? 'Downloading...' : 'Download Report File'}
            </button>
          </div>

          {/* Downloaded successfully notice (only after validation) */}
          {downloadSuccess && (
            <div className="p-3 bg-emerald-500/20 border border-emerald-500/40 rounded-xl text-emerald-300 text-xs font-semibold flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>Report downloaded successfully ({downloadedFileName}).</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export const AdminDashboardView: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  React.useEffect(() => {
    api.getAdminStats()
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8 max-w-7xl mx-auto p-4">
      <div className="glass-panel p-8 rounded-3xl border border-sky-500/20 space-y-6">
        <h2 className="text-2xl font-black text-white">System Admin & Telemetry Monitor</h2>
        <p className="text-xs text-slate-400">Platform database statistics, model catalog count, reports generated, and system health.</p>

        {loading ? (
          <div className="text-center text-xs text-slate-400 font-mono py-8 animate-pulse">
            Fetching live platform telemetry & database record counts...
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6 pt-4">
            <div className="glass-card p-4 rounded-xl text-center">
              <p className="text-xs text-slate-400 font-bold">Total Datasets</p>
              <p className="text-3xl font-extrabold text-sky-400 mt-1">{stats?.total_datasets ?? 0}</p>
            </div>
            <div className="glass-card p-4 rounded-xl text-center">
              <p className="text-xs text-slate-400 font-bold">Trained ML Models</p>
              <p className="text-3xl font-extrabold text-purple-400 mt-1">{stats?.total_models ?? 0}</p>
            </div>
            <div className="glass-card p-4 rounded-xl text-center">
              <p className="text-xs text-slate-400 font-bold">Reports Generated</p>
              <p className="text-3xl font-extrabold text-emerald-400 mt-1">{stats?.total_reports ?? 0}</p>
            </div>
            <div className="glass-card p-4 rounded-xl text-center">
              <p className="text-xs text-slate-400 font-bold">System Health</p>
              <p className="text-3xl font-extrabold text-emerald-400 mt-1">{stats?.system_health || 'OPTIMAL'}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
