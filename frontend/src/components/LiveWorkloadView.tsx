import React, { useState, useEffect, useRef } from 'react';
import { 
  Zap, 
  Activity, 
  Database, 
  ShieldCheck, 
  RefreshCw, 
  Play, 
  AlertTriangle, 
  CheckCircle2, 
  TrendingUp, 
  Terminal, 
  Clock, 
  HardDrive,
  Layers,
  Search,
  Copy,
  Check,
  ArrowRight,
  PieChart
} from 'lucide-react';
import type { 
  RealtimeMetricsResponse, 
  RealtimeStatusResponse, 
  SlowQueryItem 
} from '../types/queryguard';
import { api } from '../lib/api';

interface LiveWorkloadViewProps {
  onNavigateToAnalyze?: (queryText: string) => void;
}

export const friendlyBottleneckName = (b?: string): string => {
  switch (b) {
    case 'SEQ_SCAN':
    case 'LARGE_SEQ_SCAN':
      return 'Full Table Scan';
    case 'UNINDEXED_JOIN':
    case 'REPEATED_INNER_LOOP':
    case 'NESTED_LOOP':
      return 'Repeated Join Work';
    case 'EXPENSIVE_SORT':
      return 'Expensive Sort Spill';
    case 'HIGH_IO_SCAN':
      return 'Heavy Disk Read Scan';
    case 'HASH_JOIN':
      return 'Hash Join Spill';
    default:
      return b ? b.replace(/_/g, ' ') : 'Standard Execution';
  }
};

export const LiveWorkloadView: React.FC<LiveWorkloadViewProps> = ({ onNavigateToAnalyze }) => {
  const [metrics, setMetrics] = useState<RealtimeMetricsResponse | null>(null);
  const [status, setStatus] = useState<RealtimeStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [isRunningSample, setIsRunningSample] = useState<boolean>(false);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedBottleneck, setSelectedBottleneck] = useState<string | null>(null);
  const [copiedFp, setCopiedFp] = useState<string | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());

  const timerRef = useRef<any>(null);

  const fetchData = async () => {
    try {
      const [m, s] = await Promise.all([
        api.fetchRealtimeMetrics(),
        api.fetchRealtimeStatus()
      ]);
      if (m) setMetrics(m);
      if (s) setStatus(s);
      setLastRefreshed(new Date());
    } catch (err) {
      console.error('Failed to load realtime metrics:', err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (!autoRefresh) {
      if (timerRef.current) clearInterval(timerRef.current);
      return;
    }

    const interval = status?.is_workload_active || isRunningSample ? 3000 : 8000;
    timerRef.current = setInterval(() => {
      fetchData();
    }, interval);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [autoRefresh, status?.is_workload_active, isRunningSample]);

  const handleManualRefresh = () => {
    setIsRefreshing(true);
    fetchData();
  };

  const handleRunSampleTraffic = async () => {
    setIsRunningSample(true);
    try {
      await api.runTpchWorkload(2);
      await fetchData();
    } catch (e) {
      console.error('Error generating sample workload:', e);
    } finally {
      setIsRunningSample(false);
    }
  };

  const handleCopySql = (text: string, fp: string) => {
    navigator.clipboard.writeText(text);
    setCopiedFp(fp);
    setTimeout(() => setCopiedFp(null), 2000);
  };

  const filteredQueries = (metrics?.top_slow_queries || []).filter(q => {
    const matchesSearch = 
      q.query_fingerprint.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.masked_query.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (q.primary_bottleneck && q.primary_bottleneck.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesBottleneck = !selectedBottleneck || q.primary_bottleneck === selectedBottleneck;
    return matchesSearch && matchesBottleneck;
  });

  const getBottleneckBadge = (b?: string) => {
    const name = friendlyBottleneckName(b);
    switch (b) {
      case 'SEQ_SCAN':
      case 'LARGE_SEQ_SCAN':
        return <span className="badge badge-danger">{name}</span>;
      case 'UNINDEXED_JOIN':
      case 'REPEATED_INNER_LOOP':
        return <span className="badge badge-warning">{name}</span>;
      case 'EXPENSIVE_SORT':
        return <span className="badge badge-neutral" style={{ color: '#7C3AED', backgroundColor: '#F5F3FF', borderColor: '#DDD6FE' }}>{name}</span>;
      default:
        return <span className="badge badge-neutral">{name}</span>;
    }
  };

  const getSeverityDot = (sev: string) => {
    if (sev === 'HIGH' || sev === 'CRITICAL') return <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--danger-text)', display: 'inline-block' }} />;
    if (sev === 'MEDIUM' || sev === 'WARNING') return <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--warning-text)', display: 'inline-block' }} />;
    return <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--brand-primary)', display: 'inline-block' }} />;
  };

  const totalBottlenecks = Object.values(metrics?.bottleneck_distribution || {}).reduce((a, b) => a + b, 0) || 1;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 1200, margin: '0 auto', paddingBottom: 40 }}>
      {/* Header Banner */}
      <div className="card" style={{ padding: '20px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{
            width: 44,
            height: 44,
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--brand-primary-muted)',
            color: 'var(--brand-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Zap size={24} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>
                Live Workload Telemetry
              </h1>
              <span className="badge badge-success" style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: 'currentColor' }} />
                <span>Active Live Feed</span>
              </span>
            </div>
            <p style={{ margin: '4px 0 0', fontSize: 13, color: 'var(--text-secondary)' }}>
              Real-time query performance collected from sandbox PostgreSQL using <code style={{ backgroundColor: 'var(--bg-subtle)', padding: '2px 6px', borderRadius: 4 }}>pg_stat_statements</code>.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <button
            onClick={handleRunSampleTraffic}
            disabled={isRunningSample}
            className="btn btn-primary"
            style={{ fontSize: 12, padding: '7px 14px', gap: 6 }}
            title="Fire a batch of queries to generate fresh metrics"
          >
            {isRunningSample ? (
              <RefreshCw size={14} className="spinner" />
            ) : (
              <Play size={14} />
            )}
            <span>Simulate Traffic</span>
          </button>

          <button
            onClick={handleManualRefresh}
            disabled={isRefreshing}
            className="btn btn-secondary"
            style={{ fontSize: 12, padding: '7px 14px', gap: 6 }}
          >
            <RefreshCw size={14} className={isRefreshing ? 'spinner' : ''} />
            <span>Refresh</span>
          </button>

          <label style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            fontSize: 12,
            color: 'var(--text-secondary)',
            backgroundColor: 'var(--bg-subtle)',
            border: '1px solid var(--border-default)',
            padding: '6px 12px',
            borderRadius: 'var(--radius-sm)',
            cursor: 'pointer'
          }}>
            <input 
              type="checkbox" 
              checked={autoRefresh} 
              onChange={(e) => setAutoRefresh(e.target.checked)} 
            />
            <span>Auto-refresh ({status?.is_workload_active ? '3s' : '8s'})</span>
          </label>
        </div>
      </div>

      {/* Safety & Isolation Indicators */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 12 }}>
        <div className="card" style={{ padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 10, fontSize: 12 }}>
          <Database size={16} style={{ color: 'var(--brand-primary)', flexShrink: 0 }} />
          <div>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Target Database: </span>
            <span style={{ color: 'var(--brand-primary)', fontWeight: 600 }}>workload_db</span> (Isolated Sandbox)
          </div>
        </div>
        <div className="card" style={{ padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 10, fontSize: 12 }}>
          <ShieldCheck size={16} style={{ color: 'var(--info-text)', flexShrink: 0 }} />
          <div>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Transaction Mode: </span>
            <span style={{ color: 'var(--text-secondary)' }}>READ ONLY (Zero DDL/DML changes)</span>
          </div>
        </div>
        <div className="card" style={{ padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 10, fontSize: 12 }}>
          <CheckCircle2 size={16} style={{ color: 'var(--success-text)', flexShrink: 0 }} />
          <div>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Privacy Shield: </span>
            <span style={{ color: 'var(--text-secondary)' }}>Literals & Column Names Tokenized</span>
          </div>
        </div>
      </div>

      {/* Key Telemetry Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14 }}>
        <div className="card" style={{ padding: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-secondary)', fontSize: 12, fontWeight: 600 }}>
            <span>Average Latency</span>
            <Clock size={16} style={{ color: 'var(--brand-primary)' }} />
          </div>
          <div style={{ marginTop: 8, display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)' }}>
              {metrics?.avg_latency_ms !== undefined ? `${metrics.avg_latency_ms} ms` : '—'}
            </span>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              (p95: {metrics?.p95_latency_ms || 0} ms)
            </span>
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginTop: 4 }}>
            Mean execution across active queries
          </span>
        </div>

        <div className="card" style={{ padding: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-secondary)', fontSize: 12, fontWeight: 600 }}>
            <span>Execution Throughput</span>
            <Activity size={16} style={{ color: 'var(--info-text)' }} />
          </div>
          <div style={{ marginTop: 8, display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)' }}>
              {metrics?.total_calls_per_sec !== undefined ? `${metrics.total_calls_per_sec}` : '0.0'}
            </span>
            <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>queries / sec</span>
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginTop: 4 }}>
            Queries executed in window
          </span>
        </div>

        <div className="card" style={{ padding: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-secondary)', fontSize: 12, fontWeight: 600 }}>
            <span>Queries Needing Review</span>
            <AlertTriangle size={16} style={{ color: 'var(--warning-text)' }} />
          </div>
          <div style={{ marginTop: 8, display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontSize: 24, fontWeight: 800, color: 'var(--warning-text)' }}>
              {metrics?.slow_query_count || 0}
            </span>
            <span style={{ fontSize: 11, color: 'var(--warning-text)', fontWeight: 600 }}>slow queries</span>
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginTop: 4 }}>
            Captured by slow-query monitor
          </span>
        </div>

        <div className="card" style={{ padding: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--text-secondary)', fontSize: 12, fontWeight: 600 }}>
            <span>Buffer Cache Hit Ratio</span>
            <HardDrive size={16} style={{ color: 'var(--success-text)' }} />
          </div>
          <div style={{ marginTop: 8, display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)' }}>
              {metrics?.cache_hit_ratio_pct !== undefined ? `${metrics.cache_hit_ratio_pct}%` : '—'}
            </span>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              (CPU ~{metrics?.estimated_cpu_pct || 4}%)
            </span>
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginTop: 4 }}>
            RAM memory hits vs disk reads
          </span>
        </div>
      </div>

      {/* Latency Trend & Bottleneck Distribution */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: 16 }}>
        {/* Latency Trend Graph */}
        <div className="card" style={{ padding: 20, overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <div>
              <h3 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 8 }}>
                <TrendingUp size={16} style={{ color: 'var(--brand-primary)' }} />
                Real-Time Latency Timeline
              </h3>
              <p style={{ margin: '2px 0 0', fontSize: 11, color: 'var(--text-secondary)' }}>
                Rolling latency samples from PostgreSQL
              </p>
            </div>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              Updated: {lastRefreshed.toLocaleTimeString()}
            </span>
          </div>

          <div style={{
            height: 180,
            width: '100%',
            maxWidth: '100%',
            boxSizing: 'border-box',
            display: 'flex',
            alignItems: 'flex-end',
            gap: 5,
            padding: '16px 12px 8px',
            backgroundColor: 'var(--bg-subtle)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-default)',
            overflow: 'hidden'
          }}>
            {metrics?.latency_trend && metrics.latency_trend.length > 0 ? (
              (() => {
                const trendSlice = metrics.latency_trend.slice(-16);
                const maxLat = Math.max(...trendSlice.map(p => p.latency_ms), 10);
                return trendSlice.map((point, idx) => {
                  const heightPct = Math.min(100, Math.max(12, (point.latency_ms / maxLat) * 100));
                  return (
                    <div 
                      key={idx} 
                      style={{ 
                        flex: '1 1 0px', 
                        minWidth: 0, 
                        display: 'flex', 
                        flexDirection: 'column', 
                        alignItems: 'center', 
                        gap: 4, 
                        height: '100%', 
                        justifyContent: 'flex-end',
                        overflow: 'hidden'
                      }}
                    >
                      <div 
                        title={`${point.timestamp}: ${point.latency_ms} ms (${point.calls_per_sec} qps)`}
                        style={{
                          width: '100%',
                          height: `${heightPct}%`,
                          borderRadius: '3px 3px 0 0',
                          backgroundColor: point.latency_ms > 100 
                            ? 'var(--danger-text)' 
                            : point.latency_ms > 45 
                              ? 'var(--warning-text)' 
                              : 'var(--brand-primary)',
                          transition: 'height 0.3s ease'
                        }}
                      />
                      <span style={{ 
                        fontSize: 8, 
                        color: 'var(--text-muted)', 
                        overflow: 'hidden', 
                        textOverflow: 'ellipsis', 
                        whiteSpace: 'nowrap', 
                        width: '100%', 
                        textAlign: 'center' 
                      }}>
                        {point.timestamp.slice(-5)}
                      </span>
                    </div>
                  );
                });
              })()
            ) : (
              <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, color: 'var(--text-muted)' }}>
                Waiting for telemetry samples... Click "Simulate Traffic" to begin.
              </div>
            )}
          </div>
        </div>

        {/* Bottleneck Distribution */}
        <div className="card" style={{ padding: 20, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', overflow: 'hidden' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Layers size={16} style={{ color: 'var(--info-text)' }} />
                  <span>Main Problems Identified</span>
                </h3>
                <p style={{ margin: '2px 0 0', fontSize: 11, color: 'var(--text-secondary)' }}>
                  Interactive categorization of slow execution patterns
                </p>
              </div>
              <PieChart size={16} style={{ color: 'var(--brand-primary-text)' }} />
            </div>

            {/* SVG Pie / Donut Chart */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginTop: 14, padding: '8px 0', borderBottom: '1px solid var(--border-default)', paddingBottom: 14 }}>
              <div style={{ position: 'relative', width: 92, height: 92, flexShrink: 0 }}>
                <svg viewBox="0 0 36 36" style={{ width: '100%', height: '100%' }}>
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="#E2E8F0"
                    strokeWidth="4.2"
                  />
                  {metrics?.bottleneck_distribution && (() => {
                    const entries = Object.entries(metrics.bottleneck_distribution);
                    const total = totalBottlenecks || 1;
                    let acc = 0;
                    return entries.map(([type, count]) => {
                      const pct = Math.max(1, Math.round((count / total) * 100));
                      const offset = -acc;
                      acc += pct;
                      const isSelected = selectedBottleneck === type;
                      const color = type === 'SEQ_SCAN' || type === 'LARGE_SEQ_SCAN' ? 'var(--danger-text)' :
                        type === 'UNINDEXED_JOIN' || type === 'REPEATED_INNER_LOOP' ? 'var(--warning-text)' :
                        type === 'EXPENSIVE_SORT' ? '#7C3AED' : 'var(--brand-primary)';
                      return (
                        <path
                          key={type}
                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                          fill="none"
                          stroke={color}
                          strokeWidth={isSelected ? 5.8 : 4.2}
                          strokeDasharray={`${pct}, 100`}
                          strokeDashoffset={offset}
                          opacity={selectedBottleneck && !isSelected ? 0.45 : 1}
                          style={{
                            cursor: 'pointer',
                            transition: 'stroke-dasharray 0.3s ease, stroke-width 0.2s ease, opacity 0.2s ease'
                          }}
                          onClick={() => setSelectedBottleneck(prev => prev === type ? null : type)}
                        >
                          <title>{`${friendlyBottleneckName(type)}: ${count} (${pct}%) - Click to filter`}</title>
                        </path>
                      );
                    });
                  })()}
                </svg>
                <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', pointerEvents: 'none' }}>
                  <span style={{ fontSize: 16, fontWeight: 800, color: 'var(--text-primary)' }}>{totalBottlenecks}</span>
                  <span style={{ fontSize: 8, color: 'var(--text-muted)' }}>Found</span>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, flex: 1 }}>
                {metrics?.bottleneck_distribution && Object.entries(metrics.bottleneck_distribution).map(([type, count]) => {
                  const pct = Math.round((count / totalBottlenecks) * 100);
                  const friendly = friendlyBottleneckName(type);
                  const isSelected = selectedBottleneck === type;
                  const color = type === 'SEQ_SCAN' || type === 'LARGE_SEQ_SCAN' ? 'var(--danger-text)' :
                    type === 'UNINDEXED_JOIN' || type === 'REPEATED_INNER_LOOP' ? 'var(--warning-text)' :
                    type === 'EXPENSIVE_SORT' ? '#7C3AED' : 'var(--brand-primary)';
                  return (
                    <div 
                      key={type} 
                      onClick={() => setSelectedBottleneck(prev => prev === type ? null : type)}
                      style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'space-between', 
                        fontSize: 11,
                        cursor: 'pointer',
                        padding: '2px 6px',
                        borderRadius: 4,
                        backgroundColor: isSelected ? 'rgba(15, 118, 110, 0.08)' : 'transparent',
                        outline: isSelected ? `1px solid ${color}` : 'none',
                        transition: 'all 0.2s ease'
                      }}
                      title="Click to filter queries table below"
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: color }} />
                        <span style={{ color: isSelected ? 'var(--brand-primary)' : 'var(--text-secondary)', fontWeight: isSelected ? 700 : 500 }}>{friendly}</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <strong className="font-mono">{count}</strong>
                        <span style={{ color: 'var(--text-muted)', fontSize: 10 }}>({pct}%)</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {selectedBottleneck && (
              <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '4px 8px', backgroundColor: 'rgba(15, 118, 110, 0.08)', borderRadius: 4, fontSize: 11 }}>
                <span style={{ color: 'var(--brand-primary)', fontWeight: 600 }}>
                  Filtering: {friendlyBottleneckName(selectedBottleneck)}
                </span>
                <button
                  onClick={() => setSelectedBottleneck(null)}
                  style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 11, fontWeight: 700 }}
                >
                  ✕ Clear
                </button>
              </div>
            )}

            <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 10 }}>
              {metrics?.bottleneck_distribution && Object.entries(metrics.bottleneck_distribution).map(([type, count]) => {
                const pct = Math.round((count / totalBottlenecks) * 100);
                const friendly = friendlyBottleneckName(type);
                const isSelected = selectedBottleneck === type;
                return (
                  <div 
                    key={type} 
                    onClick={() => setSelectedBottleneck(prev => prev === type ? null : type)}
                    style={{ 
                      display: 'flex', 
                      flexDirection: 'column', 
                      gap: 3, 
                      cursor: 'pointer',
                      padding: '4px 6px',
                      borderRadius: 4,
                      backgroundColor: isSelected ? 'rgba(15, 118, 110, 0.06)' : 'transparent',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                      <span style={{ fontWeight: isSelected ? 700 : 600, color: isSelected ? 'var(--brand-primary)' : 'var(--text-primary)' }}>{friendly}</span>
                      <span style={{ color: 'var(--text-muted)' }}>{pct}%</span>
                    </div>
                    <div style={{ width: '100%', height: 6, borderRadius: 3, backgroundColor: 'var(--bg-subtle)', overflow: 'hidden' }}>
                      <div 
                        style={{
                          height: '100%',
                          width: `${pct}%`,
                          borderRadius: 3,
                          backgroundColor: type === 'SEQ_SCAN' || type === 'LARGE_SEQ_SCAN' ? 'var(--danger-text)' :
                            type === 'UNINDEXED_JOIN' || type === 'REPEATED_INNER_LOOP' ? 'var(--warning-text)' :
                            type === 'EXPENSIVE_SORT' ? '#7C3AED' : 'var(--brand-primary)'
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div style={{
            marginTop: 16,
            padding: '10px 14px',
            backgroundColor: 'var(--bg-subtle)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-default)',
            fontSize: 11,
            color: 'var(--text-secondary)'
          }}>
            <strong style={{ color: 'var(--text-primary)' }}>Safe Sandbox: </strong>
            Metrics reflect local performance inside isolated Postgres. No external telemetry sent.
          </div>
        </div>
      </div>

      {/* Slow Queries Table */}
      <div className="card" style={{ padding: 22 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, marginBottom: 16 }}>
          <div>
            <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Database size={18} style={{ color: 'var(--brand-primary)' }} />
              Queries Needing Optimization
            </h3>
            <p style={{ margin: '2px 0 0', fontSize: 12, color: 'var(--text-secondary)' }}>
              Sanitized queries ordered by execution time. Click "Analyze" to simulate fixes.
            </p>
          </div>

          <div style={{ position: 'relative', width: 260 }}>
            <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Filter fingerprint or query..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: '100%',
                padding: '7px 10px 7px 30px',
                fontSize: 12,
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-default)',
                color: 'var(--text-primary)'
              }}
            />
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="table" style={{ width: '100%', fontSize: 12 }}>
            <thead>
              <tr>
                <th style={{ padding: '10px 14px' }}>Query ID</th>
                <th style={{ padding: '10px 14px' }}>Sanitized SQL</th>
                <th style={{ padding: '10px 14px' }}>Main Problem</th>
                <th style={{ padding: '10px 14px', textAlign: 'right' }}>Calls</th>
                <th style={{ padding: '10px 14px', textAlign: 'right' }}>Average Time</th>
                <th style={{ padding: '10px 14px', textAlign: 'right' }}>p95 Time</th>
                <th style={{ padding: '10px 14px', textAlign: 'center' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredQueries.length > 0 ? (
                filteredQueries.map((q) => (
                  <tr key={q.query_fingerprint}>
                    <td style={{ padding: '12px 14px', whiteSpace: 'nowrap', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        {getSeverityDot(q.severity)}
                        <span>{q.query_fingerprint}</span>
                      </div>
                    </td>
                    <td style={{ padding: '12px 14px', maxWidth: 360, fontFamily: 'var(--font-mono)', fontSize: 11 }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 6 }}>
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'var(--text-primary)' }}>
                          {q.masked_query}
                        </span>
                        <button
                          onClick={() => handleCopySql(q.masked_query, q.query_fingerprint)}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            color: 'var(--text-muted)',
                            cursor: 'pointer',
                            flexShrink: 0
                          }}
                          title="Copy sanitized SQL"
                        >
                          {copiedFp === q.query_fingerprint ? (
                            <Check size={13} style={{ color: 'var(--success-text)' }} />
                          ) : (
                            <Copy size={13} />
                          )}
                        </button>
                      </div>
                    </td>
                    <td style={{ padding: '12px 14px', whiteSpace: 'nowrap' }}>
                      {getBottleneckBadge(q.primary_bottleneck)}
                    </td>
                    <td style={{ padding: '12px 14px', textAlign: 'right', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {q.calls.toLocaleString()}
                    </td>
                    <td style={{ padding: '12px 14px', textAlign: 'right', fontWeight: 700, color: 'var(--danger-text)' }}>
                      {q.mean_time_ms} ms
                    </td>
                    <td style={{ padding: '12px 14px', textAlign: 'right', color: 'var(--text-secondary)' }}>
                      {q.p95_time_ms} ms
                    </td>
                    <td style={{ padding: '12px 14px', textAlign: 'center', whiteSpace: 'nowrap' }}>
                      <button
                        onClick={() => onNavigateToAnalyze && onNavigateToAnalyze(q.masked_query)}
                        className="btn btn-secondary"
                        style={{ fontSize: 11, padding: '4px 10px', gap: 4 }}
                      >
                        <Terminal size={12} />
                        <span>Analyze</span>
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>
                    No queries found matching the search filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
