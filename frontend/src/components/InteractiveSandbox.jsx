import React, { useState } from 'react';
import { 
  Terminal, 
  Play, 
  Sparkles, 
  ShieldCheck, 
  Cpu, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  ArrowRight,
  RotateCcw,
  Zap,
  Code2
} from 'lucide-react';

const PRESET_SCENARIOS = [
  {
    name: "Temporary Bank Error (UPI)",
    desc: "₹2,499 UPI failure due to bank server timeout with high previous customer success rate (91%).",
    data: {
      amount: 2499,
      payment_method: "UPI",
      failure_code: "BANK_SERVER_ERROR",
      customer_age_days: 210,
      previous_transactions: 12,
      previous_success_rate: 0.91,
      previous_failures: 1,
      retry_count: 0,
      fraud_risk_score: 0.03,
      customer_value: 0.75,
      merchant_category: "ECOMMERCE"
    }
  },
  {
    name: "Card Expired (Permanent)",
    desc: "₹899 subscription attempt failed because credit card reached expiry date. Retrying card directly will fail.",
    data: {
      amount: 899,
      payment_method: "CREDIT_CARD",
      failure_code: "CARD_EXPIRED",
      customer_age_days: 90,
      previous_transactions: 3,
      previous_success_rate: 0.70,
      previous_failures: 1,
      retry_count: 0,
      fraud_risk_score: 0.02,
      customer_value: 0.50,
      merchant_category: "SAAS_SUBSCRIPTION"
    }
  },
  {
    name: "Max Retries Exceeded (High Ticket)",
    desc: "₹12,999 EdTech payment that already failed 3 times. Automated retries must stop and escalate.",
    data: {
      amount: 12999,
      payment_method: "DEBIT_CARD",
      failure_code: "INSUFFICIENT_FUNDS",
      customer_age_days: 350,
      previous_transactions: 8,
      previous_success_rate: 0.80,
      previous_failures: 3,
      retry_count: 3,
      fraud_risk_score: 0.05,
      customer_value: 0.85,
      merchant_category: "EDTECH"
    }
  },
  {
    name: "High Fraud Risk Velocity",
    desc: "₹45,000 transaction with high fraud risk score (0.88). Policy engine must intercept and block.",
    data: {
      amount: 45000,
      payment_method: "CREDIT_CARD",
      failure_code: "FRAUD_SUSPECTED",
      customer_age_days: 12,
      previous_transactions: 1,
      previous_success_rate: 0.0,
      previous_failures: 1,
      retry_count: 0,
      fraud_risk_score: 0.88,
      customer_value: 0.10,
      merchant_category: "TRAVEL_HOSPITALITY"
    }
  }
];

export default function InteractiveSandbox() {
  const [formData, setFormData] = useState(PRESET_SCENARIOS[0].data);
  const [activePresetIndex, setActivePresetIndex] = useState(0);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSelectPreset = (index) => {
    setActivePresetIndex(index);
    setFormData(PRESET_SCENARIOS[index].data);
    setResult(null);
  };

  const handleRunTest = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch('/api/agent/decide', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        const data = await res.json();
        setResult(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 animate-fade-in">
      
      {/* Top Banner */}
      <div className="glass-card rounded-2xl p-6 border border-slate-800">
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Terminal className="h-5 w-5 text-sky-400" />
          Interactive AI Decision Sandbox
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Inject real-time failed payment parameters to evaluate the ML Scorer, ReAct Agent tool invocation, and Policy Engine Guardrail decisions.
        </p>

        {/* Preset scenario tabs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-4">
          {PRESET_SCENARIOS.map((preset, idx) => (
            <button
              key={idx}
              onClick={() => handleSelectPreset(idx)}
              className={`p-3 rounded-xl border text-left transition-all ${
                activePresetIndex === idx
                  ? 'bg-sky-500/10 border-sky-400 text-sky-300 shadow-md'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
              }`}
            >
              <span className="text-xs font-bold font-mono block text-white mb-1">
                {preset.name}
              </span>
              <p className="text-[11px] text-slate-400 line-clamp-2">
                {preset.desc}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid: Input Form on Left, Output on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left: Input Editor */}
        <div className="lg:col-span-5 glass-card rounded-2xl p-6 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
              <Code2 className="h-4 w-4 text-sky-400" />
              Payment Payload Editor
            </h2>
            <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
              JSON Parameters
            </span>
          </div>

          <form onSubmit={handleRunTest} className="space-y-4 text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-slate-400 font-medium block mb-1">Amount (₹ INR)</label>
                <input
                  type="number"
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white font-mono"
                />
              </div>

              <div>
                <label className="text-slate-400 font-medium block mb-1">Payment Method</label>
                <select
                  value={formData.payment_method}
                  onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white font-mono"
                >
                  <option value="UPI">UPI</option>
                  <option value="CREDIT_CARD">Credit Card</option>
                  <option value="DEBIT_CARD">Debit Card</option>
                  <option value="NETBANKING">NetBanking</option>
                  <option value="MANDATE">Recurring Mandate</option>
                </select>
              </div>
            </div>

            <div>
              <label className="text-slate-400 font-medium block mb-1">Failure Code / Reason</label>
              <select
                value={formData.failure_code}
                onChange={(e) => setFormData({ ...formData, failure_code: e.target.value })}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white font-mono"
              >
                <option value="BANK_SERVER_ERROR">BANK_SERVER_ERROR (Temporary outage)</option>
                <option value="INSUFFICIENT_FUNDS">INSUFFICIENT_FUNDS (Account balance low)</option>
                <option value="CARD_EXPIRED">CARD_EXPIRED (Permanent card failure)</option>
                <option value="UPI_TRANSACTION_LIMIT">UPI_TRANSACTION_LIMIT (Daily ceiling reached)</option>
                <option value="AUTH_FAILED_OTP_TIMEOUT">AUTH_FAILED_OTP_TIMEOUT (3DS drop-off)</option>
                <option value="NETWORK_TIMEOUT">NETWORK_TIMEOUT (Gateway lag)</option>
                <option value="MANDATE_EXECUTION_FAILED">MANDATE_EXECUTION_FAILED (Recurring rejected)</option>
                <option value="FRAUD_SUSPECTED">FRAUD_SUSPECTED (High risk score)</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-slate-400 font-medium block mb-1">Previous Success Rate (0 - 1)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  value={formData.previous_success_rate}
                  onChange={(e) => setFormData({ ...formData, previous_success_rate: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white font-mono"
                />
              </div>

              <div>
                <label className="text-slate-400 font-medium block mb-1">Previous Retries Count</label>
                <input
                  type="number"
                  min="0"
                  max="10"
                  value={formData.retry_count}
                  onChange={(e) => setFormData({ ...formData, retry_count: parseInt(e.target.value) || 0 })}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white font-mono"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-slate-400 font-medium block mb-1">Fraud Risk Score (0 - 1)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  value={formData.fraud_risk_score}
                  onChange={(e) => setFormData({ ...formData, fraud_risk_score: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white font-mono"
                />
              </div>

              <div>
                <label className="text-slate-400 font-medium block mb-1">Merchant Category</label>
                <select
                  value={formData.merchant_category}
                  onChange={(e) => setFormData({ ...formData, merchant_category: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white font-mono"
                >
                  <option value="ECOMMERCE">E-Commerce</option>
                  <option value="SAAS_SUBSCRIPTION">SaaS Subscription</option>
                  <option value="EDTECH">EdTech</option>
                  <option value="TRAVEL_HOSPITALITY">Travel & Hospitality</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-bold rounded-xl shadow-lg shadow-sky-500/20 flex items-center justify-center gap-2 transition active:scale-[0.99]"
            >
              {loading ? (
                <>Processing Autonomous Pipeline...</>
              ) : (
                <>
                  <Zap className="h-4 w-4 fill-current" />
                  Run Autonomous Agent Decision
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right: Agent Decision & Guardrail Output */}
        <div className="lg:col-span-7 space-y-4">
          {result ? (
            <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-5 animate-fade-in">
              
              {/* Output Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-2">
                <div>
                  <span className="text-[10px] uppercase font-bold text-sky-400 font-mono">
                    Agent Decision Output
                  </span>
                  <h3 className="text-lg font-bold text-white">
                    Action: {result.final_action}
                  </h3>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                    result.policy_verdict === 'ALLOWED' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                    result.policy_verdict === 'MODIFIED' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                    'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                  }`}>
                    Policy: {result.policy_verdict}
                  </span>
                </div>
              </div>

              {/* 3 Metrics */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-center">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">ML Recovery Prob</span>
                  <span className={`text-xl font-bold font-mono ${
                    result.recovery_probability >= 0.7 ? 'text-emerald-400' :
                    result.recovery_probability >= 0.4 ? 'text-sky-400' : 'text-rose-400'
                  }`}>
                    {Math.round(result.recovery_probability * 100)}%
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-center">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">Expected Recovery</span>
                  <span className="text-xl font-bold font-mono text-emerald-300">
                    ₹{result.expected_recovered_value?.toLocaleString()}
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-center">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">Confidence</span>
                  <span className="text-xl font-bold font-mono text-indigo-300">
                    {result.confidence_tier}
                  </span>
                </div>
              </div>

              {/* Step by Step Execution Timeline */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono">
                  Autonomous Decision & Execution Timeline
                </h4>
                
                <div className="space-y-3 border-l-2 border-slate-800 ml-3 pl-4">
                  {result.audit_trail && result.audit_trail.map((step, idx) => (
                    <div key={idx} className="relative space-y-1">
                      <div className="absolute -left-[23px] top-1 w-3 h-3 rounded-full bg-slate-900 border-2 border-sky-400"></div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-bold text-white font-mono">{step.title}</span>
                        <span className="text-[10px] text-slate-500 font-mono">{step.timestamp}</span>
                      </div>
                      <p className="text-xs text-slate-300">{step.details}</p>
                      {step.tool_call && (
                        <div className="mt-1 px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px] font-mono text-sky-300 inline-block">
                          Tool Called: {step.tool_call}()
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

            </div>
          ) : (
            <div className="glass-card rounded-2xl p-12 border border-slate-800 text-center flex flex-col items-center justify-center min-h-[420px]">
              <div className="w-14 h-14 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center mb-3">
                <Sparkles className="h-6 w-6 text-sky-400" />
              </div>
              <h3 className="text-sm font-bold text-white">Click Run to Test Agent Brain</h3>
              <p className="text-xs text-slate-400 max-w-sm mt-1">
                Select any preset above or customize transaction details on the left to see the agent classify the failure, run the ML model, check guardrails, and execute tools.
              </p>
            </div>
          )}
        </div>

      </div>

    </div>
  );
}
