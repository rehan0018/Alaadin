import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  Activity, 
  ShieldCheck, 
  Zap, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Clock, 
  DollarSign, 
  Sparkles,
  Eye,
  Layers,
  Radio
} from 'lucide-react';

export default function AgentLiveStream({ onSelectPayment }) {
  const [isRunning, setIsRunning] = useState(false);
  const [speed, setSpeed] = useState(1); // 1x, 2x, 5x
  const [events, setEvents] = useState([]);
  const [liveRecoveredINR, setLiveRecoveredINR] = useState(0);
  const [liveAttempts, setLiveAttempts] = useState(0);
  const [liveSuccessCount, setLiveSuccessCount] = useState(0);
  const [activeStepIndex, setActiveStepIndex] = useState(0);
  const [batchLoading, setBatchLoading] = useState(false);
  const [batchSuccessMsg, setBatchSuccessMsg] = useState(null);

  const socketRef = useRef(null);
  const intervalRef = useRef(null);

  const pipelineStages = [
    { id: 'detect', label: '1. Detect', desc: 'Ingest Payment Event' },
    { id: 'understand', label: '2. Understand', desc: 'Diagnose Root Cause' },
    { id: 'decide', label: '3. Decide', desc: 'Calibrated ML & ERV' },
    { id: 'guardrails', label: '4. Policy Gate', desc: 'Hard Boundary Veto' },
    { id: 'act', label: '5. Act', desc: 'Execute Tool & Retry' },
    { id: 'verify', label: '6. Verify', desc: 'Check Settlement' },
  ];

  // Fetch sample live payments via WebSocket or API
  const processNextSimulatedEvent = async () => {
    try {
      const sampleCodes = [
        { code: "BANK_SERVER_ERROR", method: "UPI", amt: 2499.0, successRate: 0.92, retries: 0, fraud: 0.03, mins: 10 },
        { code: "INSUFFICIENT_FUNDS", method: "DEBIT_CARD", amt: 1499.0, successRate: 0.75, retries: 1, fraud: 0.04, mins: 45 },
        { code: "CARD_EXPIRED", method: "CREDIT_CARD", amt: 899.0, successRate: 0.60, retries: 0, fraud: 0.02, mins: 15 },
        { code: "NETWORK_TIMEOUT", method: "UPI", amt: 4999.0, successRate: 0.95, retries: 0, fraud: 0.01, mins: 5 },
        { code: "AUTH_FAILED_OTP_TIMEOUT", method: "UPI", amt: 1999.0, successRate: 0.82, retries: 0, fraud: 0.05, mins: 20 },
        { code: "FRAUD_SUSPECTED", method: "CREDIT_CARD", amt: 35000.0, successRate: 0.20, retries: 0, fraud: 0.88, mins: 2 },
        { code: "UPI_TRANSACTION_LIMIT", method: "UPI", amt: 12500.0, successRate: 0.89, retries: 1, fraud: 0.02, mins: 60 },
        { code: "MANDATE_EXECUTION_FAILED", method: "MANDATE", amt: 999.0, successRate: 0.94, retries: 1, fraud: 0.01, mins: 30 },
      ];

      const sample = sampleCodes[Math.floor(Math.random() * sampleCodes.length)];
      const randomPayId = `PAY_${Math.floor(10000 + Math.random() * 90000)}`;

      const response = await fetch('/api/agent/decide', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          payment_id: randomPayId,
          amount: sample.amt,
          payment_method: sample.method,
          failure_code: sample.code,
          previous_success_rate: sample.successRate,
          retry_count: sample.retries,
          time_since_failure_mins: sample.mins,
          fraud_risk_score: sample.fraud
        })
      });

      if (!response.ok) return;
      const data = await response.json();

      setActiveStepIndex((prev) => (prev + 1) % 6);
      setEvents((prev) => [data, ...prev.slice(0, 49)]);
      setLiveAttempts((prev) => prev + 1);

      if (data.is_recovered) {
        setLiveRecoveredINR((prev) => prev + data.recovered_amount);
        setLiveSuccessCount((prev) => prev + 1);
      }
    } catch (e) {
      console.error("Simulation error", e);
    }
  };

  useEffect(() => {
    if (isRunning) {
      const delay = Math.max(400, 1500 / speed);
      intervalRef.current = setInterval(processNextSimulatedEvent, delay);
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isRunning, speed]);

  const handleReset = () => {
    setIsRunning(false);
    setEvents([]);
    setLiveRecoveredINR(0);
    setLiveAttempts(0);
    setLiveSuccessCount(0);
    setBatchSuccessMsg(null);
  };

  const handleRunBatch1000 = async () => {
    setBatchLoading(true);
    setBatchSuccessMsg(null);
    try {
      const res = await fetch('/api/simulate/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sample_size: 1000 })
      });
      if (res.ok) {
        const data = await res.json();
        setBatchSuccessMsg(`Successfully simulated 1,000 transactions! Recovered ₹${data.summary.recovered_lakhs} Lakhs (${data.summary.recovery_rate_pct}% rate).`);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setBatchLoading(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      
      {/* Top Header & Ticker */}
      <div className="glass-card rounded-2xl p-6 border border-slate-800 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <span className="flex h-2.5 w-2.5 relative">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${isRunning ? 'bg-emerald-400 opacity-75' : 'bg-slate-500'}`}></span>
              <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${isRunning ? 'bg-emerald-500' : 'bg-slate-600'}`}></span>
            </span>
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-sky-400">
              Autonomous Command Center
            </span>
            <span className="text-xs text-slate-500">|</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-emerald-400 border border-slate-700">
              Environment: TEST / SANDBOX
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-sky-300 border border-slate-700">
              Razorpay API: READY
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-white">
            Detect → Understand → Decide (ERV) → Policy Boundary → Act → Verify → Stop
          </h1>
        </div>

        {/* Live Counters */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="px-4 py-2 rounded-xl bg-slate-900 border border-slate-800">
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Live Recovered</span>
            <span className="text-lg font-bold font-mono text-emerald-400">
              ₹{liveRecoveredINR.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
            </span>
          </div>

          <div className="px-4 py-2 rounded-xl bg-slate-900 border border-slate-800">
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Recoveries</span>
            <span className="text-lg font-bold font-mono text-sky-300">
              {liveSuccessCount} / {liveAttempts}
            </span>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-2 bg-slate-900 p-1.5 rounded-xl border border-slate-800">
            <button
              onClick={() => setIsRunning(!isRunning)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                isRunning 
                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30 hover:bg-rose-500/30' 
                  : 'bg-emerald-500 text-slate-950 font-bold hover:bg-emerald-400 shadow-md'
              }`}
            >
              {isRunning ? <><Pause className="h-3.5 w-3.5 fill-current" /> Pause</> : <><Play className="h-3.5 w-3.5 fill-current" /> Run Live</>}
            </button>

            <button
              onClick={processNextSimulatedEvent}
              className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
              title="Step 1 Event"
            >
              Step
            </button>

            {/* Speed toggle */}
            <div className="flex items-center bg-slate-950 rounded-lg p-0.5 border border-slate-800 text-[10px] font-mono">
              {[1, 2, 5].map((s) => (
                <button
                  key={s}
                  onClick={() => setSpeed(s)}
                  className={`px-2 py-1 rounded ${speed === s ? 'bg-indigo-600 text-white font-bold' : 'text-slate-400 hover:text-white'}`}
                >
                  {s}x
                </button>
              ))}
            </div>

            <button
              onClick={handleRunBatch1000}
              disabled={batchLoading}
              className="px-2.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
              title="Run 1,000 Batch Simulation"
            >
              {batchLoading ? 'Simulating...' : 'Batch 1k'}
            </button>

            <button
              onClick={handleReset}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800"
              title="Reset Live Stream"
            >
              <RotateCcw className="h-3.5 w-3.5" />
            </button>
          </div>

        </div>
      </div>

      {batchSuccessMsg && (
        <div className="px-5 py-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold flex items-center gap-2 animate-fade-in">
          <CheckCircle2 className="h-4 w-4" />
          {batchSuccessMsg}
        </div>
      )}

      {/* Visual Animated Pipeline Stage Nodes */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {pipelineStages.map((stage, idx) => {
          const isActive = idx === activeStepIndex && isRunning;
          return (
            <div 
              key={stage.id}
              className={`rounded-xl p-3.5 border transition-all duration-300 relative overflow-hidden ${
                isActive 
                  ? 'bg-indigo-950/40 border-sky-400/80 shadow-lg shadow-sky-500/10' 
                  : 'bg-slate-900/60 border-slate-800/80'
              }`}
            >
              {isActive && (
                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-sky-400 to-indigo-500 animate-pulse"></div>
              )}
              <div className="flex items-center justify-between">
                <span className={`text-xs font-bold font-mono ${isActive ? 'text-sky-300' : 'text-slate-400'}`}>
                  {stage.label}
                </span>
                {isActive && <Sparkles className="h-3.5 w-3.5 text-sky-400 animate-spin" />}
              </div>
              <p className="text-[11px] text-slate-400 mt-1 truncate">
                {stage.desc}
              </p>
            </div>
          );
        })}
      </div>

      {/* Live Event Stream Feed */}
      <div className="glass-card rounded-2xl border border-slate-800 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/40">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-sky-400 animate-pulse" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              Live Decision Activity Stream
            </h2>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
              {events.length} events logged
            </span>
          </div>
          <span className="text-xs text-slate-400 hidden sm:block">
            Click any event card to inspect structured Decision Rationale & itemized policy verification
          </span>
        </div>

        <div className="divide-y divide-slate-800/60 max-h-[620px] overflow-y-auto">
          {events.length === 0 ? (
            <div className="text-center py-16 px-4">
              <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto mb-3">
                <Zap className="h-5 w-5 text-sky-400" />
              </div>
              <h3 className="text-sm font-semibold text-slate-300">Ready to simulate failed transactions</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
                Click "Run Live" to watch RecoverAI detect failed payments, optimize multi-action ERV, enforce policy safety boundaries, and verify banking settlements.
              </p>
              <button
                onClick={() => setIsRunning(true)}
                className="px-4 py-2 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs"
              >
                Start Live Stream
              </button>
            </div>
          ) : (
            events.map((evt, idx) => (
              <div
                key={`${evt.payment_id}-${idx}`}
                onClick={() => onSelectPayment(evt)}
                className="p-5 hover:bg-slate-900/60 transition cursor-pointer group flex flex-col lg:flex-row lg:items-center justify-between gap-4"
              >
                {/* Left: Payment & Root Cause */}
                <div className="space-y-1.5 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-xs font-bold text-white px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
                      {evt.payment_id}
                    </span>
                    <span className="font-mono text-xs font-bold text-emerald-400">
                      ₹{evt.amount?.toLocaleString()}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700 font-sans">
                      {evt.payment_method}
                    </span>
                    <span className="text-xs font-medium text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20 font-mono">
                      {evt.failure_code}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 flex items-center gap-1.5 font-sans">
                    <span className="text-slate-400 font-medium">Diagnostic:</span>
                    <span>{evt.action_summary}</span>
                  </p>
                </div>

                {/* Middle: ML Score & Policy Check */}
                <div className="flex items-center gap-4 lg:px-4 border-l border-slate-800/80">
                  <div className="text-center min-w-[70px]">
                    <span className="text-[10px] text-slate-400 uppercase font-bold block">P(Recovery)</span>
                    <span className={`text-sm font-bold font-mono ${
                      evt.recovery_probability >= 0.75 ? 'text-emerald-400' :
                      evt.recovery_probability >= 0.45 ? 'text-sky-400' : 'text-rose-400'
                    }`}>
                      {Math.round(evt.recovery_probability * 100)}%
                    </span>
                  </div>

                  <div className="min-w-[120px]">
                    <span className="text-[10px] text-slate-400 uppercase font-bold block">Policy Guardrail</span>
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full inline-flex items-center gap-1 font-sans ${
                      evt.policy_verdict === 'APPROVED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' :
                      evt.policy_verdict === 'HUMAN_APPROVAL_REQUIRED' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/30' :
                      'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                    }`}>
                      {evt.policy_verdict === 'APPROVED' && <CheckCircle2 className="h-3 w-3" />}
                      {evt.policy_verdict === 'HUMAN_APPROVAL_REQUIRED' && <AlertTriangle className="h-3 w-3" />}
                      {evt.policy_verdict === 'BLOCKED' && <XCircle className="h-3 w-3" />}
                      {evt.policy_verdict}
                    </span>
                  </div>
                </div>

                {/* Right: Outcome Status & Inspect Button */}
                <div className="flex items-center justify-between lg:justify-end gap-3 min-w-[170px]">
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase font-bold block text-right">Outcome</span>
                    <span className={`text-xs font-bold font-mono ${
                      evt.is_recovered ? 'text-emerald-400' : 'text-slate-400'
                    }`}>
                      {evt.is_recovered ? `₹${evt.recovered_amount?.toLocaleString()} Recovered` : 'Action Pending'}
                    </span>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectPayment(evt);
                    }}
                    className="p-1.5 rounded-lg bg-slate-800 group-hover:bg-sky-500/20 group-hover:text-sky-300 text-slate-400 transition"
                    title="View Decision Rationale"
                  >
                    <Eye className="h-4 w-4" />
                  </button>
                </div>

              </div>
            ))
          )}
        </div>
      </div>

    </div>
  );
}
