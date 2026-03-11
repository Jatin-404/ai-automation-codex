import { useState } from 'react'
import useWorkflowStore from '../../store/workflowStore'
import { ChevronDown, ChevronUp, CheckCircle2, XCircle, Clock, X } from 'lucide-react'
import './OutputPanel.css'

export default function OutputPanel() {
  const { runResult, runError, isRunning, clearRunResult } = useWorkflowStore()
  const [expanded, setExpanded] = useState(true)
  const [activeTab, setActiveTab] = useState('output')

  if (!runResult && !runError && !isRunning) return null

  return (
    <div className={`output-panel ${expanded ? 'output-panel--expanded' : ''}`}>
      {/* Bar */}
      <div className="output-panel__bar" onClick={() => setExpanded(!expanded)}>
        <div className="output-panel__bar-left">
          {isRunning && <><Clock size={14} className="spin" /><span>Running workflow…</span></>}
          {runResult && !isRunning && <><CheckCircle2 size={14} color="var(--green)" /><span>Workflow completed</span></>}
          {runError && !isRunning && <><XCircle size={14} color="var(--red)" /><span>Workflow failed</span></>}
        </div>
        <div className="output-panel__bar-right">
          {runResult && (
            <div className="output-tabs">
              {['output', 'log', 'raw'].map(tab => (
                <button
                  key={tab}
                  className={`tab-btn ${activeTab === tab ? 'tab-btn--active' : ''}`}
                  onClick={e => { e.stopPropagation(); setActiveTab(tab) }}
                >{tab}</button>
              ))}
            </div>
          )}
          <button className="icon-btn" onClick={e => { e.stopPropagation(); clearRunResult() }}><X size={13}/></button>
          {expanded ? <ChevronDown size={14}/> : <ChevronUp size={14}/>}
        </div>
      </div>

      {/* Content */}
      {expanded && (
        <div className="output-panel__content">
          {isRunning && (
            <div className="output-loading">
              <div className="loading-dots"><span/><span/><span/></div>
              <p>Executing nodes…</p>
            </div>
          )}

          {runError && (
            <div className="output-error">
              <XCircle size={18} color="var(--red)"/>
              <div>
                <strong>Error</strong>
                <p>{typeof runError === 'string' ? runError : JSON.stringify(runError, null, 2)}</p>
              </div>
            </div>
          )}

          {runResult && !isRunning && (
            <>
              {activeTab === 'output' && (
                <div className="output-result">
                  <div className="result-header">
                    <span className="result-badge result-badge--success">✅ Success</span>
                    <span className="result-run-id">Run: {runResult.run_id?.slice(0, 8)}</span>
                  </div>
                  <pre className="result-json">
                    {JSON.stringify(runResult.final_output, null, 2)}
                  </pre>
                </div>
              )}

              {activeTab === 'log' && (
                <div className="output-log">
                  {runResult.log?.map((entry, i) => (
                    <div key={i} className={`log-entry log-entry--${entry.status}`}>
                      <span className="log-status">{statusIcon(entry.status)}</span>
                      <span className="log-node">{entry.node_id}</span>
                      <span className="log-msg">{entry.message}</span>
                      <span className="log-time">{entry.timestamp?.slice(11, 19)}</span>
                    </div>
                  ))}
                </div>
              )}

              {activeTab === 'raw' && (
                <pre className="result-json">
                  {JSON.stringify(runResult, null, 2)}
                </pre>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

function statusIcon(status) {
  return { success: '✅', error: '❌', running: '⏳', skipped: '⏭', branch: '🔀', started: '▶', completed: '🏁' }[status] || '•'
}