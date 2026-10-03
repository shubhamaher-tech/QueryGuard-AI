import React, { useState } from 'react';
import { 
  Volume2, 
  X, 
  ShieldCheck, 
  Play, 
  Pause, 
  Check, 
  Copy,
  AlertCircle
} from 'lucide-react';

interface VoiceSummaryDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export const VoiceSummaryDialog: React.FC<VoiceSummaryDialogProps> = ({ isOpen, onClose }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const sanitizedText = `QueryGuard Alert Summary:
A high-impact bottleneck was diagnosed on query fingerprint FP_7C91E88B. 
Sequential scan on table token TBL_SALES with 12.4 million rows contributed to an average execution time of 2.45 seconds. 
A composite B-tree index on column token COL_REGION_ID and COL_TX_DATE was simulated in HypoPG. 
The simulated planner cost decreased by 83.3%, from 182,341 to 30,510. 
Estimated write overhead is 1 to 2 milliseconds per write. 
Status: Validated, awaiting explicit DBA human approval. No production changes were applied.`;

  const handleCopy = () => {
    navigator.clipboard.writeText(sanitizedText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleTogglePlay = () => {
    if (isPlaying) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
    } else {
      if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(sanitizedText);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.onend = () => setIsPlaying(false);
        utterance.onerror = () => setIsPlaying(false);
        window.speechSynthesis.speak(utterance);
        setIsPlaying(true);
      } else {
        alert('Web Speech API is not supported in this browser.');
      }
    }
  };

  return (
    <div className="drawer-backdrop" onClick={onClose} style={{ justifyContent: 'center', alignItems: 'center' }}>
      <div className="modal-dialog" onClick={(e) => e.stopPropagation()} style={{ padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 32,
              height: 32,
              borderRadius: 'var(--radius-sm)',
              backgroundColor: 'var(--brand-primary-muted)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--brand-primary)'
            }}>
              <Volume2 size={18} />
            </div>
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)' }}>
                Sanitized Voice Summary (ElevenLabs / Audio Preview)
              </h2>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                Optional accessibility feature (PRD FR-13)
              </span>
            </div>
          </div>

          <button onClick={onClose} className="btn btn-ghost" style={{ padding: 4 }}>
            <X size={16} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Outbound Privacy Verification */}
          <div style={{
            backgroundColor: 'var(--bg-subtle)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-sm)',
            padding: 12,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            fontSize: 12
          }}>
            <ShieldCheck size={18} style={{ color: 'var(--brand-primary)', flexShrink: 0 }} />
            <span style={{ color: 'var(--text-secondary)' }}>
              <strong>Zero-Leakage Assurance:</strong> Outbound voice payload contains zero database credentials, zero raw SQL queries, and zero unmasked business identifiers. Only the sanitized text below is processed.
            </span>
          </div>

          {/* Outbound Text Preview */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 500 }}>
                Exact Outbound Sanitized Text:
              </label>
              <button onClick={handleCopy} className="btn btn-secondary" style={{ fontSize: 11, padding: '3px 8px' }}>
                {copied ? <Check size={12} style={{ color: 'var(--success)' }} /> : <Copy size={12} />}
                <span>{copied ? 'Copied' : 'Copy Text'}</span>
              </button>
            </div>

            <pre className="code-block" style={{ fontSize: 12, whiteSpace: 'pre-wrap', maxHeight: 180 }}>
              {sanitizedText}
            </pre>
          </div>

          {/* Audio Player Controls */}
          <div style={{
            backgroundColor: 'var(--bg-surface-raised)',
            border: '1px solid var(--border-strong)',
            borderRadius: 'var(--radius-sm)',
            padding: '14px 18px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <button 
                onClick={handleTogglePlay}
                className="btn btn-primary"
                style={{ borderRadius: '50%', width: 40, height: 40, padding: 0 }}
                title={isPlaying ? "Pause summary playback" : "Listen to sanitized summary"}
              >
                {isPlaying ? <Pause size={18} /> : <Play size={18} style={{ marginLeft: 2 }} />}
              </button>
              <div>
                <strong style={{ fontSize: 13, color: 'var(--text-primary)' }}>
                  {isPlaying ? 'Synthesizing voice playback...' : 'Listen to Sanitized Summary'}
                </strong>
                <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                  Clear, accessible operational alert summary for on-call engineers.
                </p>
              </div>
            </div>

            <span className="badge badge-brand" style={{ fontSize: 11 }}>
              {isPlaying ? 'Playing Audio' : 'Ready'}
            </span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 4 }}>
            <button onClick={onClose} className="btn btn-secondary">
              Close Preview
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
