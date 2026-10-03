import React, { useState } from 'react';
import { 
  X, 
  CheckCircle2, 
  XCircle, 
  ShieldCheck, 
  AlertTriangle, 
  UserCheck, 
  FileCode,
  Lock
} from 'lucide-react';
import { Recommendation, User } from '../types/queryguard';

interface ApprovalDrawerProps {
  recommendation: Recommendation | null;
  decisionType: 'APPROVED' | 'REJECTED' | null;
  currentUser: User;
  isOpen: boolean;
  onClose: () => void;
  onSubmitDecision: (recId: string, decision: 'APPROVED' | 'REJECTED', reason?: string) => void;
}

export const ApprovalDrawer: React.FC<ApprovalDrawerProps> = ({
  recommendation,
  decisionType,
  currentUser,
  isOpen,
  onClose,
  onSubmitDecision
}) => {
  const [acknowledgedSafety, setAcknowledgedSafety] = useState(false);
  const [reason, setReason] = useState('');
  const [rejectionCategory, setRejectionCategory] = useState('Insufficient confidence');

  if (!isOpen || !recommendation || !decisionType) return null;

  const isDba = currentUser.role === 'DBA';
  const isApprove = decisionType === 'APPROVED';

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isApprove && !acknowledgedSafety) return;
    
    const finalReason = isApprove 
      ? (reason.trim() || 'Approved based on HypoPG cost reduction and low write risk.')
      : `${rejectionCategory}: ${reason.trim() || 'Optimization declined by reviewer.'}`;

    onSubmitDecision(recommendation.id, decisionType, finalReason);
    onClose();
  };

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        {/* Drawer Header */}
        <div style={{
          padding: '20px 24px',
          borderBottom: '1px solid var(--border-default)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {isApprove ? (
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
                <CheckCircle2 size={18} />
              </div>
            ) : (
              <div style={{
                width: 32,
                height: 32,
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--danger-muted)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--danger)'
              }}>
                <XCircle size={18} />
              </div>
            )}
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
                {isApprove ? 'Human DBA Approval Gate' : 'Reject Recommendation'}
              </h2>
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                Actor: {currentUser.name} ({currentUser.role})
              </span>
            </div>
          </div>

          <button onClick={onClose} className="btn btn-ghost" style={{ padding: 4 }}>
            <X size={16} />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 20, flex: 1 }}>
          {/* Target Summary Card */}
          <div style={{
            backgroundColor: 'var(--bg-subtle)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-sm)',
            padding: 14,
            display: 'flex',
            flexDirection: 'column',
            gap: 6
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <strong style={{ fontSize: 13, color: 'var(--text-primary)' }}>
                {recommendation.title}
              </strong>
              <span className="badge badge-brand font-mono">{recommendation.actionType}</span>
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              Risk: <strong style={{ color: 'var(--success)' }}>{recommendation.riskLevel}</strong> • Est. Improvement: <strong style={{ color: 'var(--brand-primary)' }}>70–85%</strong>
            </div>
          </div>

          {/* Role Check Alert if not DBA */}
          {!isDba && (
            <div style={{
              backgroundColor: 'var(--warning-muted)',
              border: '1px solid rgba(245, 185, 66, 0.4)',
              borderRadius: 'var(--radius-sm)',
              padding: 12,
              display: 'flex',
              gap: 10,
              fontSize: 12,
              color: 'var(--warning)'
            }}>
              <AlertTriangle size={18} style={{ flexShrink: 0 }} />
              <div>
                <strong>Role Authorization Warning:</strong> Your current actor role is <code>{currentUser.role}</code>. Enterprise policy designates only <code>DBA</code> to record binding change approvals. Please switch roles to <strong>Priya Sharma (DBA)</strong> in the top bar to proceed.
              </div>
            </div>
          )}

          {isApprove ? (
            <>
              {/* Production Safety Acknowledgment */}
              <div style={{
                backgroundColor: 'var(--bg-surface-raised)',
                border: '1px solid var(--border-strong)',
                borderRadius: 'var(--radius-sm)',
                padding: 14,
                display: 'flex',
                flexDirection: 'column',
                gap: 10
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--brand-primary)', fontWeight: 600, fontSize: 12 }}>
                  <ShieldCheck size={16} />
                  <span>Mandatory Safety Confirmation</span>
                </div>
                <label style={{ display: 'flex', alignItems: 'flex-start', gap: 10, cursor: 'pointer', fontSize: 12, color: 'var(--text-secondary)' }}>
                  <input
                    type="checkbox"
                    checked={acknowledgedSafety}
                    onChange={(e) => setAcknowledgedSafety(e.target.checked)}
                    style={{ marginTop: 2, accentColor: 'var(--brand-primary)' }}
                    required
                  />
                  <span>
                    I confirm that I have reviewed the simulated plan delta and understand that <strong>this approval does NOT deploy changes to production</strong>. It generates a locally resolved change script for human DBA execution.
                  </span>
                </label>
              </div>

              {/* Optional Approval Note */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <label style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 500 }}>
                  Approval Note (Recorded in Immutable Audit Log):
                </label>
                <textarea
                  rows={3}
                  placeholder="e.g. Approved for execution during next maintenance window. Verified write overhead is acceptable."
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  style={{ width: '100%', resize: 'vertical' }}
                />
              </div>
            </>
          ) : (
            <>
              {/* Rejection Category & Reason */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <label style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 500 }}>
                  Rejection Reason Category:
                </label>
                <select
                  value={rejectionCategory}
                  onChange={(e) => setRejectionCategory(e.target.value)}
                  style={{ width: '100%' }}
                >
                  <option value="Insufficient confidence">Insufficient simulation confidence</option>
                  <option value="Write overhead unacceptable">Write overhead unacceptable for table SLA</option>
                  <option value="Existing index covers this pattern">Existing index already covers pattern</option>
                  <option value="Schema migration planned">Upcoming schema redesign renders index obsolete</option>
                  <option value="Other / Custom">Other operational concern</option>
                </select>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <label style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 500 }}>
                  Forensic Notes (Used for Ranker Feedback):
                </label>
                <textarea
                  rows={3}
                  placeholder="Provide feedback so QueryGuard ranker can adjust future score weights..."
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  style={{ width: '100%', resize: 'vertical' }}
                  required
                />
              </div>
            </>
          )}

          {/* Footer Submit Buttons */}
          <div style={{ marginTop: 'auto', display: 'flex', justifyContent: 'flex-end', gap: 10, paddingTop: 16, borderTop: '1px solid var(--border-default)' }}>
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button
              type="submit"
              disabled={(!isDba) || (isApprove && !acknowledgedSafety)}
              className={isApprove ? 'btn btn-primary' : 'btn btn-danger'}
            >
              {isApprove ? (
                <>
                  <CheckCircle2 size={14} />
                  <span>Confirm Approval (Generate Script)</span>
                </>
              ) : (
                <>
                  <XCircle size={14} />
                  <span>Confirm Rejection</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
