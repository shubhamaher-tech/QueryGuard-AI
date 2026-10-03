import React, { useState } from 'react';
import { 
  FileText, 
  Search, 
  Filter, 
  Download, 
  ShieldCheck, 
  Copy, 
  Check, 
  Eye, 
  X,
  Code,
  Calendar,
  UserCheck
} from 'lucide-react';
import { AuditLogItem } from '../types/queryguard';

interface AuditLogsViewProps {
  logs: AuditLogItem[];
}

export const AuditLogsView: React.FC<AuditLogsViewProps> = ({ logs }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [eventFilter, setEventFilter] = useState('ALL');
  const [selectedLog, setSelectedLog] = useState<AuditLogItem | null>(null);
  const [copiedJson, setCopiedJson] = useState(false);

  const filteredLogs = logs.filter(log => {
    const matchesSearch = 
      log.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.actorName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.entityId.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesEvent = eventFilter === 'ALL' || log.eventType === eventFilter;

    return matchesSearch && matchesEvent;
  });

  const handleCopyJson = (obj: any) => {
    navigator.clipboard.writeText(JSON.stringify(obj, null, 2));
    setCopiedJson(true);
    setTimeout(() => setCopiedJson(false), 2000);
  };

  const handleExportAll = () => {
    const blob = new Blob([JSON.stringify(filteredLogs, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `queryguard_sanitized_audit_${Date.now()}.json`;
    a.click();
  };

  const getEventBadgeClass = (eventType: AuditLogItem['eventType']) => {
    switch (eventType) {
      case 'APPROVED':
        return 'badge-success';
      case 'REJECTED':
      case 'PRIVACY_BLOCKED':
        return 'badge-danger';
      case 'SIMULATED':
        return 'badge-brand';
      case 'MASKED':
      case 'ANALYZED':
        return 'badge-info';
      default:
        return 'badge-neutral';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <h1 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>
              Immutable Audit Logs
            </h1>
            <span className="badge badge-brand">
              {filteredLogs.length} Events Recorded
            </span>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4 }}>
            Tamper-resistant audit record of telemetry ingestion, masking, analysis, simulation, and DBA decisions.
          </p>
        </div>

        <button 
          onClick={handleExportAll}
          className="btn btn-secondary"
          style={{ fontSize: 12, padding: '7px 14px' }}
        >
          <Download size={14} />
          <span>Export Sanitized Audit JSON</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="card" style={{ padding: '12px 16px', display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1, minWidth: 260, position: 'relative' }}>
          <Search size={15} style={{ position: 'absolute', left: 10, color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Search audit descriptions, actors, or entity IDs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ width: '100%', paddingLeft: 32 }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Event Type:</span>
          <select 
            value={eventFilter} 
            onChange={(e) => setEventFilter(e.target.value)}
            style={{ fontSize: 12 }}
          >
            <option value="ALL">All Event Types</option>
            <option value="INGESTED">Ingested</option>
            <option value="MASKED">Masked</option>
            <option value="ANALYZED">Analyzed</option>
            <option value="SIMULATED">Simulated</option>
            <option value="APPROVED">Approved</option>
            <option value="REJECTED">Rejected</option>
            <option value="PRIVACY_BLOCKED">Privacy Blocked</option>
          </select>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Event Type</th>
              <th>Actor & Role</th>
              <th>Target Entity</th>
              <th>Event Summary</th>
              <th>Privacy Status</th>
              <th style={{ textAlign: 'right' }}>Payload</th>
            </tr>
          </thead>
          <tbody>
            {filteredLogs.map(log => (
              <tr key={log.id}>
                <td style={{ whiteSpace: 'nowrap' }}>
                  <span className="font-mono tabular-nums" style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    {log.timestamp}
                  </span>
                </td>

                <td>
                  <span className={`badge ${getEventBadgeClass(log.eventType)}`}>
                    {log.eventType}
                  </span>
                </td>

                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)' }}>
                      {log.actorName}
                    </span>
                    <span className="badge badge-neutral" style={{ fontSize: 10 }}>
                      {log.actorRole}
                    </span>
                  </div>
                </td>

                <td>
                  <span className="font-mono" style={{ fontSize: 11, color: 'var(--brand-primary)' }}>
                    {log.entityId}
                  </span>
                </td>

                <td style={{ maxWidth: 360 }}>
                  <span style={{ fontSize: 12, color: 'var(--text-primary)' }}>
                    {log.description}
                  </span>
                </td>

                <td>
                  <span className="badge badge-brand" style={{ fontSize: 10 }}>
                    <ShieldCheck size={11} />
                    {log.privacyStatus}
                  </span>
                </td>

                <td style={{ textAlign: 'right' }}>
                  <button 
                    onClick={() => setSelectedLog(log)}
                    className="btn btn-secondary" 
                    style={{ padding: '4px 8px', fontSize: 11 }}
                  >
                    <Eye size={12} />
                    <span>Inspect</span>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Log Detail Inspector Modal */}
      {selectedLog && (
        <div className="drawer-backdrop" onClick={() => setSelectedLog(null)} style={{ justifyContent: 'center', alignItems: 'center' }}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()} style={{ padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <Code size={18} style={{ color: 'var(--brand-primary)' }} />
                <div>
                  <h3 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>
                    Audit Event Payload: {selectedLog.id}
                  </h3>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    {selectedLog.timestamp} • {selectedLog.eventType}
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <button 
                  onClick={() => handleCopyJson(selectedLog)}
                  className="btn btn-secondary" 
                  style={{ fontSize: 11, padding: '4px 8px' }}
                >
                  {copiedJson ? <Check size={12} style={{ color: 'var(--success)' }} /> : <Copy size={12} />}
                  <span>{copiedJson ? 'Copied' : 'Copy JSON'}</span>
                </button>
                <button onClick={() => setSelectedLog(null)} className="btn btn-ghost" style={{ padding: 4 }}>
                  <X size={16} />
                </button>
              </div>
            </div>

            <pre className="code-block" style={{ maxHeight: 360 }}>
              {JSON.stringify(selectedLog, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};
