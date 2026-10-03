export type UserRole = 'DBA' | 'ENGINEER' | 'VIEWER';

export interface User {
  id: string;
  name: string;
  role: UserRole;
  avatar: string;
}

export type DataSourceMode = 'DEMO' | 'CONNECTED_POSTGRES';
export type ConnectionStatus = 'CONNECTED' | 'ERROR' | 'DISCONNECTED';

export interface DataSource {
  id: string;
  name: string;
  mode: DataSourceMode;
  connectionStatus: ConnectionStatus;
  privacyConfigVersion: string;
  endpoint?: string;
  lastSyncAt: string;
}

export type BottleneckType = 
  | 'LARGE_SEQ_SCAN'
  | 'REPEATED_INNER_LOOP'
  | 'EXPENSIVE_SORT'
  | 'CARDINALITY_MISMATCH'
  | 'TIME_RANGE_REPETITION'
  | 'INSUFFICIENT_EVIDENCE';

export type AnalysisStatus = 'NEW' | 'ANALYZED' | 'SIMULATED' | 'APPROVED' | 'REJECTED' | 'ABSTAINED';
export type PrivacyStatus = 'VERIFIED_MASKED' | 'BLOCKED' | 'ERROR';
export type ConfidenceLevel = 'LOW' | 'MEDIUM' | 'HIGH';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

export interface PlanNodeData {
  id: string;
  parentId?: string;
  operatorType: 'SEQ_SCAN' | 'INDEX_SCAN' | 'INDEX_ONLY_SCAN' | 'NESTED_LOOP' | 'HASH_JOIN' | 'SORT' | 'AGGREGATE';
  relationToken?: string;
  indexToken?: string;
  joinType?: 'INNER' | 'LEFT' | 'RIGHT';
  estimatedCost: number;
  estimatedRowsBucket: string;
  actualRowsBucket?: string;
  actualTimeMsBucket?: string;
  loopsBucket?: string;
  scanType?: string;
  filterColumns?: string[];
  sortColumns?: string[];
  isCritical: boolean;
  depth: number;
  notes?: string;
}

export interface PlanGraphData {
  id: string;
  queryEventId: string;
  planCost: number;
  planDepth: number;
  nodeCount: number;
  nodes: PlanNodeData[];
}

export type RecommendationActionType = 
  | 'INDEX'
  | 'SQL_REWRITE'
  | 'PARTITION_ADVISORY'
  | 'STATS_ADVISORY'
  | 'ABSTAIN';

export type RecommendationStatus = 
  | 'DRAFT'
  | 'SIMULATING'
  | 'VALIDATED'
  | 'REJECTED_BY_SAFETY'
  | 'APPROVED'
  | 'REJECTED'
  | 'DEFERRED';

export interface RankingScoreBreakdown {
  score: number; // Formula: 0.45*readBenefit - 0.20*writePenalty - 0.15*storagePenalty - 0.20*operationalRisk
  readBenefit: number;
  writePenalty: number;
  storagePenalty: number;
  operationalRisk: number;
}

export interface EvidencePacket {
  version: string;
  bottleneckType: string;
  affectedPlanNodes: string[];
  reasonCodes: string[];
  observedEvidence: {
    scanType?: string;
    loopCountBucket?: string;
    relationSizeBucket?: string;
    cardinalityMismatchRatio?: number;
    sortSpillDetected?: boolean;
  };
  recommendedAction: string;
  maskedChangeTemplate: string;
  alternativesConsidered: Array<{
    action: string;
    rank: number;
    reasonLowerRank: string;
  }>;
  simulationSummary?: {
    status: string;
    label: string;
    improvementRangePercent: [number, number];
  };
  confidence: ConfidenceLevel;
  riskLevel: RiskLevel;
  limitations: string[];
  privacyStatus: string;
}

export interface SimulationResult {
  id: string;
  recommendationId: string;
  simulationEngine: 'HYPOPG' | 'EXPLAIN' | 'RULE_ESTIMATOR';
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'UNSUPPORTED' | 'FAILED';
  baseline: {
    plannerCost: number;
    dominantOperations: string[];
    executionTimeEstimateMs: number;
  };
  candidate: {
    plannerCost: number;
    dominantOperations: string[];
    executionTimeEstimateMs: number;
  };
  estimatedImprovementPercentRange: [number, number];
  estimatedWriteOverheadMsRange: [number, number];
  estimatedStorageOverheadGbRange: [number, number];
  confidence: ConfidenceLevel;
  limitations: string[];
  runAt: string;
}

export interface Recommendation {
  id: string;
  queryEventId: string;
  actionType: RecommendationActionType;
  title: string;
  maskedChangeTemplate: string;
  status: RecommendationStatus;
  confidence: ConfidenceLevel;
  riskLevel: RiskLevel;
  rankingScore: RankingScoreBreakdown;
  evidence: EvidencePacket;
  simulation?: SimulationResult;
  createdAt: string;
  resolvedAt?: string;
  resolvedBy?: string;
  rejectionReason?: string;
}

export interface QueryEvent {
  id: string;
  queryFingerprint: string;
  title: string;
  maskedQueryTemplate: string;
  latencyMsBucket: string;
  averageDurationMs: number;
  frequencyBucket: string;
  callsPerMin: number;
  impactScore: number;
  bottleneckType: BottleneckType;
  analysisStatus: AnalysisStatus;
  privacyStatus: PrivacyStatus;
  observedAt: string;
  planGraph: PlanGraphData;
  recommendations: Recommendation[];
}

export interface AuditLogItem {
  id: string;
  timestamp: string;
  actorId: string;
  actorName: string;
  actorRole: UserRole;
  eventType: 'INGESTED' | 'MASKED' | 'ANALYZED' | 'SIMULATED' | 'APPROVED' | 'REJECTED' | 'PRIVACY_BLOCKED' | 'SETTINGS_CHANGED';
  entityType: 'QUERY' | 'RECOMMENDATION' | 'SIMULATION' | 'PRIVACY_GATEWAY';
  entityId: string;
  description: string;
  metadataJson: Record<string, any>;
  privacyStatus: PrivacyStatus;
}

export interface PredictionProbability {
  label: string;
  probability: number;
  severity?: string;
}

export interface GNNInferenceResult {
  model_available: boolean;
  predicted_label?: string | null;
  predicted_bottleneck?: string | null;
  confidence: number;
  top_3_predictions: PredictionProbability[];
  top_predictions: PredictionProbability[];
  model_version: string;
  dataset_version: string;
  is_low_confidence: boolean;
  confidence_threshold: number;
  rule_engine_label?: string | null;
  rule_disagreement: boolean;
  agreement_status: 'AGREES_WITH_RULE_ENGINE' | 'DIFFERS_FROM_RULE_ENGINE' | 'LOW_CONFIDENCE' | 'MODEL_UNAVAILABLE';
  highlighted_node_indices: number[];
  usage_policy?: string;
  privacy_status?: string;
  disclaimer: string;
}

export interface PerClassMetric {
  precision: number;
  recall: number;
  f1_score: number;
  support: number;
}

export interface GNNEvaluationMetrics {
  model_version: string;
  dataset_version: string;
  total_samples: number;
  train_samples: number;
  val_samples: number;
  test_samples: number;
  accuracy: number;
  macro_f1: number;
  per_class_metrics: Record<string, PerClassMetric>;
  confusion_matrix: number[][];
  classes: string[];
  trained_at: string;
  random_seed: number;
  disclaimer: string;
}

export interface GNNStatusResponse {
  model_available: boolean;
  ml_dependencies_installed: boolean;
  model_version: string;
  dataset_version: string;
  dataset_graph_count: number;
  label_distribution: Record<string, number>;
  accuracy?: number | null;
  macro_f1?: number | null;
  trained_at?: string | null;
  confidence_threshold: number;
  disclaimer: string;
}

export interface SampleQueryItem {
  id: string;
  name: string;
  dataset: string;
  description: string;
  sql: string;
  expected_bottleneck: string;
  complexity: 'SIMPLE' | 'MODERATE' | 'COMPLEX';
}

export interface BenchmarkInfo {
  id: string;
  name: string;
  description: string;
  is_available: boolean;
  table_count: number;
  estimated_rows: number;
  tables: string[];
  sample_queries: SampleQueryItem[];
}

export interface BenchmarkStatusResponse {
  benchmarks: BenchmarkInfo[];
  active_dataset: string;
  environment: string;
}

export interface AnalysisJob {
  analysis_id: string;
  source_type: string;
  sandbox_dataset: string;
  status: 'PENDING' | 'VALIDATING' | 'MASKING' | 'EXPLAINING' | 'ANALYZING' | 'COMPLETED' | 'FAILED';
  masked_query_template: string;
  query_fingerprint: string;
  privacy_check_passed: number;
  masked_literals_count: number;
  tokenized_identifiers_count: number;
  created_at: string;
  completed_at?: string | null;
  safe_error_code?: string | null;
  safe_error_message?: string | null;
  diagnosis?: string | null;
  main_bottleneck?: string | null;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  recommendation_count: number;
  plan_json?: any;
  plan_graph?: {
    nodes: Array<{
      node_uid: string;
      operator_type: string;
      relation_token?: string;
      estimated_cost_bucket?: string;
      estimated_rows_bucket?: string;
      loops_bucket?: string;
      is_bottleneck?: boolean;
      bottleneck_type?: string;
      details_json?: any;
    }>;
    edges: Array<{
      parent_node_uid: string;
      child_node_uid: string;
    }>;
    depth?: number;
    total_cost?: number;
  };
  xai_evidence?: {
    bottleneck_type?: string;
    affected_plan_nodes?: string[];
    evidence_signals?: string[];
    recommended_action?: string;
    cost_reduction_estimate?: string;
    confidence_score?: number;
    honesty_label?: string;
  };
  gnn_prediction?: GNNInferenceResult;
  recommendations?: Array<{
    id: string;
    type: string;
    title: string;
    description: string;
    action_sql: string;
    estimated_improvement_pct: number;
    risk_level: string;
    status: string;
  }>;
  simulation?: {
    simulation_id?: string;
    simulation_engine?: string;
    live_hypopg?: boolean;
    baseline_cost?: number;
    simulated_cost?: number;
    cost_improvement_pct?: number;
    estimated_latency_reduction_pct?: number;
    write_latency_impact_ms?: number;
    storage_overhead_mb?: number;
    simulated_plan_nodes?: any[];
    disclaimer?: string;
    honesty_label?: string;
  };
  approval_status: 'PENDING' | 'APPROVED' | 'REJECTED';
  approval_comment?: string | null;
  approved_by?: string | null;
  approved_at?: string | null;
  privacy_status: string;
}

// Realtime Telemetry Types
export interface RealtimeStatusResponse {
  connected: boolean;
  mode: string;
  polling_interval_sec: number;
  is_workload_active: boolean;
  database_name: string;
  anonymization_active: boolean;
  pg_stat_statements_active: boolean;
  last_poll_time?: string | null;
}

export interface SlowQueryItem {
  query_fingerprint: string;
  masked_query: string;
  calls: number;
  total_time_ms: number;
  mean_time_ms: number;
  p95_time_ms: number;
  rows_per_call: number;
  primary_bottleneck?: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  last_seen: string;
}

export interface LatencyTrendPoint {
  timestamp: string;
  latency_ms: number;
  calls_per_sec: number;
}

export interface RealtimeMetricsResponse {
  timestamp: string;
  total_calls_per_sec: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  slow_query_count: number;
  estimated_cpu_pct: number;
  cache_hit_ratio_pct: number;
  active_connections: number;
  latency_trend: LatencyTrendPoint[];
  bottleneck_distribution: Record<string, number>;
  top_slow_queries: SlowQueryItem[];
  privacy_statement: string;
}

export interface ConnectionConfigResponse {
  active_mode: string;
  sandbox_available: boolean;
  external_mode_status: string;
  safety_message: string;
}

// Benchmark Types
export interface BenchmarkCatalogItem {
  id: string;
  name: string;
  category: string;
  scale: string;
  status: 'ACTIVE' | 'READY' | 'AVAILABLE' | 'SCAFFOLDED';
  installed: boolean;
  table_count: number;
  disk_size_mb: number;
  description: string;
  hardware_warning?: string | null;
}

export interface BenchmarkCatalogStatus {
  benchmarks: BenchmarkCatalogItem[];
  active_dataset: string;
  environment: string;
}

export interface BenchmarkSetupStatus {
  dataset: string;
  scale_factor: number;
  status: 'IDLE' | 'GENERATING' | 'VALIDATING' | 'CLEANING' | 'LOADING' | 'READY' | 'FAILED';
  progress_pct: number;
  current_stage: string;
  message: string;
  error?: string | null;
  updated_at: string;
}

export interface BenchmarkSummaryResponse {
  dataset: string;
  scale_factor: number;
  is_installed: boolean;
  status: string;
  table_count: number;
  estimated_rows: number;
  table_rows: Record<string, number>;
  approved_queries_count: number;
  disk_size_estimate_mb: number;
  privacy_statement: string;
}

export interface RunWorkloadResponse {
  job_id: string;
  status: string;
  queries_executed: number;
  total_iterations: number;
  duration_ms: number;
  message: string;
  telemetry_collected: boolean;
}

export interface GNNModelItem {
  model_version: string;
  dataset_version: string;
  accuracy?: number;
  macro_f1?: number;
  trained_at?: string;
  is_active: boolean;
}

export interface GNNModelsResponse {
  models: GNNModelItem[];
  active_model: string;
}

export interface DashboardVisualSummary {
  kpis: {
    slow_queries: { value: number; trend: string; status: string };
    critical_bottlenecks: { value: number; trend: string; status: string };
    simulations_passed: { value: number; trend: string; status: string };
    pending_reviews: { value: number; trend: string; status: string };
    privacy_checks_passed: { value: number; trend: string; status: string };
  };
  top_priority: {
    fingerprint: string;
    severity: string;
    bottleneck_type: string;
    diagnosis: string;
    improvement_range: string;
    risk_level: string;
    query_id?: string;
    recommendation_id?: string;
  };
  charts: {
    latency_trend: Array<{ time: string; latency: number; p95: number; qps: number }>;
    query_frequency: Array<any>;
    bottleneck_breakdown?: Array<{ type: string; count: number; pct: number; color: string }>;
    bottleneck_distribution?: Array<any>;
    query_health: any;
  };
  pipeline_stages: Array<{
    id: string;
    name: string;
    status: string;
    icon: string;
  }>;
  environment_label: string;
  privacy_label: string;
  last_refreshed: string;
}

export interface RealtimeVisualMetrics {
  gauges: {
    latency: { value_ms: number; threshold_warning: number; threshold_critical: number; status: string };
    throughput: { qps: number; unit: string; status: string };
    cache_hit: { percentage: number; target_pct: number; status: string };
    cpu_estimate: { percentage: number; status: string };
  };
  slow_query_bars: Array<{
    query_token: string;
    avg_time_ms: number;
    calls: number;
    bottleneck_type: string;
    table_token: string;
  }>;
  scan_distribution: {
    seq_scan_pct: number;
    index_scan_pct: number;
    bitmap_scan_pct: number;
  };
  is_collecting: boolean;
  last_updated: string;
}

export interface RecommendationsVisualSummary {
  total_recommendations: number;
  pending_approval: number;
  approved: number;
  rejected: number;
  recommendations_by_type: {
    composite_index: number;
    query_rewrite: number;
    partitioning: number;
    table_stats: number;
  };
  visual_cards: Array<{
    id: string;
    query_token: string;
    type: string;
    title: string;
    benefit_ring_pct: number;
    risk_badge: string;
    cost_before: number;
    cost_after: number;
    evidence_chips: string[];
    status: string;
    can_approve: boolean;
    can_simulate: boolean;
  }>;
}

export interface ModelsVisualSummary {
  active_model?: string;
  is_available?: boolean;
  accuracy?: number;
  macro_f1?: number;
  accuracy_pct?: number;
  macro_f1_pct?: number;
  latency_overhead_ms?: number;
  confusion_matrix?: number[][] | {
    labels?: string[];
    matrix?: number[][];
  };
  classes?: string[];
  per_class_metrics?: Record<string, {
    precision: number;
    recall: number;
    f1_score: number;
    support?: number;
  }>;
  class_metrics?: Array<{
    class_name: string;
    precision: number;
    recall: number;
    f1_score: number;
  }>;
  available_models?: Array<any>;
  dataset_graph_count?: number;
  label_distribution?: Record<string, number>;
  disclaimer?: string;
}

export interface BenchmarksVisualSummary {
  benchmarks: BenchmarkCatalogItem[];
  active_benchmark: string;
  pipeline_status: {
    current_stage: string;
    stages: Array<{ name: string; status: string; progress_pct: number }>;
    progress_pct: number;
  };
  storage_summary: {
    total_disk_mb: number;
    table_count: number;
    total_synthetic_rows: number;
  };
}


