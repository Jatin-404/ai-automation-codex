import { Handle, Position, useReactFlow } from '@xyflow/react'
import { useState } from 'react'
import useWorkflowStore from '../../store/workflowStore'
import clsx from 'clsx'
import './BaseNode.css'

const CATEGORY_COLORS = {
  trigger: '#3b82f6',
  action:  '#10b981',
  ai:      '#8b5cf6',
  logic:   '#ef4444',
}

export default function BaseNode({ id, data, selected }) {
  const { selectNode, nodes } = useWorkflowStore()
  const node = nodes.find(n => n.id === id)
  const def = data.definition || {}
  const color = CATEGORY_COLORS[def.category] || '#6366f1'

  const handleClick = (e) => {
    e.stopPropagation()
    selectNode(node)
  }

  const hasInput  = def.inputs  > 0
  const hasOutput = def.outputs > 0
  const hasTwoOutputs = def.outputs === 2

  return (
    <div
      className={clsx('base-node', selected && 'base-node--selected')}
      style={{ '--node-color': color }}
      onClick={handleClick}
    >
      {/* Input handle */}
      {hasInput && (
        <Handle
          type="target"
          position={Position.Left}
          className="node-handle node-handle--input"
        />
      )}

      {/* Node header */}
      <div className="base-node__header">
        <span className="base-node__icon">{def.icon || '⚙️'}</span>
        <div className="base-node__titles">
          <span className="base-node__label">{data.label || def.label}</span>
          <span className="base-node__type">{def.category}</span>
        </div>
        <div className="base-node__status-dot" />
      </div>

      {/* Config preview */}
      <div className="base-node__preview">
        {getConfigPreview(data.config, def)}
      </div>

      {/* Output handle(s) */}
      {hasOutput && !hasTwoOutputs && (
        <Handle
          type="source"
          position={Position.Right}
          id="output-0"
          className="node-handle node-handle--output"
        />
      )}

      {/* Split node: TRUE / FALSE handles */}
      {hasTwoOutputs && (
        <>
          <Handle
            type="source"
            position={Position.Right}
            id="output-0"
            style={{ top: '35%' }}
            className="node-handle node-handle--output node-handle--true"
          />
          <Handle
            type="source"
            position={Position.Right}
            id="output-1"
            style={{ top: '65%' }}
            className="node-handle node-handle--output node-handle--false"
          />
          <div className="split-labels">
            <span className="split-label split-label--true">✅</span>
            <span className="split-label split-label--false">❌</span>
          </div>
        </>
      )}
    </div>
  )
}

function getConfigPreview(config, def) {
  if (!config || Object.keys(config).length === 0) {
    return <span className="preview-empty">Click to configure →</span>
  }
  // Show the first 2 filled config values as a preview
  const entries = Object.entries(config).filter(([, v]) => v !== '' && v !== null && v !== undefined)
  const top = entries.slice(0, 2)
  return top.map(([k, v]) => (
    <div key={k} className="preview-row">
      <span className="preview-key">{k}:</span>
      <span className="preview-val">{String(v).slice(0, 28)}</span>
    </div>
  ))
}