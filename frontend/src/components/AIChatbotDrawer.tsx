import React, { useState } from 'react';
import { X, Send, Bot, User, Sparkles } from 'lucide-react';
import { api } from '../services/api';

interface AIChatbotDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  datasetId?: number;
}

export const AIChatbotDrawer: React.FC<AIChatbotDrawerProps> = ({ isOpen, onClose, datasetId }) => {
  const [messages, setMessages] = useState([
    { sender: 'ai', text: 'Hello! I am your PragyaDrishti AI Data Scientist Agent. Ask me anything about your uploaded dataset, schema properties, correlations, missing values, or model predictions!' }
  ]);
  const [inputPrompt, setInputPrompt] = useState('');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSend = async () => {
    if (!inputPrompt.trim()) return;
    const userMsg = inputPrompt;
    setMessages((prev) => [...prev, { sender: 'user', text: userMsg }]);
    setInputPrompt('');
    setLoading(true);

    try {
      const res = await api.askChatbot(userMsg, datasetId);
      setMessages((prev) => [...prev, { sender: 'ai', text: res.answer || res.detail || 'Analysis complete.' }]);
    } catch (e: any) {
      setMessages((prev) => [...prev, { sender: 'ai', text: e.message || 'Please upload or select a dataset first.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-96 glass-panel border-l border-slate-800 shadow-2xl flex flex-col justify-between">
      {/* Drawer Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-400">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">AI Data Scientist Agent</h3>
            <p className="text-[10px] text-slate-400">Dataset Context Aware • Gemini 1.5</p>
          </div>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-white">
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Messages List */}
      <div className="flex-1 p-4 overflow-y-auto space-y-3">
        {messages.map((m, idx) => (
          <div key={idx} className={`flex gap-2.5 ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            {m.sender === 'ai' && (
              <div className="w-7 h-7 rounded-lg bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-400 shrink-0 mt-1">
                <Sparkles className="w-3.5 h-3.5" />
              </div>
            )}
            <div className={`p-3 rounded-2xl text-xs leading-relaxed max-w-[80%] ${
              m.sender === 'user'
                ? 'bg-sky-500 text-white rounded-br-none'
                : 'glass-card text-slate-200 border border-slate-800 rounded-bl-none font-mono'
            }`}>
              {m.text}
            </div>
          </div>
        ))}
        {loading && (
          <p className="text-[11px] text-slate-500 animate-pulse font-mono">AI is reading dataset schema metrics & calculating factual answers...</p>
        )}
      </div>

      {/* Input Form */}
      <div className="p-4 border-t border-slate-800 flex gap-2">
        <input
          type="text"
          value={inputPrompt}
          onChange={(e) => setInputPrompt(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask about your dataset..."
          className="flex-1 glass-card bg-slate-900 border border-slate-700 text-slate-100 text-xs rounded-xl px-3 py-2.5 focus:outline-none focus:border-purple-500"
        />
        <button onClick={handleSend} className="bg-purple-600 hover:bg-purple-500 text-white px-4 rounded-xl text-xs font-bold transition-all">
          <Send className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
