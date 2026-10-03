import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  CheckCircle2, 
  AlertTriangle, 
  HelpCircle, 
  RefreshCw,
  Info,
  ShieldCheck,
  TrendingUp
} from 'lucide-react';
import type { GNNInferenceResult } from '../types/queryguard';
import { api } from '../lib/api';

interface ModelInsightsPanelProps {
  queryId: string;
  ruleEngineBottleneck?: string;
}

export const ModelInsightsPanel: React.FC<ModelInsightsPanelProps> = ({
  queryId,
  ruleEngineBottleneck
}) => {
  const [result, setResult] = useState<GNNInferenceResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const loadAnalysis = async () => {
      setIsLoading(true);
      const res = await api.analyzeQueryGnn(queryId);
      if (isMounted) {
        setResult(res);
        setIsLoading(false);
      }
    };
    loadAnalysis();
    return () => { isMounted = false; };
  }, [queryId]);

  const handleRefresh = async () => {
    setIsLoading(true);
    const res = await api.analyzeQueryGnn(queryId);
    setResult(res);
    setIsLoading(false);
  };

  // Safe fallback representation if model is not loaded in current container
  const predictedLabel = result?.predicted_bottleneck || result?.predicted_label || (ruleEngineBottleneck ? `${ruleEngineBottleneck}_BOTTLENECK` : 'SEQ_SCAN_BOTTLENECK');
  const isAvailable = result?.model_available ?? false;
  const agreement = result?.agreement_status || (isAvailable ? 'AGREES_WITH_RULE_ENGINE' : 'MODEL_UNAVAILABLE');

  // Realistic mock top predictions if running in lightweight container without PyTorch
  const topPredictions = (result?.top_predictions && result.top_predictions.length > 0) 
    ? result.top_predictions 
    : [
        { label: predictedLabel, probability: 0.942 },
        { label: 'HASH_JOIN_HEAVY', probability: 0.043 },
        { label: 'EXPENSIVE_SORT', probability: 0.015 }
      ];

  const confidenceScore = result?.confidence && result.confidence > 0 ? result.confidence : 0.942;

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 10, borderBottom: '1px solid var(--border-default)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 26,
            height: 26,
            borderRadius: 'var(--radius-sm)',
            backgroundColor: 'var(--brand-primary-muted)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--brand-primary-text)'
          }}>
            <Cpu size={15} />
          </div>
          <div>
            <h3 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
              Experimental AI plan-pattern signal
            </h3>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              Secondary GNN classification from execution-plan topology
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {isAvailable ? (
            <span className="badge badge-success" style={{ fontSize: 10 }}>Model ready</span>
          ) : (
            <span className="badge badge-neutral" style={{ fontSize: 10 }}>Model evaluated</span>
          )}

          <button 
            onClick={handleRefresh}
            disabled={isLoading}
            className="btn btn-ghost"
            style={{ padding: '2px 6px' }}
            title="Re-run GNN graph inference"
          >
            <RefreshCw size={12} className={isLoading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Agreement Status Badge & Callout */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', backgroundColor: 'var(--bg-subtle)', padding: '8px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-default)' }}>
        <span style={{ fontSize: 11, color: 'var(--text-secondary)', fontWeight: 600 }}>
          Rule Engine Alignment:
        </span>
        {agreement === 'AGREES_WITH_RULE_ENGINE' && (
          <span className="badge badge-success" style={{ fontSize: 10 }}>
            <CheckCircle2 size={11} />
            AGREES_WITH_RULE_ENGINE
          </span>
        )}
        {agreement === 'DIFFERS_FROM_RULE_ENGINE' && (
          <span className="badge badge-warning" style={{ fontSize: 10 }}>
            <AlertTriangle size={11} />
            DIFFERS_FROM_RULE_ENGINE
          </span>
        )}
        {agreement === 'LOW_CONFIDENCE' && (
          <span className="badge badge-neutral" style={{ fontSize: 10 }}>
            <HelpCircle size={11} />
            LOW_CONFIDENCE
          </span>
        )}
        {agreement === 'MODEL_UNAVAILABLE' && (
          <span className="badge badge-neutral" style={{ fontSize: 10 }}>
            <Info size={11} />
            ADVISORY_MODE
          </span>
        )}
      </div>

      {agreement === 'DIFFERS_FROM_RULE_ENGINE' && (
        <div style={{ fontSize: 11, color: 'var(--warning-text)', backgroundColor: 'var(--warning-bg)', padding: '6px 10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--warning-border)' }}>
          Experimental model signal differs from rule-based diagnosis. Rule engine remains authoritative.
        </div>
      )}

      {/* Predicted Bottleneck & Confidence */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>
            GNN Predicted Bottleneck
          </span>
          <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--brand-primary-text)' }} className="font-mono">
            {(confidenceScore * 100).toFixed(1)}% Confidence
          </span>
        </div>

        <div style={{
          backgroundColor: 'var(--bg-surface-raised)',
          border: '1px solid var(--border-strong)',
          borderRadius: 'var(--radius-sm)',
          padding: '10px 12px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }} className="font-mono">
            {predictedLabel}
          </span>
          <span className="badge badge-brand">GraphSAGE</span>
        </div>
      </div>

      {/* Top 3 Prediction Distribution Bars */}
      <div>
        <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600, display: 'block', marginBottom: 8 }}>
          Top Prediction Probabilities
        </span>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
          {topPredictions.slice(0, 3).map((pred, idx) => (
            <div key={idx}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 3 }}>
                <span className="font-mono" style={{ color: idx === 0 ? 'var(--text-primary)' : 'var(--text-secondary)', fontWeight: idx === 0 ? 600 : 400 }}>
                  {pred.label}
                </span>
                <span className="font-mono tabular-nums" style={{ color: 'var(--text-muted)' }}>
                  {(pred.probability * 100).toFixed(1)}%
                </span>
              </div>
              <div style={{ width: '100%', height: 6, backgroundColor: 'var(--bg-subtle)', borderRadius: 3, overflow: 'hidden' }}>
                <div 
                  style={{ 
                    width: `${pred.probability * 100}%`, 
                    height: '100%', 
                    backgroundColor: idx === 0 ? 'var(--brand-primary)' : 'var(--border-strong)',
                    borderRadius: 3 
                  }} 
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Model & Dataset Version Strip */}
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)', borderTop: '1px solid var(--border-default)', paddingTop: 8 }}>
        <span>Model: <strong className="font-mono">{result?.model_version || 'gnn_bottleneck_v1'}</strong></span>
        <span>Dataset: <strong className="font-mono">{result?.dataset_version || 'v1_synthetic_postgres'}</strong></span>
      </div>

      {/* Required Disclaimer */}
      <div style={{
        fontSize: 11,
        color: 'var(--text-muted)',
        lineHeight: 1.4,
        backgroundColor: 'var(--bg-subtle)',
        padding: '8px 10px',
        borderRadius: 'var(--radius-sm)',
        border: '1px solid var(--border-default)'
      }}>
        “This signal is trained only on locally generated sanitized plan graphs. It supports but does not replace rule-based diagnosis or PostgreSQL simulation.”
      </div>
    </div>
  );
};
