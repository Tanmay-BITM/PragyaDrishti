import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { LandingPage } from './components/LandingPage';
import { PersonalDashboard } from './components/PersonalDashboard';
import { DatasetUpload } from './components/DatasetUpload';
import { AutoCleanView } from './components/AutoCleanView';
import { PromptMLEngine } from './components/PromptMLEngine';
import { NLAnalyticsView } from './components/NLAnalyticsView';
import { VisualizationEngine } from './components/VisualizationEngine';
import { AIInsightsView } from './components/AIInsightsView';
import { PredictiveAnalyticsView } from './components/PredictiveAnalyticsView';
import { ReportGeneratorView, AdminDashboardView } from './components/ReportGeneratorView';
import { AIChatbotDrawer } from './components/AIChatbotDrawer';
import { AuthView } from './components/AuthView';
import { Dataset } from './types';
import { api } from './services/api';

export function App() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('pd_token'));
  const [user, setUser] = useState<any>(() => {
    const u = localStorage.getItem('pd_user');
    return u ? JSON.parse(u) : null;
  });

  const [activeTab, setActiveTab] = useState('landing');
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [activeDataset, setActiveDataset] = useState<Dataset | null>(null);

  const refreshDatasets = () => {
    if (token) {
      api.getDatasets().then((data) => {
        // Deduplicate records by id
        const unique = Array.from(new Map(data.map((d) => [d.id, d])).values());
        setDatasets(unique);
        setActiveDataset((current) => {
          if (!current && unique.length > 0) return unique[0];
          if (current) {
            const match = unique.find((d) => d.id === current.id);
            return match || (unique.length > 0 ? unique[0] : null);
          }
          return null;
        });
      });
    }
  };

  useEffect(() => {
    refreshDatasets();
  }, [token]);

  const handleLoginSuccess = (userData: any, accessToken: string) => {
    localStorage.setItem('pd_token', accessToken);
    localStorage.setItem('pd_user', JSON.stringify(userData));
    setToken(accessToken);
    setUser(userData);
    setActiveTab('landing');
  };

  const handleLogout = () => {
    localStorage.removeItem('pd_token');
    localStorage.removeItem('pd_user');
    setToken(null);
    setUser(null);
  };

  const handleUploadSuccess = (newDs: Dataset) => {
    setDatasets((prev) => {
      const filtered = prev.filter((d) => d.id !== newDs.id && d.filename !== newDs.filename);
      return [newDs, ...filtered];
    });
    setActiveDataset(newDs);
  };

  const handleSelectDataset = (ds: Dataset) => {
    setActiveDataset(ds);
  };

  // If user is not authenticated, render Login/Register entry gate
  if (!token) {
    return <AuthView onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col font-sans selection:bg-sky-500 selection:text-white">
      {/* Header Navigation with Global Dataset Context Switcher */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenChat={() => setIsChatOpen(true)}
        user={user}
        onLogout={handleLogout}
        datasets={datasets}
        activeDataset={activeDataset}
        onSelectDataset={handleSelectDataset}
      />

      {/* Main Layout Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

        {/* Content View Container */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 pb-20">
          {activeTab === 'landing' && <LandingPage onStart={() => setActiveTab('prompt-ml')} />}
          {activeTab === 'dashboard' && <PersonalDashboard datasets={datasets} onNavigate={setActiveTab} />}
          {activeTab === 'datasets' && (
            <DatasetUpload
              datasets={datasets}
              selectedDataset={activeDataset}
              onSelectDataset={handleSelectDataset}
              onUploadSuccess={handleUploadSuccess}
              onNavigateToClean={(ds) => { setActiveDataset(ds); setActiveTab('auto-clean'); }}
            />
          )}
          {activeTab === 'auto-clean' && (
            <AutoCleanView
              dataset={activeDataset}
              onCleaningComplete={refreshDatasets}
            />
          )}
          {(activeTab === 'prompt-ml' || activeTab === 'automl') && (
            <PromptMLEngine
              datasets={datasets}
              selectedDataset={activeDataset}
              onSelectDataset={handleSelectDataset}
            />
          )}
          {activeTab === 'analytics' && <NLAnalyticsView dataset={activeDataset} />}
          {activeTab === 'visualization' && <VisualizationEngine dataset={activeDataset} />}
          {activeTab === 'insights' && <AIInsightsView dataset={activeDataset} />}
          {activeTab === 'forecasting' && <PredictiveAnalyticsView dataset={activeDataset} onNavigate={setActiveTab} />}
          {activeTab === 'reports' && <ReportGeneratorView dataset={activeDataset} />}
          {activeTab === 'admin' && <AdminDashboardView />}
        </main>
      </div>

      {/* AI Chatbot Drawer (Always strictly dataset-aware) */}
      <AIChatbotDrawer isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} datasetId={activeDataset?.id} />
    </div>
  );
}

export default App;
