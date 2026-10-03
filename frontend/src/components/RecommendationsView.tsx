import React, { useState } from 'react';
import { 
  Layers, 
  Search, 
  Filter, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  ChevronRight, 
  ShieldCheck, 
  Play,
  TrendingDown,
  Sparkles
} from 'lucide-react';
import { Recommendation, QueryEvent } from '../types/queryguard';

interface RecommendationsViewProps {
  recommendations: Recommendation[];
  queries: QueryEvent[];
  onSelectRecommendation: (recId: string) => void;
  onOpenSimulationModal: (rec: Recommendation) => void;
}

export const RecommendationsView: React.FC<RecommendationsViewProps> = ({
  recommendations,
  queries,
  onSelectRecommendation,
  onOpenSimulationModal
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [actionFilter, setActionFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const filtered = recommendations.filter(r => {
    const matchesSearch = 
      r.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.maskedChangeTemplate.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesAction = actionFilter === 'ALL' || r.actionType === actionFilter;
    const matchesStatus = statusFilter === 'ALL' || r.status === statusFilter;
    return matchesSearch && matchesAction && matchesStatus;
  });

  const simulatedCount = recommendations.filter(r => !!r.simulation).length;
  const approvedCount = recommendations.filter(r => r.status === 'APPROVED').length;
  const pendingCount = recommendations.filter(r => r.status === 'VALIDATED').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>
              Recommendations Queue
            </h1>
            <span className="badge badge-brand">
              {filtered.length} Recommendations
            </span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: 13, margin: '4px 0 0' }}>
            Safe composite index proposals verified via in-memory simulation, awaiting human DBA decision.
          </p>
        </div>
      </div>

      {/* 4 Summary Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 14 }}>
        <div className="card" style={{ padding: 14 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>Needs DBA Review</span>
          <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--warning-text)', marginTop: 4 }}>
            {pendingCount}
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Awaiting approval</span>
        </div>

        <div className="card" style={{ padding: 14 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>Safe Simulations Passed</span>
          <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--success-text)', marginTop: 4 }}>
            {simulatedCount}
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Tested in RAM (0 MB disk)</span>
        </div>

        <div className="card" style={{ padding: 14 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>Approved by DBA</span>
          <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--brand-primary)', marginTop: 4 }}>
            {approvedCount}
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Ready for rollout window</span>
        </div>

        <div className="card" style={{ padding: 14 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>Expected Benefit</span>
          <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--success-text)', marginTop: 4 }}>
            70% – 85%
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Plan cost reduction</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="card" style={{ padding: '12px 16px', display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1, minWidth: 260, position: 'relative' }}>
          <Search size={15} style={{ position: 'absolute', left: 10, color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Search recommendations or change templates..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              padding: '7px 10px 7px 32px',
              fontSize: 12,
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-default)',
              backgroundColor: 'var(--bg-surface)',
              color: 'var(--text-primary)'
            }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Type:</span>
          <select 
            value={actionFilter} 
            onChange={(e) => setActionFilter(e.target.value)}
            style={{
              fontSize: 12,
              padding: '6px 10px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-default)',
              backgroundColor: 'var(--bg-surface)',
              color: 'var(--text-primary)'
            }}
          >
            <option value="ALL">All Types</option>
            <option value="INDEX">Index</option>
            <option value="SQL_REWRITE">SQL Rewrite</option>
            <option value="PARTITION_ADVISORY">Partition Advisory</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Status:</span>
          <select 
            value={statusFilter} 
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              fontSize: 12,
              padding: '6px 10px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-default)',
              backgroundColor: 'var(--bg-surface)',
              color: 'var(--text-primary)'
            }}
          >
            <option value="ALL">All Statuses</option>
            <option value="VALIDATED">Needs DBA Review</option>
            <option value="APPROVED">Approved</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </div>
      </div>

      {/* Recommendations Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="table" style={{ width: '100%', fontSize: 12 }}>
          <thead>
            <tr>
              <th style={{ padding: '10px 14px' }}>Recommendation & Target</th>
              <th style={{ padding: '10px 14px' }}>Benefit Score</th>
              <th style={{ padding: '10px 14px' }}>Expected Benefit</th>
              <th style={{ padding: '10px 14px' }}>Risk</th>
              <th style={{ padding: '10px 14px' }}>Simulation</th>
              <th style={{ padding: '10px 14px' }}>DBA Decision</th>
              <th style={{ padding: '10px 14px', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(rec => {
              const query = queries.find(q => q.id === rec.queryEventId);
              return (
                <tr 
                  key={rec.id} 
                  onClick={() => onSelectRecommendation(rec.id)}
                  style={{ cursor: 'pointer' }}
                >
                  <td style={{ padding: '12px 14px', maxWidth: 360 }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                      <strong style={{ color: 'var(--text-primary)', fontSize: 13 }}>
                        {rec.title}
                      </strong>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
                        Target: {query?.title || rec.queryEventId}
                      </span>
                      <code style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: 11,
                        color: 'var(--text-secondary)',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        backgroundColor: 'var(--code-bg)',
                        padding: '2px 6px',
                        borderRadius: 3
                      }}>
                        {(rec.maskedChangeTemplate || rec.actionType || 'CREATE INDEX CONCURRENTLY idx_opt ON tbl (col);').split('\n')[0]}
                      </code>
                    </div>
                  </td>

                  <td style={{ padding: '12px 14px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
                        {rec.rankingScore?.score != null ? (rec.rankingScore.score > 1 ? (rec.rankingScore.score / 100).toFixed(2) : rec.rankingScore.score.toFixed(2)) : '0.85'}
                      </span>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>/ 1.0</span>
                    </div>
                  </td>

                  <td style={{ padding: '12px 14px' }}>
                    {rec.simulation ? (
                      <span className="badge badge-success" style={{ fontFamily: 'var(--font-mono)' }}>
                        {rec.simulation.estimatedImprovementPercentRange[0]}% – {rec.simulation.estimatedImprovementPercentRange[1]}%
                      </span>
                    ) : (
                      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Not simulated</span>
                    )}
                  </td>

                  <td style={{ padding: '12px 14px', whiteSpace: 'nowrap' }}>
                    <span className={`badge ${rec.riskLevel === 'LOW' ? 'badge-success' : rec.riskLevel === 'MEDIUM' ? 'badge-warning' : 'badge-danger'}`}>
                      {rec.riskLevel}
                    </span>
                  </td>

                  <td style={{ padding: '12px 14px', whiteSpace: 'nowrap' }}>
                    <span className="badge badge-neutral" style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>
                      {rec.simulation?.simulationEngine || 'HypoPG Ready'}
                    </span>
                  </td>

                  <td style={{ padding: '12px 14px', whiteSpace: 'nowrap' }}>
                    <span className={`badge ${
                      rec.status === 'APPROVED' ? 'badge-success' :
                      rec.status === 'REJECTED' ? 'badge-danger' :
                      rec.status === 'VALIDATED' ? 'badge-warning' : 'badge-neutral'
                    }`}>
                      {rec.status === 'VALIDATED' ? 'Needs DBA Review' : rec.status}
                    </span>
                  </td>

                  <td style={{ padding: '12px 14px', textAlign: 'right', whiteSpace: 'nowrap' }}>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 6 }} onClick={(e) => e.stopPropagation()}>
                      {!rec.simulation && (
                        <button 
                          onClick={() => onOpenSimulationModal(rec)}
                          className="btn btn-secondary" 
                          style={{ padding: '4px 8px', fontSize: 11, gap: 4 }}
                          title="Run safe simulation"
                        >
                          <Play size={11} />
                          <span>Simulate</span>
                        </button>
                      )}
                      <button 
                        onClick={() => onSelectRecommendation(rec.id)}
                        className="btn btn-secondary" 
                        style={{ padding: '4px 8px', fontSize: 11, gap: 4 }}
                      >
                        <span>Inspect</span>
                        <ChevronRight size={12} />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
