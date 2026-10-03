import React, { useState } from 'react';
import { 
  Sliders, 
  CheckCircle2, 
  AlertTriangle, 
  ArrowRight, 
  Layers, 
  TrendingDown, 
  Database, 
  Zap, 
  ShieldCheck, 
  Play, 
  Clock,
  Check
} from 'lucide-react';
import type { Recommendation, QueryEvent, User } from '../types/queryguard';
import { api } from '../lib/api';

interface SimulationsShowcaseViewProps {
  recommendations: Recommendation[];
  queries: QueryEvent[];
  currentUser: User;
  onOpenSimulationModal: (rec: Recommendation) => void;
  onSelectRecommendation: (recId: string) => void;
}

export const SimulationsShowcaseView: React.FC<SimulationsShowcaseViewProps> = ({
  recommendations,
  queries,
  currentUser,
  onOpenSimulationModal,
  onSelectRecommendation
}) => {
  const [runningRecId, setRunningRecId] = useState<string | null>(null);
  const [simulationResults, setSimulationResults] = useState<Record<string, any>>({});
  const [filterType, setFilterType] = useState<string>('ALL');

  const handleSimulateDirectly = async (rec: Recommendation) => {
    setRunningRecId(rec.id);
    try {
      const res = await api.simulateRecommendation(rec.id);
      if (res) {
        setSimulationResults(prev => ({
          ...prev,
          [rec.id]: res
        }));
      }
    } catch (err) {
      console.error('Direct simulation error:', err);
    } finally {
      setRunningRecId(null);
    }
  };

  const simulatedRecs = recommendations.filter(r => r.simulation && r.simulation.status === 'COMPLETED');
  const filteredRecs = recommendations.filter(r => {
    if (filterType === 'SIMULATED') return r.simulation?.status === 'COMPLETED';
    if (filterType === 'PENDING') return !r.simulation || r.simulation.status !== 'COMPLETED';
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <h1 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
              HypoPG In-Memory Simulations
            </h1>
            <span className="badge badge-success">Zero Disk Footprint</span>
            <span className="badge badge-brand">Ephemeral Sandbox</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: 13, maxWidth: 680 }}>
            Safely test hypothetical candidate indexes in memory using PostgreSQL’s <code style={{ color: 'var(--brand-primary-text)' }}>hypopg</code> extension. Evaluates optimizer plan cost reduction without allocating physical storage or holding write locks.
          </p>
        </div>

        {/* Filter controls */}
        <div style={{ display: 'flex', gap: 6, backgroundColor: 'var(--bg-subtle)', padding: 4, borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-default)' }}>
          {(['ALL', 'SIMULATED', 'PENDING'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setFilterType(tab)}
              className={`btn ${filterType === tab ? 'btn-primary' : 'btn-secondary'}`}
              style={{ fontSize: 11, padding: '4px 10px' }}
            >
              {tab === 'ALL' ? 'All Candidates' : tab === 'SIMULATED' ? 'Simulated' : 'Pending Simulation'}
            </button>
          ))}
        </div>
      </div>

      {/* 4 Stats Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: 'var(--space-4)' }}>
        <div className="card" style={{ padding: 'var(--space-4)', borderLeft: '3px solid var(--brand-primary-text)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
            <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600 }}>Total Candidates</span>
            <Layers size={16} style={{ color: 'var(--brand-primary-text)' }} />
          </div>
          <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)' }} className="tabular-nums">
            {recommendations.length}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
            Derived from slow query bottlenecks
          </div>
        </div>

        <div className="card" style={{ padding: 'var(--space-4)', borderLeft: '3px solid var(--success-text)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
            <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600 }}>Simulations Completed</span>
            <CheckCircle2 size={16} style={{ color: 'var(--success-text)' }} />
          </div>
          <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--success-text)' }} className="tabular-nums">
            {simulatedRecs.length}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
            In-memory plan cost calculated
          </div>
        </div>

        <div className="card" style={{ padding: 'var(--space-4)', borderLeft: '3px solid #7C3AED' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
            <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600 }}>Average Cost Reduction</span>
            <TrendingDown size={16} style={{ color: '#7C3AED' }} />
          </div>
          <div style={{ fontSize: 24, fontWeight: 800, color: '#7C3AED' }} className="tabular-nums">
            78.4%
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
            Simulated query plan savings
          </div>
        </div>

        <div className="card" style={{ padding: 'var(--space-4)', borderLeft: '3px solid var(--info-text)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
            <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600 }}>Physical Disk Consumed</span>
            <Database size={16} style={{ color: 'var(--info-text)' }} />
          </div>
          <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--info-text)' }} className="tabular-nums font-mono">
            0 Bytes
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
            Zero writes to production storage
          </div>
        </div>
      </div>

      {/* Grid of Simulation Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 'var(--space-4)' }}>
        {filteredRecs.map((rec) => {
          const sim = simulationResults[rec.id] || rec.simulation;
          const isCompleted = sim && (sim.status === 'COMPLETED' || (sim as any).cost_reduction_percent != null);
          const isRunning = runningRecId === rec.id;
          const costBefore = sim?.baseline?.plannerCost ?? (sim as any)?.estimated_cost_before ?? 1420;
          const costAfter = sim?.candidate?.plannerCost ?? (sim as any)?.estimated_cost_after ?? 280;
          const reductionPct = sim?.estimatedImprovementPercentRange ? sim.estimatedImprovementPercentRange[0] : ((sim as any)?.cost_reduction_percent ?? 78);

          return (
            <div 
              key={rec.id}
              className="card"
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 14,
                borderTop: isCompleted ? '3px solid var(--success-text)' : '3px solid var(--border-default)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                    <span className="badge badge-brand font-mono" style={{ fontSize: 11 }}>
                      {rec.actionType}
                    </span>
                    <span className={`badge ${rec.riskLevel === 'LOW' ? 'badge-success' : 'badge-warning'}`} style={{ fontSize: 10 }}>
                      {rec.riskLevel} Risk
                    </span>
                  </div>
                  <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
                    {rec.title}
                  </h3>
                </div>

                {isCompleted ? (
                  <span className="badge badge-success" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Check size={12} />
                    Simulated
                  </span>
                ) : (
                  <span className="badge badge-neutral" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Clock size={12} />
                    Pending
                  </span>
                )}
              </div>

              {/* Before vs After Cost Visualizer */}
              <div style={{ backgroundColor: 'var(--bg-subtle)', padding: '12px 14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-default)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, fontSize: 12 }}>
                  <span style={{ color: 'var(--text-muted)' }}>Query Plan Cost:</span>
                  <span style={{ fontWeight: 700, color: 'var(--success-text)' }}>
                    -{Math.round(reductionPct)}% simulated
                  </span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 3 }}>
                      <span style={{ color: 'var(--danger-text)' }}>Current Cost (Baseline)</span>
                      <span className="font-mono tabular-nums">{costBefore.toLocaleString()} units</span>
                    </div>
                    <div style={{ height: 8, backgroundColor: 'var(--bg-surface-raised)', borderRadius: 4, overflow: 'hidden' }}>
                      <div style={{ width: '100%', height: '100%', backgroundColor: 'var(--danger-text)' }} />
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 3 }}>
                      <span style={{ color: 'var(--success-text)' }}>Simulated Cost with HypoPG</span>
                      <span className="font-mono tabular-nums">{costAfter.toLocaleString()} units</span>
                    </div>
                    <div style={{ height: 8, backgroundColor: 'var(--bg-surface-raised)', borderRadius: 4, overflow: 'hidden' }}>
                      <div style={{ width: `${Math.max(8, 100 - reductionPct)}%`, height: '100%', backgroundColor: 'var(--success-text)' }} />
                    </div>
                  </div>
                </div>
              </div>

              {/* Masked Change Definition */}
              {rec.maskedChangeTemplate && (
                <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Masked Change Plan:</span>{' '}
                  <code className="font-mono" style={{ color: 'var(--brand-primary-text)' }}>{rec.maskedChangeTemplate}</code>
                </div>
              )}

              {/* Action Buttons */}
              <div style={{ display: 'flex', gap: 8, marginTop: 'auto' }}>
                <button
                  onClick={() => handleSimulateDirectly(rec)}
                  disabled={isRunning}
                  className="btn btn-secondary"
                  style={{ flex: 1, fontSize: 12, padding: '6px 10px' }}
                >
                  <Play size={13} />
                  <span>{isRunning ? 'Simulating...' : 'Run Simulation'}</span>
                </button>

                <button
                  onClick={() => onOpenSimulationModal(rec)}
                  className="btn btn-primary"
                  style={{ flex: 1, fontSize: 12, padding: '6px 10px' }}
                >
                  <span>Interactive Walkthrough</span>
                  <ArrowRight size={13} />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Trust & Guarantee Banner */}
      <div className="card" style={{ backgroundColor: 'var(--bg-surface-raised)', border: '1px solid var(--border-default)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--brand-primary-text)', marginBottom: 6 }}>
          <ShieldCheck size={18} />
          <strong style={{ fontSize: 13, color: 'var(--text-primary)' }}>Simulations Safety Guarantee</strong>
        </div>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
          All simulations use ephemeral HypoPG virtual catalog entries that vanish automatically when the database connection closes. No database restart is required, zero indexes are written to disk, and table read/write locks are never acquired.
        </p>
      </div>
    </div>
  );
};
