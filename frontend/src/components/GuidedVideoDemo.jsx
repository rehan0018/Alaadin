import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  SkipForward, 
  SkipBack, 
  X, 
  Sparkles, 
  ShieldCheck, 
  Cpu, 
  TrendingUp, 
  Layers, 
  CheckCircle2, 
  AlertTriangle,
  Flame,
  Volume2,
  Tv
} from 'lucide-react';

const DEMO_STEPS = [
  {
    id: 1,
    tab: 'executive',
    title: '1. The Problem: The Hidden ₹65L Revenue Leak',
    duration: 35,
    subtitle: 'Why traditional payment recovery fails',
    narration: 'Online merchants lose up to 10% of their top-line revenue to failed payment attempts. Traditional systems use dumb automation — blindly retrying transactions or spamming generic email reminders. This causes bank gateway penalties, customer friction, and costly fraud chargebacks.',
    badge: 'Problem Statement'
  },
  {
    id: 2,
    tab: 'executive',
    title: '2. The Solution: Autonomous Revenue Recovery Lifecycle',
    duration: 40,
    subtitle: 'Detect → Understand → Decide (ERV) → Policy → Act → Verify → Stop',
    narration: 'Alaadin is an autonomous AI agent that closes the loop between prediction and action. It diagnoses the root cause of every failure, optimizes multi-action Expected Recovery Value (ERV), passes decisions through a Hard Safety Policy Engine, and verifies banking settlement.',
    badge: 'Architecture'
  },
  {
    id: 3,
    tab: 'executive',
    title: '3. Scientific 3-Way Benchmark Experiment',
    duration: 45,
    subtitle: 'Identical 10,000 cohort evaluated against a Common Counterfactual Environment',
    narration: 'We evaluated Static Retry, Rule-Based Recovery, and Alaadin side-by-side on 10,000 holdout transactions. Alaadin generated +75.1% revenue lift (₹27.58 Lakhs recovered vs ₹15.75L static), eliminated 4,500 wasted retries, had 0 disallowed actions executed, and dropped cost per recovery to ₹2.80.',
    badge: 'Empirical ROI'
  },
  {
    id: 4,
    tab: 'sandbox',
    title: '4. Inside the Brain: ERV Action Optimization',
    duration: 45,
    subtitle: 'Expected Recovery Value = P(success | action) × Amount − Costs',
    narration: 'Instead of arbitrary IF/ELSE rules, Alaadin evaluates candidate actions mathematically. For a temporary bank outage, retrying after a 30-minute cooldown maximizes net ERV (₹2,174), while payment links yield lower returns due to customer drop-off.',
    badge: 'Decision Engine'
  },
  {
    id: 5,
    tab: 'failurelab',
    title: '5. Agent Failure Lab: "What If the Agent is Wrong?"',
    duration: 50,
    subtitle: 'Hard Policy Engine maintains the final, absolute veto over money movement',
    narration: 'Autonomous models must never have unchecked authority over money movement. In our Failure Lab, we stress-test edge cases: Already Succeeded payments are BLOCKED by State Lock, Fraud Risk 0.91 is BLOCKED by Fraud Gate, and ₹2,00,000 transactions mandate Human Approval.',
    badge: 'Safety Guarantee'
  },
  {
    id: 6,
    tab: 'livestream',
    title: '6. Live Command Center & Sub-Second Batch Simulation',
    duration: 45,
    subtitle: 'Real-time WebSocket streaming with 6-stage lifecycle visualization',
    narration: 'The Live Command Center connects directly via WebSocket, streaming payment events through Detect, Understand, Decide, Policy Gate, Act, and Verify. Our vectorized inference engine executes 1,000-payment batch simulations in just 313 milliseconds.',
    badge: 'Real-time Execution'
  },
  {
    id: 7,
    tab: 'explorer',
    title: '7. Auditable Decision Rationale & Compliance Export',
    duration: 35,
    subtitle: 'Itemized policy counters and 1-click CSV audit trail download',
    narration: 'Every decision produces a structured Decision Rationale card detailing why the payment failed, the calibrated probability, and itemized policy verification. Merchants can download 1-click CSV audit logs for full compliance and accounting.',
    badge: 'Audit & Compliance'
  },
  {
    id: 8,
    tab: 'executive',
    title: '8. Conclusion & The Future of Revenue Recovery',
    duration: 25,
    subtitle: 'Alaadin: Autonomous, Safe, and Empirically Proven',
    narration: 'Alaadin transforms payment recovery from dumb spam into an intelligent, mathematically optimized, and safety-bound autonomous agent that delivers massive top-line ROI. Thank you!',
    badge: 'Summary'
  }
];

export default function GuidedVideoDemo({ activeTab, setActiveTab, onClose }) {
  const [currentStepIdx, setCurrentStepIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);
  const [progress, setProgress] = useState(0); // 0 to 100%

  const currentStep = DEMO_STEPS[currentStepIdx];
  const timerRef = useRef(null);

  useEffect(() => {
    // Automatically switch active tab to match the step
    if (activeTab !== currentStep.tab) {
      setActiveTab(currentStep.tab);
    }
  }, [currentStepIdx]);

  useEffect(() => {
    if (!isPlaying) {
      if (timerRef.current) clearInterval(timerRef.current);
      return;
    }

    const stepDurationMs = currentStep.duration * 1000;
    const intervalMs = 100;
    const increment = (intervalMs / stepDurationMs) * 100;

    timerRef.current = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          // Advance to next step
          if (currentStepIdx < DEMO_STEPS.length - 1) {
            setCurrentStepIdx((idx) => idx + 1);
            return 0;
          } else {
            setIsPlaying(false);
            return 100;
          }
        }
        return prev + increment;
      });
    }, intervalMs);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, currentStepIdx, currentStep]);

  const handleNext = () => {
    if (currentStepIdx < DEMO_STEPS.length - 1) {
      setCurrentStepIdx((idx) => idx + 1);
      setProgress(0);
    }
  };

  const handlePrev = () => {
    if (currentStepIdx > 0) {
      setCurrentStepIdx((idx) => idx - 1);
      setProgress(0);
    }
  };

  const handleRestart = () => {
    setCurrentStepIdx(0);
    setProgress(0);
    setIsPlaying(true);
  };

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 w-full max-w-4xl px-4 animate-fade-in">
      <div className="bg-slate-950/95 border-2 border-sky-500/80 rounded-2xl shadow-2xl shadow-sky-500/20 backdrop-blur-xl p-5 text-white space-y-4">
        
        {/* Top Header Bar */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-sky-500/20 border border-sky-500/40 flex items-center justify-center">
              <Tv className="h-4 w-4 text-sky-400 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold font-mono uppercase text-sky-400">
                  Interactive Video Presentation Demo
                </span>
                <span className="px-2 py-0.2 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 uppercase font-mono">
                  {currentStep.badge}
                </span>
              </div>
              <h3 className="text-sm font-extrabold text-white">
                {currentStep.title}
              </h3>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-slate-400">
              Step {currentStepIdx + 1} of {DEMO_STEPS.length}
            </span>
            <button 
              onClick={onClose}
              className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white"
              title="Close Video Mode"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Verbatim Voiceover / Narration Subtitle Box */}
        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-start gap-3">
          <Volume2 className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
          <div className="space-y-1 flex-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono block">
              Narration Subtitles (Self-Playing Video Mode):
            </span>
            <p className="text-xs text-slate-200 leading-relaxed font-sans font-medium">
              "{currentStep.narration}"
            </p>
          </div>
        </div>

        {/* Timeline Progress Bar */}
        <div className="space-y-1.5">
          <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden border border-slate-800">
            <div 
              className="h-full bg-gradient-to-r from-sky-400 to-emerald-400 transition-all duration-100 ease-linear rounded-full"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono">
            <span>0:00</span>
            <span>{currentStep.subtitle}</span>
            <span>{currentStep.duration}s</span>
          </div>
        </div>

        {/* Playback Controls */}
        <div className="flex items-center justify-between pt-1">
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrev}
              disabled={currentStepIdx === 0}
              className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed text-slate-300 hover:text-white"
              title="Previous Step"
            >
              <SkipBack className="h-4 w-4" />
            </button>

            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="px-4 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs flex items-center gap-1.5 transition shadow-lg shadow-sky-500/20"
            >
              {isPlaying ? <><Pause className="h-3.5 w-3.5 fill-current" /> Pause</> : <><Play className="h-3.5 w-3.5 fill-current" /> Resume Video</>}
            </button>

            <button
              onClick={handleNext}
              disabled={currentStepIdx === DEMO_STEPS.length - 1}
              className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed text-slate-300 hover:text-white"
              title="Next Step"
            >
              <SkipForward className="h-4 w-4" />
            </button>

            <button
              onClick={handleRestart}
              className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white"
              title="Restart Video From Beginning"
            >
              <RotateCcw className="h-4 w-4" />
            </button>
          </div>

          <div className="flex items-center gap-1 text-[11px] text-slate-400">
            <span>Tip: Record your screen using <strong className="text-white">Win + Alt + R</strong> or Loom.</span>
          </div>
        </div>

      </div>
    </div>
  );
}
