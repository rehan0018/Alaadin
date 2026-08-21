import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Filter, 
  ChevronRight, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Clock, 
  ShieldCheck, 
  Cpu, 
  User, 
  CreditCard, 
  Terminal, 
  X, 
  Sparkles, 
  ArrowRight,
  ExternalLink,
  Send,
  RotateCw,
  Ban
} from 'lucide-react';

export default function PaymentInvestigation({ selectedPayment, onSelectPayment, onCloseDetail }) {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [methodFilter, setMethodFilter] = useState('ALL');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [overrideStatus, setOverrideStatus] = useState(null);

  const fetchPayments = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: '15',
        method: methodFilter,
        search: searchQuery
      });
      const res = await fetch(`/api/payments?${params}`);
      if (res.ok) {
        const data = await res.json();
        setPayments(data.data || []);
        setTotalPages(data.total_pages || 1);
      }
    } catch (e) {
      console.error("Failed to load payments", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPayments();
  }, [page, methodFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchPayments();
  };

  const handleManualOverride = async (action) => {
    if (!selectedPayment) return;
    try {
      const res = await fetch('/api/override', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          payment_id: selectedPayment.payment_id,
          action: action,
          note: 'Merchant manual override dispatched from Audit Explorer.'
        })
      });
      if (res.ok) {
        const data = await res.json();
        setOverrideStatus(data.message);
        setTimeout(() => setOverrideStatus(null), 4000);
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6 pb-12 animate-fade-in relative">
      
      {/* Top Filter Bar */}
      <div className="glass-card rounded-2xl p-5 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Search className="h-5 w-5 text-sky-400" />
            Payment Investigation & Audit Explorer
          </h1>
          <p className="text-xs text-slate-400">
            Search failed payments, inspect ML factor attribution, and audit full agent decision logs
          </p>
        </div>

        <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by Payment ID or Customer..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-400 w-64"
            />
          </div>

          <select
            value={methodFilter}
            onChange={(e) => {
              setMethodFilter(e.target.value);
              setPage(1);
            }}
            className="py-2 px-3 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-sky-400"
          >
            <option value="ALL">All Methods</option>
            <option value="UPI">UPI</option>
            <option value="CREDIT_CARD">Credit Card</option>
            <option value="DEBIT_CARD">Debit Card</option>
            <option value="NETBANKING">NetBanking</option>
            <option value="MANDATE">Recurring Mandate</option>
          </select>

          <button
            type="submit"
            className="px-4 py-2 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs rounded-xl transition"
          >
            Filter
          </button>
        </form>
      </div>

      {/* Main Table */}
      <div className="glass-card rounded-2xl border border-slate-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 border-b border-slate-800 text-slate-400 font-mono uppercase text-[10px]">
              <tr>
                <th className="px-6 py-3.5">Payment ID</th>
                <th className="px-6 py-3.5">Amount</th>
                <th className="px-6 py-3.5">Method</th>
                <th className="px-6 py-3.5">Failure Reason</th>
                <th className="px-6 py-3.5">ML Prob</th>
                <th className="px-6 py-3.5">Guardrails</th>
                <th className="px-6 py-3.5">Action Executed</th>
                <th className="px-6 py-3.5">Outcome</th>
                <th className="px-6 py-3.5 text-right">Audit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan="9" className="text-center py-12 text-slate-400">
                    Loading payments...
                  </td>
                </tr>
              ) : payments.length === 0 ? (
                <tr>
                  <td colSpan="9" className="text-center py-12 text-slate-400">
                    No payment records found matching criteria.
                  </td>
                </tr>
              ) : (
                payments.map((p) => (
                  <tr 
                    key={p.payment_id}
                    onClick={() => onSelectPayment(p)}
                    className="hover:bg-slate-900/60 transition cursor-pointer group"
                  >
                    <td className="px-6 py-4 font-mono font-bold text-white">
                      {p.payment_id}
                    </td>
                    <td className="px-6 py-4 font-mono font-semibold text-emerald-400">
                      ₹{p.amount?.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-slate-300">
                      <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-[11px]">
                        {p.payment_method}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20 text-[11px] font-mono">
                        {p.failure_code}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-mono font-bold">
                      <span className={
                        p.recovery_probability >= 0.75 ? 'text-emerald-400' :
                        p.recovery_probability >= 0.45 ? 'text-sky-400' : 'text-rose-400'
                      }>
                        {Math.round(p.recovery_probability * 100)}%
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold inline-flex items-center gap-1 ${
                        p.policy_verdict === 'ALLOWED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' :
                        p.policy_verdict === 'MODIFIED' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30' :
                        'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                      }`}>
                        {p.policy_verdict === 'ALLOWED' && <CheckCircle2 className="h-3 w-3" />}
                        {p.policy_verdict === 'MODIFIED' && <AlertTriangle className="h-3 w-3" />}
                        {p.policy_verdict === 'BLOCKED' && <XCircle className="h-3 w-3" />}
                        {p.policy_verdict}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-300 font-mono text-[11px]">
                      {p.final_action}
                    </td>
                    <td className="px-6 py-4 font-mono font-bold">
                      {p.is_recovered ? (
                        <span className="text-emerald-400">✓ Recovered</span>
                      ) : (
                        <span className="text-slate-500">Pending</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button className="text-sky-400 hover:text-sky-300 font-medium text-xs flex items-center gap-1 ml-auto">
                        Inspect <ChevronRight className="h-3.5 w-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="px-6 py-3 bg-slate-900/60 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span>Page {page} of {totalPages}</span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-white"
            >
              Previous
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-white"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Deep-Dive Audit Trail Drawer / Modal */}
      {selectedPayment && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/70 backdrop-blur-sm animate-fade-in p-4 sm:p-6">
          <div className="bg-slate-950 border border-slate-800 w-full max-w-2xl h-full max-h-[94vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden">
            
            {/* Drawer Header */}
            <div className="px-6 py-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-base font-bold text-white">
                    {selectedPayment.payment_id}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                    selectedPayment.is_recovered ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-slate-800 text-slate-400'
                  }`}>
                    {selectedPayment.is_recovered ? 'RECOVERED' : 'PENDING'}
                  </span>
                </div>
                <p className="text-xs text-slate-400">
                  Customer: {selectedPayment.customer_id || 'CUST_7821'} | Method: {selectedPayment.payment_method}
                </p>
              </div>

              <button
                onClick={onCloseDetail}
                className="p-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Notification alert if override clicked */}
            {overrideStatus && (
              <div className="bg-sky-500/10 border-b border-sky-500/30 px-6 py-2.5 text-xs text-sky-300 flex items-center gap-2 animate-fade-in">
                <Sparkles className="h-4 w-4" />
                {overrideStatus}
              </div>
            )}

            {/* Drawer Body (Scrollable) */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              
              {/* Summary Cards */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800">
                  <span className="text-[10px] uppercase font-bold text-slate-500 block">Amount</span>
                  <span className="text-base font-bold font-mono text-emerald-400">
                    ₹{selectedPayment.amount?.toLocaleString()}
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800">
                  <span className="text-[10px] uppercase font-bold text-slate-500 block">Recovery Prob</span>
                  <span className="text-base font-bold font-mono text-sky-400">
                    {Math.round((selectedPayment.recovery_probability || 0.85) * 100)}%
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800">
                  <span className="text-[10px] uppercase font-bold text-slate-500 block">Expected Value</span>
                  <span className="text-base font-bold font-mono text-indigo-300">
                    ₹{Math.round(selectedPayment.expected_recovered_value || (selectedPayment.amount * (selectedPayment.recovery_probability || 0.85))).toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Guardrails Policy Verdict */}
              <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white flex items-center gap-1.5">
                    <ShieldCheck className="h-4 w-4 text-sky-400" />
                    Merchant Policy Guardrail Check
                  </span>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                    selectedPayment.policy_verdict === 'ALLOWED' ? 'bg-emerald-500/20 text-emerald-400' :
                    selectedPayment.policy_verdict === 'MODIFIED' ? 'bg-amber-500/20 text-amber-400' :
                    'bg-rose-500/20 text-rose-400'
                  }`}>
                    {selectedPayment.policy_verdict}
                  </span>
                </div>
                <p className="text-xs text-slate-300">
                  {selectedPayment.policy_reason}
                </p>

                {/* Passed / Failed Checks */}
                {selectedPayment.passed_checks && selectedPayment.passed_checks.length > 0 && (
                  <div className="pt-2 space-y-1">
                    {selectedPayment.passed_checks.map((chk, i) => (
                      <div key={i} className="text-[11px] text-emerald-400 flex items-center gap-1.5">
                        <CheckCircle2 className="h-3 w-3" />
                        {chk}
                      </div>
                    ))}
                  </div>
                )}
                {selectedPayment.failed_checks && selectedPayment.failed_checks.length > 0 && (
                  <div className="pt-1 space-y-1">
                    {selectedPayment.failed_checks.map((chk, i) => (
                      <div key={i} className="text-[11px] text-rose-400 flex items-center gap-1.5">
                        <XCircle className="h-3 w-3" />
                        {chk}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Complete Step-by-Step ReAct Audit Trail */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono flex items-center gap-2">
                  <Terminal className="h-4 w-4 text-sky-400" />
                  Full Autonomous Agent Audit Log
                </h3>

                <div className="space-y-3 border-l-2 border-slate-800 ml-3 pl-4">
                  {selectedPayment.audit_trail && selectedPayment.audit_trail.map((step, idx) => (
                    <div key={idx} className="relative space-y-1">
                      <div className="absolute -left-[23px] top-1 w-3 h-3 rounded-full bg-slate-900 border-2 border-sky-400"></div>
                      
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-bold text-white font-mono">{step.title || step.step}</span>
                        <span className="text-[10px] text-slate-500 font-mono">{step.timestamp}</span>
                      </div>
                      
                      <p className="text-xs text-slate-300 leading-relaxed">
                        {step.details}
                      </p>

                      {step.tool_call && (
                        <div className="mt-1 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-[11px] font-mono text-sky-300 inline-block">
                          Tool Invoked: <span className="text-white font-semibold">{step.tool_call}()</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

            </div>

            {/* Drawer Footer: Manual Override Controls */}
            <div className="p-4 bg-slate-900/90 border-t border-slate-800 flex items-center justify-between gap-2">
              <span className="text-[11px] text-slate-400 font-medium">Merchant Override:</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleManualOverride('FORCE_RETRY')}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-medium flex items-center gap-1 transition"
                >
                  <RotateCw className="h-3 w-3" />
                  Retry Gateway
                </button>
                <button
                  onClick={() => handleManualOverride('SEND_CUSTOM_LINK')}
                  className="px-3 py-1.5 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold rounded-lg text-xs flex items-center gap-1 transition"
                >
                  <Send className="h-3 w-3" />
                  Send WhatsApp Link
                </button>
                <button
                  onClick={() => handleManualOverride('HALT_RECOVERY')}
                  className="px-3 py-1.5 bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/30 rounded-lg text-xs font-medium flex items-center gap-1 transition"
                >
                  <Ban className="h-3 w-3" />
                  Halt
                </button>
              </div>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
