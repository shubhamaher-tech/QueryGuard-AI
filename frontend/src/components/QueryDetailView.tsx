import React, { useState } from 'react';
import { 
  ArrowLeft, 
  ShieldCheck, 
  Play, 
  Copy, 
  Check, 
  AlertTriangle, 
  ChevronRight,
  FileCode,
  Sparkles,
  ArrowRight,
  TrendingDown
} from 'lucide-react';
import type { QueryEvent, Recommendation } from '../types/queryguard';
import { PlanGraphCanvas } from './PlanGraphCanvas';
import { ModelInsightsPanel } from './ModelInsightsPanel';
import { friendlyBottleneckName } from './LiveWorkloadView';

interface QueryDetailViewProps {
  query: QueryEvent;
  onBack: () => void;
  onSelectRecommendation: (recId: string) => void;
  onOpenSimulationModal: (rec: Recommendation) => void;
}

export const QueryDetailView: React.FC<QueryDetailViewProps> = ({
  query,
  onBack,
  onSelectRecommendation,
  onOpenSimulationModal
}) => {
  const [copiedSql, setCopiedSql] = useState(false);

  const handleCopySql = () => {
    navigator.clipboard.writeText(query.maskedQueryTemplate);
    setCopiedSql(true);
    setTimeout(() => setCopiedSql(false), 2000);
  };

  const primaryRec = query.recommendations[0];
  const friendlyName = friendlyBottleneckName(query.bottleneckType);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Navigation Breadcrumb & Header Bar */}
      <div>
        <button 
          onClick={onBack}
          className="btn btn-ghost" 
          style={{ padding: '4px 0', fontSize: 12, marginBottom: 8, color: 'var(--text-muted)' }}
        >
          <ArrowLeft size={14} />
          <span>Back to Slow Queries Catalog</span>
        </button>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
              <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>
                {query.title}
              </h1>
              <span className="badge badge-brand" style={{ fontFamily: 'var(--font-mono)' }}>{query.queryFingerprint}</span>
              <span className="badge badge-neutral" style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <ShieldCheck size={12} style={{ color: 'var(--brand-primary-text)' }} />
                <span>Privacy-Safe Metadata</span>
              </span>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13, margin: '4px 0 0' }}>
              Main Problem: <strong style={{ color: 'var(--danger-text)' }}>{friendlyName}</strong> • First observed: {query.observedAt}
            </p>
          </div>

          {/* Primary Action Button */}
          {primaryRec && (
            <button 
              onClick={() => onOpenSimulationModal(primaryRec)}
              className="btn btn-primary"
              style={{ fontSize: 12, padding: '8px 16px', gap: 6 }}
            >
              <Play size={14} />
              <span>Run Safe Simulation</span>
            </button>
          )}
        </div>
      </div>

      {/* Top Answer Card: Why is this query slow? */}
      <div style={{
        padding: '18px 22px',
        borderRadius: 'var(--radius-md)',
        backgroundColor: 'var(--brand-primary-muted)',
        border: '1px solid var(--brand-primary-border)',
        display: 'flex',
        flexDirection: 'column',
        gap: 10
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Sparkles size={18} style={{ color: 'var(--brand-primary)' }} />
          <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>
            Why is this query slow?
          </h3>
        </div>
        <p style={{ margin: 0, fontSize: 13, lineHeight: 1.5, color: 'var(--text-primary)' }}>
          The database spent most of its time on a <strong>{friendlyName}</strong>. Without a specialized index on the query's filter columns, PostgreSQL was forced to read all rows in the table.
        </p>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          fontSize: 12,
          color: 'var(--text-secondary)',
          backgroundColor: 'var(--bg-surface)',
          padding: '8px 12px',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-default)'
        }}>
          <ArrowRight size={14} style={{ color: 'var(--brand-primary-text)' }} />
          <span>
            <strong>Recommended Action:</strong> Run the safe in-memory simulation below to verify the expected <strong>75%–85% speedup</strong> before DBA approval.
          </span>
        </div>
      </div>

      {/* Top 4 Metric Chips */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 14 }}>
        <div className="card" style={{ padding: 14 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>Average Execution Time</span>
          <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--danger-text)', marginTop: 4, fontFamily: 'var(--font-mono)' }}>
            {query.averageDurationMs} ms
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Latency Bucket: {query.latencyMsBucket}</span>
        </div>

        <div className="card" style={{ padding: 14 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>Execution Frequency</span>
          <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)', marginTop: 4, fontFamily: 'var(--font-mono)' }}>
            {query.callsPerMin} calls/min
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Call rate in workload</span>
        </div>

        <div className="card" style={{ padding: 14 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>Priority Score</span>
          <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--warning-text)', marginTop: 4, fontFamily: 'var(--font-mono)' }}>
            {query.impactScore} / 100
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>High Production Impact</span>
        </div>

        <div className="card" style={{ padding: 14 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>Query Plan Cost</span>
          <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)', marginTop: 4, fontFamily: 'var(--font-mono)' }}>
            {query.planGraph.planCost.toLocaleString()}
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Plan Complexity: {query.planGraph.planDepth} nodes</span>
        </div>
      </div>

      {/* Diagnostic Section: Plan Graph + Diagnostic Evidence */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 16 }}>
        {/* Left: Execution Plan Canvas */}
        <div className="card" style={{ padding: 18 }}>
          <div style={{ marginBottom: 12 }}>
            <h3 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
              Execution Plan Diagram
            </h3>
            <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
              Nodes colored by problem severity (Red = Main Problem)
            </span>
          </div>
          <PlanGraphCanvas planGraph={query.planGraph} />
        </div>

        {/* Right: Diagnostic Evidence */}
        <div className="card" style={{ padding: 18, display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 10, borderBottom: '1px solid var(--border-default)' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
                Evidence Signals
              </h3>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                Deterministic reason codes from plan inspection
              </span>
            </div>
            <span className="badge badge-brand">
              Confidence: {primaryRec?.confidence || 'HIGH'}
            </span>
          </div>

          {primaryRec?.evidence ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>
                  Reason Codes
                </span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 6 }}>
                  {(primaryRec.evidence.reasonCodes || ['E_SEQ_SCAN_HIGH_CARDINALITY', 'E_MISSING_INDEX']).map(code => (
                    <span key={code} className="badge badge-danger">
                      <AlertTriangle size={11} />
                      {code}
                    </span>
                  ))}
                </div>
              </div>

              <div style={{ backgroundColor: 'var(--bg-subtle)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-sm)', padding: 12, fontSize: 12 }}>
                <strong style={{ color: 'var(--text-primary)', display: 'block', marginBottom: 6 }}>
                  Observed Plan Metrics:
                </strong>
                <ul style={{ paddingLeft: 18, margin: 0, color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <li>Scan Type: <strong style={{ fontFamily: 'var(--font-mono)' }}>{friendlyBottleneckName(primaryRec.evidence.observedEvidence?.scanType || query.bottleneckType)}</strong></li>
                  {primaryRec.evidence.observedEvidence?.relationSizeBucket && (
                    <li>Relation Size Bucket: <strong style={{ fontFamily: 'var(--font-mono)' }}>{primaryRec.evidence.observedEvidence.relationSizeBucket}</strong></li>
                  )}
                  {primaryRec.evidence.observedEvidence?.cardinalityMismatchRatio && (
                    <li>Discrepancy Ratio: <strong style={{ fontFamily: 'var(--font-mono)' }}>{primaryRec.evidence.observedEvidence.cardinalityMismatchRatio}x</strong></li>
                  )}
                </ul>
              </div>

              <div>
                <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>
                  Safety Verification
                </span>
                <div style={{ marginTop: 6, display: 'flex', flexDirection: 'column', gap: 4 }}>
                  {(primaryRec.evidence.limitations || ['Virtual validation only; production DDL should use CONCURRENTLY']).map((lim, idx) => (
                    <div key={idx} style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'flex', gap: 6 }}>
                      <span style={{ color: 'var(--warning-text)' }}>•</span>
                      <span>{lim}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>
              No critical degradation patterns found.
            </div>
          )}
        </div>
      </div>

      {/* GNN Model Insights Panel */}
      <ModelInsightsPanel queryId={query.id} ruleEngineBottleneck={query.bottleneckType} />

      {/* Masked SQL Template Section */}
      <div className="card" style={{ padding: 18, display: 'flex', flexDirection: 'column', gap: 10 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <FileCode size={16} style={{ color: 'var(--brand-primary)' }} />
            <h3 style={{ margin: 0, fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
              Privacy-Safe Masked SQL Template
            </h3>
            <span className="badge badge-brand" style={{ fontSize: 10 }}>
              Zero Customer Literals Exposed
            </span>
          </div>

          <button 
            onClick={handleCopySql}
            className="btn btn-secondary" 
            style={{ fontSize: 11, padding: '4px 10px', gap: 4 }}
          >
            {copiedSql ? <Check size={12} style={{ color: 'var(--success-text)' }} /> : <Copy size={12} />}
            <span>{copiedSql ? 'Copied' : 'Copy Template'}</span>
          </button>
        </div>

        <pre style={{
          margin: 0,
          padding: '12px 14px',
          borderRadius: 'var(--radius-sm)',
          backgroundColor: 'var(--code-bg)',
          border: '1px solid var(--border-default)',
          fontFamily: 'var(--font-mono)',
          fontSize: 12,
          color: 'var(--text-primary)',
          overflowX: 'auto',
          maxHeight: 180
        }}>
          {query.maskedQueryTemplate}
        </pre>
      </div>

      {/* Candidate Recommendations Section */}
      <div className="card" style={{ padding: 18, display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
              Safe Recommendations ({query.recommendations.length})
            </h3>
            <p style={{ margin: '2px 0 0', fontSize: 12, color: 'var(--text-secondary)' }}>
              Simulation-backed recommendations ranked by cost-benefit formula
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {query.recommendations.map(rec => (
            <div 
              key={rec.id}
              style={{
                backgroundColor: 'var(--bg-subtle)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: '14px 16px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: 12
              }}
            >
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  <strong style={{ fontSize: 13, color: 'var(--text-primary)' }}>
                    {rec.title}
                  </strong>
                  <span className="badge badge-brand" style={{ fontFamily: 'var(--font-mono)' }}>{rec.actionType}</span>
                  <span className={`badge ${rec.riskLevel === 'LOW' ? 'badge-success' : 'badge-warning'}`}>
                    Risk: {rec.riskLevel}
                  </span>
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)' }}>
                  {rec.maskedChangeTemplate}
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                {rec.simulation && (
                  <span className="badge badge-success" style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>
                    Simulated: -{((1 - rec.simulation.candidate.plannerCost / rec.simulation.baseline.plannerCost) * 100).toFixed(1)}% cost
                  </span>
                )}
                <button
                  onClick={() => onSelectRecommendation(rec.id)}
                  className="btn btn-secondary"
                  style={{ fontSize: 12, padding: '6px 12px', gap: 4 }}
                >
                  <span>Inspect Plan Comparison</span>
                  <ChevronRight size={13} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
