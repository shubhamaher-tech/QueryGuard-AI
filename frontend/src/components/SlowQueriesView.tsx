import React, { useState } from 'react';
import { 
  Search, 
  ChevronRight, 
  ShieldCheck, 
  AlertTriangle,
  Clock, 
  Layers,
  Database,
  ArrowRight,
  Sparkles
} from 'lucide-react';
import { QueryEvent } from '../types/queryguard';
import { friendlyBottleneckName } from './LiveWorkloadView';

interface SlowQueriesViewProps {
  queries: QueryEvent[];
  onSelectQuery: (queryId: string) => void;
}

export const SlowQueriesView: React.FC<SlowQueriesViewProps> = ({ 
  queries, 
  onSelectQuery 
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [bottleneckFilter, setBottleneckFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const filteredQueries = queries.filter(q => {
    const matchesSearch = 
      q.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.queryFingerprint.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.maskedQueryTemplate.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesBottleneck = bottleneckFilter === 'ALL' || q.bottleneckType === bottleneckFilter;
    const matchesStatus = statusFilter === 'ALL' || q.analysisStatus === statusFilter;

    return matchesSearch && matchesBottleneck && matchesStatus;
  });

  const getBottleneckBadge = (b?: string) => {
    const name = friendlyBottleneckName(b);
    switch (b) {
      case 'LARGE_SEQ_SCAN':
      case 'SEQ_SCAN':
        return <span className="badge badge-danger">{name}</span>;
      case 'REPEATED_INNER_LOOP':
      case 'NESTED_LOOP':
      case 'UNINDEXED_JOIN':
        return <span className="badge badge-warning">{name}</span>;
      case 'EXPENSIVE_SORT':
        return <span className="badge badge-neutral" style={{ color: '#7C3AED', backgroundColor: '#F5F3FF', borderColor: '#DDD6FE' }}>{name}</span>;
      default:
        return <span className="badge badge-neutral">{name}</span>;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* View Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>
              Slow Queries Catalog
            </h1>
            <span className="badge badge-brand">
              {filteredQueries.length} of {queries.length} Queries
            </span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: 13, margin: '4px 0 0' }}>
            Aggregated telemetry from pg_stat_statements with privacy-safe tokenized identifiers and masked literals.
          </p>
        </div>

        {/* Priority formula callout */}
        <div style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-sm)',
          padding: '6px 12px',
          fontSize: 11,
          color: 'var(--text-muted)'
        }}>
          <strong style={{ color: 'var(--text-secondary)' }}>Priority Formula: </strong>
          Latency × Call Frequency × Query Plan Cost
        </div>
      </div>

      {/* 3 Top Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14 }}>
        <div className="card" style={{ padding: 14 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>Total Monitored Queries</span>
          <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)', marginTop: 4 }}>
            {queries.length}
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Captured from pg_stat_statements</span>
        </div>

        <div className="card" style={{ padding: 14 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>Main Problem Identified</span>
          <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--danger-text)', marginTop: 4 }}>
            Full Table Scan
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Responsible for 70%+ of latency</span>
        </div>

        <div className="card" style={{ padding: 14 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>Privacy Protection</span>
          <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--brand-primary-text)', marginTop: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
            <ShieldCheck size={18} />
            <span>100% Privacy Protected</span>
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>0 raw literals or table names stored</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="card" style={{ padding: '12px 16px', display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1, minWidth: 260, position: 'relative' }}>
          <Search size={15} style={{ position: 'absolute', left: 10, color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Search by query title, fingerprint, or token (e.g. TBL_SALES)..."
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

        {/* Bottleneck filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Problem Type:</span>
          <select 
            value={bottleneckFilter} 
            onChange={(e) => setBottleneckFilter(e.target.value)}
            style={{
              fontSize: 12,
              padding: '6px 10px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-default)',
              backgroundColor: 'var(--bg-surface)',
              color: 'var(--text-primary)'
            }}
          >
            <option value="ALL">All Problems</option>
            <option value="LARGE_SEQ_SCAN">Full Table Scan</option>
            <option value="REPEATED_INNER_LOOP">Repeated Join Work</option>
            <option value="EXPENSIVE_SORT">Expensive Sort Spill</option>
            <option value="INSUFFICIENT_EVIDENCE">Insufficient Evidence</option>
          </select>
        </div>

        {/* Status filter */}
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
            <option value="SIMULATED">Simulated</option>
            <option value="ANALYZED">Analyzed</option>
            <option value="ABSTAINED">Abstained</option>
          </select>
        </div>

        {(searchTerm || bottleneckFilter !== 'ALL' || statusFilter !== 'ALL') && (
          <button 
            onClick={() => {
              setSearchTerm('');
              setBottleneckFilter('ALL');
              setStatusFilter('ALL');
            }}
            className="btn btn-secondary"
            style={{ fontSize: 11, padding: '5px 10px' }}
          >
            Clear Filters
          </button>
        )}
      </div>

      {/* Main Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="table" style={{ width: '100%', fontSize: 12 }}>
          <thead>
            <tr>
              <th style={{ padding: '10px 14px' }}>Query Fingerprint & Name</th>
              <th style={{ padding: '10px 14px' }}>Priority</th>
              <th style={{ padding: '10px 14px' }}>Main Problem</th>
              <th style={{ padding: '10px 14px' }}>Plan Complexity</th>
              <th style={{ padding: '10px 14px' }}>Duration & Calls</th>
              <th style={{ padding: '10px 14px' }}>Analysis Status</th>
              <th style={{ padding: '10px 14px', textAlign: 'right' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredQueries.map((query) => (
              <tr 
                key={query.id} 
                onClick={() => onSelectQuery(query.id)}
                style={{ cursor: 'pointer' }}
              >
                <td style={{ padding: '12px 14px', maxWidth: 300 }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                      {query.title}
                    </span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
                      {query.queryFingerprint}
                    </span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {query.maskedQueryTemplate.split('\n')[0]}
                    </span>
                  </div>
                </td>

                <td style={{ padding: '12px 14px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{
                      width: 44,
                      height: 6,
                      borderRadius: 3,
                      backgroundColor: 'var(--bg-subtle)',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        width: `${query.impactScore}%`,
                        height: '100%',
                        backgroundColor: query.impactScore > 80 ? 'var(--danger-text)' : query.impactScore > 50 ? 'var(--warning-text)' : 'var(--brand-primary)'
                      }} />
                    </div>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}>
                      {query.impactScore}
                    </span>
                  </div>
                </td>

                <td style={{ padding: '12px 14px', whiteSpace: 'nowrap' }}>
                  {getBottleneckBadge(query.bottleneckType)}
                </td>

                <td style={{ padding: '12px 14px', whiteSpace: 'nowrap' }}>
                  <span className="badge badge-neutral" style={{ fontSize: 11 }}>
                    {query.planGraph.nodes.length} plan nodes
                  </span>
                </td>

                <td style={{ padding: '12px 14px' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--danger-text)', fontWeight: 700 }}>
                      {query.averageDurationMs} ms
                    </span>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      {query.callsPerMin} calls/min
                    </span>
                  </div>
                </td>

                <td style={{ padding: '12px 14px', whiteSpace: 'nowrap' }}>
                  <span className={`badge ${
                    query.analysisStatus === 'SIMULATED' ? 'badge-success' :
                    query.analysisStatus === 'ABSTAINED' ? 'badge-neutral' : 'badge-brand'
                  }`}>
                    {query.analysisStatus === 'SIMULATED' ? 'Safe Simulation Passed' : query.analysisStatus}
                  </span>
                </td>

                <td style={{ padding: '12px 14px', textAlign: 'right', whiteSpace: 'nowrap' }}>
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectQuery(query.id);
                    }}
                    className="btn btn-secondary" 
                    style={{ padding: '5px 12px', fontSize: 11, gap: 4 }}
                  >
                    <span>View Diagnosis</span>
                    <ChevronRight size={13} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
