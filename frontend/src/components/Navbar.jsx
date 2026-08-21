import React from 'react';
import { 
  Zap, 
  ShieldCheck, 
  Activity, 
  BarChart3, 
  Sliders, 
  Search, 
  Cpu, 
  Github, 
  Sparkles,
  Terminal
} from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, liveStatus }) {
  const navItems = [
    { id: 'executive', label: 'Executive ROI', icon: BarChart3 },
    { id: 'livestream', label: 'Agent Command Center', icon: Activity, badge: 'Live Demo' },
    { id: 'explorer', label: 'Audit Explorer', icon: Search },
    { id: 'sandbox', label: 'Interactive Sandbox', icon: Terminal, badge: 'AI Tester' },
    { id: 'guardrails', label: 'Policy Guardrails', icon: ShieldCheck },
    { id: 'diagnostics', label: 'ML Scorer Lab', icon: Cpu },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo & Pitch */}
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-sky-500 to-emerald-400 p-[1.5px] flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <Zap className="h-5 w-5 text-sky-400 animate-pulse" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-lg tracking-tight text-white font-mono">
                  Recover<span className="text-sky-400">AI</span>
                </span>
                <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                  Autonomous
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Autonomous Revenue Recovery Agent
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center space-x-1 sm:space-x-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`relative flex items-center space-x-2 px-3 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? 'bg-slate-800 text-white shadow-sm border border-slate-700'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                  }`}
                >
                  <Icon className={`h-4 w-4 ${isActive ? 'text-sky-400' : 'text-slate-400'}`} />
                  <span className="hidden md:inline">{item.label}</span>
                  {item.badge && (
                    <span className={`text-[9px] font-bold px-1.5 py-0.2 rounded-full uppercase tracking-wider ${
                      isActive ? 'bg-sky-500/20 text-sky-300' : 'bg-slate-800 text-slate-400'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* GitHub & Live indicator */}
          <div className="flex items-center space-x-3">
            <a
              href="https://github.com/rehan0018/Alaadin"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white text-xs font-mono border border-slate-800 transition"
              title="View on GitHub"
            >
              <Github className="h-3.5 w-3.5" />
              <span className="hidden lg:inline">Alaadin</span>
            </a>
          </div>

        </div>
      </div>
    </header>
  );
}
