import React, { useState } from 'react';
import { 
  ArrowLeft, 
  ShieldCheck, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  AlertTriangle, 
  Copy, 
  Check, 
  Layers, 
  TrendingDown, 
  Database,
  ArrowRight,
  Info,
  Sliders,
  FileCode,
  Play
} from 'lucide-react';
import type { Recommendation, QueryEvent, User } from '../types/queryguard';

interface RecommendationDetailViewProps {
  recommendation: Recommendation;
  query: QueryEvent;
  currentUser: User;
  onBack: () => void;
  onOpenApprovalDrawer: (rec: Recommendation, decision: 'APPROVED' | 'REJECTED') => void;
  onOpenSimulationModal: (rec: Recommendation) => void;
}

export const RecommendationDetailView: React.FC<RecommendationDetailViewProps> = ({
  recommendation,
  query,
  currentUser,
  onBack,
  onOpenApprovalDrawer,
  onOpenSimulationModal
}) => {
  const [copiedDdl, setCopiedDdl] = useState(false);
  const [activePlanTab, setActivePlanTab] = useState<'candidate' | 'baseline'>('candidate');

  const sim = recommendation.simulation;
  const rank = {
    score: recommendation.rankingScore?.score != null 
      ? (recommendation.rankingScore.score > 1 ? recommendation.rankingScore.score / 100 : recommendation.rankingScore.score) 
      : 0.85,
    readBenefit: recommendation.rankingScore?.readBenefit != null 
      ? (recommendation.rankingScore.readBenefit > 1 ? recommendation.rankingScore.readBenefit / 100 : recommendation.rankingScore.readBenefit) 
      : 0.90,
    writePenalty: recommendation.rankingScore?.writePenalty != null 
      ? (recommendation.rankingScore.writePenalty > 1 ? recommendation.rankingScore.writePenalty / 100 : recommendation.rankingScore.writePenalty) 
      : 0.12,
    storagePenalty: recommendation.rankingScore?.storagePenalty != null 
      ? (recommendation.rankingScore.storagePenalty > 1 ? recommendation.rankingScore.storagePenalty / 100 : recommendation.rankingScore.storagePenalty) 
      : 0.15,
    operationalRisk: recommendation.rankingScore?.operationalRisk != null 
      ? (recommendation.rankingScore.operationalRisk > 1 ? recommendation.rankingScore.operationalRisk / 100 : recommendation.rankingScore.operationalRisk) 
      : 0.05,
  };

  const alternatives = (recommendation.evidence?.alternativesConsidered && recommendation.evidence.alternativesConsidered.length > 0)
    ? recommendation.evidence.alternativesConsidered
    : [
        { rank: 2, action: 'Single-Column Index on Predicate', reasonLowerRank: 'Fails to satisfy composite range/equality filter, requiring secondary heap fetches.' },
        { rank: 3, action: 'Table Partitioning Advisory', reasonLowerRank: 'Introduces operational maintenance overhead and requires schema migration window.' }
      ];

  const handleCopyDdl = () => {
    navigator.clipboard.writeText(recommendation.maskedChangeTemplate || 'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_queryguard_rec ON tbl (col);');
    setCopiedDdl(true);
    setTimeout(() => setCopiedDdl(false), 2000);
  };

  const isApproved = recommendation.status === 'APPROVED';
  const isRejected = recommendation.status === 'REJECTED';
  const isSimulationComplete = sim && sim.status === 'COMPLETED';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
      {/* Breadcrumb & Navigation */}
      <div>
        <button 
          onClick={onBack}
          className="btn btn-ghost" 
          style={{ padding: '4px 0', fontSize: 12, marginBottom: 8, color: 'var(--text-muted)' }}
        >
          <ArrowLeft size={14} />
          <span>Back to Query ({query.queryFingerprint})</span>
        </button>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <h1 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
                {recommendation.title}
              </h1>
              <span className="badge badge-brand font-mono">{recommendation.actionType}</span>
              <span className={`badge ${
                isApproved ? 'badge-success' : isRejected ? 'badge-danger' : 'badge-warning'
              }`}>
                {recommendation.status}
              </span>
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
              Target Query: <strong style={{ color: 'var(--text-secondary)' }}>{query.title}</strong> • Risk Level: <strong style={{ color: recommendation.riskLevel === 'LOW' ? 'var(--success-text)' : 'var(--warning-text)' }}>{recommendation.riskLevel}</strong>
            </p>
          </div>

          {/* Action Buttons: Approve / Reject / Simulate */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {!isSimulationComplete && (
              <button
                onClick={() => onOpenSimulationModal(recommendation)}
                className="btn btn-primary"
                style={{ fontSize: 12, padding: '8px 14px' }}
              >
                <Play size={14} />
                <span>Run HypoPG Simulation</span>
              </button>
            )}

            {isApproved ? (
              <span className="badge badge-success" style={{ padding: '8px 14px', fontSize: 13 }}>
                <CheckCircle2 size={16} />
                Approved by {recommendation.resolvedBy || 'DBA'} (Script Ready)
              </span>
            ) : isRejected ? (
              <span className="badge badge-danger" style={{ padding: '8px 14px', fontSize: 13 }}>
                <XCircle size={16} />
                Rejected: {recommendation.rejectionReason}
              </span>
            ) : (
              <>
                <button
                  onClick={() => onOpenApprovalDrawer(recommendation, 'REJECTED')}
                  className="btn btn-danger"
                  style={{ fontSize: 12, padding: '8px 14px' }}
                >
                  <XCircle size={14} />
                  <span>Reject</span>
                </button>
                <button
                  onClick={() => onOpenApprovalDrawer(recommendation, 'APPROVED')}
                  disabled={!isSimulationComplete}
                  className="btn btn-primary"
                  style={{ fontSize: 12, padding: '8px 16px' }}
                  title={!isSimulationComplete ? "Simulation required before approval" : "Approve recommendation"}
                >
                  <CheckCircle2 size={14} />
                  <span>Approve Recommendation</span>
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Decision Summary Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--space-4)' }}>
        <div className="card" style={{ padding: '14px 16px' }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>Estimated Planner Gain</span>
          <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--brand-primary-text)' }} className="tabular-nums font-mono">
            {sim ? `${sim.estimatedImprovementPercentRange[0]}% – ${sim.estimatedImprovementPercentRange[1]}%` : '70% – 85%'}
          </div>
          <span style={{ fontSize: 11, color: 'var(--warning-text)' }}>* Simulated estimate</span>
        </div>

        <div className="card" style={{ padding: '14px 16px' }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>Estimated Write Overhead</span>
          <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)' }} className="tabular-nums font-mono">
            {sim ? `+${sim.estimatedWriteOverheadMsRange[0]}–${sim.estimatedWriteOverheadMsRange[1]} ms` : '+1–2 ms'}
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Per insert/update on table</span>
        </div>

        <div className="card" style={{ padding: '14px 16px' }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>Estimated Storage Impact</span>
          <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)' }} className="tabular-nums font-mono">
            {sim ? `+${sim.estimatedStorageOverheadGbRange[0]}–${sim.estimatedStorageOverheadGbRange[1]} GB` : '+1.8–2.4 GB'}
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>B-tree index disk footprint</span>
        </div>

        <div className="card" style={{ padding: '14px 16px' }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>Ranking Score</span>
          <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)' }} className="tabular-nums font-mono">
            {rank.score.toFixed(2)} / 1.00
          </div>
          <span style={{ fontSize: 11, color: 'var(--success-text)', fontWeight: 600 }}>Rank #1 Candidate</span>
        </div>
      </div>

      {/* Transparent Ranking Formula Score Breakdown */}
      <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Sliders size={16} style={{ color: 'var(--brand-primary-text)' }} />
            <h3 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
              Deterministic Ranking Formula Breakdown
            </h3>
          </div>
          <code className="font-mono" style={{ fontSize: 11, color: 'var(--text-muted)', background: 'var(--bg-subtle)', padding: '2px 8px', borderRadius: 'var(--radius-sm)' }}>
            Score = 0.45 · ReadBenefit - 0.20 · WritePenalty - 0.15 · StoragePenalty - 0.20 · OperationalRisk
          </code>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 4 }}>
              <span style={{ color: 'var(--text-secondary)' }}>Read Benefit (+45%)</span>
              <strong className="font-mono" style={{ color: 'var(--brand-primary-text)' }}>+{(rank.readBenefit * 100).toFixed(0)}%</strong>
            </div>
            <div style={{ height: 6, backgroundColor: 'var(--bg-subtle)', borderRadius: 3, overflow: 'hidden' }}>
              <div style={{ width: `${rank.readBenefit * 100}%`, height: '100%', backgroundColor: 'var(--brand-primary-text)' }} />
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 4 }}>
              <span style={{ color: 'var(--text-secondary)' }}>Write Penalty (-20%)</span>
              <strong className="font-mono" style={{ color: 'var(--warning-text)' }}>-{(rank.writePenalty * 100).toFixed(0)}%</strong>
            </div>
            <div style={{ height: 6, backgroundColor: 'var(--bg-subtle)', borderRadius: 3, overflow: 'hidden' }}>
              <div style={{ width: `${rank.writePenalty * 100}%`, height: '100%', backgroundColor: 'var(--warning-text)' }} />
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 4 }}>
              <span style={{ color: 'var(--text-secondary)' }}>Storage Penalty (-15%)</span>
              <strong className="font-mono" style={{ color: 'var(--warning-text)' }}>-{(rank.storagePenalty * 100).toFixed(0)}%</strong>
            </div>
            <div style={{ height: 6, backgroundColor: 'var(--bg-subtle)', borderRadius: 3, overflow: 'hidden' }}>
              <div style={{ width: `${rank.storagePenalty * 100}%`, height: '100%', backgroundColor: 'var(--warning-text)' }} />
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 4 }}>
              <span style={{ color: 'var(--text-secondary)' }}>Operational Risk (-20%)</span>
              <strong className="font-mono" style={{ color: 'var(--success-text)' }}>-{(rank.operationalRisk * 100).toFixed(0)}%</strong>
            </div>
            <div style={{ height: 6, backgroundColor: 'var(--bg-subtle)', borderRadius: 3, overflow: 'hidden' }}>
              <div style={{ width: `${rank.operationalRisk * 100}%`, height: '100%', backgroundColor: 'var(--success-text)' }} />
            </div>
          </div>
        </div>
      </div>

      {/* Main Comparison Section: Left (Plan Diff) + Right (Evidence & Alternatives) */}
      <div style={{ display: 'grid', gridTemplateColumns: '7fr 5fr', gap: 'var(--space-6)' }}>
        {/* Left: Before vs. Candidate Plan Comparison */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
                HypoPG What-If Plan Comparison
              </h3>
              <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                Virtual index simulation evaluated within read-only sandbox session
              </p>
            </div>

            <div style={{ display: 'flex', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-default)', padding: 2 }}>
              <button
                onClick={() => setActivePlanTab('candidate')}
                style={{
                  padding: '3px 10px',
                  fontSize: 11,
                  borderRadius: 'var(--radius-sm)',
                  background: activePlanTab === 'candidate' ? 'var(--brand-primary-muted)' : 'transparent',
                  color: activePlanTab === 'candidate' ? 'var(--brand-primary-text)' : 'var(--text-muted)',
                  fontWeight: activePlanTab === 'candidate' ? 700 : 500
                }}
              >
                Candidate Plan (HypoPG)
              </button>
              <button
                onClick={() => setActivePlanTab('baseline')}
                style={{
                  padding: '3px 10px',
                  fontSize: 11,
                  borderRadius: 'var(--radius-sm)',
                  background: activePlanTab === 'baseline' ? 'var(--bg-surface-raised)' : 'transparent',
                  color: activePlanTab === 'baseline' ? 'var(--text-primary)' : 'var(--text-muted)',
                  fontWeight: activePlanTab === 'baseline' ? 700 : 500
                }}
              >
                Baseline Plan
              </button>
            </div>
          </div>

          {/* Plan Comparison Metric Delta Banner */}
          {sim && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              backgroundColor: 'var(--bg-surface-raised)',
              border: '1px solid var(--border-strong)',
              borderRadius: 'var(--radius-sm)',
              padding: '12px 16px'
            }}>
              <div>
                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Baseline Planner Cost</span>
                <div className="font-mono tabular-nums" style={{ fontSize: 16, color: 'var(--danger-text)', textDecoration: 'line-through' }}>
                  {sim.baseline.plannerCost.toLocaleString()}
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <span className="badge badge-success" style={{ fontSize: 12 }}>
                  -83.3% Cost Reduction
                </span>
                <ArrowRight size={16} style={{ color: 'var(--brand-primary-text)', marginTop: 2 }} />
              </div>

              <div>
                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Simulated Candidate Cost</span>
                <div className="font-mono tabular-nums" style={{ fontSize: 18, fontWeight: 700, color: 'var(--brand-primary-text)' }}>
                  {sim.candidate.plannerCost.toLocaleString()}
                </div>
              </div>
            </div>
          )}

          {/* Plan Text Diff Representation */}
          <div className="code-block" style={{ fontSize: 12 }}>
            {activePlanTab === 'candidate' ? (
              <div>
                <span style={{ color: 'var(--success-text)' }}>+ Aggregate  (cost=30510.8..30515.2 rows=100)</span>{'\n'}
                <span style={{ color: 'var(--success-text)' }}>+   -&gt;  Hash Join  (cost=12.4..30490.1 rows=2400)</span>{'\n'}
                <span style={{ color: 'var(--success-text)' }}>+         Hash Cond: (TBL_SALES.COL_STORE_ID = TBL_STORES.COL_ID)</span>{'\n'}
                <span style={{ color: 'var(--success-text)' }}>+         -&gt;  Index Scan using <span style={{ textDecoration: 'underline' }}>&lt;hypo_idx_sales_region_date&gt;</span> on TBL_SALES  (cost=0.42..29800.0 rows=2400)</span>{'\n'}
                <span style={{ color: 'var(--text-muted)' }}>                 Index Cond: ((COL_REGION_ID = 4) AND (COL_TX_DATE &gt;= :TIMESTAMP))</span>{'\n'}
                <span style={{ color: 'var(--text-muted)' }}>                 Filter: (COL_STATUS = :TEXT)</span>
              </div>
            ) : (
              <div>
                <span style={{ color: 'var(--danger-text)' }}>- Aggregate  (cost=182341.2..182345.0 rows=100)</span>{'\n'}
                <span style={{ color: 'var(--danger-text)' }}>-   -&gt;  Nested Loop  (cost=8.4..178920.0 rows=124000)</span>{'\n'}
                <span style={{ color: 'var(--danger-text)' }}>-         -&gt;  Index Scan using IDX_STORES_PKEY on TBL_STORES  (cost=0.28..8.4 rows=1)</span>{'\n'}
                <span style={{ color: 'var(--danger-text)' }}>-         -&gt;  Seq Scan on TBL_SALES  (cost=0.0..178900.5 rows=12400000)</span>{'\n'}
                <span style={{ color: 'var(--danger-text)' }}>-                 Filter: ((COL_STATUS = :TEXT) AND (COL_TX_DATE &gt;= :TIMESTAMP) AND (COL_REGION_ID = 4))</span>
              </div>
            )}
          </div>
        </div>

        {/* Right: Why This Ranked Highest & Alternatives */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
              Decision Rationale & Alternatives
            </h3>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              Why this optimization was prioritized over alternative architectural changes
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ backgroundColor: 'var(--bg-subtle)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-sm)', padding: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--brand-primary-text)', fontWeight: 700, fontSize: 12, marginBottom: 4 }}>
                <CheckCircle2 size={14} />
                <span>Primary Recommendation (Rank #1)</span>
              </div>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.45 }}>
                A composite B-tree index on equality predicate (<code>COL_REGION_ID</code>) followed by range predicate (<code>COL_TX_DATE</code>) converts an expensive table sequential scan into a targeted index range scan.
              </p>
            </div>

            {alternatives.map((alt, idx) => (
              <div key={idx} style={{ backgroundColor: 'var(--bg-subtle)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-sm)', padding: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Alternative #{alt.rank}: {alt.action}
                  </span>
                  <span className="badge badge-neutral" style={{ fontSize: 10 }}>Lower Rank</span>
                </div>
                <p style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.45 }}>
                  <strong>Reason lower rank:</strong> {alt.reasonLowerRank}
                </p>
              </div>
            ))}
          </div>

          {/* Rollback Guidance */}
          <div style={{ backgroundColor: 'var(--bg-surface-raised)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-sm)', padding: 12 }}>
            <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--warning-text)', display: 'block', marginBottom: 4 }}>
              Rollback & Operational Guidance
            </span>
            <p style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.45 }}>
              If write degradation exceeds threshold after production application, rollback safely using:
            </p>
            <pre className="font-mono" style={{ fontSize: 11, background: 'var(--bg-subtle)', padding: '6px 8px', borderRadius: 4, marginTop: 6, color: 'var(--text-primary)' }}>
              DROP INDEX CONCURRENTLY IF EXISTS idx_sales_region_date;
            </pre>
          </div>
        </div>
      </div>

      {/* Masked Change Script Template Section */}
      <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <FileCode size={16} style={{ color: 'var(--brand-primary-text)' }} />
            <h3 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
              Proposed DDL Change Template (CONCURRENTLY)
            </h3>
            <span className="badge badge-success" style={{ fontSize: 10 }}>
              Zero Table Lock Policy
            </span>
          </div>

          <button 
            onClick={handleCopyDdl}
            className="btn btn-secondary" 
            style={{ fontSize: 11, padding: '4px 10px' }}
          >
            {copiedDdl ? <Check size={12} style={{ color: 'var(--success-text)' }} /> : <Copy size={12} />}
            <span>{copiedDdl ? 'Copied' : 'Copy Script Template'}</span>
          </button>
        </div>

        <pre className="code-block">
          {recommendation.maskedChangeTemplate || recommendation.actionType || 'CREATE INDEX CONCURRENTLY idx_tbl_opt ON tbl (col);'}
        </pre>
      </div>
    </div>
  );
};
