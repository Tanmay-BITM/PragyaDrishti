import { Dataset, MLModel, ReportItem } from '../types';

const API_BASE = '/api/v1';

export const api = {
  // Authentication
  async login(email: string, password: string) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) {
      let errorDetail = 'Invalid email or password';
      try {
        const err = await res.json();
        if (err && err.detail) errorDetail = err.detail;
      } catch (e) {}
      throw new Error(errorDetail);
    }
    return await res.json();
  },

  async register(fullName: string, email: string, password: string) {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ full_name: fullName, email, password })
    });
    if (!res.ok) {
      let errorDetail = 'Registration failed';
      try {
        const err = await res.json();
        if (err && err.detail) errorDetail = err.detail;
      } catch (e) {}
      throw new Error(errorDetail);
    }
    return await res.json();
  },

  // Datasets
  async getDatasets(): Promise<Dataset[]> {
    try {
      const res = await fetch(`${API_BASE}/datasets/list`);
      if (res.ok) return await res.json();
    } catch (e) {}
    return [];
  },

  async uploadDataset(file: File): Promise<Dataset> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/datasets/upload`, { method: 'POST', body: formData });
    if (!res.ok) {
      let errorDetail = `Upload failed (HTTP ${res.status})`;
      try {
        const err = await res.json();
        if (err && err.detail) errorDetail = err.detail;
      } catch (e) {}
      throw new Error(errorDetail);
    }
    return await res.json();
  },

  async previewDataset(datasetId: number) {
    const res = await fetch(`${API_BASE}/datasets/${datasetId}/preview`);
    if (!res.ok) {
      let errorDetail = `Preview failed (HTTP ${res.status})`;
      try {
        const err = await res.json();
        if (err && err.detail) errorDetail = err.detail;
      } catch (e) {}
      throw new Error(errorDetail);
    }
    return await res.json();
  },

  async autoCleanDataset(datasetId: number, req = { fill_missing: true, remove_duplicates: true, handle_outliers: true }) {
    const res = await fetch(`${API_BASE}/datasets/${datasetId}/auto-clean`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req)
    });
    if (!res.ok) {
      let errorDetail = `Auto-clean failed (HTTP ${res.status})`;
      try {
        const err = await res.json();
        if (err && err.detail) errorDetail = err.detail;
      } catch (e) {}
      throw new Error(errorDetail);
    }
    return await res.json();
  },

  // Prompt-to-ML
  async trainFromPrompt(prompt: string, datasetId: number, targetColumn?: string): Promise<MLModel> {
    const res = await fetch(`${API_BASE}/prompt-ml/train`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, dataset_id: datasetId, target_column: targetColumn })
    });
    if (!res.ok) {
      let errorDetail = `Model training failed (HTTP ${res.status})`;
      try {
        const err = await res.json();
        if (err && err.detail) errorDetail = err.detail;
      } catch (e) {}
      throw new Error(errorDetail);
    }
    return await res.json();
  },

  // Predict Endpoint Call
  async predictModel(modelId: number, features: Record<string, any>) {
    const res = await fetch(`${API_BASE}/prompt-ml/predict/${modelId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ features })
    });
    if (!res.ok) {
      let errorDetail = `Prediction execution failed (HTTP ${res.status})`;
      try {
        const err = await res.json();
        if (err && err.detail) errorDetail = err.detail;
      } catch (e) {}
      throw new Error(errorDetail);
    }
    return await res.json();
  },

  // AutoML Benchmark
  async runAutoML(datasetId: number, targetColumn?: string, taskType: string = 'auto'): Promise<MLModel> {
    const res = await fetch(`${API_BASE}/automl/train`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dataset_id: datasetId, target_column: targetColumn, task_type: taskType })
    });
    if (!res.ok) {
      let errorDetail = `AutoML benchmark failed (HTTP ${res.status})`;
      try {
        const err = await res.json();
        if (err && err.detail) errorDetail = err.detail;
      } catch (e) {}
      throw new Error(errorDetail);
    }
    return await res.json();
  },

  // Reports Generation
  async generateReport(title: string, reportType: string, summary: string, datasetId?: number) {
    const url = datasetId 
      ? `${API_BASE}/reports/generate?title=${encodeURIComponent(title)}&report_type=${reportType}&summary=${encodeURIComponent(summary)}&dataset_id=${datasetId}`
      : `${API_BASE}/reports/generate?title=${encodeURIComponent(title)}&report_type=${reportType}&summary=${encodeURIComponent(summary)}`;
    const res = await fetch(url, { method: 'POST' });
    if (!res.ok) {
      let errorDetail = `Report generation failed (HTTP ${res.status})`;
      try {
        const err = await res.json();
        if (err && err.detail) errorDetail = err.detail;
      } catch (e) {}
      throw new Error(errorDetail);
    }
    return await res.json();
  },

  async downloadReport(reportId: number) {
    const res = await fetch(`${API_BASE}/reports/download/${reportId}`);
    if (!res.ok) {
      let errorDetail = `Download failed (HTTP ${res.status})`;
      try {
        const err = await res.json();
        if (err && err.detail) errorDetail = err.detail;
      } catch (e) {}
      throw new Error(errorDetail);
    }
    const contentType = res.headers.get('Content-Type') || 'application/octet-stream';
    const blob = await res.blob();
    return { blob, contentType };
  },

  // NL Analytics
  async runNLQuery(datasetId: number, query: string) {
    const res = await fetch(`${API_BASE}/analytics/query/${datasetId}?query=${encodeURIComponent(query)}`, { method: 'POST' });
    if (!res.ok) {
      let errorDetail = `Analytics query failed (HTTP ${res.status})`;
      try {
        const err = await res.json();
        if (err && err.detail) errorDetail = err.detail;
      } catch (e) {}
      throw new Error(errorDetail);
    }
    return await res.json();
  },

  // Forecasting
  async getForecast(datasetId: number, targetColumn?: string) {
    const url = targetColumn 
      ? `${API_BASE}/forecasting/${datasetId}?target_column=${encodeURIComponent(targetColumn)}`
      : `${API_BASE}/forecasting/${datasetId}`;
    const res = await fetch(url);
    if (!res.ok) {
      let errorDetail = `Forecasting failed (HTTP ${res.status})`;
      try {
        const err = await res.json();
        if (err && err.detail) errorDetail = err.detail;
      } catch (e) {}
      throw new Error(errorDetail);
    }
    return await res.json();
  },

  // AI Insights
  async getInsights(datasetId: number) {
    const res = await fetch(`${API_BASE}/analytics/insights/${datasetId}`);
    if (!res.ok) {
      let errorDetail = `Failed to fetch executive insights (HTTP ${res.status})`;
      try {
        const err = await res.json();
        if (err && err.detail) errorDetail = err.detail;
      } catch (e) {}
      throw new Error(errorDetail);
    }
    return await res.json();
  },

  // Chatbot (Dataset Aware)
  async askChatbot(prompt: string, datasetId?: number) {
    const url = datasetId 
      ? `${API_BASE}/chatbot/ask?prompt=${encodeURIComponent(prompt)}&dataset_id=${datasetId}`
      : `${API_BASE}/chatbot/ask?prompt=${encodeURIComponent(prompt)}`;
    const res = await fetch(url, { method: 'POST' });
    if (!res.ok) {
      let errorDetail = `Chatbot failed (HTTP ${res.status})`;
      try {
        const err = await res.json();
        if (err && err.detail) errorDetail = err.detail;
      } catch (e) {}
      throw new Error(errorDetail);
    }
    return await res.json();
  },

  // Admin Stats
  async getAdminStats() {
    const res = await fetch(`${API_BASE}/admin/stats`);
    if (!res.ok) throw new Error(`Failed to load admin stats (HTTP ${res.status})`);
    return await res.json();
  },

  // Dataset ML Models
  async getDatasetModels(datasetId: number): Promise<MLModel[]> {
    try {
      const res = await fetch(`${API_BASE}/prompt-ml/models/${datasetId}`);
      if (res.ok) return await res.json();
    } catch (e) {}
    return [];
  }
};

