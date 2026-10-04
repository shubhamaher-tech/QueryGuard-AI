import { 
  User, 
  DataSource, 
  QueryEvent, 
  AuditLogItem 
} from '../types/queryguard';

export const INITIAL_USERS: User[] = [
  {
    id: 'usr-1',
    employee_id: 'EMP-DBA-01',
    name: 'Priya Sharma',
    full_name: 'Priya Sharma',
    email: 'priya.sharma@queryguard.io',
    role: 'DBA',
    department: 'Database Reliability & Architecture',
    hierarchy_level: 3,
    avatar: 'PS',
    permissions: [
      'APPROVE_PRODUCTION_INDEX',
      'REJECT_PRODUCTION_INDEX',
      'SIMULATE_HYPOPG',
      'RETRAIN_GNN_MODEL',
      'FLUSH_TELEMETRY',
      'EXPORT_SECURITY_AUDIT',
      'MANAGE_SETTINGS'
    ]
  },
  {
    id: 'usr-2',
    employee_id: 'EMP-ENG-02',
    name: 'Arjun Patel',
    full_name: 'Arjun Patel',
    email: 'arjun.patel@queryguard.io',
    role: 'ENGINEER',
    department: 'Platform & Application Engineering',
    hierarchy_level: 2,
    avatar: 'AP',
    permissions: [
      'SIMULATE_HYPOPG',
      'SUBMIT_INDEX_PROPOSAL',
      'ANALYZE_EXPLAIN_PLAN',
      'VIEW_SLOW_QUERIES'
    ]
  },
  {
    id: 'usr-3',
    employee_id: 'EMP-AUD-03',
    name: 'Alex Vance',
    full_name: 'Alex Vance',
    email: 'alex.vance@queryguard.io',
    role: 'VIEWER',
    department: 'Security & Compliance Governance',
    hierarchy_level: 1,
    avatar: 'AV',
    permissions: [
      'VIEW_AUDIT_LOGS',
      'INSPECT_PRIVACY_MASKS',
      'VIEW_TELEMETRY'
    ]
  },
];

export const INITIAL_DATA_SOURCE: DataSource = {
  id: 'ds-pg-01',
  name: 'Local E-Commerce Cluster (Demo)',
  mode: 'DEMO',
  connectionStatus: 'CONNECTED',
  privacyConfigVersion: 'v1.4.2-strict',
  endpoint: 'postgresql://***@localhost:5432/ecommerce_prod (read-only telemetry role)',
  lastSyncAt: 'Just now',
};

export const INITIAL_QUERIES: QueryEvent[] = [
  {
    id: 'qry-7c91',
    queryFingerprint: 'FP_7C91E88B429A',
    title: 'Weekly Regional Sales Aggregation Report',
    maskedQueryTemplate: `SELECT 
  COL_REGION_ID, 
  DATE_TRUNC(:TEXT, COL_TX_DATE) AS tx_week, 
  COUNT(*), 
  SUM(COL_AMOUNT)
FROM TBL_SALES
JOIN TBL_STORES ON TBL_SALES.COL_STORE_ID = TBL_STORES.COL_ID
WHERE COL_STATUS = :TEXT 
  AND COL_TX_DATE >= :TIMESTAMP 
  AND COL_TX_DATE < :TIMESTAMP
GROUP BY 1, 2
ORDER BY 4 DESC;`,
    latencyMsBucket: '1S_TO_5S',
    averageDurationMs: 2450.4,
    frequencyBucket: '100_TO_1K_PER_HR',
    callsPerMin: 18.2,
    impactScore: 92.4,
    bottleneckType: 'LARGE_SEQ_SCAN',
    analysisStatus: 'SIMULATED',
    privacyStatus: 'VERIFIED_MASKED',
    observedAt: '2 mins ago',
    planGraph: {
      id: 'pg-7c91',
      queryEventId: 'qry-7c91',
      planCost: 182341.2,
      planDepth: 4,
      nodeCount: 5,
      nodes: [
        {
          id: 'node_1',
          operatorType: 'AGGREGATE',
          estimatedCost: 182341.2,
          estimatedRowsBucket: '100_TO_1K',
          actualRowsBucket: '100_TO_1K',
          actualTimeMsBucket: '2S_TO_3S',
          loopsBucket: '1',
          depth: 0,
          isCritical: false,
          notes: 'GroupAggregate on COL_REGION_ID, date_trunc'
        },
        {
          id: 'node_2',
          parentId: 'node_1',
          operatorType: 'NESTED_LOOP',
          joinType: 'INNER',
          estimatedCost: 178920.0,
          estimatedRowsBucket: '1M_TO_10M',
          actualRowsBucket: '1M_TO_10M',
          actualTimeMsBucket: '2S_TO_3S',
          loopsBucket: '1',
          depth: 1,
          isCritical: true,
          notes: 'High cost nested loop with unindexed inner sequential scan'
        },
        {
          id: 'node_3',
          parentId: 'node_2',
          operatorType: 'INDEX_SCAN',
          relationToken: 'TBL_STORES',
          indexToken: 'IDX_STORES_PKEY',
          estimatedCost: 8.4,
          estimatedRowsBucket: '100_TO_1K',
          actualRowsBucket: '100_TO_1K',
          actualTimeMsBucket: '1MS_TO_10MS',
          loopsBucket: '1',
          depth: 2,
          isCritical: false,
          notes: 'Index scan using primary key'
        },
        {
          id: 'node_4',
          parentId: 'node_2',
          operatorType: 'SEQ_SCAN',
          relationToken: 'TBL_SALES',
          estimatedCost: 178900.5,
          estimatedRowsBucket: '1M_TO_10M',
          actualRowsBucket: '1M_TO_10M',
          actualTimeMsBucket: '2S_TO_3S',
          loopsBucket: '100_TO_1K',
          scanType: 'SEQ_SCAN',
          filterColumns: ['COL_STATUS', 'COL_TX_DATE', 'COL_REGION_ID'],
          depth: 2,
          isCritical: true,
          notes: 'Sequential scan filtering 12.4M rows without composite index'
        }
      ]
    },
    recommendations: [
      {
        id: 'rec-01',
        queryEventId: 'qry-7c91',
        actionType: 'INDEX',
        title: 'Composite B-Tree Index on (COL_REGION_ID, COL_TX_DATE)',
        maskedChangeTemplate: 'CREATE INDEX CONCURRENTLY ON TBL_SALES (COL_REGION_ID, COL_TX_DATE) WHERE COL_STATUS = :TEXT;',
        status: 'VALIDATED',
        confidence: 'HIGH',
        riskLevel: 'LOW',
        rankingScore: {
          score: 0.74,
          readBenefit: 0.88,
          writePenalty: 0.12,
          storagePenalty: 0.08,
          operationalRisk: 0.05
        },
        evidence: {
          version: '1.0',
          bottleneckType: 'LARGE_SEQ_SCAN',
          affectedPlanNodes: ['node_2', 'node_4'],
          reasonCodes: [
            'LARGE_SEQ_SCAN',
            'REPEATED_INNER_LOOP',
            'MISSING_COMPOSITE_INDEX_PATTERN'
          ],
          observedEvidence: {
            scanType: 'SEQ_SCAN',
            loopCountBucket: '100_TO_1K',
            relationSizeBucket: '10M_TO_100M'
          },
          recommendedAction: 'COMPOSITE_INDEX',
          maskedChangeTemplate: 'CREATE INDEX CONCURRENTLY ON TBL_SALES (COL_REGION_ID, COL_TX_DATE) WHERE COL_STATUS = :TEXT;',
          alternativesConsidered: [
            {
              action: 'PARTITION_ADVISORY',
              rank: 2,
              reasonLowerRank: 'Table size 12.4M is manageable with indexing; partitioning imposes higher operational migration risk.'
            },
            {
              action: 'SQL_REWRITE',
              rank: 3,
              reasonLowerRank: 'Query shape is already normalized; planner bottleneck is storage access path.'
            }
          ],
          simulationSummary: {
            status: 'COMPLETED',
            label: 'Planner-based simulated estimate (HypoPG)',
            improvementRangePercent: [70, 85]
          },
          confidence: 'HIGH',
          riskLevel: 'LOW',
          limitations: [
            'Planner cost reduction is not a guaranteed wall-clock runtime promise.',
            'Write overhead estimated based on 45 inserts/sec workload profile.',
            'CREATE INDEX CONCURRENTLY requires zero table write locks but consumes I/O during build.'
          ],
          privacyStatus: 'Verified: No raw rows, literals, or plaintext schema identifiers exported.'
        },
        simulation: {
          id: 'sim-01',
          recommendationId: 'rec-01',
          simulationEngine: 'HYPOPG',
          status: 'COMPLETED',
          baseline: {
            plannerCost: 182341.2,
            dominantOperations: ['SEQ_SCAN', 'NESTED_LOOP'],
            executionTimeEstimateMs: 2450.0
          },
          candidate: {
            plannerCost: 30510.8,
            dominantOperations: ['INDEX_SCAN', 'HASH_JOIN'],
            executionTimeEstimateMs: 380.0
          },
          estimatedImprovementPercentRange: [72, 85],
          estimatedWriteOverheadMsRange: [1, 2],
          estimatedStorageOverheadGbRange: [1.8, 2.4],
          confidence: 'HIGH',
          limitations: [
            'HypoPG modifies virtual planner state; no physical disk index created.',
            'Write overhead measured on synthetic update distribution.',
            'Actual production runtime depends on buffer cache warmness.'
          ],
          runAt: '5 mins ago'
        },
        createdAt: '10 mins ago'
      }
    ]
  },
  {
    id: 'qry-3e42',
    queryFingerprint: 'FP_3E42B10499C1',
    title: 'Customer Order History & Status Lookup',
    maskedQueryTemplate: `SELECT 
  TBL_CUSTOMERS.COL_ID, 
  TBL_CUSTOMERS.COL_NAME, 
  TBL_ORDERS.COL_ID, 
  TBL_ORDERS.COL_TOTAL_AMOUNT,
  TBL_ORDERS.COL_CREATED_AT
FROM TBL_CUSTOMERS
JOIN TBL_ORDERS ON TBL_CUSTOMERS.COL_ID = TBL_ORDERS.COL_CUST_ID
WHERE TBL_ORDERS.COL_STATUS = :TEXT 
  AND TBL_CUSTOMERS.COL_TIER = :TEXT
ORDER BY TBL_ORDERS.COL_CREATED_AT DESC
LIMIT :INT;`,
    latencyMsBucket: '1S_TO_5S',
    averageDurationMs: 1820.6,
    frequencyBucket: '1K_TO_10K_PER_HR',
    callsPerMin: 42.5,
    impactScore: 88.6,
    bottleneckType: 'REPEATED_INNER_LOOP',
    analysisStatus: 'SIMULATED',
    privacyStatus: 'VERIFIED_MASKED',
    observedAt: '4 mins ago',
    planGraph: {
      id: 'pg-3e42',
      queryEventId: 'qry-3e42',
      planCost: 94820.0,
      planDepth: 3,
      nodeCount: 4,
      nodes: [
        {
          id: 'node_1',
          operatorType: 'SORT',
          estimatedCost: 94820.0,
          estimatedRowsBucket: '10_TO_100',
          actualRowsBucket: '10_TO_100',
          actualTimeMsBucket: '1S_TO_2S',
          loopsBucket: '1',
          depth: 0,
          isCritical: false,
          notes: 'Top-N Sort on COL_CREATED_AT'
        },
        {
          id: 'node_2',
          parentId: 'node_1',
          operatorType: 'NESTED_LOOP',
          joinType: 'INNER',
          estimatedCost: 92400.0,
          estimatedRowsBucket: '10K_TO_100K',
          actualRowsBucket: '10K_TO_100K',
          actualTimeMsBucket: '1S_TO_2S',
          loopsBucket: '1',
          depth: 1,
          isCritical: true,
          notes: 'Nested Loop repeatedly rescanning inner order relation'
        },
        {
          id: 'node_3',
          parentId: 'node_2',
          operatorType: 'INDEX_SCAN',
          relationToken: 'TBL_CUSTOMERS',
          indexToken: 'IDX_CUST_TIER',
          estimatedCost: 142.0,
          estimatedRowsBucket: '1K_TO_10K',
          actualRowsBucket: '1K_TO_10K',
          actualTimeMsBucket: '5MS_TO_20MS',
          loopsBucket: '1',
          depth: 2,
          isCritical: false
        },
        {
          id: 'node_4',
          parentId: 'node_2',
          operatorType: 'SEQ_SCAN',
          relationToken: 'TBL_ORDERS',
          estimatedCost: 92100.0,
          estimatedRowsBucket: '1M_TO_10M',
          actualRowsBucket: '10K_TO_100K',
          actualTimeMsBucket: '1S_TO_2S',
          loopsBucket: '1K_TO_10K',
          scanType: 'SEQ_SCAN',
          filterColumns: ['COL_CUST_ID', 'COL_STATUS'],
          depth: 2,
          isCritical: true,
          notes: 'Foreign key scan without covering composite index'
        }
      ]
    },
    recommendations: [
      {
        id: 'rec-02',
        queryEventId: 'qry-3e42',
        actionType: 'INDEX',
        title: 'Covering Index on (COL_CUST_ID, COL_STATUS) INCLUDE (COL_TOTAL_AMOUNT, COL_CREATED_AT)',
        maskedChangeTemplate: 'CREATE INDEX CONCURRENTLY ON TBL_ORDERS (COL_CUST_ID, COL_STATUS) INCLUDE (COL_TOTAL_AMOUNT, COL_CREATED_AT);',
        status: 'VALIDATED',
        confidence: 'HIGH',
        riskLevel: 'LOW',
        rankingScore: {
          score: 0.79,
          readBenefit: 0.92,
          writePenalty: 0.15,
          storagePenalty: 0.10,
          operationalRisk: 0.05
        },
        evidence: {
          version: '1.0',
          bottleneckType: 'REPEATED_INNER_LOOP',
          affectedPlanNodes: ['node_2', 'node_4'],
          reasonCodes: [
            'REPEATED_INNER_LOOP',
            'CARDINALITY_MISMATCH',
            'MISSING_FOREIGN_KEY_INDEX'
          ],
          observedEvidence: {
            scanType: 'SEQ_SCAN',
            loopCountBucket: '1K_TO_10K',
            relationSizeBucket: '1M_TO_10M',
            cardinalityMismatchRatio: 14.2
          },
          recommendedAction: 'INDEX',
          maskedChangeTemplate: 'CREATE INDEX CONCURRENTLY ON TBL_ORDERS (COL_CUST_ID, COL_STATUS) INCLUDE (COL_TOTAL_AMOUNT, COL_CREATED_AT);',
          alternativesConsidered: [
            {
              action: 'STATS_ADVISORY',
              rank: 2,
              reasonLowerRank: 'ANALYZE refresh needed but cannot replace missing join-key index.'
            }
          ],
          simulationSummary: {
            status: 'COMPLETED',
            label: 'Planner-based simulated estimate (HypoPG)',
            improvementRangePercent: [78, 88]
          },
          confidence: 'HIGH',
          riskLevel: 'LOW',
          limitations: [
            'INCLUDE columns add ~15% index byte width over standard composite index.',
            'Order insertion volume is moderate (80 tx/sec).'
          ],
          privacyStatus: 'Verified: No raw rows or plaintext schema identifiers used.'
        },
        simulation: {
          id: 'sim-02',
          recommendationId: 'rec-02',
          simulationEngine: 'HYPOPG',
          status: 'COMPLETED',
          baseline: {
            plannerCost: 94820.0,
            dominantOperations: ['NESTED_LOOP', 'SEQ_SCAN'],
            executionTimeEstimateMs: 1820.0
          },
          candidate: {
            plannerCost: 14220.0,
            dominantOperations: ['INDEX_ONLY_SCAN', 'HASH_JOIN'],
            executionTimeEstimateMs: 210.0
          },
          estimatedImprovementPercentRange: [78, 88],
          estimatedWriteOverheadMsRange: [1, 3],
          estimatedStorageOverheadGbRange: [2.1, 3.2],
          confidence: 'HIGH',
          limitations: [
            'Simulated using HypoPG virtual index.',
            'Index-Only scan requires up-to-date visibility map.'
          ],
          runAt: '6 mins ago'
        },
        createdAt: '12 mins ago'
      }
    ]
  },
  {
    id: 'qry-9f18',
    queryFingerprint: 'FP_9F185A27EE33',
    title: 'Multi-Year Audit & Security Event Scan',
    maskedQueryTemplate: `SELECT 
  COL_ACTOR_TOKEN, 
  COL_EVENT_TYPE, 
  COL_SEVERITY, 
  COL_CREATED_AT
FROM TBL_AUDIT_LOGS
WHERE COL_CREATED_AT >= :TIMESTAMP 
  AND COL_CREATED_AT < :TIMESTAMP
  AND COL_SEVERITY = :TEXT
ORDER BY COL_CREATED_AT DESC
LIMIT :INT;`,
    latencyMsBucket: '5S_TO_30S',
    averageDurationMs: 5640.0,
    frequencyBucket: '10_TO_100_PER_HR',
    callsPerMin: 2.8,
    impactScore: 84.1,
    bottleneckType: 'EXPENSIVE_SORT',
    analysisStatus: 'SIMULATED',
    privacyStatus: 'VERIFIED_MASKED',
    observedAt: '7 mins ago',
    planGraph: {
      id: 'pg-9f18',
      queryEventId: 'qry-9f18',
      planCost: 312900.5,
      planDepth: 2,
      nodeCount: 3,
      nodes: [
        {
          id: 'node_1',
          operatorType: 'SORT',
          estimatedCost: 312900.5,
          estimatedRowsBucket: '100K_TO_1M',
          actualRowsBucket: '100K_TO_1M',
          actualTimeMsBucket: '5S_TO_10S',
          loopsBucket: '1',
          depth: 0,
          isCritical: true,
          notes: 'High-cost disk sort spilling ~140MB to temporary tablespace'
        },
        {
          id: 'node_2',
          parentId: 'node_1',
          operatorType: 'SEQ_SCAN',
          relationToken: 'TBL_AUDIT_LOGS',
          estimatedCost: 260000.0,
          estimatedRowsBucket: '10M_TO_100M',
          actualRowsBucket: '10M_TO_100M',
          actualTimeMsBucket: '3S_TO_5S',
          loopsBucket: '1',
          scanType: 'SEQ_SCAN',
          filterColumns: ['COL_CREATED_AT', 'COL_SEVERITY'],
          depth: 1,
          isCritical: true,
          notes: 'Full table sequential scan on 45.2M audit records'
        }
      ]
    },
    recommendations: [
      {
        id: 'rec-03',
        queryEventId: 'qry-9f18',
        actionType: 'INDEX',
        title: 'Ordered Partial B-Tree Index on (COL_SEVERITY, COL_CREATED_AT DESC)',
        maskedChangeTemplate: 'CREATE INDEX CONCURRENTLY ON TBL_AUDIT_LOGS (COL_SEVERITY, COL_CREATED_AT DESC);',
        status: 'VALIDATED',
        confidence: 'HIGH',
        riskLevel: 'LOW',
        rankingScore: {
          score: 0.72,
          readBenefit: 0.84,
          writePenalty: 0.14,
          storagePenalty: 0.12,
          operationalRisk: 0.05
        },
        evidence: {
          version: '1.0',
          bottleneckType: 'EXPENSIVE_SORT',
          affectedPlanNodes: ['node_1', 'node_2'],
          reasonCodes: [
            'EXPENSIVE_SORT',
            'TIME_RANGE_REPETITION',
            'LARGE_SEQ_SCAN'
          ],
          observedEvidence: {
            scanType: 'SEQ_SCAN',
            sortSpillDetected: true,
            relationSizeBucket: '10M_TO_100M'
          },
          recommendedAction: 'INDEX',
          maskedChangeTemplate: 'CREATE INDEX CONCURRENTLY ON TBL_AUDIT_LOGS (COL_SEVERITY, COL_CREATED_AT DESC);',
          alternativesConsidered: [
            {
              action: 'PARTITION_ADVISORY',
              rank: 2,
              reasonLowerRank: 'Partitioning by monthly range is strategically recommended for retention, but requires migration window.'
            }
          ],
          simulationSummary: {
            status: 'COMPLETED',
            label: 'Planner-based simulated estimate (HypoPG)',
            improvementRangePercent: [68, 79]
          },
          confidence: 'HIGH',
          riskLevel: 'LOW',
          limitations: [
            'Avoids disk spill by delivering pre-sorted index tuples.',
            'Retention purging should also consider time partitioning.'
          ],
          privacyStatus: 'Verified: Sanitized tokens and bucketed cardinalities only.'
        },
        simulation: {
          id: 'sim-03',
          recommendationId: 'rec-03',
          simulationEngine: 'HYPOPG',
          status: 'COMPLETED',
          baseline: {
            plannerCost: 312900.5,
            dominantOperations: ['SORT', 'SEQ_SCAN'],
            executionTimeEstimateMs: 5640.0
          },
          candidate: {
            plannerCost: 89100.0,
            dominantOperations: ['INDEX_SCAN'],
            executionTimeEstimateMs: 920.0
          },
          estimatedImprovementPercentRange: [68, 79],
          estimatedWriteOverheadMsRange: [2, 4],
          estimatedStorageOverheadGbRange: [4.2, 5.8],
          confidence: 'HIGH',
          limitations: [
            'HypoPG simulated estimate only.',
            'Audit log table is append-only (low update contention).'
          ],
          runAt: '8 mins ago'
        },
        createdAt: '15 mins ago'
      },
      {
        id: 'rec-04',
        queryEventId: 'qry-9f18',
        actionType: 'PARTITION_ADVISORY',
        title: 'Strategic Partitioning Advisory: Range Partition by Month',
        maskedChangeTemplate: '-- ADVISORY ONLY (No automated migration executed):\n-- Partition TBL_AUDIT_LOGS BY RANGE (COL_CREATED_AT)\n-- Facilitates instant partition drop for retention policy and localized index scans.',
        status: 'VALIDATED',
        confidence: 'MEDIUM',
        riskLevel: 'HIGH',
        rankingScore: {
          score: 0.51,
          readBenefit: 0.90,
          writePenalty: 0.05,
          storagePenalty: 0.00,
          operationalRisk: 0.65
        },
        evidence: {
          version: '1.0',
          bottleneckType: 'TIME_RANGE_REPETITION',
          affectedPlanNodes: ['node_2'],
          reasonCodes: [
            'TIME_RANGE_REPETITION',
            'LARGE_DATASET_RETENTION'
          ],
          observedEvidence: {
            scanType: 'SEQ_SCAN',
            relationSizeBucket: '10M_TO_100M'
          },
          recommendedAction: 'PARTITION_ADVISORY',
          maskedChangeTemplate: '-- Architectural Partitioning Advisory',
          alternativesConsidered: [],
          confidence: 'MEDIUM',
          riskLevel: 'HIGH',
          limitations: [
            'Advisory only; QueryGuard never executes automated table migrations or DDL mutations in production.'
          ],
          privacyStatus: 'Verified: No plaintext identifiers used.'
        },
        createdAt: '15 mins ago'
      }
    ]
  },
  {
    id: 'qry-1a84',
    queryFingerprint: 'FP_1A84D3100B7',
    title: 'Ad-hoc Inventory Reorder Batch Query',
    maskedQueryTemplate: `SELECT COL_PRODUCT_ID, COL_WAREHOUSE_ID, COL_STOCK_LEVEL
FROM TBL_INVENTORY
WHERE COL_UPDATED_AT > NOW() - INTERVAL :INTERVAL;`,
    latencyMsBucket: '100MS_TO_1S',
    averageDurationMs: 420.0,
    frequencyBucket: '1_TO_10_PER_HR',
    callsPerMin: 0.2,
    impactScore: 28.0,
    bottleneckType: 'INSUFFICIENT_EVIDENCE',
    analysisStatus: 'ABSTAINED',
    privacyStatus: 'VERIFIED_MASKED',
    observedAt: '25 mins ago',
    planGraph: {
      id: 'pg-1a84',
      queryEventId: 'qry-1a84',
      planCost: 450.0,
      planDepth: 1,
      nodeCount: 1,
      nodes: [
        {
          id: 'node_1',
          operatorType: 'INDEX_SCAN',
          relationToken: 'TBL_INVENTORY',
          indexToken: 'IDX_INV_UPDATED',
          estimatedCost: 450.0,
          estimatedRowsBucket: '100_TO_1K',
          actualRowsBucket: '100_TO_1K',
          actualTimeMsBucket: '100MS_TO_1S',
          loopsBucket: '1',
          depth: 0,
          isCritical: false
        }
      ]
    },
    recommendations: [
      {
        id: 'rec-05',
        queryEventId: 'qry-1a84',
        actionType: 'ABSTAIN',
        title: 'System Abstains: Insufficient Evidence of Degradation',
        maskedChangeTemplate: '-- NO ACTION RECOMMENDED\n-- Existing B-tree index is optimal; planner cost is already minimal (<500).',
        status: 'VALIDATED',
        confidence: 'HIGH',
        riskLevel: 'LOW',
        rankingScore: {
          score: 0.0,
          readBenefit: 0.0,
          writePenalty: 0.0,
          storagePenalty: 0.0,
          operationalRisk: 0.0
        },
        evidence: {
          version: '1.0',
          bottleneckType: 'INSUFFICIENT_EVIDENCE',
          affectedPlanNodes: ['node_1'],
          reasonCodes: ['INSUFFICIENT_EVIDENCE', 'OPTIMAL_ACCESS_PATH'],
          observedEvidence: {
            scanType: 'INDEX_SCAN'
          },
          recommendedAction: 'ABSTAIN',
          maskedChangeTemplate: '-- System intentionally abstains rather than producing false certainty.',
          alternativesConsidered: [],
          confidence: 'HIGH',
          riskLevel: 'LOW',
          limitations: [
            'System abstention prevents false certainty and index bloat.'
          ],
          privacyStatus: 'Verified: Sanitized query template.'
        },
        createdAt: '25 mins ago'
      }
    ]
  }
];

export const INITIAL_AUDIT_LOGS: AuditLogItem[] = [
  {
    id: 'aud-001',
    timestamp: '2026-10-03 13:40:12 UTC',
    actorId: 'system',
    actorName: 'Privacy Gateway',
    actorRole: 'DBA',
    eventType: 'INGESTED',
    entityType: 'QUERY',
    entityId: 'qry-7c91',
    description: 'PostgreSQL EXPLAIN plan ingested from demo workload.',
    metadataJson: { source: 'demo_seeder', rawByteSize: 4120, planNodes: 5 },
    privacyStatus: 'VERIFIED_MASKED'
  },
  {
    id: 'aud-002',
    timestamp: '2026-10-03 13:40:13 UTC',
    actorId: 'system',
    actorName: 'Privacy Gateway',
    actorRole: 'DBA',
    eventType: 'MASKED',
    entityType: 'PRIVACY_GATEWAY',
    entityId: 'qry-7c91',
    description: 'Literals replaced with :INT/:TEXT/:TIMESTAMP, schema tokens hashed via HMAC-SHA256.',
    metadataJson: { literalsReplaced: 4, tokensGenerated: ['TBL_SALES', 'TBL_STORES', 'COL_REGION_ID'] },
    privacyStatus: 'VERIFIED_MASKED'
  },
  {
    id: 'aud-003',
    timestamp: '2026-10-03 13:40:15 UTC',
    actorId: 'system',
    actorName: 'Rule Engine',
    actorRole: 'DBA',
    eventType: 'ANALYZED',
    entityType: 'QUERY',
    entityId: 'qry-7c91',
    description: 'Deterministic rule detected LARGE_SEQ_SCAN & REPEATED_INNER_LOOP.',
    metadataJson: { ruleId: 'LARGE_SEQ_SCAN', severity: 'HIGH', confidence: 'HIGH' },
    privacyStatus: 'VERIFIED_MASKED'
  },
  {
    id: 'aud-004',
    timestamp: '2026-10-03 13:42:01 UTC',
    actorId: 'usr-1',
    actorName: 'Priya Sharma (DBA)',
    actorRole: 'DBA',
    eventType: 'SIMULATED',
    entityType: 'SIMULATION',
    entityId: 'sim-01',
    description: 'Safe HypoPG virtual index simulation completed. Cost reduced from 182,341 to 30,510 (-83.3%).',
    metadataJson: { engine: 'HYPOPG', costBefore: 182341.2, costAfter: 30510.8, physicalDDLExecuted: false },
    privacyStatus: 'VERIFIED_MASKED'
  }
];

export const PRIVACY_SELF_TEST_FIXTURES = [
  {
    name: 'Raw SQL Literals & Comments',
    rawInput: "SELECT * FROM users WHERE email = 'priya@corp.internal' AND password_hash = 'secret123' /* audit-check */",
    expectedMasked: "SELECT :ARRAY FROM TBL_A88F WHERE COL_E01 = :TEXT AND COL_P02 = :TEXT",
    status: 'PASS',
    reason: 'Comments stripped; sensitive literals replaced with typed placeholders (:TEXT).'
  },
  {
    name: 'Schema Identifier HMAC Tokenization',
    rawInput: "SELECT customer_id, order_total FROM customer_orders WHERE status = 'COMPLETED'",
    expectedMasked: "SELECT COL_A10, COL_B22 FROM TBL_C99 WHERE COL_S04 = :TEXT",
    status: 'PASS',
    reason: 'Tenant-scoped keyed HMAC-SHA256 irreversible by analysis service.'
  },
  {
    name: 'Leakage Interceptor (Fail-Closed)',
    rawInput: "SELECT * FROM payments WHERE api_key = 'sk_live_99214' OR card_num = '4111222233334444'",
    expectedMasked: "[BLOCKED BY PRIVACY GATEWAY - ZERO RAW DATA EXPORTED]",
    status: 'PASS',
    reason: 'Leakage pattern detected; event quarantined and analysis blocked.'
  },
  {
    name: 'AST Parse & Read-Only Enforcement',
    rawInput: "DROP TABLE sensitive_logs; SELECT 1;",
    expectedMasked: "[BLOCKED: MULTI_STATEMENT_OR_DDL_FORBIDDEN]",
    status: 'PASS',
    reason: 'SQL Safety Gateway rejected destructive DDL; single SELECT statement policy enforced.'
  }
];
