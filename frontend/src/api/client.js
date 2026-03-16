import axios from 'axios'

const normalizeBase = (raw) => {
  if (!raw) return raw
  return raw.endsWith('/') ? raw.slice(0, -1) : raw
}

const inferBaseURL = () => {
  if (typeof window === 'undefined') return '/api'
  const { hostname, port, origin } = window.location
  const isLocal = hostname === 'localhost' || hostname === '127.0.0.1'
  const isFrontendPort = port === '5173' || port === '4173'
  if (isLocal && isFrontendPort) return `http://${hostname}:8000/api`
  return `${origin}/api`
}

const baseURL = normalizeBase(import.meta.env.VITE_API_BASE_URL || inferBaseURL())
const api = axios.create({ baseURL })

// ── Workflow execution ────────────────────────────────────────
export const runWorkflow = (nodes, edges, payload = null) =>
  api.post('/workflows/run', { nodes, edges, payload })

export const runWorkflowNode = (nodes, edges, node_id, payload = null) =>
  api.post('/workflows/run-node', { nodes, edges, node_id, payload })

export const validateWorkflow = (nodes, edges) =>
  api.post('/workflows/validate', { nodes, edges })

// ── Scheduler ────────────────────────────────────────────────
export const activateSchedule = (workflowId, nodes, edges, intervalType, intervalValue) =>
  api.post('/workflows/schedule', {
    workflow_id: workflowId,
    nodes,
    edges,
    interval_type: intervalType,
    interval_value: intervalValue
  })

export const deactivateSchedule = (workflowId) =>
  api.delete(`/workflows/schedule/${workflowId}`)

export const getScheduledJobs = () =>
  api.get('/workflows/schedule')

// ── Webhooks ─────────────────────────────────────────────────
export const testWebhook = (path, payload = {}, method = 'post') =>
  api.request({ url: `/webhooks${path}`, method, data: payload })

export const registerWebhook = (path, method, nodes, edges) =>
  api.post('/workflows/webhook/register', { path, method, nodes, edges })

export const unregisterWebhook = (path, method) =>
  api.post('/workflows/webhook/unregister', { path, method })

// ── Node palette ─────────────────────────────────────────────
export const fetchAvailableNodes = () =>
  api.get('/nodes')

export const getExampleWorkflow = () =>
  api.get('/workflows/example')
