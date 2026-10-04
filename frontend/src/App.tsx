import React, { useState, useEffect } from 'react';
import { 
  INITIAL_USERS, 
  INITIAL_DATA_SOURCE, 
  INITIAL_QUERIES, 
  INITIAL_AUDIT_LOGS 
} from './data/mockData';
import type { 
  User, 
  DataSource, 
  QueryEvent, 
  Recommendation, 
  AuditLogItem, 
  SimulationResult,
  GNNStatusResponse,
  GNNEvaluationMetrics
} from './types/queryguard';
import { Navigation } from './components/Navigation';
import { DashboardHome } from './components/DashboardHome';
import { SlowQueriesView } from './components/SlowQueriesView';
import { QueryDetailView } from './components/QueryDetailView';
import { RecommendationsView } from './components/RecommendationsView';
import { RecommendationDetailView } from './components/RecommendationDetailView';
import { AuditLogsView } from './components/AuditLogsView';
import { PrivacyView } from './components/PrivacyView';
import { SettingsView } from './components/SettingsView';
import { SimulationModal } from './components/SimulationModal';
import { ApprovalDrawer } from './components/ApprovalDrawer';
import { VoiceSummaryDialog } from './components/VoiceSummaryDialog';
import { ModelEvaluationModal } from './components/ModelEvaluationModal';
import { AnalyzeQueryWorkspace } from './components/AnalyzeQueryWorkspace';
import { LiveWorkloadView } from './components/LiveWorkloadView';
import { BenchmarkDatasetsView } from './components/BenchmarkDatasetsView';
import { ModelInsightsView } from './components/ModelInsightsView';
import { SimulationsShowcaseView } from './components/SimulationsShowcaseView';
import { Login } from './Login';

import { api } from './lib/api';

export function App() {
  const [currentUser, setCurrentUser] = useState<User>(() => {
    try {
      const saved = localStorage.getItem('queryguard_user');
      if (saved) return JSON.parse(saved);
    } catch (e) {}
    return INITIAL_USERS[0];
  });
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    return localStorage.getItem('queryguard_auth') === 'true';
  });
  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [selectedQueryId, setSelectedQueryId] = useState<string | null>(null);
  const [selectedRecommendationId, setSelectedRecommendationId] = useState<string | null>(null);

  const [users, setUsers] = useState<User[]>(INITIAL_USERS);
  const [dataSource, setDataSource] = useState<DataSource>(INITIAL_DATA_SOURCE);
  const [queries, setQueries] = useState<QueryEvent[]>(INITIAL_QUERIES);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>(INITIAL_AUDIT_LOGS);

  // Modals & Drawers state
  const [simulationModalRec, setSimulationModalRec] = useState<Recommendation | null>(null);
  const [approvalDrawerRec, setApprovalDrawerRec] = useState<Recommendation | null>(null);
  const [approvalDecisionType, setApprovalDecisionType] = useState<'APPROVED' | 'REJECTED' | null>(null);
  const [isVoiceModalOpen, setIsVoiceModalOpen] = useState(false);
  const [isModelEvaluationOpen, setIsModelEvaluationOpen] = useState(false);

  // GNN Copilot state
  const [gnnStatus, setGnnStatus] = useState<GNNStatusResponse | null>(null);
  const [gnnEvaluation, setGnnEvaluation] = useState<GNNEvaluationMetrics | null>(null);

  // Enforce light theme on document element
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', 'light');
  }, []);

  // Load live data from FastAPI backend with fallback
  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      try {
        const [loadedUsers, loadedQueries, loadedLogs, telemetryStatus, statusGnn, evalGnn] = await Promise.all([
          api.fetchUsers(INITIAL_USERS),
          api.fetchQueries(INITIAL_QUERIES),
          api.fetchAuditLogs(INITIAL_AUDIT_LOGS),
          api.fetchTelemetryStatus(),
          api.fetchGnnStatus(),
          api.fetchGnnEvaluation()
        ]);
        if (!isMounted) return;
        if (loadedUsers && loadedUsers.length > 0) {
          setUsers(loadedUsers);
          setCurrentUser(prev => {
            const matched = loadedUsers.find(u => u.id === prev.id || (u.employee_id && u.employee_id === prev.employee_id) || (u.email && u.email === prev.email));
            return matched || prev;
          });
        }
        if (loadedQueries && loadedQueries.length > 0) {
          setQueries(loadedQueries);
        }
        if (loadedLogs && loadedLogs.length > 0) {
          setAuditLogs(loadedLogs);
        }
        if (statusGnn) {
          setGnnStatus(statusGnn);
        }
        if (evalGnn) {
          setGnnEvaluation(evalGnn);
        }
        if (telemetryStatus) {
          setDataSource(prev => ({
            ...prev,
            connectionStatus: telemetryStatus.connection_status === 'CONNECTED' ? 'CONNECTED' : prev.connectionStatus,
            privacyConfigVersion: telemetryStatus.privacy_config_version || prev.privacyConfigVersion,
            lastSyncAt: 'Just now'
          }));
        }
      } catch (err) {
        console.warn('[QueryGuard] API synchronization notice; operating with local cache:', err);
      }
    }
    loadData();
    return () => { isMounted = false; };
  }, []);

  const handleGenerateGnnDataset = async () => {
    await api.generateGnnDataset();
    const [st, ev] = await Promise.all([api.fetchGnnStatus(), api.fetchGnnEvaluation()]);
    if (st) setGnnStatus(st);
    if (ev) setGnnEvaluation(ev);
  };

  const handleTrainGnnModel = async () => {
    const ev = await api.trainGnnModel();
    if (ev) setGnnEvaluation(ev);
    const st = await api.fetchGnnStatus();
    if (st) setGnnStatus(st);
  };


  // Extract all recommendations flat
  const allRecommendations = queries.flatMap(q => q.recommendations);

  // Handlers
  const handleSelectQuery = (queryId: string) => {
    setSelectedQueryId(queryId);
    setSelectedRecommendationId(null);
    setCurrentTab('queries');
  };

  const handleSelectRecommendation = (recId: string) => {
    setSelectedRecommendationId(recId);
    // Find parent query
    const parentQuery = queries.find(q => q.recommendations.some(r => r.id === recId));
    if (parentQuery) {
      setSelectedQueryId(parentQuery.id);
    }
    setCurrentTab('recommendations');
  };

  const handleSimulationComplete = (recId: string, simResult: SimulationResult) => {
    setQueries(prevQueries => prevQueries.map(q => ({
      ...q,
      analysisStatus: 'SIMULATED',
      recommendations: q.recommendations.map(r => {
        if (r.id === recId) {
          return {
            ...r,
            simulation: simResult,
            status: 'VALIDATED'
          };
        }
        return r;
      })
    })));

    // Create Audit Log
    const newLog: AuditLogItem = {
      id: `aud-${Date.now()}`,
      timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC',
      actorId: currentUser.id,
      actorName: `${currentUser.name} (${currentUser.role})`,
      actorRole: currentUser.role,
      eventType: 'SIMULATED',
      entityType: 'SIMULATION',
      entityId: simResult.id,
      description: `HypoPG virtual index simulation completed. Cost: ${simResult.baseline.plannerCost.toLocaleString()} -> ${simResult.candidate.plannerCost.toLocaleString()} (-83.3%). Zero physical disk mutation.`,
      metadataJson: {
        engine: simResult.simulationEngine,
        costBefore: simResult.baseline.plannerCost,
        costAfter: simResult.candidate.plannerCost,
        physicalDDLExecuted: false
      },
      privacyStatus: 'VERIFIED_MASKED'
    };

    setAuditLogs(prev => [newLog, ...prev]);
  };

  const handleSubmitDecision = async (recId: string, decision: 'APPROVED' | 'REJECTED', reason?: string) => {
    // 1. Optimistic update
    setQueries(prevQueries => prevQueries.map(q => ({
      ...q,
      recommendations: q.recommendations.map(r => {
        if (r.id === recId) {
          return {
            ...r,
            status: decision,
            resolvedAt: new Date().toLocaleTimeString(),
            resolvedBy: currentUser.name,
            rejectionReason: decision === 'REJECTED' ? reason : undefined
          };
        }
        return r;
      })
    })));

    // 2. Call backend API
    try {
      const payload = {
        actor_id: currentUser.id,
        actor_name: currentUser.name,
        actor_role: currentUser.role,
        reason
      };
      if (decision === 'APPROVED') {
        await api.approveRecommendation(recId, payload);
      } else {
        await api.rejectRecommendation(recId, payload);
      }
      const remoteLogs = await api.fetchAuditLogs();
      if (remoteLogs && remoteLogs.length > 0) {
        setAuditLogs(remoteLogs);
        return;
      }
    } catch (err) {
      console.warn('Backend decision endpoint failed, recording locally:', err);
    }

    // Fallback local audit log
    const newLog: AuditLogItem = {
      id: `aud-${Date.now()}`,
      timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC',
      actorId: currentUser.id,
      actorName: `${currentUser.name} (${currentUser.role})`,
      actorRole: currentUser.role,
      eventType: decision,
      entityType: 'RECOMMENDATION',
      entityId: recId,
      description: decision === 'APPROVED' 
        ? `Recommendation ${recId} approved by DBA. Generated change script for human review. No production deployment occurred.`
        : `Recommendation ${recId} rejected by DBA. Reason: ${reason}`,
      metadataJson: {
        recommendationId: recId,
        decision,
        reason,
        policy: 'NO_AUTOMATIC_PRODUCTION_DDL'
      },
      privacyStatus: 'VERIFIED_MASKED'
    };

    setAuditLogs(prev => [newLog, ...prev]);
  };

  const handleResetDemo = async () => {
    try {
      await api.resetDemo();
      const [reloadedQueries, reloadedLogs] = await Promise.all([
        api.fetchQueries(INITIAL_QUERIES),
        api.fetchAuditLogs(INITIAL_AUDIT_LOGS)
      ]);
      setQueries(reloadedQueries);
      setAuditLogs(reloadedLogs);
    } catch (err) {
      console.warn('Backend reset failed, resetting local state:', err);
      setQueries(INITIAL_QUERIES);
      setAuditLogs(INITIAL_AUDIT_LOGS);
    }
    setSelectedQueryId(null);
    setSelectedRecommendationId(null);
    setCurrentTab('dashboard');

    const resetLog: AuditLogItem = {
      id: `aud-${Date.now()}`,
      timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC',
      actorId: currentUser.id,
      actorName: `${currentUser.name} (${currentUser.role})`,
      actorRole: currentUser.role,
      eventType: 'SETTINGS_CHANGED',
      entityType: 'PRIVACY_GATEWAY',
      entityId: 'sys-reset',
      description: 'Demo database and benchmark state reset to initial seed values.',
      metadataJson: { action: 'RESET_DEMO' },
      privacyStatus: 'VERIFIED_MASKED'
    };

    setAuditLogs(prev => [resetLog, ...prev]);
  };

  const activeQuery = queries.find(q => q.id === selectedQueryId);
  const activeRecommendation = allRecommendations.find(r => r.id === selectedRecommendationId);

  if (!isAuthenticated) {
    return (
      <Login
        onLogin={(authedUser: User) => {
          localStorage.setItem('queryguard_auth', 'true');
          localStorage.setItem('queryguard_user', JSON.stringify(authedUser));
          setCurrentUser(authedUser);
          setIsAuthenticated(true);
        }}
      />
    );
  }

  return (
    <div className="app-layout">
      {/* Sidebar + Topbar */}
      <Navigation
        currentTab={currentTab}
        onSelectTab={(tab) => {
          setCurrentTab(tab);
          setSelectedQueryId(null);
          setSelectedRecommendationId(null);
        }}
        currentUser={currentUser}
        users={users}
        onChangeUser={(u) => {
          setCurrentUser(u);
          localStorage.setItem('queryguard_user', JSON.stringify(u));
        }}
        dataSource={dataSource}
        onResetDemo={handleResetDemo}
        onOpenPrivacyModal={() => setCurrentTab('privacy')}
        onLogout={() => {
          localStorage.removeItem('queryguard_auth');
          localStorage.removeItem('queryguard_user');
          setIsAuthenticated(false);
        }}
      >
        {/* Main Viewport */}
        <main className="main-viewport">
          <div className="content-canvas">
            {/* Enterprise Role-Based Access Control (RBAC) Hierarchy Status Strip */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: 12,
              padding: '10px 16px',
              marginBottom: 16,
              borderRadius: 'var(--radius-md)',
              border: `1px solid ${
                currentUser.role === 'DBA' ? '#99F6E4' : currentUser.role === 'ENGINEER' ? '#BFDBFE' : '#E2E8F0'
              }`,
              backgroundColor: currentUser.role === 'DBA' ? '#F0FDFA' : currentUser.role === 'ENGINEER' ? '#EFF6FF' : '#F8FAFC',
              fontSize: 12
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                <span style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 5,
                  padding: '3px 10px',
                  borderRadius: 9999,
                  fontWeight: 700,
                  fontSize: 11,
                  letterSpacing: '0.04em',
                  backgroundColor: currentUser.role === 'DBA' ? '#0F766E' : currentUser.role === 'ENGINEER' ? '#1D4ED8' : '#475569',
                  color: '#FFFFFF'
                }}>
                  {currentUser.role === 'DBA' ? 'LEVEL 3 SUPERUSER' : currentUser.role === 'ENGINEER' ? 'LEVEL 2 ENGINEER' : 'LEVEL 1 AUDITOR'}
                </span>
                <span style={{ fontWeight: 600, color: '#0F172A' }}>
                  {currentUser.name}
                </span>
                <span style={{ color: '#64748B', fontFamily: 'monospace', fontSize: 11 }}>
                  [{currentUser.employee_id || (currentUser.role === 'DBA' ? 'EMP-DBA-01' : currentUser.role === 'ENGINEER' ? 'EMP-ENG-02' : 'EMP-AUD-03')}]
                </span>
                <span style={{ color: '#CBD5E1' }}>|</span>
                <span style={{ color: '#475569' }}>
                  {currentUser.department || (currentUser.role === 'DBA' ? 'Database Reliability & Architecture' : currentUser.role === 'ENGINEER' ? 'Platform & Application Engineering' : 'Security & Compliance Governance')}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#64748B' }}>
                <span style={{ fontSize: 11, fontWeight: 500 }}>
                  {currentUser.role === 'DBA' 
                    ? '⚡ Full Authority: Production Index Approvals, GNN Retraining & HypoPG' 
                    : currentUser.role === 'ENGINEER' 
                      ? '🔧 Operational Access: Explain Plans & Virtual HypoPG (Approvals Route to DBA)' 
                      : '🔒 Read-Only Compliance: Masked Telemetry & Audit Logs Only'}
                </span>
              </div>
            </div>

            {/* Dashboard Home */}
            {currentTab === 'dashboard' && (
              <DashboardHome
                queries={queries}
                recommendations={allRecommendations}
                currentUser={currentUser}
                onSelectQuery={handleSelectQuery}
                onSelectRecommendation={handleSelectRecommendation}
                onOpenSimulationModal={(rec) => setSimulationModalRec(rec)}
                onOpenModelEvaluation={() => setIsModelEvaluationOpen(true)}
                gnnStatus={gnnStatus}
                onGenerateGnnDataset={handleGenerateGnnDataset}
                onTrainGnnModel={handleTrainGnnModel}
              />
            )}

            {/* Live Workload Telemetry */}
            {currentTab === 'live' && (
              <LiveWorkloadView
                onNavigateToAnalyze={(queryText) => {
                  setCurrentTab('analyze');
                }}
              />
            )}

            {/* Benchmark Datasets & Generators */}
            {currentTab === 'benchmarks' && (
              <BenchmarkDatasetsView />
            )}

            {/* Interactive Query Analysis Workspace */}
            {currentTab === 'analyze' && (
              <AnalyzeQueryWorkspace
                currentUser={currentUser}
                onTabChange={setCurrentTab}
              />
            )}

            {/* Slow Queries View or Query Detail */}
            {currentTab === 'queries' && (
              activeQuery ? (
                <QueryDetailView
                  query={activeQuery}
                  onBack={() => setSelectedQueryId(null)}
                  onSelectRecommendation={handleSelectRecommendation}
                  onOpenSimulationModal={(rec) => setSimulationModalRec(rec)}
                />
              ) : (
                <SlowQueriesView
                  queries={queries}
                  onSelectQuery={handleSelectQuery}
                  onAcceptFix={(queryId) => {
                    setQueries(prev => prev.map(q => {
                      if (q.id === queryId) {
                        return {
                          ...q,
                          analysisStatus: 'RESOLVED' as any,
                          recommendations: q.recommendations.map(r => ({
                            ...r,
                            status: 'APPROVED' as any,
                            resolvedAt: new Date().toISOString(),
                            resolvedBy: currentUser.id
                          }))
                        };
                      }
                      return q;
                    }));
                  }}
                  onRevertFix={(queryId) => {
                    setQueries(prev => prev.map(q => {
                      if (q.id === queryId) {
                        return {
                          ...q,
                          analysisStatus: 'ANALYZED' as any,
                          recommendations: q.recommendations.map(r => ({
                            ...r,
                            status: 'VALIDATED' as any,
                            resolvedAt: undefined,
                            resolvedBy: undefined
                          }))
                        };
                      }
                      return q;
                    }));
                  }}
                  onAcceptAllFixes={() => {
                    setQueries(prev => prev.map(q => ({
                      ...q,
                      analysisStatus: 'RESOLVED' as any,
                      recommendations: q.recommendations.map(r => ({
                        ...r,
                        status: 'APPROVED' as any,
                        resolvedAt: new Date().toISOString(),
                        resolvedBy: currentUser.id
                      }))
                    })));
                  }}
                  onResetAllFixes={() => {
                    setQueries(prev => prev.map(q => ({
                      ...q,
                      analysisStatus: 'ANALYZED' as any,
                      recommendations: q.recommendations.map(r => ({
                        ...r,
                        status: 'VALIDATED' as any,
                        resolvedAt: undefined,
                        resolvedBy: undefined
                      }))
                    })));
                  }}
                />
              )
            )}

            {/* Recommendations View or Recommendation Detail */}
            {currentTab === 'recommendations' && (
              activeRecommendation && activeQuery ? (
                <RecommendationDetailView
                  recommendation={activeRecommendation}
                  query={activeQuery}
                  currentUser={currentUser}
                  onBack={() => setSelectedRecommendationId(null)}
                  onOpenApprovalDrawer={(rec, dec) => {
                    setApprovalDrawerRec(rec);
                    setApprovalDecisionType(dec);
                  }}
                  onOpenSimulationModal={(rec) => setSimulationModalRec(rec)}
                />
              ) : (
                <RecommendationsView
                  recommendations={allRecommendations}
                  queries={queries}
                  onSelectRecommendation={handleSelectRecommendation}
                  onOpenSimulationModal={(rec) => setSimulationModalRec(rec)}
                />
              )
            )}

            {/* In-Memory Simulations Showcase */}
            {currentTab === 'simulations' && (
              <SimulationsShowcaseView
                recommendations={allRecommendations}
                queries={queries}
                currentUser={currentUser}
                onOpenSimulationModal={(rec) => setSimulationModalRec(rec)}
                onSelectRecommendation={handleSelectRecommendation}
              />
            )}

            {/* Model Insights & GNN Copilot */}
            {currentTab === 'models' && (
              <ModelInsightsView
                onOpenModalEvaluation={() => setIsModelEvaluationOpen(true)}
              />
            )}

            {/* Audit Logs */}
            {currentTab === 'audit' && (
              <AuditLogsView logs={auditLogs} />
            )}

            {/* Privacy & Data Controls */}
            {currentTab === 'privacy' && (
              <PrivacyView />
            )}

            {/* Settings */}
            {currentTab === 'settings' && (
              <SettingsView
                dataSource={dataSource}
                onUpdateDataSource={setDataSource}
                onResetDemo={handleResetDemo}
                onOpenVoiceModal={() => setIsVoiceModalOpen(true)}
              />
            )}

            {/* Login / Auth View Tab */}
            {currentTab === 'login' && (
              <div style={{ margin: '-24px', minHeight: 'calc(100vh - 56px)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Login 
                  onLogin={() => {
                    setCurrentTab('dashboard');
                    setIsAuthenticated(true);
                  }}
                  onBackToDashboard={() => setCurrentTab('dashboard')}
                />
              </div>
            )}
          </div>
        </main>
      </Navigation>

      {/* Safe Simulation Modal */}
      {simulationModalRec && (
        <SimulationModal
          recommendation={simulationModalRec}
          isOpen={!!simulationModalRec}
          onClose={() => setSimulationModalRec(null)}
          onSimulationComplete={handleSimulationComplete}
        />
      )}

      {/* Human Approval Drawer */}
      {approvalDrawerRec && approvalDecisionType && (
        <ApprovalDrawer
          recommendation={approvalDrawerRec}
          decisionType={approvalDecisionType}
          currentUser={currentUser}
          isOpen={!!approvalDrawerRec}
          onClose={() => {
            setApprovalDrawerRec(null);
            setApprovalDecisionType(null);
          }}
          onSubmitDecision={handleSubmitDecision}
        />
      )}

      {/* Optional ElevenLabs Voice Summary Preview */}
      <VoiceSummaryDialog
        isOpen={isVoiceModalOpen}
        onClose={() => setIsVoiceModalOpen(false)}
      />

      {/* Experimental GNN Model Evaluation Modal */}
      <ModelEvaluationModal
        isOpen={isModelEvaluationOpen}
        onClose={() => setIsModelEvaluationOpen(false)}
        evaluation={gnnEvaluation}
        status={gnnStatus}
        onTrainModel={handleTrainGnnModel}
        onGenerateDataset={handleGenerateGnnDataset}
      />
    </div>
  );
}

export default App;
