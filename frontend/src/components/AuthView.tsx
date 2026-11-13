import React, { useState } from 'react';
import { Mail, Lock, User, LogIn, Sparkles, ShieldCheck, AlertCircle, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';

interface AuthViewProps {
  onLoginSuccess: (user: any, token: string) => void;
}

export const AuthView: React.FC<AuthViewProps> = ({ onLoginSuccess }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const data = await api.login(email, password);
      onLoginSuccess(data.user, data.access_token);
    } catch (err: any) {
      setErrorMsg(err.message || 'Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setErrorMsg('Passwords do not match');
      return;
    }
    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await api.register(fullName, email, password);
      setSuccessMsg('Account created successfully! Please sign in with your credentials.');
      setIsRegister(false);
      setPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      setErrorMsg(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col items-center justify-center p-4 relative overflow-hidden font-sans selection:bg-sky-500 selection:text-white">
      {/* Ambient background glow effects */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-sky-500/10 rounded-full blur-[128px] pointer-events-none" />
      <div className="absolute bottom-1/4 left-1/3 w-80 h-80 bg-purple-500/10 rounded-full blur-[128px] pointer-events-none" />

      <div className="w-full max-w-md space-y-8 relative z-10">
        {/* Brand Header */}
        <div className="text-center space-y-3">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-sky-500 via-indigo-500 to-purple-500 p-0.5 shadow-glow mx-auto">
            <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center">
              <Sparkles className="w-7 h-7 text-sky-400" />
            </div>
          </div>
          
          <h1 className="text-4xl md:text-5xl font-black tracking-tight text-white uppercase font-sans">
            PRAGYADRISHTI
          </h1>
          
          <p className="text-sm font-semibold text-slate-400 tracking-wide">
            AI-Powered Data Analytics & Visualization
          </p>
        </div>

        {/* Auth Card */}
        <div className="glass-panel p-8 rounded-3xl border border-sky-500/20 shadow-2xl space-y-6 bg-slate-900/60 backdrop-blur-xl">
          {!isRegister ? (
            /* Login Form */
            <div className="space-y-6">
              <div className="space-y-1">
                <h2 className="text-2xl font-black text-white">Welcome Back</h2>
                <p className="text-xs text-slate-400 font-medium">Sign in to continue to PragyaDrishti.</p>
              </div>

              {errorMsg && (
                <div className="glass-card p-3.5 rounded-xl border border-rose-500/40 bg-rose-950/20 flex items-center gap-2.5 text-rose-300 text-xs font-semibold">
                  <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                  <span>{errorMsg}</span>
                </div>
              )}

              {successMsg && (
                <div className="glass-card p-3.5 rounded-xl border border-emerald-500/40 bg-emerald-950/20 flex items-center gap-2.5 text-emerald-300 text-xs font-semibold">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>{successMsg}</span>
                </div>
              )}

              <form onSubmit={handleLogin} className="space-y-4">
                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">Email</label>
                  <div className="relative">
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="name@company.com"
                      required
                      className="w-full glass-card bg-slate-950/80 border border-slate-700 text-slate-100 text-xs rounded-xl px-4 py-3.5 pl-10 focus:outline-none focus:border-sky-500 transition-colors"
                    />
                    <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">Password</label>
                  <div className="relative">
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      required
                      className="w-full glass-card bg-slate-950/80 border border-slate-700 text-slate-100 text-xs rounded-xl px-4 py-3.5 pl-10 focus:outline-none focus:border-sky-500 transition-colors"
                    />
                    <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-sky-500 via-indigo-600 to-purple-600 hover:from-sky-400 hover:to-purple-500 text-white py-3.5 rounded-xl text-xs font-black tracking-wider uppercase shadow-glow flex items-center justify-center gap-2 transition-all disabled:opacity-50 mt-2"
                >
                  <LogIn className="w-4 h-4" /> {loading ? 'Signing In...' : 'LOGIN'}
                </button>
              </form>

              <div className="text-center pt-2 border-t border-slate-800/80">
                <p className="text-xs text-slate-400">
                  Don't have an account?{' '}
                  <button
                    type="button"
                    onClick={() => { setIsRegister(true); setErrorMsg(null); setSuccessMsg(null); }}
                    className="text-sky-400 font-bold hover:underline ml-1"
                  >
                    Create Account
                  </button>
                </p>
              </div>
            </div>
          ) : (
            /* Register Form */
            <div className="space-y-6">
              <div className="space-y-1">
                <h2 className="text-2xl font-black text-white">Create Account</h2>
                <p className="text-xs text-slate-400 font-medium">Create your account to get started.</p>
              </div>

              {errorMsg && (
                <div className="glass-card p-3.5 rounded-xl border border-rose-500/40 bg-rose-950/20 flex items-center gap-2.5 text-rose-300 text-xs font-semibold">
                  <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                  <span>{errorMsg}</span>
                </div>
              )}

              <form onSubmit={handleRegister} className="space-y-4">
                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">Full Name</label>
                  <div className="relative">
                    <input
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Alex Morgan"
                      required
                      className="w-full glass-card bg-slate-950/80 border border-slate-700 text-slate-100 text-xs rounded-xl px-4 py-3.5 pl-10 focus:outline-none focus:border-sky-500 transition-colors"
                    />
                    <User className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">Email</label>
                  <div className="relative">
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="name@company.com"
                      required
                      className="w-full glass-card bg-slate-950/80 border border-slate-700 text-slate-100 text-xs rounded-xl px-4 py-3.5 pl-10 focus:outline-none focus:border-sky-500 transition-colors"
                    />
                    <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">Password</label>
                  <div className="relative">
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      required
                      className="w-full glass-card bg-slate-950/80 border border-slate-700 text-slate-100 text-xs rounded-xl px-4 py-3.5 pl-10 focus:outline-none focus:border-sky-500 transition-colors"
                    />
                    <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">Confirm Password</label>
                  <div className="relative">
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="••••••••"
                      required
                      className="w-full glass-card bg-slate-950/80 border border-slate-700 text-slate-100 text-xs rounded-xl px-4 py-3.5 pl-10 focus:outline-none focus:border-sky-500 transition-colors"
                    />
                    <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-sky-500 via-indigo-600 to-purple-600 hover:from-sky-400 hover:to-purple-500 text-white py-3.5 rounded-xl text-xs font-black tracking-wider uppercase shadow-glow flex items-center justify-center gap-2 transition-all disabled:opacity-50 mt-2"
                >
                  <ShieldCheck className="w-4 h-4" /> {loading ? 'Creating Account...' : 'CREATE ACCOUNT'}
                </button>
              </form>

              <div className="text-center pt-2 border-t border-slate-800/80">
                <p className="text-xs text-slate-400">
                  Already have an account?{' '}
                  <button
                    type="button"
                    onClick={() => { setIsRegister(false); setErrorMsg(null); setSuccessMsg(null); }}
                    className="text-sky-400 font-bold hover:underline ml-1"
                  >
                    Login
                  </button>
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
