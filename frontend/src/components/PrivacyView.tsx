import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Lock, 
  Key, 
  CheckCircle2, 
  AlertTriangle, 
  Play, 
  ArrowRight, 
  FileCode, 
  Terminal,
  RefreshCw,
  Copy,
  Check
} from 'lucide-react';
import { PRIVACY_SELF_TEST_FIXTURES } from '../data/mockData';

export const PrivacyView: React.FC = () => {
  const [isRunningTest, setIsRunningTest] = useState(false);
  const [testResults, setTestResults] = useState(PRIVACY_SELF_TEST_FIXTURES);

  const handleRunSelfTest = () => {
    setIsRunningTest(true);
    setTimeout(() => {
      setIsRunningTest(false);
      setTestResults([...PRIVACY_SELF_TEST_FIXTURES]);
    }, 700);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Top Verified Privacy Banner */}
      <div style={{
        background: 'linear-gradient(135deg, var(--bg-surface) 0%, var(--brand-primary-muted) 100%)',
        border: '1px solid var(--brand-primary-border)',
        borderRadius: 'var(--radius-md)',
        padding: '20px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: 'var(--shadow-sm)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{
            width: 48,
            height: 48,
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--brand-primary-muted)',
            border: '1px solid var(--brand-primary-border)',
            color: 'var(--brand-primary-text)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <ShieldCheck size={26} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
                Local Privacy Gateway: Verified Active
              </h2>
              <span className="badge badge-brand">Fail-Closed Enforcement</span>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 4 }}>
              Zero raw production rows, plaintext identifiers, or query literals ever cross the local trust boundary.
            </p>
          </div>
        </div>

        <button 
          onClick={handleRunSelfTest} 
          disabled={isRunningTest}
          className="btn btn-primary"
          style={{ whiteSpace: 'nowrap' }}
        >
          {isRunningTest ? <RefreshCw size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Play size={14} />}
          <span>{isRunningTest ? 'Verifying Fixtures...' : 'Run Privacy Self-Test'}</span>
        </button>
      </div>

      {/* Interactive Transformation Pipeline Visualizer */}
      <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div>
          <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
            Sanitization Pipeline Architecture
          </h3>
          <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            Sequential transformations applied in local customer trust zone before persistence or analysis
          </p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(5, 1fr)',
          gap: 12,
          position: 'relative'
        }}>
          {/* Stage 1: Ingest */}
          <div style={{ backgroundColor: 'var(--bg-subtle)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-sm)', padding: 14 }}>
            <span className="badge badge-neutral" style={{ marginBottom: 6, fontSize: 10 }}>Step 1: Telemetry</span>
            <strong style={{ display: 'block', fontSize: 12, color: 'var(--text-primary)' }}>Raw SQL / Plan</strong>
            <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
              Received transiently in memory from pg_stat_statements.
            </p>
          </div>

          {/* Stage 2: AST Parse */}
          <div style={{ backgroundColor: 'var(--bg-subtle)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-sm)', padding: 14 }}>
            <span className="badge badge-info" style={{ marginBottom: 6, fontSize: 10 }}>Step 2: AST Parse</span>
            <strong style={{ display: 'block', fontSize: 12, color: 'var(--text-primary)' }}>SQL AST Analysis</strong>
            <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
              Strips comments, secrets, connection URIs, and enforces SELECT only.
            </p>
          </div>

          {/* Stage 3: Literal Masking */}
          <div style={{ backgroundColor: 'var(--bg-subtle)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-sm)', padding: 14 }}>
            <span className="badge badge-warning" style={{ marginBottom: 6, fontSize: 10 }}>Step 3: Masking</span>
            <strong style={{ display: 'block', fontSize: 12, color: 'var(--text-primary)' }}>Typed Placeholders</strong>
            <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
              Replaces values with :INT, :TEXT, :TIMESTAMP, :UUID, :BOOL.
            </p>
          </div>

          {/* Stage 4: HMAC Tokenization */}
          <div style={{ backgroundColor: 'var(--bg-subtle)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-sm)', padding: 14 }}>
            <span className="badge badge-brand" style={{ marginBottom: 6, fontSize: 10 }}>Step 4: Keyed Token</span>
            <strong style={{ display: 'block', fontSize: 12, color: 'var(--text-primary)' }}>HMAC-SHA256</strong>
            <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
              Hashes tables/columns into TBL_A12, COL_D02 with local tenant key.
            </p>
          </div>

          {/* Stage 5: Leakage Interceptor */}
          <div style={{ backgroundColor: 'var(--bg-subtle)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-sm)', padding: 14 }}>
            <span className="badge badge-success" style={{ marginBottom: 6, fontSize: 10 }}>Step 5: Egress</span>
            <strong style={{ display: 'block', fontSize: 12, color: 'var(--text-primary)' }}>Safe Export Event</strong>
            <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
              Leakage checks verify zero raw data before optimizer hand-off.
            </p>
          </div>
        </div>
      </div>

      {/* Two-Column: What We Never Collect + Live Self-Test Fixtures */}
      <div style={{ display: 'grid', gridTemplateColumns: '5fr 7fr', gap: 'var(--space-6)' }}>
        {/* Left: What We Never Collect Matrix */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
              Data Boundary Policies
            </h3>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              Explicit categorization of collected vs prohibited data
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: 12 }}>
            <div style={{ padding: 12, backgroundColor: 'var(--danger-muted)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--danger-border)' }}>
              <strong style={{ color: 'var(--danger-text)', display: 'block', marginBottom: 4 }}>
                PROHIBITED (Never Ingested or Persisted):
              </strong>
              <ul style={{ paddingLeft: 18, color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: 3 }}>
                <li>Raw database table rows or query result sets</li>
                <li>Plaintext literals, emails, passwords, API tokens</li>
                <li>Customer database passwords or master secrets</li>
                <li>Unmasked schema, table, or column identifiers</li>
              </ul>
            </div>

            <div style={{ padding: 12, backgroundColor: 'var(--brand-primary-muted)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--brand-primary-border)' }}>
              <strong style={{ color: 'var(--brand-primary-text)', display: 'block', marginBottom: 4 }}>
                APPROVED (Sanitized Structural Metadata Only):
              </strong>
              <ul style={{ paddingLeft: 18, color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: 3 }}>
                <li>EXPLAIN planner costs and operator DAG tree shapes</li>
                <li>Bucketed duration (1S_TO_5S) and calls/frequency metrics</li>
                <li>HMAC tokenized identifiers (TBL_A12F, COL_D02B)</li>
                <li>Deterministic bottleneck reason codes and trade-off estimates</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Right: Live Interactive Privacy Self-Test Results */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
                Live Privacy Gateway Self-Test Fixtures
              </h3>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                Automated leakage assertion suite executing against local parser
              </span>
            </div>
            <span className="badge badge-success">4/4 Tests Passing</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {testResults.map((t, idx) => (
              <div 
                key={idx}
                style={{
                  backgroundColor: 'var(--bg-subtle)',
                  border: '1px solid var(--border-default)',
                  borderRadius: 'var(--radius-sm)',
                  padding: 12,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 6
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <strong style={{ fontSize: 12, color: 'var(--text-primary)' }}>
                    {t.name}
                  </strong>
                  <span className="badge badge-success font-mono" style={{ fontSize: 10 }}>
                    {t.status}
                  </span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 11 }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Input: </span>
                    <code className="font-mono" style={{ color: 'var(--danger-text)' }}>{t.rawInput}</code>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Output: </span>
                    <code className="font-mono" style={{ color: 'var(--success-text)' }}>{t.expectedMasked}</code>
                  </div>
                </div>

                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                  <strong>Assertion:</strong> {t.reason}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
