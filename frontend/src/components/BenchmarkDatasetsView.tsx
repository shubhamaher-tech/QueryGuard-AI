import React, { useState, useEffect } from 'react';
import { 
  Server, 
  Database, 
  ShieldCheck, 
  Play, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle2, 
  Trash2, 
  Layers, 
  HardDrive, 
  Check, 
  Sparkles,
  ArrowRight
} from 'lucide-react';
import type { 
  BenchmarkCatalogItem, 
  BenchmarkSetupStatus, 
  BenchmarkSummaryResponse,
  GNNModelItem
} from '../types/queryguard';
import { api } from '../lib/api';

export const BenchmarkDatasetsView: React.FC = () => {
  const [catalog, setCatalog] = useState<BenchmarkCatalogItem[]>([]);
  const [activeDataset, setActiveDataset] = useState<string>('ecommerce_synthetic');
  const [tpchSummary, setTpchSummary] = useState<BenchmarkSummaryResponse | null>(null);
  const [setupStatus, setSetupStatus] = useState<BenchmarkSetupStatus | null>(null);
  const [models, setModels] = useState<GNNModelItem[]>([]);
  const [activeModel, setActiveModel] = useState<string>('gnn_bottleneck_v2');

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [workloadIterations, setWorkloadIterations] = useState<number>(2);

  const loadData = async () => {
    try {
      const [catData, sumData, statusData, modelData] = await Promise.all([
        api.fetchBenchmarkCatalog(),
        api.fetchTpchSummary(),
        api.fetchTpchStatus(),
        api.fetchGNNModels()
      ]);

      if (catData?.benchmarks) {
        setCatalog(catData.benchmarks);
        setActiveDataset(catData.active_dataset);
      }
      if (sumData) setTpchSummary(sumData);
      if (statusData) setSetupStatus(statusData);
      if (modelData?.models) {
        setModels(modelData.models);
        setActiveModel(modelData.active_model);
      }
    } catch (err) {
      console.error('Failed to load benchmark data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (!setupStatus || !['GENERATING', 'VALIDATING', 'CLEANING', 'LOADING'].includes(setupStatus.status)) {
      return;
    }

    const interval = setInterval(async () => {
      const st = await api.fetchTpchStatus();
      if (st) {
        setSetupStatus(st);
        if (st.status === 'READY' || st.status === 'FAILED') {
          await loadData();
        }
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [setupStatus?.status]);

  const handleStartSetup = async (scaleFactor: number = 0.1) => {
    setIsProcessing(true);
    setActionMessage(`Initiating TPC-H SF ${scaleFactor} generation and validation...`);
    try {
      const st = await api.setupTpch(scaleFactor, true);
      setSetupStatus(st);
      setActionMessage(`Generating TPC-H SF ${scaleFactor} files in background...`);
    } catch (e: any) {
      setActionMessage(`Setup failed: ${e.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleLoadDatabase = async () => {
    setIsProcessing(true);
    setActionMessage('Loading processed files into workload-postgres tables...');
    try {
      const res = await api.loadTpch();
      setActionMessage(`Successfully loaded ${res.tables?.lineitem?.rows_loaded || 60000} lineitem rows into workload_db.`);
      await loadData();
    } catch (e: any) {
      setActionMessage(`Load error: ${e.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRunWorkload = async () => {
    setIsProcessing(true);
    setActionMessage(`Executing ${workloadIterations} iterations of approved TPC-H benchmark queries...`);
    try {
      const res = await api.runTpchWorkload(workloadIterations);
      setActionMessage(`Workload complete: Executed ${res.queries_executed} queries in ${res.duration_ms} ms. pg_stat_statements refreshed.`);
      await loadData();
    } catch (e: any) {
      setActionMessage(`Workload run error: ${e.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleResetTables = async () => {
    if (!confirm('Are you sure you want to reset/truncate TPC-H benchmark tables?')) return;
    setIsProcessing(true);
    try {
      await api.resetTpch();
      setActionMessage('TPC-H benchmark tables reset.');
      await loadData();
    } catch (e: any) {
      setActionMessage(`Reset error: ${e.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSelectModel = async (version: string) => {
    try {
      await api.selectGNNModel(version);
      setActiveModel(version);
      setActionMessage(`Active GNN inference checkpoint updated to ${version}`);
    } catch (e: any) {
      setActionMessage(`Failed to switch model: ${e.message}`);
    }
  };

  const isGenerating = setupStatus && ['GENERATING', 'VALIDATING', 'CLEANING', 'LOADING'].includes(setupStatus.status);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 1200, margin: '0 auto', paddingBottom: 40 }}>
      {/* Top Banner */}
      <div className="card" style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
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
              <Database size={24} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>
                  Benchmark Workload Sandbox
                </h1>
                <span className="badge badge-success">Local Sandbox</span>
                <span className="badge badge-brand">Zero Data Exposure</span>
              </div>
              <p style={{ margin: '4px 0 0', fontSize: 13, color: 'var(--text-secondary)' }}>
                Reproducible PostgreSQL benchmarks for testing optimizer bottlenecks, plan graphs, and hypothetical indexes safely.
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <button
              onClick={() => loadData()}
              disabled={isLoading || isProcessing}
              className="btn btn-secondary"
              style={{ fontSize: 12, padding: '7px 14px', gap: 6 }}
            >
              <RefreshCw size={14} className={isLoading ? 'spinner' : ''} />
              <span>Refresh Status</span>
            </button>
          </div>
        </div>

        {actionMessage && (
          <div style={{
            padding: '10px 14px',
            borderRadius: 'var(--radius-sm)',
            backgroundColor: 'var(--bg-subtle)',
            border: '1px solid var(--border-default)',
            fontSize: 12,
            color: 'var(--text-primary)',
            display: 'flex',
            alignItems: 'center',
            gap: 8
          }}>
            <CheckCircle2 size={16} style={{ color: 'var(--success-text)' }} />
            <span>{actionMessage}</span>
          </div>
        )}

        {/* Progress Bar for Setup */}
        {isGenerating && (
          <div style={{
            padding: '14px 18px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--brand-primary-muted)',
            border: '1px solid var(--brand-primary-border)',
            display: 'flex',
            flexDirection: 'column',
            gap: 8
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, fontWeight: 600, color: 'var(--brand-primary-text)' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <RefreshCw size={14} className="spinner" />
                <span>{setupStatus?.current_stage || 'Processing benchmark setup...'}</span>
              </span>
              <span>{setupStatus?.progress_pct || 0}%</span>
            </div>
            <div style={{ width: '100%', height: 6, borderRadius: 3, backgroundColor: 'var(--bg-surface)', overflow: 'hidden' }}>
              <div 
                style={{
                  height: '100%',
                  width: `${setupStatus?.progress_pct || 15}%`,
                  backgroundColor: 'var(--brand-primary)',
                  transition: 'width 0.3s ease'
                }}
              />
            </div>
            <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
              {setupStatus?.message}
            </span>
          </div>
        )}
      </div>

      {/* Strict Sandbox Guarantee Card */}
      <div className="card" style={{ padding: '14px 18px', display: 'flex', alignItems: 'flex-start', gap: 12 }}>
        <ShieldCheck size={20} style={{ color: 'var(--success-text)', flexShrink: 0, marginTop: 2 }} />
        <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
          <strong style={{ color: 'var(--text-primary)' }}>Strict Local Sandbox & Privacy Guarantee: </strong>
          All benchmark tables reside exclusively in the local <code style={{ backgroundColor: 'var(--bg-subtle)', padding: '2px 5px', borderRadius: 3, color: 'var(--brand-primary)' }}>workload-postgres</code> container. 
          The QueryGuard application database, GNN dataset, and frontend only receive masked query structures with zero raw data rows or literals.
        </div>
      </div>

      {/* Benchmark Workload Catalog */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 16 }}>
        {/* 1. Synthetic E-Commerce (Default) */}
        <div className="card" style={{ padding: 22, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: 16 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <Database size={20} style={{ color: 'var(--brand-primary)' }} />
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
                  Synthetic E-Commerce
                </h3>
              </div>
              <span className="badge badge-success">ACTIVE & READY</span>
            </div>

            <p style={{ margin: 0, fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Baseline transactional schema with deliberately unindexed columns on transactions to induce realistic query bottlenecks.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginTop: 16, paddingTop: 14, borderTop: '1px solid var(--border-default)', fontSize: 12 }}>
              <div>
                <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block' }}>Tables</span>
                <strong style={{ color: 'var(--text-primary)' }}>5 Tables</strong>
              </div>
              <div>
                <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block' }}>Total Rows</span>
                <strong style={{ color: 'var(--text-primary)' }}>~16,500</strong>
              </div>
              <div>
                <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block' }}>Footprint</span>
                <strong style={{ color: 'var(--text-primary)' }}>~15 MB</strong>
              </div>
            </div>
          </div>

          <div style={{ paddingTop: 12, borderTop: '1px solid var(--border-default)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 12 }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--success-text)', fontWeight: 600 }}>
              <Check size={14} /> Loaded in workload_db
            </span>
            <span style={{ color: 'var(--text-muted)' }}>Default Sandbox</span>
          </div>
        </div>

        {/* 2. TPC-H SF 0.1 (Decision Support) */}
        <div className="card" style={{ padding: 22, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: 16 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <Server size={20} style={{ color: '#7C3AED' }} />
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
                  TPC-H Decision Support (SF 0.1)
                </h3>
              </div>
              <span className={`badge ${tpchSummary?.is_installed ? 'badge-success' : 'badge-warning'}`}>
                {tpchSummary?.is_installed ? 'INSTALLED & READY' : 'AVAILABLE'}
              </span>
            </div>

            <p style={{ margin: 0, fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Standard analytical decision-support benchmark with 8 tables and 7 approved query templates testing complex joins, aggregations, and full table scans.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, marginTop: 16, paddingTop: 14, borderTop: '1px solid var(--border-default)', fontSize: 12 }}>
              <div>
                <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block' }}>Tables</span>
                <strong style={{ color: 'var(--text-primary)' }}>8 Tables</strong>
              </div>
              <div>
                <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block' }}>Rows</span>
                <strong style={{ color: 'var(--text-primary)' }}>{tpchSummary?.estimated_rows?.toLocaleString() || '~87,000'}</strong>
              </div>
              <div>
                <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block' }}>Queries</span>
                <strong style={{ color: 'var(--text-primary)' }}>7 Queries</strong>
              </div>
              <div>
                <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block' }}>Disk</span>
                <strong style={{ color: 'var(--text-primary)' }}>~{tpchSummary?.disk_size_estimate_mb || 8.0} MB</strong>
              </div>
            </div>
          </div>

          <div style={{ paddingTop: 14, borderTop: '1px solid var(--border-default)', display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 8 }}>
              <button
                onClick={() => handleStartSetup(0.1)}
                disabled={isProcessing || !!isGenerating}
                className="btn btn-secondary"
                style={{ fontSize: 11, padding: '5px 10px' }}
              >
                1. Generate .tbl
              </button>

              <button
                onClick={handleLoadDatabase}
                disabled={isProcessing || !!isGenerating}
                className="btn btn-secondary"
                style={{ fontSize: 11, padding: '5px 10px' }}
              >
                2. Load into DB
              </button>

              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginLeft: 'auto' }}>
                <select
                  value={workloadIterations}
                  onChange={(e) => setWorkloadIterations(Number(e.target.value))}
                  style={{ fontSize: 11, padding: '4px 8px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-default)', backgroundColor: 'var(--bg-surface)' }}
                >
                  <option value={1}>1 run</option>
                  <option value={2}>2 runs</option>
                  <option value={5}>5 runs</option>
                </select>

                <button
                  onClick={handleRunWorkload}
                  disabled={isProcessing || !!isGenerating}
                  className="btn btn-primary"
                  style={{ fontSize: 11, padding: '5px 10px', gap: 4 }}
                >
                  <Play size={12} />
                  <span>3. Run Workload</span>
                </button>
              </div>

              <button
                onClick={handleResetTables}
                disabled={isProcessing || !!isGenerating}
                className="btn btn-ghost"
                style={{ padding: 4, color: 'var(--danger-text)' }}
                title="Reset/Truncate TPC-H tables"
              >
                <Trash2 size={14} />
              </button>
            </div>
          </div>
        </div>

        {/* 3. TPC-H SF 1.0 (Hardware Warning) */}
        <div className="card" style={{ padding: 22, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: 16 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <HardDrive size={20} style={{ color: 'var(--warning-text)' }} />
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
                  TPC-H SF 1.0 (~1 GB)
                </h3>
              </div>
              <span className="badge badge-neutral">AVAILABLE</span>
            </div>

            <p style={{ margin: 0, fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Full scale 1.0 TPC-H dataset with 6,000,000 line items designed for stress-testing planner cardinality estimation.
            </p>

            <div style={{
              marginTop: 14,
              padding: '10px 12px',
              borderRadius: 'var(--radius-sm)',
              backgroundColor: 'var(--warning-muted)',
              border: '1px solid var(--warning-border)',
              display: 'flex',
              alignItems: 'flex-start',
              gap: 8,
              fontSize: 11,
              color: 'var(--warning-text)'
            }}>
              <AlertTriangle size={15} style={{ flexShrink: 0, marginTop: 1 }} />
              <div>
                <strong>Hardware Advisory: </strong> Requires ~4 GB RAM and ~1.2 GB disk storage. Recommended for high-spec workstations.
              </div>
            </div>
          </div>

          <div style={{ paddingTop: 12, borderTop: '1px solid var(--border-default)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 12 }}>
            <button
              onClick={() => handleStartSetup(1.0)}
              disabled={isProcessing || !!isGenerating}
              className="btn btn-secondary"
              style={{ fontSize: 11, padding: '5px 12px' }}
            >
              Generate SF 1.0 (High Spec)
            </button>
            <span style={{ color: 'var(--text-muted)' }}>~6M Rows</span>
          </div>
        </div>

        {/* 4. Join Order Benchmark (JOB / IMDb) */}
        <div className="card" style={{ padding: 22, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: 16 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <Layers size={20} style={{ color: 'var(--info-text)' }} />
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
                  Join Order Benchmark (JOB / IMDb)
                </h3>
              </div>
              <span className="badge badge-neutral">SCAFFOLDED</span>
            </div>

            <p style={{ margin: 0, fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Real-world schema featuring 21 interconnected tables with severe cross-table correlations to test join order optimization.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginTop: 16, paddingTop: 14, borderTop: '1px solid var(--border-default)', fontSize: 12 }}>
              <div>
                <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block' }}>Tables</span>
                <strong style={{ color: 'var(--text-primary)' }}>21 Tables</strong>
              </div>
              <div>
                <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block' }}>Domain</span>
                <strong style={{ color: 'var(--text-primary)' }}>Cinema / IMDb</strong>
              </div>
              <div>
                <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block' }}>Status</span>
                <strong style={{ color: 'var(--brand-primary)' }}>Ready for Extension</strong>
              </div>
            </div>
          </div>

          <div style={{ paddingTop: 12, borderTop: '1px solid var(--border-default)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 12 }}>
            <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>Join order expansion module</span>
            <span className="badge badge-neutral">Roadmap</span>
          </div>
        </div>
      </div>

      {/* GNN Model Checkpoint Selector */}
      <div className="card" style={{ padding: 22, display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
          <div>
            <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Sparkles size={16} style={{ color: 'var(--brand-primary)' }} />
              GNN Classifier Model Checkpoints
            </h3>
            <p style={{ margin: '2px 0 0', fontSize: 12, color: 'var(--text-secondary)' }}>
              Select which trained Graph Neural Network model evaluates execution plan graphs.
            </p>
          </div>
          <span className="badge badge-brand" style={{ fontFamily: 'var(--font-mono)' }}>
            Active: {activeModel}
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 12 }}>
          {models.map((m) => (
            <div 
              key={m.model_version}
              onClick={() => handleSelectModel(m.model_version)}
              style={{
                padding: '14px 16px',
                borderRadius: 'var(--radius-md)',
                border: activeModel === m.model_version ? '2px solid var(--brand-primary)' : '1px solid var(--border-default)',
                backgroundColor: activeModel === m.model_version ? 'var(--brand-primary-muted)' : 'var(--bg-surface)',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 13, color: 'var(--text-primary)' }}>
                  {m.model_version}
                </span>
                {activeModel === m.model_version && (
                  <span className="badge badge-success" style={{ fontSize: 10 }}>
                    <Check size={11} /> Active
                  </span>
                )}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6, marginTop: 10, fontSize: 11 }}>
                <div>
                  <span style={{ color: 'var(--text-muted)', display: 'block' }}>Dataset</span>
                  <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>{m.dataset_version}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)', display: 'block' }}>Accuracy</span>
                  <span style={{ color: 'var(--success-text)', fontWeight: 700 }}>
                    {m.accuracy !== undefined ? `${(m.accuracy * 100).toFixed(1)}%` : '—'}
                  </span>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)', display: 'block' }}>Macro F1</span>
                  <span style={{ color: 'var(--brand-primary-text)', fontWeight: 700 }}>
                    {m.macro_f1 !== undefined ? m.macro_f1.toFixed(3) : '—'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
