import React, { Component, ErrorInfo, ReactNode, StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './App.css'
import App from './App.tsx'

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class RootErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[QueryGuard UI Error]', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          padding: 24,
          fontFamily: 'system-ui, sans-serif',
          backgroundColor: '#F5F7FA',
          color: '#1E293B'
        }}>
          <div style={{
            maxWidth: 540,
            width: '100%',
            backgroundColor: '#FFFFFF',
            borderRadius: 12,
            border: '1px solid #E2E8F0',
            padding: 28,
            boxShadow: '0 4px 16px rgba(0,0,0,0.06)'
          }}>
            <h2 style={{ margin: '0 0 8px', fontSize: 18, color: '#DC2626' }}>
              QueryGuard AI Interface Notice
            </h2>
            <p style={{ margin: '0 0 16px', fontSize: 13, color: '#64748B' }}>
              An interface error occurred while rendering the dashboard. Click reload to refresh.
            </p>
            <pre style={{
              margin: '0 0 20px',
              padding: 12,
              borderRadius: 6,
              backgroundColor: '#F8FAFC',
              border: '1px solid #E2E8F0',
              fontSize: 12,
              color: '#DC2626',
              overflowX: 'auto',
              whiteSpace: 'pre-wrap'
            }}>
              {this.state.error?.message || 'Unknown error'}
            </pre>
            <button
              onClick={() => window.location.reload()}
              style={{
                backgroundColor: '#0F766E',
                color: '#FFFFFF',
                border: 'none',
                borderRadius: 6,
                padding: '8px 16px',
                fontSize: 13,
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              Reload Dashboard
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RootErrorBoundary>
      <App />
    </RootErrorBoundary>
  </StrictMode>,
)
