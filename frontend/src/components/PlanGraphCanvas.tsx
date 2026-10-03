import React, { useState } from 'react';
import { 
  ZoomIn, 
  ZoomOut, 
  Maximize2, 
  AlertCircle, 
  ArrowDown, 
  Filter,
  CheckCircle2,
  ListTree,
  Network,
  Layers,
  ChevronRight
} from 'lucide-react';
import type { PlanGraphData, PlanNodeData } from '../types/queryguard';

interface PlanGraphCanvasProps {
  planGraph: PlanGraphData;
  onSelectNode?: (node: PlanNodeData) => void;
}

export const PlanGraphCanvas: React.FC<PlanGraphCanvasProps> = ({ 
  planGraph, 
  onSelectNode 
}) => {
  const [selectedNodeId, setSelectedNodeId] = useState<string>(
    planGraph.nodes.find(n => n.isCritical)?.id || planGraph.nodes[0]?.id || ''
  );
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [viewMode, setViewMode] = useState<'graph' | 'tree'>('graph');

  const selectedNode = planGraph.nodes.find(n => n.id === selectedNodeId);

  const handleNodeClick = (node: PlanNodeData) => {
    setSelectedNodeId(node.id);
    if (onSelectNode) onSelectNode(node);
  };

  const getOperatorColor = (type: PlanNodeData['operatorType'], isCritical: boolean) => {
    if (isCritical) return 'var(--graph-critical)';
    switch (type) {
      case 'SEQ_SCAN':
        return 'var(--graph-scan)';
      case 'INDEX_SCAN':
      case 'INDEX_ONLY_SCAN':
        return 'var(--graph-index)';
      case 'NESTED_LOOP':
      case 'HASH_JOIN':
        return 'var(--graph-join)';
      case 'SORT':
      case 'AGGREGATE':
        return 'var(--graph-sort)';
      default:
        return 'var(--info-text)';
    }
  };

  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column', height: 440 }}>
      {/* Header bar with controls */}
      <div style={{
        padding: '10px 16px',
        backgroundColor: 'var(--bg-subtle)',
        borderBottom: '1px solid var(--border-default)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontWeight: 700, fontSize: 13, color: 'var(--text-primary)' }}>
            Execution Plan Graph (Visual DAG)
          </span>
          <span className="badge badge-neutral" style={{ fontSize: 11 }}>
            {planGraph.nodeCount} Operators • Depth {planGraph.planDepth}
          </span>
          <span className="badge badge-brand" style={{ fontSize: 11 }}>
            Query Plan Cost: {planGraph.planCost.toLocaleString()}
          </span>
        </div>

        {/* View toggle and zoom controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{ display: 'flex', background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-default)', padding: 2 }}>
            <button
              onClick={() => setViewMode('graph')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                padding: '4px 8px',
                fontSize: 11,
                borderRadius: 'var(--radius-sm)',
                background: viewMode === 'graph' ? 'var(--bg-surface-raised)' : 'transparent',
                color: viewMode === 'graph' ? 'var(--text-primary)' : 'var(--text-muted)',
                fontWeight: viewMode === 'graph' ? 700 : 500
              }}
            >
              <Network size={12} />
              <span>DAG Canvas</span>
            </button>
            <button
              onClick={() => setViewMode('tree')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                padding: '4px 8px',
                fontSize: 11,
                borderRadius: 'var(--radius-sm)',
                background: viewMode === 'tree' ? 'var(--bg-surface-raised)' : 'transparent',
                color: viewMode === 'tree' ? 'var(--text-primary)' : 'var(--text-muted)',
                fontWeight: viewMode === 'tree' ? 700 : 500
              }}
            >
              <ListTree size={12} />
              <span>Tree Hierarchy</span>
            </button>
          </div>

          <div style={{ height: 16, width: 1, backgroundColor: 'var(--border-default)', margin: '0 4px' }} />

          <button 
            onClick={() => setZoomLevel(prev => Math.min(prev + 0.15, 1.4))}
            className="btn btn-ghost" 
            style={{ padding: 4 }} 
            title="Zoom In"
          >
            <ZoomIn size={14} />
          </button>
          <button 
            onClick={() => setZoomLevel(prev => Math.max(prev - 0.15, 0.7))}
            className="btn btn-ghost" 
            style={{ padding: 4 }} 
            title="Zoom Out"
          >
            <ZoomOut size={14} />
          </button>
          <button 
            onClick={() => {
              setZoomLevel(1);
              const crit = planGraph.nodes.find(n => n.isCritical);
              if (crit) setSelectedNodeId(crit.id);
            }}
            className="btn btn-ghost" 
            style={{ padding: 4 }} 
            title="Focus Critical Path / Reset"
          >
            <Maximize2 size={14} />
          </button>
        </div>
      </div>

      {/* Main split canvas: Visual DAG on Left, Node Inspector on Right */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Canvas area */}
        <div style={{
          flex: 1,
          overflow: 'auto',
          backgroundColor: '#F8FAFC',
          backgroundImage: 'radial-gradient(#CBD5E1 1px, transparent 1px)',
          backgroundSize: '20px 20px',
          padding: 24,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          position: 'relative'
        }}>
          {/* Graph Legend */}
          <div style={{
            position: 'absolute',
            bottom: 12,
            left: 12,
            display: 'flex',
            gap: 12,
            background: '#FFFFFF',
            border: '1px solid #E2E8F0',
            padding: '6px 12px',
            borderRadius: 'var(--radius-sm)',
            fontSize: 11,
            boxShadow: 'var(--shadow-sm)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#DC2626' }} />
              <span style={{ color: 'var(--text-secondary)' }}>Bottleneck Path</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--graph-scan)' }} />
              <span style={{ color: 'var(--text-secondary)' }}>Seq Scan</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--graph-join)' }} />
              <span style={{ color: 'var(--text-secondary)' }}>Join</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--graph-index)' }} />
              <span style={{ color: 'var(--text-secondary)' }}>Index Scan</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--graph-sort)' }} />
              <span style={{ color: 'var(--text-secondary)' }}>Sort/Aggregate</span>
            </div>
          </div>

          {/* Conditional View: Graph vs Tree */}
          {viewMode === 'graph' ? (
            <div style={{
              transform: `scale(${zoomLevel})`,
              transformOrigin: 'top center',
              transition: 'transform 0.15s ease',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 14,
              width: '100%',
              maxWidth: 600
            }}>
              {planGraph.nodes.map((node, index) => {
                const isSelected = node.id === selectedNodeId;
                const opColor = getOperatorColor(node.operatorType, node.isCritical);

                return (
                  <React.Fragment key={node.id}>
                    {index > 0 && (
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', color: '#94A3B8', margin: '-6px 0' }}>
                        <div style={{ width: 2, height: 12, backgroundColor: node.isCritical ? '#FECACA' : '#E2E8F0' }} />
                        <ArrowDown size={14} style={{ color: node.isCritical ? '#DC2626' : '#94A3B8' }} />
                      </div>
                    )}

                    <div
                      onClick={() => handleNodeClick(node)}
                      style={{
                        width: '100%',
                        backgroundColor: node.isCritical ? '#FEF2F2' : isSelected ? '#FFFFFF' : '#FFFFFF',
                        border: isSelected 
                          ? '2px solid #0F766E' 
                          : node.isCritical 
                            ? '1px solid #FECACA' 
                            : '1px solid #E2E8F0',
                        borderRadius: 'var(--radius-md)',
                        padding: '12px 16px',
                        cursor: 'pointer',
                        boxShadow: node.isCritical ? '0 2px 8px rgba(220, 38, 38, 0.12)' : '0 2px 4px rgba(15, 23, 42, 0.05)',
                        transition: 'all 0.15s ease',
                        position: 'relative'
                      }}
                      className={node.isCritical ? 'pulse-critical' : ''}
                    >
                      {node.isCritical && (
                        <span 
                          className="badge badge-danger" 
                          style={{ position: 'absolute', top: -9, right: 12, fontSize: 10, padding: '1px 6px', backgroundColor: '#FEF2F2', border: '1px solid #FECACA', color: '#DC2626' }}
                        >
                          Bottleneck Node
                        </span>
                      )}

                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{
                            display: 'inline-block',
                            width: 10,
                            height: 10,
                            borderRadius: 2,
                            backgroundColor: opColor
                          }} />
                          <strong style={{ fontSize: 13, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                            {node.operatorType}
                          </strong>
                          {node.relationToken && (
                            <span className="badge badge-neutral font-mono" style={{ fontSize: 11 }}>
                              {node.relationToken}
                            </span>
                          )}
                          {node.joinType && (
                            <span className="badge badge-info" style={{ fontSize: 10 }}>
                              {node.joinType}
                            </span>
                          )}
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 12 }}>
                          <span style={{ color: 'var(--text-muted)' }}>Cost:</span>
                          <strong className="font-mono tabular-nums" style={{ color: node.isCritical ? 'var(--danger-text)' : 'var(--text-secondary)' }}>
                            {node.estimatedCost.toLocaleString()}
                          </strong>
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)' }}>
                        <div>
                          <span>Est. Rows: </span>
                          <span className="font-mono" style={{ color: 'var(--text-secondary)' }}>{node.estimatedRowsBucket}</span>
                          {node.actualRowsBucket && (
                            <>
                              <span style={{ margin: '0 4px' }}>•</span>
                              <span>Actual: </span>
                              <span className="font-mono" style={{ color: 'var(--text-secondary)' }}>{node.actualRowsBucket}</span>
                            </>
                          )}
                        </div>
                        {node.filterColumns && node.filterColumns.length > 0 && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                            <Filter size={11} />
                            <span className="font-mono">{node.filterColumns.join(', ')}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </React.Fragment>
                );
              })}
            </div>
          ) : (
            /* Tree Hierarchy View */
            <div style={{ width: '100%', maxWidth: 620, display: 'flex', flexDirection: 'column', gap: 8 }}>
              {planGraph.nodes.map((node) => {
                const isSelected = node.id === selectedNodeId;
                const indent = node.depth * 24;
                const opColor = getOperatorColor(node.operatorType, node.isCritical);

                return (
                  <div
                    key={node.id}
                    onClick={() => handleNodeClick(node)}
                    style={{
                      marginLeft: indent,
                      backgroundColor: isSelected ? 'var(--bg-surface-raised)' : 'var(--bg-surface)',
                      border: `1px solid ${isSelected ? 'var(--brand-primary)' : 'var(--border-default)'}`,
                      borderRadius: 'var(--radius-sm)',
                      padding: '10px 14px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <ChevronRight size={13} style={{ color: 'var(--text-muted)' }} />
                      <span style={{ width: 8, height: 8, borderRadius: 2, backgroundColor: opColor }} />
                      <strong className="font-mono" style={{ fontSize: 12, color: 'var(--text-primary)' }}>
                        {node.operatorType}
                      </strong>
                      {node.relationToken && (
                        <span className="badge badge-neutral font-mono" style={{ fontSize: 10 }}>
                          {node.relationToken}
                        </span>
                      )}
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      {node.isCritical && (
                        <span className="badge badge-danger" style={{ fontSize: 10 }}>
                          Bottleneck
                        </span>
                      )}
                      <span className="font-mono tabular-nums" style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                        cost={node.estimatedCost.toLocaleString()}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Node Inspector Panel on Right */}
        <div style={{
          width: 290,
          borderLeft: '1px solid var(--border-default)',
          backgroundColor: 'var(--bg-surface)',
          padding: 16,
          overflowY: 'auto'
        }}>
          <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: 12 }}>
            Node Inspector
          </div>

          {selectedNode ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span style={{
                    width: 10,
                    height: 10,
                    borderRadius: 2,
                    backgroundColor: getOperatorColor(selectedNode.operatorType, selectedNode.isCritical)
                  }} />
                  <strong style={{ fontSize: 14, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                    {selectedNode.operatorType}
                  </strong>
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  ID: {selectedNode.id} • Depth {selectedNode.depth}
                </div>
              </div>

              {selectedNode.isCritical && (
                <div style={{
                  background: 'var(--danger-muted)',
                  border: '1px solid var(--danger-border)',
                  padding: 10,
                  borderRadius: 'var(--radius-sm)',
                  fontSize: 11,
                  color: 'var(--danger-text)',
                  lineHeight: 1.4
                }}>
                  <strong>Critical Path Bottleneck:</strong> Primary execution cost contributor in the plan graph.
                </div>
              )}

              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 6, borderBottom: '1px solid var(--border-default)' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Relation Token:</span>
                  <span className="font-mono" style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                    {selectedNode.relationToken || 'None (In-Memory)'}
                  </span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 6, borderBottom: '1px solid var(--border-default)' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Estimated Cost:</span>
                  <span className="font-mono tabular-nums" style={{ color: 'var(--text-primary)', fontWeight: 700 }}>
                    {selectedNode.estimatedCost.toLocaleString()}
                  </span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 6, borderBottom: '1px solid var(--border-default)' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Estimated Rows:</span>
                  <span className="font-mono" style={{ color: 'var(--text-secondary)' }}>
                    {selectedNode.estimatedRowsBucket}
                  </span>
                </div>

                {selectedNode.actualRowsBucket && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 6, borderBottom: '1px solid var(--border-default)' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Actual Rows:</span>
                    <span className="font-mono" style={{ color: 'var(--text-secondary)' }}>
                      {selectedNode.actualRowsBucket}
                    </span>
                  </div>
                )}

                {selectedNode.actualTimeMsBucket && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 6, borderBottom: '1px solid var(--border-default)' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Execution Time:</span>
                    <span className="font-mono" style={{ color: 'var(--text-secondary)' }}>
                      {selectedNode.actualTimeMsBucket}
                    </span>
                  </div>
                )}

                {selectedNode.filterColumns && selectedNode.filterColumns.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4, paddingBottom: 6, borderBottom: '1px solid var(--border-default)' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Filter Predicates:</span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                      {selectedNode.filterColumns.map(col => (
                        <span key={col} className="badge badge-neutral font-mono" style={{ fontSize: 10 }}>
                          {col}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {selectedNode.notes && (
                <div style={{ fontSize: 11, color: 'var(--text-secondary)', background: 'var(--bg-subtle)', padding: 10, borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-default)', lineHeight: 1.4 }}>
                  <strong>Diagnostic Note:</strong> {selectedNode.notes}
                </div>
              )}
            </div>
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>
              Select a node in the graph to inspect detailed execution metadata.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
