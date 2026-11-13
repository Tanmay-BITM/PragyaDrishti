import React from 'react';
import { Sparkles, Brain, Cpu, Wand2, BarChart2, ShieldCheck, ArrowRight, CheckCircle2, Star, Zap } from 'lucide-react';

interface LandingPageProps {
  onStart: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onStart }) => {
  return (
    <div className="space-y-16 py-6 px-4 md:px-8 max-w-7xl mx-auto">
      {/* Hero Section */}
      <section className="relative text-center py-16 space-y-8 overflow-hidden rounded-3xl glass-panel border border-slate-800/80 p-8">
        <div className="absolute -top-24 -left-24 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-sky-500/10 border border-sky-500/30 text-sky-400 text-xs font-bold shadow-glow">
          <Sparkles className="w-4 h-4" /> Next-Generation AI Data Scientist Platform
        </div>

        <h1 className="text-4xl md:text-6xl font-black tracking-tight text-white leading-tight max-w-4xl mx-auto">
          Turn Raw Data into <span className="text-gradient">Intelligent Insights</span> with AI
        </h1>

        <p className="text-base md:text-xl text-slate-300 max-w-2xl mx-auto font-semibold leading-relaxed tracking-wide">
          From Raw Data to Real Intelligence — All in One Platform.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
          <button
            onClick={onStart}
            className="flex items-center gap-3 bg-gradient-to-r from-sky-500 via-indigo-500 to-purple-600 hover:from-sky-400 hover:to-purple-500 text-white px-8 py-4 rounded-2xl text-sm font-extrabold shadow-glow transition-all transform hover:scale-105"
          >
            Launch Prompt-to-ML Engine
            <ArrowRight className="w-4 h-4" />
          </button>
          
          <button
            onClick={onStart}
            className="glass-card hover:bg-slate-800/80 text-slate-200 border border-slate-700 px-6 py-4 rounded-2xl text-sm font-semibold transition-all"
          >
            Explore Interactive Demo
          </button>
        </div>

        {/* Feature Counters */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 pt-12 border-t border-slate-800/60 max-w-4xl mx-auto">
          {[
            { label: 'ML Algorithms', val: '10+ Benchmark' },
            { label: 'Auto Cleaning', val: '100% Automated' },
            { label: 'REST Deployments', val: 'Instant 1-Click' },
            { label: 'Report Formats', val: 'PDF, Excel, PPTX' },
          ].map((stat, i) => (
            <div key={i} className="glass-card p-4 rounded-2xl">
              <p className="text-xl font-extrabold text-sky-400">{stat.val}</p>
              <p className="text-xs text-slate-400 mt-1">{stat.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features Grid */}
      <section className="space-y-8">
        <div className="text-center space-y-3">
          <h2 className="text-2xl md:text-3xl font-extrabold text-white">Enterprise AI Data Science Capabilities</h2>
          <p className="text-sm text-slate-400 max-w-xl mx-auto">Complete end-to-end automation from raw dataset ingestion to deployed production APIs.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { title: 'Flagship Prompt-to-ML', desc: 'Type prompts like "Predict churn" or "Forecast revenue". AI auto-detects task type, pre-processes, builds model leaderboard, and exports .pkl.', icon: Brain, badge: 'Flagship' },
            { title: 'AutoML & Hyperparameter Tuning', desc: 'Compares Random Forest, XGBoost, LightGBM, SVM, and PyTorch MLPs with 5-Fold Cross Validation & SHAP explanations.', icon: Cpu },
            { title: 'Automated Data Cleaner', desc: 'Instant data quality scoring, missing value imputation, IQR outlier clipping, duplicate removal, and type normalization.', icon: Wand2 },
            { title: 'Interactive Chart Studio', desc: '13 dynamic chart types (Bar, Line, Scatter, Heatmap, Correlation Matrix, Radar) with custom drag-and-drop dashboard composer.', icon: BarChart2 },
            { title: 'Predictive Analytics Studio', desc: 'Real-time model inference and forecasting engine using trained pipelines with exact feature schemas and interactive parameter inputs.', icon: ShieldCheck },
            { title: 'Multi-Format Reports', desc: 'One-click export of complete executive analytical reports in PDF, Excel, PowerPoint, and interactive HTML.', icon: Zap },
          ].map((feat, i) => {
            const Icon = feat.icon;
            return (
              <div key={i} className="glass-card p-6 rounded-2xl space-y-4 hover:border-sky-500/40 relative">
                {feat.badge && (
                  <span className="absolute top-4 right-4 bg-purple-500/20 text-purple-300 border border-purple-500/30 text-[10px] px-2 py-0.5 rounded-full font-bold">
                    {feat.badge}
                  </span>
                )}
                <div className="w-12 h-12 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
                  <Icon className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-white">{feat.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{feat.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Pricing Section */}
      <section className="space-y-8 py-8">
        <div className="text-center space-y-3">
          <h2 className="text-2xl md:text-3xl font-extrabold text-white">Transparent SaaS Pricing</h2>
          <p className="text-sm text-slate-400">Choose the ideal plan for your team or organization.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { plan: 'Starter', price: '$0', desc: 'Ideal for individuals & students', feats: ['3 Datasets / month', 'Standard ML Models', 'Basic Charts', 'Community Support'] },
            { plan: 'Pro Analyst', price: '$49', desc: 'For data scientists & business teams', feats: ['Unlimited Datasets', 'Full AutoML & XGBoost', 'Flagship Prompt-to-ML', 'PDF/Excel Reports', 'Instant REST APIs'], highlight: true },
            { plan: 'Enterprise', price: '$199', desc: 'For high-scale enterprise deployments', feats: ['Dedicated Cloud Compute', 'Face Recognition Module', 'Custom Model Tuning', 'SLA 99.9% Uptime', '24/7 Security Audit'] },
          ].map((tier, i) => (
            <div key={i} className={`glass-card p-8 rounded-3xl space-y-6 flex flex-col justify-between ${tier.highlight ? 'border-2 border-sky-500 shadow-glow' : ''}`}>
              <div className="space-y-4">
                <h3 className="text-xl font-bold text-white">{tier.plan}</h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-extrabold text-sky-400">{tier.price}</span>
                  <span className="text-xs text-slate-400">/ month</span>
                </div>
                <p className="text-xs text-slate-400">{tier.desc}</p>
                <div className="space-y-2 pt-4 border-t border-slate-800">
                  {tier.feats.map((f, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-xs text-slate-300">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                      {f}
                    </div>
                  ))}
                </div>
              </div>
              <button onClick={onStart} className={`w-full py-3 rounded-xl text-xs font-bold transition-all ${tier.highlight ? 'bg-sky-500 hover:bg-sky-400 text-white shadow-md' : 'glass-card hover:bg-slate-800 text-slate-200'}`}>
                Get Started
              </button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
