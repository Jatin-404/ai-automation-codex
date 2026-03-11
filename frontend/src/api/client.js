import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

// ── Workflow execution ────────────────────────────────────────
export const runWorkflow = (nodes, edges, payload = null) =>
  api.post('/workflows/run', { nodes, edges, payload })

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
export const testWebhook = (path, payload = {}) =>
  api.post(`/webhooks${path}`, payload)

// ── Node palette ─────────────────────────────────────────────
export const fetchAvailableNodes = () =>
  api.get('/nodes')

export const getExampleWorkflow = () =>
  api.get('/workflows/example')