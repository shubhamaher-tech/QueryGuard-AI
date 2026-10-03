import React from 'react';
import { 
  ShieldCheck, 
  Database, 
  Activity, 
  Sliders, 
  FileText, 
  Lock, 
  UserCheck, 
  RefreshCw,
  Layers,
  Terminal,
  Zap,
  Server,
  Brain
} from 'lucide-react';
import type { User, DataSource } from '../types/queryguard';

interface NavigationProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  currentUser: User;
  users: User[];
  onChangeUser: (user: User) => void;
  dataSource: DataSource;
  onResetDemo: () => void;
  onOpenPrivacyModal: () => void;
  children?: React.ReactNode;
}

export const Navigation: React.FC<NavigationProps> = ({
  currentTab,
  onSelectTab,
  currentUser,
  users,
  onChangeUser,
  dataSource,
  onResetDemo,
  onOpenPrivacyModal,
  children
}) => {
  const navItems = [
    { id: 'dashboard', label: 'Overview', icon: Activity },
    { id: 'analyze', label: 'Analyze Query', icon: Terminal, badge: 'Interactive' },
    { id: 'live', label: 'Live Workload', icon: Zap, badge: 'Live' },
    { id: 'queries', label: 'Slow Queries', icon: Database, badge: '4' },
    { id: 'recommendations', label: 'Recommendations', icon: Layers, badge: '3' },
    { id: 'simulations', label: 'Simulations', icon: Sliders, badge: 'HypoPG' },
    { id: 'models', label: 'Model Insights', icon: Brain, badge: 'GNN' },
    { id: 'audit', label: 'Audit Trail', icon: FileText },
    { id: 'benchmarks', label: 'Benchmark Data', icon: Server, badge: 'TPC-H' },
    { id: 'settings', label: 'Settings', icon: Lock },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      {/* Top Bar Header */}
      <header className="top-bar" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 20px', minHeight: 56, backgroundColor: '#FFFFFF', borderBottom: '1px solid #E2E8F0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          {/* Logo / Brand */}
          <div 
            onClick={() => onSelectTab('dashboard')}
            style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}
          >
            <div style={{
              width: 32,
              height: 32,
              borderRadius: 'var(--radius-sm)',
              backgroundColor: 'var(--brand-primary-muted)',
              border: '1px solid var(--brand-primary-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--brand-primary-text)',
              fontWeight: 800,
              fontSize: 13,
              letterSpacing: '-0.03em'
            }}>
              QG
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontWeight: 700, fontSize: 15, letterSpacing: '-0.02em', color: 'var(--text-heading)' }}>
                  QueryGuard AI
                </span>
                <span className="badge badge-brand" style={{ fontSize: 10, padding: '2px 7px' }}>
                  Enterprise DBA
                </span>
              </div>
            </div>
          </div>

          <div style={{ height: 20, width: 1, backgroundColor: 'var(--border-default)', margin: '0 4px' }} />

          {/* Connection status indicator */}
          <div 
            style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 7, 
              backgroundColor: '#F0FDF4', 
              padding: '4px 10px', 
              borderRadius: 'var(--radius-sm)',
              border: '1px solid #BBF7D0',
              fontSize: 12
            }}
          >
            <span style={{ 
              width: 8, 
              height: 8, 
              borderRadius: '50%', 
              backgroundColor: dataSource.connectionStatus === 'CONNECTED' ? '#16A34A' : '#DC2626',
              boxShadow: dataSource.connectionStatus === 'CONNECTED' ? '0 0 6px rgba(22, 163, 74, 0.4)' : 'none',
              display: 'inline-block'
            }} />
            <span style={{ color: '#15803D', fontWeight: 600 }}>
              {dataSource.connectionStatus === 'CONNECTED' ? 'Connected' : 'Offline'}
            </span>
          </div>

          {/* Persistent Environment Label */}
          <div 
            style={{ 
              padding: '4px 10px', 
              fontSize: 11,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              backgroundColor: '#FFFBEB',
              border: '1px solid #FDE68A',
              color: '#D97706',
              borderRadius: 'var(--radius-sm)',
              fontWeight: 600
            }}
            title="Local sandbox — synthetic benchmark data, safe for experimentation"
          >
            <Database size={13} />
            <span>Local Sandbox</span>
          </div>

          {/* Persistent Privacy Label */}
          <button 
            onClick={onOpenPrivacyModal}
            style={{ 
              cursor: 'pointer', 
              padding: '4px 10px', 
              fontSize: 11,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              backgroundColor: '#F0FDFA',
              border: '1px solid #99F6E4',
              color: '#0F766E',
              borderRadius: 'var(--radius-sm)',
              fontWeight: 600
            }}
            title="Privacy-Safe Metadata — All identifiers tokenized and literals stripped"
          >
            <ShieldCheck size={14} />
            <span>Privacy Protected</span>
          </button>

          {/* Last Updated Time */}
          <div style={{ fontSize: 11, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
            <span>•</span>
            <span>Updated just now</span>
          </div>
        </div>

        {/* Right side controls: Action CTA, Role selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          {/* Analyze Query Fast CTA */}
          <button
            onClick={() => onSelectTab('analyze')}
            className="btn btn-primary"
            style={{ padding: '7px 16px', fontSize: 12, fontWeight: 600 }}
            title="Open interactive query analyzer workspace"
          >
            <Terminal size={14} />
            <span>Analyze Query</span>
          </button>

          <button 
            onClick={onResetDemo}
            className="btn btn-secondary" 
            style={{ fontSize: 12, padding: '6px 12px' }}
            title="Reset seeded benchmark data and status"
          >
            <RefreshCw size={13} />
            <span>Reset Demo</span>
          </button>

          {/* User / Role Switcher */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, backgroundColor: '#FFFFFF', padding: '3px 8px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-default)' }}>
            <UserCheck size={14} style={{ color: 'var(--brand-primary-text)' }} />
            <select
              value={currentUser.id}
              onChange={(e) => {
                const found = users.find(u => u.id === e.target.value);
                if (found) onChangeUser(found);
              }}
              style={{
                backgroundColor: 'transparent',
                border: 'none',
                padding: '2px 4px',
                fontSize: 12,
                fontWeight: 600,
                color: 'var(--text-primary)',
                cursor: 'pointer'
              }}
            >
              {users.map(u => (
                <option key={u.id} value={u.id} style={{ backgroundColor: '#FFFFFF', color: '#1E293B' }}>
                  {u.name} ({u.role})
                </option>
              ))}
            </select>
          </div>
        </div>
      </header>

      {/* Sidebar + Main Viewport Layout */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <aside className="sidebar" style={{ width: 240, minWidth: 240, backgroundColor: '#FFFFFF', borderRight: '1px solid #E2E8F0', display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: 'var(--space-4) var(--space-4) var(--space-2)' }}>
            <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: 8 }}>
              Navigation
            </div>
          </div>

          <nav style={{ display: 'flex', flexDirection: 'column', gap: 3, padding: '0 var(--space-2)' }}>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectTab(item.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '9px 12px',
                    borderRadius: 'var(--radius-sm)',
                    backgroundColor: isActive ? '#F0FDFA' : 'transparent',
                    color: isActive ? '#0F766E' : '#64748B',
                    border: isActive ? '1px solid #CCFBF1' : '1px solid transparent',
                    fontWeight: isActive ? 600 : 500,
                    fontSize: 13,
                    textAlign: 'left',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.backgroundColor = '#F1F5F9';
                      e.currentTarget.style.color = '#1E293B';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.backgroundColor = 'transparent';
                      e.currentTarget.style.color = '#64748B';
                    }
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <Icon 
                      size={16} 
                      style={{ 
                        color: isActive ? '#0F766E' : '#64748B',
                        transition: 'color 0.15s ease'
                      }} 
                    />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span style={{
                      fontSize: 10,
                      padding: '1px 6px',
                      borderRadius: 'var(--radius-full)',
                      backgroundColor: isActive ? 'var(--brand-primary-muted)' : 'var(--bg-subtle)',
                      color: isActive ? 'var(--brand-primary-text)' : 'var(--text-muted)',
                      fontWeight: 700
                    }}>
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* Bottom Trust & Compliance Card */}
          <div style={{ marginTop: 'auto', padding: 'var(--space-3)', borderTop: '1px solid #E2E8F0', display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{
              backgroundColor: '#F0FDF4',
              borderRadius: 'var(--radius-sm)',
              padding: '10px 12px',
              border: '1px solid #BBF7D0',
              fontSize: 11,
              lineHeight: 1.4
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#16A34A', fontWeight: 700, marginBottom: 2 }}>
                <ShieldCheck size={13} />
                <span>DBA Review Required</span>
              </div>
              <p style={{ color: '#166534', fontSize: 10, margin: 0 }}>
                Zero automatic production changes. Every suggestion must be approved by a human DBA.
              </p>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)', padding: '0 4px' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: '#16A34A' }} />
                Local Sandbox • Safe
              </span>
              <span className="font-mono" style={{ fontSize: 10 }}>v1.0-light</span>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        {children}
      </div>
    </div>
  );
};
