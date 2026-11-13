import React, { useState } from 'react';
import { X, ShieldCheck, Mail, Lock, User, LogIn, ArrowRight } from 'lucide-react';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    alert(`Successfully authenticated as ${email || 'user@pragyadrishti.ai'}`);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="glass-panel w-full max-w-md p-8 rounded-3xl border border-sky-500/20 shadow-2xl relative space-y-6">
        <button onClick={onClose} className="absolute top-4 right-4 text-slate-400 hover:text-white">
          <X className="w-5 h-5" />
        </button>

        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 mx-auto">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <h3 className="text-2xl font-black text-white">{isRegister ? 'Create Account' : 'Welcome Back'}</h3>
          <p className="text-xs text-slate-400">PragyaDrishti Enterprise Access</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label className="text-xs font-bold text-slate-400">Email Address</label>
            <div className="relative">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="analyst@domain.com"
                required
                className="w-full glass-card bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-xl px-4 py-3 pl-10 focus:outline-none focus:border-sky-500"
              />
              <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3.5" />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-bold text-slate-400">Password</label>
            <div className="relative">
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full glass-card bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-xl px-4 py-3 pl-10 focus:outline-none focus:border-sky-500"
              />
              <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3.5" />
            </div>
          </div>

          <button
            type="submit"
            className="w-full bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white py-3.5 rounded-xl text-xs font-bold shadow-glow flex items-center justify-center gap-2 transition-all"
          >
            <LogIn className="w-4 h-4" /> {isRegister ? 'Register Account' : 'Sign In'}
          </button>
        </form>

        <div className="relative text-center">
          <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-slate-800" /></div>
          <span className="relative bg-slate-950 px-3 text-[11px] text-slate-500 uppercase font-bold">Or Single Sign-On</span>
        </div>

        <button
          onClick={() => { alert('Authenticated via Google OAuth 2.0'); onClose(); }}
          className="w-full glass-card hover:bg-slate-800 text-slate-200 border border-slate-700 py-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-all"
        >
          <span className="font-bold text-sky-400">G</span> Continue with Google OAuth
        </button>

        <p className="text-center text-xs text-slate-400">
          {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
          <button onClick={() => setIsRegister(!isRegister)} className="text-sky-400 font-bold hover:underline">
            {isRegister ? 'Sign In' : 'Register Now'}
          </button>
        </p>
      </div>
    </div>
  );
};
