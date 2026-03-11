import { useCallback, useRef } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  useReactFlow,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import useWorkflowStore from '../../store/workflowStore'
import nodeTypes from '../Nodes/nodeTypes'
import OutputPanel from '../OutputPanel/OutputPanel'
import './Canvas.css'

const TRIGGER_TYPES = ['manual_trigger', 'webhook_trigger', 'scheduler']

export default function Canvas() {
  const {
    nodes, edges,
    onNodesChange, onEdgesChange, onConnect,
    addNode, clearSelection,
    nodeRunStates,
  } = useWorkflowStore()

  const reactFlowWrapper = useRef(null)
  const { screenToFlowPosition } = useReactFlow()

  const onDragOver = useCallback((e) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }, [])

  const onDrop = useCallback((e) => {
    e.preventDefault()
    const type = e.dataTransfer.getData('application/reactflow-type')
    const defRaw = e.dataTransfer.getData('application/reactflow-def')
    if (!type || !defRaw) return

    // Only allow one trigger node at a time
    const existingTrigger = nodes.find(n => TRIGGER_TYPES.includes(n.type))
    if (TRIGGER_TYPES.includes(type) && existingTrigger) {
      alert('You can only have one trigger node per workflow.\nDelete the existing trigger first.')
      return
    }

    const definition = JSON.parse(defRaw)
    const position = screenToFlowPosition({ x: e.clientX, y: e.clientY })
    addNode(type, position, definition)
  }, [screenToFlowPosition, addNode, nodes])

  const onPaneClick = useCallback(() => clearSelection(), [clearSelection])

  // Inject run state into node data for visual feedback
  const nodesWithState = nodes.map(n => ({
    ...n,
    data: {
      ...n.data,
      runState: nodeRunStates?.[n.id] || 'idle'
    },
    className: nodeRunStates?.[n.id]
      ? `node-state--${nodeRunStates[n.id]}`
      : ''
  }))

  const hasTrigger = nodes.some(n => TRIGGER_TYPES.includes(n.type))

  return (
    <div className="canvas-wrapper" ref={reactFlowWrapper}>
      <ReactFlow
        nodes={nodesWithState}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onPaneClick={onPaneClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        defaultEdgeOptions={{
          animated: true,
          style: { stroke: '#3d4680', strokeWidth: 2 }
        }}
        connectionLineStyle={{ stroke: '#6366f1', strokeWidth: 2 }}
        snapToGrid={true}
        snapGrid={[15, 15]}
        deleteKeyCode="Delete"
      >
        <Background variant={BackgroundVariant.Dots} gap={24} size={1} color="#1f2440" />
        <Controls showInteractive={false} />
        <MiniMap
          nodeColor={n => {
            const state = nodeRunStates?.[n.id]
            if (state === 'success') return '#10b981'
            if (state === 'error')   return '#ef4444'
            if (state === 'skipped') return '#94a3b8'
            const def = n.data?.definition
            return { trigger:'#3b82f6', action:'#10b981', ai:'#8b5cf6', logic:'#ef4444' }[def?.category] || '#6366f1'
          }}
          maskColor="rgba(12,14,26,0.8)"
        />
      </ReactFlow>

      {/* Empty state */}
      {nodes.length === 0 && <EmptyState />}

      {/* "No trigger" hint when nodes exist but no trigger */}
      {nodes.length > 0 && !hasTrigger && (
        <div className="canvas-hint">
          <span>⚡</span> Add a <strong>Trigger</strong> node to run this workflow
        </div>
      )}

      <OutputPanel />
    </div>
  )
}

function EmptyState() {
  return (
    <div className="canvas-empty">
      <div className="canvas-empty__inner">
        <div className="canvas-empty__icon">⚡</div>
        <h2>Build your first workflow</h2>
        <p>Drag nodes from the left panel onto the canvas.<br/>Connect them to create an automation.</p>
        <div className="canvas-empty__steps">
          <div className="step"><span>1</span> Drag a <strong>Trigger</strong> node first</div>
          <div className="step"><span>2</span> Add <strong>Action</strong> nodes</div>
          <div className="step"><span>3</span> Connect them with arrows</div>
          <div className="step"><span>4</span> Click <strong>Run Workflow</strong></div>
        </div>
      </div>
    </div>
  )
}
