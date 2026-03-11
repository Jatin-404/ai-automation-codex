import { create } from 'zustand'
import { addEdge, applyNodeChanges, applyEdgeChanges } from '@xyflow/react'
import { nanoid } from '../utils/nanoid'

const TRIGGER_TYPES = ['manual_trigger', 'webhook_trigger', 'scheduler']

const useWorkflowStore = create((set, get) => ({
  // ── Canvas ────────────────────────────────────────────────────
  nodes: [],
  edges: [],
  selectedNode: null,

  onNodesChange: (changes) =>
    set({ nodes: applyNodeChanges(changes, get().nodes) }),

  onEdgesChange: (changes) =>
    set({ edges: applyEdgeChanges(changes, get().edges) }),

  onConnect: (connection) =>
    set({ edges: addEdge({ ...connection, id: `e-${nanoid()}`, animated: true }, get().edges) }),

  addNode: (nodeType, position, definition) => {
    const id = `node-${nanoid()}`
    const newNode = {
      id,
      type: nodeType,
      position,
      data: { label: definition.label, config: {}, definition }
    }
    set({ nodes: [...get().nodes, newNode] })
    return id
  },

  updateNodeConfig: (nodeId, config) =>
    set({
      nodes: get().nodes.map(n =>
        n.id === nodeId ? { ...n, data: { ...n.data, config } } : n
      )
    }),

  updateNodeLabel: (nodeId, label) =>
    set({
      nodes: get().nodes.map(n =>
        n.id === nodeId ? { ...n, data: { ...n.data, label } } : n
      )
    }),

  deleteNode: (nodeId) =>
    set({
      nodes: get().nodes.filter(n => n.id !== nodeId),
      edges: get().edges.filter(e => e.source !== nodeId && e.target !== nodeId),
      selectedNode: get().selectedNode?.id === nodeId ? null : get().selectedNode
    }),

  selectNode: (node) => set({ selectedNode: node }),
  clearSelection: () => set({ selectedNode: null }),

  // ── Trigger awareness ─────────────────────────────────────────
  getTriggerNode: () => {
    return get().nodes.find(n => TRIGGER_TYPES.includes(n.type)) || null
  },

  getTriggerType: () => {
    const trigger = get().nodes.find(n => TRIGGER_TYPES.includes(n.type))
    return trigger?.type || null
  },

  // ── Input field tracking (for config panel expression builder) ─
  // nodeId → { fieldName: exampleValue }
  nodeOutputSchemas: {},

  setNodeOutputSchema: (nodeId, schema) =>
    set({ nodeOutputSchemas: { ...get().nodeOutputSchemas, [nodeId]: schema } }),

  // Get the output schema of the node connected BEFORE the selected node
  getInputSchemaForNode: (nodeId) => {
    const edges = get().edges
    const schemas = get().nodeOutputSchemas
    const nodes = get().nodes
    const incomingEdges = edges.filter(e => e.target === nodeId)
    if (!incomingEdges.length) return {}
    if (incomingEdges.length === 1) {
      return schemas[incomingEdges[0].source] || {}
    }
    const merged = {}
    incomingEdges.forEach(e => {
      const sourceNode = nodes.find(n => n.id === e.source)
      const label = sourceNode?.data?.label || sourceNode?.id || e.source
      const inputLabel = e.targetHandle ? `${label} (${e.targetHandle})` : label
      merged[inputLabel] = schemas[e.source] || {}
    })
    return merged
  },

  // ── Run state ─────────────────────────────────────────────────
  isRunning: false,
  runResult: null,
  runError: null,
  nodeRunStates: {}, // nodeId → 'running' | 'success' | 'error'

  setRunning: (v) => set({ isRunning: v }),

  setRunResult: (r) => {
    // Extract per-node states from the log
    const nodeRunStates = {}
    const nodeOutputSchemas = { ...get().nodeOutputSchemas }

    if (r?.log) {
      r.log.forEach(entry => {
        if (entry.node_id === 'engine') return
        if (['success', 'error', 'running', 'skipped'].includes(entry.status)) {
          nodeRunStates[entry.node_id] = entry.status
        }
      })
    }

    // Store output schemas from node items (n8n-style)
    if (r?.node_items) {
      Object.entries(r.node_items).forEach(([nodeId, outputs]) => {
        const firstItem = outputs?.[0]?.[0]
        const json = firstItem?.json
        if (json && typeof json === 'object' && !Array.isArray(json)) {
          nodeOutputSchemas[nodeId] = json
        } else if (json !== undefined) {
          nodeOutputSchemas[nodeId] = { value: json }
        }
      })
    } else if (r?.node_outputs) {
      Object.entries(r.node_outputs).forEach(([nodeId, output]) => {
        if (output && typeof output === 'object' && !Array.isArray(output)) {
          nodeOutputSchemas[nodeId] = output
        } else if (output !== null && output !== undefined) {
          nodeOutputSchemas[nodeId] = { value: output }
        }
      })
    }

    set({ runResult: r, runError: null, nodeRunStates, nodeOutputSchemas })
  },

  setRunError: (e) => set({ runError: e, runResult: null }),
  clearRunResult: () => set({ runResult: null, runError: null, nodeRunStates: {} }),

  // ── Scheduler activation ─────────────────────────────────────
  scheduledWorkflows: {},  // workflowId → { active, interval }

  setScheduleActive: (workflowId, info) =>
    set({ scheduledWorkflows: { ...get().scheduledWorkflows, [workflowId]: info } }),

  removeSchedule: (workflowId) => {
    const sw = { ...get().scheduledWorkflows }
    delete sw[workflowId]
    set({ scheduledWorkflows: sw })
  },

  // ── Node palette ─────────────────────────────────────────────
  availableNodes: [],
  setAvailableNodes: (nodes) => set({ availableNodes: nodes }),
}))

export default useWorkflowStore
