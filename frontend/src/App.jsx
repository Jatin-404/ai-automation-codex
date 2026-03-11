import { useEffect, useState } from 'react'
import { ReactFlowProvider } from '@xyflow/react'
import useWorkflowStore from './store/workflowStore'
import { fetchAvailableNodes, runWorkflow } from './api/client'
import axios from 'axios'
import Sidebar from './components/Sidebar/Sidebar'
import Canvas from './components/Canvas/Canvas'

import NodeEditor from './components/NodeEditor/NodeEditor'
import { Play, Save, Zap, Loader, Clock, Webhook, AlertCircle, StopCircle } from 'lucide-react'
import './App.css'

export default function App() {
  const {
    nodes, edges,
    setAvailableNodes,
    isRunning, setRunning, setRunResult, setRunError, selectedNode,
    getTriggerType, getTriggerNode,
    scheduledWorkflows, setScheduleActive, removeSchedule,
  } = useWorkflowStore()

  const triggerType = getTriggerType()
  const triggerNode = getTriggerNode()
  const [scheduleActive, setScheduleActiveLocal] = useState(false)
  const [webhookActive, setWebhookActive] = useState(false)

  useEffect(() => {
    fetchAvailableNodes()
      .then(res => setAvailableNodes(res.data))
      .catch(() => setAvailableNodes(FALLBACK_NODES))
  }, [])

  const getSerializedNodes = () => nodes.map(n => ({
    id: n.id, type: n.type, position: n.position,
    data: { label: n.data.label, config: n.data.config || {} }
  }))

  // ── Manual / Webhook trigger → run immediately ────────────────
  const handleRun = async () => {
    if (isRunning) return
    if (nodes.length === 0) { alert('Add at least one node to the canvas first.'); return }
    if (!triggerType) { alert('Add a trigger node first (Manual, Webhook, or Schedule).'); return }

    setRunning(true)
    setRunResult(null)
    setRunError(null)
    try {
      const res = await runWorkflow(getSerializedNodes(), edges)
      setRunResult(res.data)
    } catch (err) {
      const detail = err.response?.data?.detail
      setRunError(typeof detail === 'object' ? detail?.error || JSON.stringify(detail) : detail || err.message)
    } finally {
      setRunning(false)
    }
  }

  // ── Scheduler trigger → activate/deactivate ───────────────────
  const handleScheduleToggle = async () => {
    if (!triggerNode) return
    const cfg = triggerNode.data.config || {}
    const workflowId = cfg.workflow_id || `workflow-${triggerNode.id}`

    if (scheduleActive) {
      try {
        await axios.delete(`/api/workflows/schedule/${workflowId}`)
        removeSchedule(workflowId)
        setScheduleActiveLocal(false)
      } catch (e) {
        alert('Could not stop schedule: ' + e.message)
      }
    } else {
      if (!cfg.workflow_id) { alert('Set a Workflow ID in the Schedule Trigger node first.'); return }
      try {
        await axios.post('/api/workflows/schedule', {
          workflow_id: workflowId,
          nodes: getSerializedNodes(),
          edges,
          interval_type: cfg.interval_type || 'hour',
          interval_value: parseInt(cfg.interval_value || 1)
        })
        setScheduleActive(workflowId, { interval_type: cfg.interval_type, interval_value: cfg.interval_value })
        setScheduleActiveLocal(true)
      } catch (e) {
        alert('Could not activate schedule: ' + (e.response?.data?.detail || e.message))
      }
    }
  }

  // -- Webhook trigger -> register/unregister + test --
  const handleWebhookToggle = async () => {
    if (!triggerNode) return
    const cfg = triggerNode.data.config || {}
    const path = cfg.path || '/webhook'
    const method = (cfg.method || 'POST').toUpperCase()
    if (webhookActive) {
      try {
        await axios.post('/api/workflows/webhook/unregister', { path, method })
        setWebhookActive(false)
      } catch (e) {
        alert('Could not disable webhook: ' + (e.response?.data?.detail || e.message))
      }
      return
    }
    try {
      await axios.post('/api/workflows/webhook/register', {
        path,
        method,
        nodes: getSerializedNodes(),
        edges,
      })
      setWebhookActive(true)
    } catch (e) {
      alert('Could not activate webhook: ' + (e.response?.data?.detail || e.message))
    }
  }

  const handleTestWebhook = async () => {
    if (!triggerNode) return
    const cfg = triggerNode.data.config || {}
    const path = cfg.path || '/webhook'
    setRunResult(null)
    setRunError(null)
    try {
      const payload = { test: true, triggered_at: new Date().toISOString() }
      const res = await axios({
        method: (cfg.method || 'POST').toLowerCase(),
        url: `/api/webhooks${path}`,
        data: payload
      })
      setRunResult(res.data)
    } catch (err) {
      const detail = err.response?.data?.detail
      setRunError(typeof detail === 'object' ? detail?.error || JSON.stringify(detail) : detail || err.message)
    }
  }

  const handleSave = () => {
    const workflow = { nodes, edges, savedAt: new Date().toISOString() }
    const blob = new Blob([JSON.stringify(workflow, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = 'workflow.json'; a.click()
    URL.revokeObjectURL(url)
  }

  // ── Render correct action button based on trigger type ────────
  const renderActionButton = () => {
    if (!triggerType) {
      return (
        <button className="btn btn--disabled" disabled>
          <AlertCircle size={14}/> Add a Trigger
        </button>
      )
    }

    if (triggerType === 'scheduler') {
      return (
        <button
          className={`btn ${scheduleActive ? 'btn--stop' : 'btn--schedule'}`}
          onClick={handleScheduleToggle}
        >
          {scheduleActive
            ? <><StopCircle size={14}/> Stop Schedule</>
            : <><Clock size={14}/> Activate Schedule</>
          }
        </button>
      )
    }

    if (triggerType === 'webhook_trigger') {
      const path = triggerNode?.data?.config?.path || '/webhook'
      const method = (triggerNode?.data?.config?.method || 'POST').toUpperCase()
      return (
        <>
          <span className="webhook-url-badge" title={`${method} http://localhost:8000/api/webhooks${path}`}>
            <Webhook size={12}/> {method} {path}
          </span>
          <button className={`btn ${webhookActive ? 'btn--stop' : 'btn--schedule'}`} onClick={handleWebhookToggle}>
            {webhookActive ? <><StopCircle size={14}/> Disable Webhook</> : <><Clock size={14}/> Activate Webhook</>}
          </button>
          <button className="btn btn--run" onClick={handleTestWebhook} disabled={isRunning}>
            {isRunning ? <><Loader size={14} className="spin"/> Running…</> : <><Play size={14}/> Test Webhook</>}
          </button>
        </>
      )
    }

    // manual_trigger
    return (
      <button className={`btn btn--run ${isRunning ? 'btn--running' : ''}`} onClick={handleRun} disabled={isRunning}>
        {isRunning ? <><Loader size={14} className="spin"/> Running…</> : <><Play size={14}/> Run Workflow</>}
      </button>
    )
  }

  return (
    <ReactFlowProvider>
      <div className="app">
        <header className="app-header">
          <div className="app-header__brand">
            <div className="brand-logo"><Zap size={18} strokeWidth={2.5}/></div>
            <span className="brand-name">FlowAI</span>
            <span className="brand-badge">MVP</span>
          </div>
          <div className="app-header__workflow-info">
            <span className="workflow-name">Untitled Workflow</span>
            <span className="node-count">{nodes.length} node{nodes.length !== 1 ? 's' : ''}</span>
            {triggerType && (
              <span className="trigger-badge">
                {triggerType === 'manual_trigger' ? '▶️ Manual' : triggerType === 'scheduler' ? '⏰ Scheduled' : '🔗 Webhook'}
              </span>
            )}
          </div>
          <div className="app-header__actions">
            <button className="btn btn--save" onClick={handleSave}><Save size={14}/> Save</button>
            {renderActionButton()}
          </div>
        </header>
        <div className="app-body">
          <Sidebar />
          <Canvas />
          {selectedNode && <NodeEditor />}
          
        </div>
      </div>
    </ReactFlowProvider>
  )
}

const FALLBACK_NODES = [
  { type:'manual_trigger',  label:'Manual Trigger',      description:'Start by clicking Run Workflow',              category:'trigger', color:'#6366f1', icon:'▶️', inputs:0, outputs:1, config_schema:[{key:'note',label:'Note',type:'text',placeholder:'What does this workflow do?'}] },
  { type:'webhook_trigger', label:'Webhook Trigger',      description:'Starts when an HTTP request is received',     category:'trigger', color:'#3b82f6', icon:'🔗', inputs:0, outputs:1, config_schema:[{key:'path',label:'Webhook Path',type:'text',placeholder:'/my-webhook'},{key:'method',label:'Method',type:'select',options:['GET','POST','PUT'],default:'POST'}] },
  { type:'scheduler',       label:'Schedule Trigger',     description:'Runs automatically on a repeating schedule',  category:'trigger', color:'#f59e0b', icon:'⏰', inputs:0, outputs:1, config_schema:[{key:'interval_type',label:'Run Every',type:'select',options:['minute','hour','day','week'],default:'hour'},{key:'interval_value',label:'Amount',type:'number',default:1},{key:'workflow_id',label:'Workflow ID',type:'text',placeholder:'my-daily-report'}] },
  { type:'http_request',    label:'HTTP Request',         description:'Call any external API',                       category:'action',  color:'#10b981', icon:'🌐', inputs:1, outputs:1, config_schema:[{key:'url',label:'URL',type:'text',placeholder:'https://api.example.com'},{key:'method',label:'Method',type:'select',options:['GET','POST','PUT','DELETE'],default:'GET'},{key:'headers',label:'Headers (JSON)',type:'textarea',placeholder:'{"Authorization": "Bearer token"}'},{key:'body',label:'Body (JSON)',type:'textarea',placeholder:'{"key": "value"}'},{key:'use_input_as_body',label:'Use previous output as body',type:'boolean',default:false}] },
  { type:'set_transform',   label:'Set / Transform Data', description:'Add, rename, or update fields',                category:'action',  color:'#06b6d4', icon:'✏️', inputs:1, outputs:1, config_schema:[{key:'mode',label:'Mode',type:'select',options:['Manual Mapping','Keep Only Mapped Fields'],default:'Manual Mapping'},{key:'field_mappings',label:'field_mappings',type:'hidden',default:'[]'},{key:'include_input',label:'Include Other Input Fields',type:'boolean',default:false}] },
  { type:'code_node',       label:'Code (JavaScript)',    description:'Write custom JS to transform data',           category:'action',  color:'#eab308', icon:'</>',inputs:1, outputs:1, config_schema:[{key:'code',label:'JavaScript Code',type:'textarea',placeholder:'// input = previous node data\nreturn {\n  result: input.value\n}'}] },
  { type:'notification',    label:'Send Notification',    description:'Send email or Slack message',                 category:'action',  color:'#ec4899', icon:'🔔', inputs:1, outputs:1, config_schema:[{key:'channel',label:'Send via',type:'select',options:['Email (SMTP)','Slack Webhook'],default:'Email (SMTP)'},{key:'smtp_host',label:'SMTP Host',type:'text',placeholder:'smtp.gmail.com'},{key:'smtp_user',label:'Your Email',type:'text',placeholder:'you@gmail.com'},{key:'smtp_pass',label:'App Password',type:'text',placeholder:'xxxx xxxx xxxx'},{key:'to_email',label:'Send To',type:'text',placeholder:'colleague@company.com'},{key:'subject',label:'Subject',type:'text',placeholder:'Workflow Result'},{key:'message',label:'Message',type:'textarea',placeholder:'Result: {{data}}'},{key:'slack_webhook_url',label:'Slack Webhook URL',type:'text',placeholder:'https://hooks.slack.com/...'},{key:'slack_message',label:'Slack Message',type:'textarea',placeholder:'Result: {{data}}'}] },
  { type:'whatsapp',        label:'WhatsApp',             description:'Send WhatsApp via Twilio',                    category:'action',  color:'#25d366', icon:'💬', inputs:1, outputs:1, config_schema:[{key:'provider',label:'Provider',type:'select',options:['Twilio','simulate'],default:'simulate'},{key:'to_number',label:'To (phone)',type:'text',placeholder:'+919876543210'},{key:'message',label:'Message',type:'textarea',placeholder:'Result: {{data}}'}] },
  { type:'if_condition',    label:'IF Condition',         description:'Branch based on a condition',                 category:'logic',   color:'#f97316', icon:'🔀', inputs:1, outputs:2, config_schema:[{key:'field',label:'Field to check',type:'text',placeholder:'status'},{key:'condition',label:'Condition',type:'select',options:['equals','not equals','greater than','less than','contains','is empty','is not empty']},{key:'value',label:'Value',type:'text',placeholder:'active'}] },
  { type:'split',           label:'Split / Condition',    description:'Route data down different paths',             category:'logic',   color:'#ef4444', icon:'🔀', inputs:1, outputs:2, config_schema:[{key:'field',label:'Field to check',type:'text',placeholder:'status'},{key:'condition',label:'Condition',type:'select',options:['equals','not equals','greater than','less than','contains','is empty','is not empty']},{key:'value',label:'Value',type:'text',placeholder:'active'}] },
  { type:'loop_node',       label:'Loop / Split Items',   description:'Process each item in a list',                 category:'logic',   color:'#8b5cf6', icon:'🔁', inputs:1, outputs:1, config_schema:[{key:'field',label:'List field',type:'text',placeholder:'items'},{key:'mode',label:'Output mode',type:'select',options:['Pass all items as array','Pass first item only','Pass last item only','Pass count only'],default:'Pass all items as array'},{key:'max_items',label:'Max items',type:'number',default:100}] },
  { type:'merge',           label:'Merge',                description:'Combine data from multiple branches',         category:'logic',   color:'#64748b', icon:'🔗', inputs:2, outputs:1, config_schema:[{key:'mode',label:'How to merge',type:'select',options:['Combine into one object','Put into array','Keep first branch only','Keep second branch only'],default:'Combine into one object'}] },
  { type:'ai_node',         label:'AI Node',              description:'Process with AI model',                       category:'ai',      color:'#8b5cf6', icon:'🤖', inputs:1, outputs:1, config_schema:[{key:'provider',label:'Provider',type:'select',options:['simulate','ollama','openai_compatible'],default:'simulate'},{key:'model',label:'Model Name',type:'text',placeholder:'llama3'},{key:'prompt',label:'System Prompt',type:'textarea',placeholder:'Summarize this data:'}] },
]
