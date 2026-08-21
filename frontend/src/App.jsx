import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import ExecutiveDashboard from './components/ExecutiveDashboard';
import AgentLiveStream from './components/AgentLiveStream';
import AgentFailureLab from './components/AgentFailureLab';
import PaymentInvestigation from './components/PaymentInvestigation';
import InteractiveSandbox from './components/InteractiveSandbox';
import GuardrailManager from './components/GuardrailManager';
import ModelDiagnostics from './components/ModelDiagnostics';

export default function App() {
  const [activeTab, setActiveTab] = useState('executive');
  const [stats, setStats] = useState(null);
  const [selectedPayment, setSelectedPayment] = useState(null);

  const fetchStats = async () => {
    try {
      const res = await fetch('/api/stats');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (e) {
      console.error('Failed to fetch stats', e);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleTriggerLiveDemo = () => {
    setActiveTab('livestream');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        {activeTab === 'executive' && (
          <ExecutiveDashboard 
            stats={stats} 
            onTriggerLiveDemo={handleTriggerLiveDemo}
          />
        )}

        {activeTab === 'livestream' && (
          <AgentLiveStream 
            onSelectPayment={(payment) => setSelectedPayment(payment)}
          />
        )}

        {activeTab === 'failurelab' && (
          <AgentFailureLab />
        )}

        {activeTab === 'explorer' && (
          <PaymentInvestigation 
            selectedPayment={selectedPayment}
            onSelectPayment={(payment) => setSelectedPayment(payment)}
            onCloseDetail={() => setSelectedPayment(null)}
          />
        )}

        {activeTab === 'sandbox' && (
          <InteractiveSandbox />
        )}

        {activeTab === 'guardrails' && (
          <GuardrailManager />
        )}

        {activeTab === 'diagnostics' && (
          <ModelDiagnostics />
        )}
      </main>

      {/* Detail Modal for Live Stream inspection */}
      {activeTab === 'livestream' && selectedPayment && (
        <PaymentInvestigation 
          selectedPayment={selectedPayment}
          onSelectPayment={(payment) => setSelectedPayment(payment)}
          onCloseDetail={() => setSelectedPayment(null)}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-6 text-center text-xs text-slate-500 font-mono">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Alaadin — Autonomous Payment Recovery Agent | Track: AI Revenue Recovery</span>
          <span>Detect → Understand → Decide (ERV) → Policy Boundary → Act → Verify → Stop</span>
        </div>
      </footer>
    </div>
  );
}
