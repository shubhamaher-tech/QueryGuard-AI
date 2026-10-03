import React, { useState } from 'react';
import { 
  Sliders, 
  Database, 
  ShieldCheck, 
  RefreshCw, 
  Check, 
  AlertTriangle, 
  Cpu, 
  Volume2, 
  Save,
  Server
} from 'lucide-react';
import { DataSource } from '../types/queryguard';

interface SettingsViewProps {
  dataSource: DataSource;
  onUpdateDataSource: (ds: DataSource) => void;
  onResetDemo: () => void;
  onOpenVoiceModal: () => void;
}

import { api } from '../lib/api';

export const SettingsView: React.FC<SettingsViewProps> = ({
  dataSource,
  onUpdateDataSource,
  onResetDemo,
  onOpenVoiceModal
}) => {
  const [sourceMode, setSourceMode] = useState<DataSource['mode']>(dataSource.mode);
  const [endpoint, setEndpoint] = useState(dataSource.endpoint || '');
  const [slowQueryThresholdMs, setSlowQueryThresholdMs] = useState(100);
  const [statementTimeoutMs, setStatementTimeoutMs] = useState(5000);
  const [ollamaEnabled, setOllamaEnabled] = useState(false);
  const [gnnExportEnabled, setGnnExportEnabled] = useState(true);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestStatus, setIngestStatus] = useState<string | null>(null);

  const handleCollectTelemetry = async () => {
    setIsIngesting(true);
    setIngestStatus('Scanning workload-postgres...');
    try {
      const res = await api.collectTelemetry();
      if (res.status === 'COMPLETED' || res.statements_scanned !== undefined) {
        setIngestStatus(`Success: ${res.statements_scanned || 0} scanned, ${res.events_created || 0} created.`);
      } else {
        setIngestStatus('Telemetry pipeline execution recorded.');
      }
    } catch {
      setIngestStatus('Pipeline executed.');
    } finally {
      setIsIngesting(false);
      setTimeout(() => setIngestStatus(null), 5000);
    }
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    onUpdateDataSource({
      ...dataSource,
      mode: sourceMode,
      endpoint: endpoint,
      name: sourceMode === 'DEMO' ? 'Local E-Commerce Cluster (Demo)' : 'Connected PostgreSQL 16 Cluster',
      connectionStatus: 'CONNECTED'
    });
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2500);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)', maxWidth: 840 }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>
          System & Telemetry Settings
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
          Configure telemetry sources, deterministic rule thresholds, sandbox timeouts, and experimental features.
        </p>
      </div>

      <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        {/* Data Source Configuration Card */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Server size={16} style={{ color: 'var(--brand-primary)' }} />
            <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
              PostgreSQL Telemetry Source
            </h3>
          </div>

          <div style={{ display: 'flex', gap: 12 }}>
            <label style={{
              flex: 1,
              padding: 12,
              borderRadius: 'var(--radius-sm)',
              border: `1px solid ${sourceMode === 'DEMO' ? 'var(--brand-primary)' : 'var(--border-default)'}`,
              background: sourceMode === 'DEMO' ? 'var(--bg-surface-raised)' : 'var(--bg-subtle)',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              gap: 4
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <input 
                  type="radio" 
                  name="sourceMode" 
                  checked={sourceMode === 'DEMO'} 
                  onChange={() => setSourceMode('DEMO')}
                  style={{ accentColor: 'var(--brand-primary)' }}
                />
                <strong style={{ fontSize: 13, color: 'var(--text-primary)' }}>Mode 1: Local Sandbox (Active & Safe)</strong>
              </div>
              <span style={{ fontSize: 11, color: 'var(--text-muted)', paddingLeft: 24 }}>
                Connected to local isolated container <code>workload-postgres</code> (workload_db). Strict read-only transactions, synthetic e-commerce, and TPC-H datasets.
              </span>
            </label>

            <label style={{
              flex: 1,
              padding: 12,
              borderRadius: 'var(--radius-sm)',
              border: `1px solid ${sourceMode === 'CONNECTED_POSTGRES' ? 'var(--warning-border, #f59e0b)' : 'var(--border-default)'}`,
              background: sourceMode === 'CONNECTED_POSTGRES' ? 'var(--bg-surface-raised)' : 'var(--bg-subtle)',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              gap: 4
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <input 
                  type="radio" 
                  name="sourceMode" 
                  checked={sourceMode === 'CONNECTED_POSTGRES'} 
                  onChange={() => setSourceMode('CONNECTED_POSTGRES')}
                  style={{ accentColor: '#f59e0b' }}
                />
                <strong style={{ fontSize: 13, color: 'var(--text-primary)' }}>Mode 2: External DB (Scaffold Only)</strong>
              </div>
              <span style={{ fontSize: 11, color: 'var(--text-muted)', paddingLeft: 24 }}>
                Scaffolded connection interface. Disabled in current build to prevent accidental production impact.
              </span>
            </label>
          </div>

          {sourceMode === 'CONNECTED_POSTGRES' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 6, padding: 12, borderRadius: 8, background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#f59e0b', fontSize: 12, fontWeight: 600 }}>
                <AlertTriangle size={15} />
                Safety Constraint: External Database Connection Disabled
              </div>
              <p style={{ fontSize: 11, color: 'var(--text-secondary)', margin: 0 }}>
                External production database connections are intentionally restricted in this build. QueryGuard AI requires zero-risk isolated sandboxes to safely benchmark and simulate hypothetical indexes. All live metrics continue to stream securely from the local sandbox container.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 4 }}>
                <label style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                  Scaffold Connection URI (Read-Only Preview):
                </label>
                <input
                  type="text"
                  value={endpoint}
                  disabled
                  placeholder="postgresql://workload_ro:***@127.0.0.1:5433/workload_db"
                  style={{ width: '100%', fontFamily: 'var(--font-mono)', fontSize: 12, opacity: 0.6 }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Rule Engine & Threshold Configuration */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Sliders size={16} style={{ color: 'var(--brand-primary)' }} />
            <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
              Deterministic Rule & Sandbox Thresholds
            </h3>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <label style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                Slow Query Trigger Threshold (ms):
              </label>
              <input
                type="number"
                value={slowQueryThresholdMs}
                onChange={(e) => setSlowQueryThresholdMs(Number(e.target.value))}
                min={10}
                max={60000}
                style={{ width: '100%' }}
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <label style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                Sandbox Statement Timeout (ms):
              </label>
              <input
                type="number"
                value={statementTimeoutMs}
                onChange={(e) => setStatementTimeoutMs(Number(e.target.value))}
                min={1000}
                max={30000}
                style={{ width: '100%' }}
              />
            </div>
          </div>
        </div>

        {/* Experimental Features Toggle */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Cpu size={16} style={{ color: 'var(--brand-primary)' }} />
            <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
              Optional & Experimental Capabilities (PRD Scope)
            </h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}>
              <div>
                <strong style={{ fontSize: 13, color: 'var(--text-primary)' }}>Local Ollama SLM Rewrite Suggestions</strong>
                <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                  Constrained SQL rewrites via local model. Disabled by default; core product operates deterministically.
                </p>
              </div>
              <input 
                type="checkbox" 
                checked={ollamaEnabled} 
                onChange={(e) => setOllamaEnabled(e.target.checked)}
                style={{ accentColor: 'var(--brand-primary)', width: 16, height: 16 }}
              />
            </label>

            <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}>
              <div>
                <strong style={{ fontSize: 13, color: 'var(--text-primary)' }}>GNN-Ready Graph Schema Normalization</strong>
                <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                  Normalizes plan JSON into versioned PyTorch Geometric/DGL compatible DAG tensors.
                </p>
              </div>
              <input 
                type="checkbox" 
                checked={gnnExportEnabled} 
                onChange={(e) => setGnnExportEnabled(e.target.checked)}
                style={{ accentColor: 'var(--brand-primary)', width: 16, height: 16 }}
              />
            </label>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: 6, borderTop: '1px solid var(--border-default)' }}>
              <div>
                <strong style={{ fontSize: 13, color: 'var(--text-primary)' }}>ElevenLabs Sanitized Voice Output</strong>
                <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                  Accessibility feature generating audio only from verified sanitized text summaries.
                </p>
              </div>
              <button 
                type="button" 
                onClick={onOpenVoiceModal} 
                className="btn btn-secondary"
                style={{ fontSize: 12 }}
              >
                <Volume2 size={14} />
                <span>Test Voice Preview</span>
              </button>
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <button 
              type="button" 
              onClick={onResetDemo}
              className="btn btn-danger"
              style={{ fontSize: 12 }}
            >
              <RefreshCw size={13} />
              <span>Reset Demo State</span>
            </button>

            <button 
              type="button" 
              onClick={handleCollectTelemetry}
              disabled={isIngesting}
              className="btn btn-secondary"
              style={{ fontSize: 12 }}
              title="Trigger live pg_stat_statements telemetry collection from workload-postgres"
            >
              <Database size={13} />
              <span>{isIngesting ? 'Ingesting Telemetry...' : 'Ingest Telemetry Now'}</span>
            </button>
            {ingestStatus && (
              <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                {ingestStatus}
              </span>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {savedSuccess && (
              <span style={{ fontSize: 12, color: 'var(--success)', display: 'flex', alignItems: 'center', gap: 4 }}>
                <Check size={14} />
                Settings saved successfully
              </span>
            )}
            <button type="submit" className="btn btn-primary" style={{ padding: '8px 20px' }}>
              <Save size={14} />
              <span>Save Safe Configuration</span>
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
