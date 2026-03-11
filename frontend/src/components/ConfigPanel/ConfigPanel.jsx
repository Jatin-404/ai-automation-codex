import { useState, useEffect, useRef } from 'react'
import useWorkflowStore from '../../store/workflowStore'
import { X, Trash2, ChevronDown, ChevronRight, Braces, Copy, Check } from 'lucide-react'
import './ConfigPanel.css'

const CATEGORY_COLOR = { trigger:'#3b82f6', action:'#10b981', ai:'#8b5cf6', logic:'#f97316' }

export default function ConfigPanel() {
  const { selectedNode, updateNodeConfig, updateNodeLabel, deleteNode, clearSelection, getInputSchemaForNode, runResult, nodeRunStates } = useWorkflowStore()
  const [localConfig, setLocalConfig] = useState({})
  const [localLabel, setLocalLabel] = useState('')
  const [inputExpanded, setInputExpanded] = useState(true)
  const [outputExpanded, setOutputExpanded] = useState(true)
  const [activeFieldRef, setActiveFieldRef] = useState(null) // which field is focused for expression insert
  const fieldRefs = useRef({})

  useEffect(() => {
    if (selectedNode) {
      setLocalConfig(selectedNode.data.config || {})
      setLocalLabel(selectedNode.data.label || '')
    }
  }, [selectedNode?.id])

  if (!selectedNode) {
    return (
      <div className="cp cp--empty">
        <div className="cp__empty-state">
          <span className="empty-icon">👆</span>
          <p>Click any node to configure it</p>
        </div>
      </div>
    )
  }

  const def = selectedNode.data.definition || {}
  const schema = def.config_schema || []
  const color = CATEGORY_COLOR[def.category] || '#6366f1'
  const inputSchema = getInputSchemaForNode(selectedNode.id)
  const hasInputFields = Object.keys(inputSchema).length > 0
  const nodeOutput = runResult?.node_outputs?.[selectedNode.id]
  const nodeStatus = nodeRunStates?.[selectedNode.id]

  const handleChange = (key, value) => {
    const next = { ...localConfig, [key]: value }
    setLocalConfig(next)
    updateNodeConfig(selectedNode.id, next)
  }

  const handleLabelChange = (e) => {
    setLocalLabel(e.target.value)
    updateNodeLabel(selectedNode.id, e.target.value)
  }

  // Insert a field reference like {{fieldName}} into the focused input
  const insertFieldRef = (fieldName) => {
    if (!activeFieldRef) return
    const ref = fieldRefs.current[activeFieldRef]
    if (!ref) return
    const expr = `{{${fieldName}}}`
    const start = ref.selectionStart ?? (localConfig[activeFieldRef] || '').length
    const end   = ref.selectionEnd   ?? start
    const current = localConfig[activeFieldRef] || ''
    const next = current.slice(0, start) + expr + current.slice(end)
    handleChange(activeFieldRef, next)
    // restore focus
    setTimeout(() => {
      ref.focus()
      ref.setSelectionRange(start + expr.length, start + expr.length)
    }, 50)
  }

  const flattenObject = (obj, prefix = '') => {
    if (!obj || typeof obj !== 'object') return {}
    return Object.entries(obj).reduce((acc, [k, v]) => {
      const key = prefix ? `${prefix}.${k}` : k
      if (v && typeof v === 'object' && !Array.isArray(v)) {
        Object.assign(acc, flattenObject(v, key))
      } else {
        acc[key] = v
      }
      return acc
    }, {})
  }

  const flatInputFields = flattenObject(inputSchema)

  return (
    <div className="cp">
      {/* ── Node Header ── */}
      <div className="cp__header" style={{ '--nc': color }}>
        <div className="cp__header-left">
          <div className="cp__icon-wrap" style={{ background: `${color}22`, border: `1px solid ${color}44` }}>
            <span className="cp__icon">{def.icon}</span>
          </div>
          <div>
            <span className="cp__category">{def.category}</span>
            <input
              className="cp__label-input"
              value={localLabel}
              onChange={handleLabelChange}
              placeholder="Node name"
            />
          </div>
        </div>
        <button className="icon-btn" onClick={clearSelection}><X size={15}/></button>
      </div>

      {/* ── Status bar if ran ── */}
      {nodeStatus && (
        <div className={`cp__status cp__status--${nodeStatus}`}>
          {nodeStatus === 'success' ? '✅ Ran successfully' : nodeStatus === 'error' ? '❌ Failed' : '⏳ Running…'}
        </div>
      )}

      <div className="cp__body">

        {/* ── INPUT DATA section (n8n style) ── */}
        {hasInputFields && (
          <section className="cp__section">
            <button className="cp__section-header" onClick={() => setInputExpanded(v => !v)}>
              <Braces size={13}/>
              <span>Input Data</span>
              <span className="cp__section-hint">click a field to insert it</span>
              {inputExpanded ? <ChevronDown size={13}/> : <ChevronRight size={13}/>}
            </button>
            {inputExpanded && (
              <div className="cp__input-fields">
                {Object.entries(flatInputFields).map(([key, val]) => (
                  <div
                    key={key}
                    className="cp__field-chip"
                    title={`Insert {{${key}}} — value: ${JSON.stringify(val)}`}
                    onClick={() => insertFieldRef(key)}
                  >
                    <span className="chip-key">{key}</span>
                    <span className="chip-val">{truncate(JSON.stringify(val), 20)}</span>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {/* ── Node description ── */}
        {def.description && (
          <div className="cp__desc">{def.description}</div>
        )}

        {/* ── Config fields ── */}
        {schema.length > 0 && (
          <section className="cp__section cp__section--config">
            <div className="cp__section-title">Parameters</div>
            {schema.map(field => (
              <ConfigField
                key={field.key}
                field={field}
                value={localConfig[field.key] ?? field.default ?? ''}
                onChange={(v) => handleChange(field.key, v)}
                onFocus={() => setActiveFieldRef(field.key)}
                onBlur={() => {}}
                fieldRef={el => { fieldRefs.current[field.key] = el }}
                inputFields={flatInputFields}
                isActive={activeFieldRef === field.key}
              />
            ))}
          </section>
        )}

        {/* ── Output preview ── */}
        {nodeOutput !== undefined && (
          <section className="cp__section">
            <button className="cp__section-header" onClick={() => setOutputExpanded(v => !v)}>
              <span>📤</span>
              <span>Output</span>
              {outputExpanded ? <ChevronDown size={13}/> : <ChevronRight size={13}/>}
            </button>
            {outputExpanded && (
              <div className="cp__output-preview">
                <OutputPreview data={nodeOutput} />
              </div>
            )}
          </section>
        )}

      </div>

      {/* ── Footer ── */}
      <div className="cp__footer">
        <button className="delete-btn" onClick={() => deleteNode(selectedNode.id)}>
          <Trash2 size={13}/> Delete Node
        </button>
      </div>
    </div>
  )
}

// ─── Config Field ─────────────────────────────────────────────
function ConfigField({ field, value, onChange, onFocus, fieldRef, inputFields, isActive }) {
  const { type, label, placeholder, options, help, min, max, step, required } = field

  const inputClass = `cf__input ${isActive ? 'cf__input--active' : ''}`

  return (
    <div className="cf">
      <div className="cf__header">
        <label className="cf__label">
          {label}
          {required && <span className="cf__required">*</span>}
        </label>
        {help && <span className="cf__hint" title={help}>?</span>}
      </div>

      {type === 'text' && (
        <div className="cf__input-wrap">
          <input
            ref={fieldRef}
            className={inputClass}
            value={value}
            onChange={e => onChange(e.target.value)}
            placeholder={placeholder}
            onFocus={onFocus}
          />
        </div>
      )}

      {type === 'textarea' && (
        <div className="cf__input-wrap">
          <textarea
            ref={fieldRef}
            className={`${inputClass} cf__textarea`}
            value={value}
            onChange={e => onChange(e.target.value)}
            placeholder={placeholder}
            rows={4}
            onFocus={onFocus}
          />
        </div>
      )}

      {type === 'select' && (
        <select className="cf__input cf__select" value={value} onChange={e => onChange(e.target.value)}>
          {options?.map(opt => <option key={opt} value={opt}>{opt}</option>)}
        </select>
      )}

      {type === 'number' && (
        <input
          ref={fieldRef}
          className={inputClass}
          type="number"
          value={value}
          onChange={e => onChange(Number(e.target.value))}
          min={min} max={max}
          onFocus={onFocus}
        />
      )}

      {type === 'boolean' && (
        <label className="cf__toggle">
          <input type="checkbox" checked={!!value} onChange={e => onChange(e.target.checked)} />
          <span className="toggle-track"><span className="toggle-thumb"/></span>
          <span className="toggle-text">{value ? 'Yes' : 'No'}</span>
        </label>
      )}

      {type === 'slider' && (
        <div className="cf__slider-row">
          <input type="range" className="cf__slider" value={value}
            min={min??0} max={max??1} step={step??0.1}
            onChange={e => onChange(Number(e.target.value))} />
          <span className="cf__slider-val">{value}</span>
        </div>
      )}

      {help && <p className="cf__help">{help}</p>}
    </div>
  )
}

// ─── Output Preview ───────────────────────────────────────────
function OutputPreview({ data }) {
  const [copied, setCopied] = useState(false)
  const str = JSON.stringify(data, null, 2)

  const copy = () => {
    navigator.clipboard.writeText(str)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  if (data === null || data === undefined) return <span className="op__null">null</span>

  if (typeof data === 'object') {
    return (
      <div className="op">
        <button className="op__copy" onClick={copy}>
          {copied ? <Check size={11}/> : <Copy size={11}/>}
        </button>
        <div className="op__table">
          {Object.entries(data).map(([k, v]) => (
            <div key={k} className="op__row">
              <span className="op__key">{k}</span>
              <span className="op__val">{truncate(JSON.stringify(v), 40)}</span>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return <pre className="op__raw">{str}</pre>
}

function truncate(str, n) {
  return str && str.length > n ? str.slice(0, n) + '…' : str
}