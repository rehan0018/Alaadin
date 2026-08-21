import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  Save, 
  Sparkles, 
  CheckCircle2, 
  Sliders, 
  Clock, 
  Lock, 
  Ban,
  DollarSign
} from 'lucide-react';

export default function GuardrailManager() {
  const [policy, setPolicy] = useState({
    max_retries: 3,
    max_notifications: 2,
    max_recovery_window_hours: 72,
    fraud_risk_threshold: 0.65,
    enforce_quiet_hours: true,
    high_ticket_escalation_amount: 15000.0,
    allow_automated_discounts: true
  });

  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    fetch('/api/policy')
      .then((res) => res.json())
      .then((data) => {
        if (data) setPolicy(data);
      })
      .catch(console.error);
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await fetch('/api/policy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(policy)
      });
      if (res.ok) {
        setSavedSuccess(true);
        setTimeout(() => setSavedSuccess(false), 3000);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      
      {/* Top Banner */}
      <div className="glass-card rounded-2xl p-6 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              Razorpay Enterprise Grade
            </span>
            <span className="text-xs text-slate-400">Accountability & Boundary Controls</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-white flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-sky-400" />
            Merchant Policy Engine & Guardrails
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Autonomous agents must respect strict merchant boundaries. Guardrails prevent customer spam, intercept high-risk fraud attempts, and guarantee that already-settled transactions are never retried.
          </p>
        </div>

        {savedSuccess && (
          <div className="px-4 py-2 rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-xs font-semibold flex items-center gap-2 animate-fade-in">
            <CheckCircle2 className="h-4 w-4" />
            Guardrails Updated Live!
          </div>
        )}
      </div>

      <form onSubmit={handleSave} className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Sliders and Controls */}
        <div className="lg:col-span-7 space-y-4">
          
          {/* Card 1: Retries & Notifications */}
          <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-5">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
              <Sliders className="h-4 w-4 text-sky-400" />
              Contact & Execution Limits
            </h2>

            {/* Max Retries */}
            <div>
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="font-semibold text-slate-200">Maximum Automated Gateway Retries</span>
                <span className="font-mono font-bold text-sky-400 px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                  {policy.max_retries} Attempts
                </span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                step="1"
                value={policy.max_retries}
                onChange={(e) => setPolicy({ ...policy, max_retries: parseInt(e.target.value) })}
                className="w-full h-2 bg-slate-900 rounded-lg appearance-none cursor-pointer accent-sky-400"
              />
              <span className="text-[11px] text-slate-500 mt-1 block">
                Attempts beyond {policy.max_retries} are automatically terminated or escalated to merchant support.
              </span>
            </div>

            {/* Max Customer Notifications */}
            <div>
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="font-semibold text-slate-200">Maximum Customer Outreach Messages</span>
                <span className="font-mono font-bold text-indigo-400 px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                  {policy.max_notifications} Messages
                </span>
              </div>
              <input
                type="range"
                min="1"
                max="4"
                step="1"
                value={policy.max_notifications}
                onChange={(e) => setPolicy({ ...policy, max_notifications: parseInt(e.target.value) })}
                className="w-full h-2 bg-slate-900 rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
              <span className="text-[11px] text-slate-500 mt-1 block">
                Suppresses customer fatigue across WhatsApp, SMS, and Email.
              </span>
            </div>

            {/* Max Recovery Window */}
            <div>
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="font-semibold text-slate-200">Recovery Time Window</span>
                <span className="font-mono font-bold text-emerald-400 px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                  {policy.max_recovery_window_hours} Hours
                </span>
              </div>
              <input
                type="range"
                min="12"
                max="120"
                step="12"
                value={policy.max_recovery_window_hours}
                onChange={(e) => setPolicy({ ...policy, max_recovery_window_hours: parseInt(e.target.value) })}
                className="w-full h-2 bg-slate-900 rounded-lg appearance-none cursor-pointer accent-emerald-500"
              />
            </div>
          </div>

          {/* Card 2: Risk & Escalation */}
          <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-5">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
              <Lock className="h-4 w-4 text-rose-400" />
              Risk Thresholds & Quiet Hours
            </h2>

            {/* Fraud Risk Cutoff */}
            <div>
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="font-semibold text-slate-200">Fraud Risk Score Interception Gate</span>
                <span className="font-mono font-bold text-rose-400 px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                  Score &gt; {policy.fraud_risk_threshold}
                </span>
              </div>
              <input
                type="range"
                min="0.3"
                max="0.9"
                step="0.05"
                value={policy.fraud_risk_threshold}
                onChange={(e) => setPolicy({ ...policy, fraud_risk_threshold: parseFloat(e.target.value) })}
                className="w-full h-2 bg-slate-900 rounded-lg appearance-none cursor-pointer accent-rose-500"
              />
              <span className="text-[11px] text-slate-500 mt-1 block">
                Transactions with risk score exceeding this cutoff are immediately frozen from automated retries.
              </span>
            </div>

            {/* High Ticket Escalation Amount */}
            <div>
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="font-semibold text-slate-200">High-Ticket Escalation Threshold (₹ INR)</span>
                <span className="font-mono font-bold text-amber-400 px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                  ₹{policy.high_ticket_escalation_amount?.toLocaleString()}
                </span>
              </div>
              <input
                type="number"
                value={policy.high_ticket_escalation_amount}
                onChange={(e) => setPolicy({ ...policy, high_ticket_escalation_amount: parseFloat(e.target.value) || 0 })}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white font-mono text-xs"
              />
            </div>

            {/* Quiet Hours Toggle */}
            <div className="flex items-center justify-between pt-2 border-t border-slate-800">
              <div>
                <span className="text-xs font-semibold text-white block">Enforce Night Quiet Hours (10 PM - 8 AM)</span>
                <span className="text-[11px] text-slate-400">Holds customer messages during nighttime hours.</span>
              </div>
              <button
                type="button"
                onClick={() => setPolicy({ ...policy, enforce_quiet_hours: !policy.enforce_quiet_hours })}
                className={`w-12 h-6 rounded-full transition-colors relative ${
                  policy.enforce_quiet_hours ? 'bg-sky-500' : 'bg-slate-800'
                }`}
              >
                <div className={`w-5 h-5 rounded-full bg-white transition-transform ${
                  policy.enforce_quiet_hours ? 'translate-x-6' : 'translate-x-0.5'
                }`} />
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={saving}
            className="w-full py-3 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-bold rounded-xl shadow-lg shadow-sky-500/20 flex items-center justify-center gap-2 transition"
          >
            <Save className="h-4 w-4" />
            {saving ? 'Updating Active Guardrails...' : 'Save & Enforce Policy Engine'}
          </button>
        </div>

        {/* Right: Policy Rulebook Explanation */}
        <div className="lg:col-span-5 glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
            Active Guardrail Rules
          </h3>

          <div className="space-y-3 text-xs">
            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <div className="flex items-center gap-2 text-emerald-400 font-bold">
                <CheckCircle2 className="h-4 w-4" />
                State Lock Guardrail
              </div>
              <p className="text-slate-400 text-[11px]">
                If a payment has already settled as SUCCESS via bank webhooks or customer link, all agent actions are instantly terminated.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <div className="flex items-center gap-2 text-emerald-400 font-bold">
                <CheckCircle2 className="h-4 w-4" />
                Opt-Out Compliance
              </div>
              <p className="text-slate-400 text-[11px]">
                If a customer has opted out of marketing or recovery communications, customer-facing notifications are suppressed while silent smart retries proceed.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <div className="flex items-center gap-2 text-emerald-400 font-bold">
                <CheckCircle2 className="h-4 w-4" />
                Fraud Defense
              </div>
              <p className="text-slate-400 text-[11px]">
                Payments scoring above {policy.fraud_risk_threshold} fraud risk are halted to protect merchant from chargeback penalties and network blacklisting.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <div className="flex items-center gap-2 text-emerald-400 font-bold">
                <CheckCircle2 className="h-4 w-4" />
                High-Ticket Escalation
              </div>
              <p className="text-slate-400 text-[11px]">
                Payments above ₹{policy.high_ticket_escalation_amount?.toLocaleString()} are routed to merchant support agents with complete diagnostic briefings.
              </p>
            </div>
          </div>
        </div>

      </form>

    </div>
  );
}
