import { useState, useEffect, useRef } from 'react'
import useWorkflowStore from '../../store/workflowStore'
import { X, Play, Loader, Search, Copy, Check, GripVertical, Plus, Trash2, ChevronDown } from 'lucide-react'
import { runWorkflowNode } from '../../api/client'
import './NodeEditor.css'

const CATEGORY_COLOR = {
  trigger: '#3b82f6', action: '#10b981', ai: '#8b5cf6', logic: '#f97316'
}

const FIELD_TYPES = ['String', 'Number', 'Boolean', 'Array', 'Object']

export default function NodeEditor() {
  const {
    selectedNode, clearSelection,
    updateNodeConfig, updateNodeLabel,
    deleteNode,
    nodes, edges,
    getInputSchemaForNode,
    runResult, nodeRunStates,
    setRunResult,
  } = useWorkflowStore()

  const [localConfig, setLocalConfig]   = useState({})
  const [localLabel, setLocalLabel]     = useState('')
  const [activeTab, setActiveTab]       = useState('parameters')
  const [inputTab, setInputTab]         = useState('schema')
  const [outputTab, setOutputTab]       = useState('schema')
  const [isExecuting, setIsExecuting]   = useState(false)
  const [stepResult, setStepResult]     = useState(null)
  const [stepError, setStepError]       = useState(null)
  const [focusedField, setFocusedField] = useState(null)
  const [searchInput, setSearchInput]   = useState('')
  const [copied, setCopied]             = useState(false)
  const fieldRefs = useRef({})
  const dragFieldName = useRef(null)

  useEffect(() => {
    if (selectedNode) {
      setLocalConfig(selectedNode.data.config || {})
      setLocalLabel(selectedNode.data.label || '')
      setStepResult(null)
      setStepError(null)
    }
  }, [selectedNode?.id])

  if (!selectedNode) return null

  const def    = selectedNode.data.definition || {}
  const schema = def.config_schema || []
  const color  = CATEGORY_COLOR[def.category] || '#6366f1'
  const isSetTransform = selectedNode.type === 'set_transform'

  const inputSchema   = getInputSchemaForNode(selectedNode.id)
  const flatInput     = flattenObject(inputSchema)
  const filteredInput = Object.entries(flatInput).filter(([k]) =>
    k.toLowerCase().includes(searchInput.toLowerCase())
  )
  const hasInput  = Object.keys(flatInput).length > 0

  const outputItems = stepResult?.node_items?.[selectedNode.id]?.[0]
                   ?? runResult?.node_items?.[selectedNode.id]?.[0]
  const outputData = outputItems
    ? outputItems.map(i => i?.json ?? i)
    : (stepResult?.node_outputs?.[selectedNode.id] ?? runResult?.node_outputs?.[selectedNode.id])
  const schemaSource = Array.isArray(outputData) ? outputData[0] : outputData
  const flatOutput = schemaSource ? flattenObject(schemaSource) : {}
  const hasOutput  = outputData !== undefined

  const handleChange = (key, value) => {
    const next = { ...localConfig, [key]: value }
    setLocalConfig(next)
    updateNodeConfig(selectedNode.id, next)
  }

  const handleLabelChange = (e) => {
    setLocalLabel(e.target.value)
    updateNodeLabel(selectedNode.id, e.target.value)
  }

  // ── Drag from input panel ─────────────────────────────────────
  const onDragStart = (e, fieldName) => {
    dragFieldName.current = fieldName
    e.dataTransfer.setData('text/plain', fieldName)
    e.dataTransfer.effectAllowed = 'copy'
  }

  // Insert expression into a focused text/textarea field
  const insertExpr = (fieldName) => {
    if (!focusedField) return
    const ref = fieldRefs.current[focusedField]
    const expr = `{{${fieldName}}}`
    const current = localConfig[focusedField] || ''
    if (ref && ref.selectionStart !== undefined) {
      const s = ref.selectionStart, en = ref.selectionEnd
      const next = current.slice(0, s) + expr + current.slice(en)
      handleChange(focusedField, next)
      setTimeout(() => { ref.focus(); ref.setSelectionRange(s + expr.length, s + expr.length) }, 30)
    } else {
      handleChange(focusedField, current + expr)
    }
  }

  // ── Execute Step ─────────────────────────────────────────────
  const executeStep = async () => {
    setIsExecuting(true)
    setStepResult(null)
    setStepError(null)
    try {
      const serialized = nodes.map(n => ({
        id: n.id, type: n.type, position: n.position,
        data: { label: n.data.label, config: n.data.config || {} }
      }))
      const res = await runWorkflowNode(serialized, edges, selectedNode.id)
      setStepResult(res.data)
      setRunResult(res.data)
    } catch (err) {
      const detail = err.response?.data?.detail
      setStepError(typeof detail === 'object' ? detail?.error || JSON.stringify(detail) : detail || err.message)
    } finally {
      setIsExecuting(false)
    }
  }

  const copyOutput = () => {
    navigator.clipboard.writeText(JSON.stringify(outputData, null, 2))
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  const nodeStatus = nodeRunStates?.[selectedNode.id]
    ?? (stepResult?.node_items?.[selectedNode.id] !== undefined ? 'success' : undefined)
    ?? (stepError ? 'error' : undefined)

  return (
    <div className="ne-overlay" onClick={e => { if (e.target === e.currentTarget) clearSelection() }}>
      <div className="ne">

        {/* ── Top bar ─────────────────────────────────────── */}
        <div className="ne__topbar" style={{ '--nc': color }}>
          <div className="ne__topbar-left">
            <div className="ne__node-icon" style={{ background: `${color}22`, border: `1px solid ${color}44` }}>
              {def.icon}
            </div>
            <div className="ne__node-info">
              <input className="ne__node-label" value={localLabel} onChange={handleLabelChange} placeholder="Node name"/>
              <span className="ne__node-category">{def.category} · {def.type}</span>
            </div>
            {nodeStatus && (
              <span className={`ne__status-badge ne__status-badge--${nodeStatus}`}>
                {nodeStatus === 'success' ? '✅ Success'
                  : nodeStatus === 'error' ? '❌ Error'
                  : nodeStatus === 'skipped' ? '⏭ Skipped'
                  : '⏳ Running'}
              </span>
            )}
          </div>
          <div className="ne__topbar-right">
            <div className="ne__tabs">
              <button className={`ne__tab ${activeTab==='parameters'?'ne__tab--active':''}`} onClick={() => setActiveTab('parameters')}>Parameters</button>
              <button className={`ne__tab ${activeTab==='settings'  ?'ne__tab--active':''}`} onClick={() => setActiveTab('settings')}>Settings</button>
            </div>
            <button className={`ne__execute-btn ${isExecuting?'ne__execute-btn--running':''}`} onClick={executeStep} disabled={isExecuting}>
              {isExecuting ? <><Loader size={13} className="spin"/> Running…</> : <><Play size={13}/> Execute step</>}
            </button>
            <button className="ne__close" onClick={clearSelection}><X size={16}/></button>
          </div>
        </div>

        {/* ── 3 columns ────────────────────────────────────── */}
        <div className="ne__body">

          {/* LEFT: INPUT */}
          <div className="ne__panel ne__panel--input">
            <div className="ne__panel-header">
              <span className="ne__panel-title">INPUT</span>
              {hasInput && (
                <div className="ne__panel-search">
                  <Search size={11}/>
                  <input className="ne__search-input" placeholder="Search fields…"
                    value={searchInput} onChange={e => setSearchInput(e.target.value)}/>
                </div>
              )}
            </div>
            <div className="ne__panel-tabs">
              {['schema','table','json'].map(t => (
                <button key={t} className={`ne__ptab ${inputTab===t?'ne__ptab--active':''}`} onClick={() => setInputTab(t)}>{t}</button>
              ))}
            </div>
            {!hasInput ? (
              <div className="ne__empty-panel">
                <span>🔌</span>
                <p>No input data yet</p>
                <small>Run the workflow or connect a node before this one</small>
              </div>
            ) : (
              <div className="ne__panel-content">
                {inputTab === 'schema' && <SchemaView fields={filteredInput} onDragStart={onDragStart} onInsert={insertExpr} />}
                {inputTab === 'table'  && <TableView data={inputSchema} />}
                {inputTab === 'json'   && <JsonView  data={inputSchema} />}
              </div>
            )}
          </div>

          {/* CENTER: PARAMETERS */}
          <div className="ne__panel ne__panel--params">
            {activeTab === 'parameters' && (
              <>
                {def.description && <div className="ne__desc">{def.description}</div>}

                {/* ── Set/Transform: visual field builder ──── */}
                {isSetTransform ? (
                  <SetTransformEditor
                    config={localConfig}
                    onChange={handleChange}
                    flatInput={flatInput}
                    dragFieldName={dragFieldName}
                    hasInput={hasInput}
                  />
                ) : (
                  /* ── Generic parameter fields ─────────────── */
                  schema.length === 0 ? (
                    <div className="ne__empty-panel"><span>⚙️</span><p>No parameters for this node</p></div>
                  ) : (
                    <div className="ne__fields">
                      {schema.map(field => (
                        field.type === 'conditions' ? (
                          <ConditionsEditor
                            key={field.key}
                            value={localConfig[field.key] ?? []}
                            onChange={v => handleChange(field.key, v)}
                            dragFieldName={dragFieldName}
                          />
                        ) : (
                          <ParamField
                            key={field.key}
                            field={field}
                            value={localConfig[field.key] ?? field.default ?? ''}
                            onChange={v => handleChange(field.key, v)}
                            onFocus={() => setFocusedField(field.key)}
                            fieldRef={el => { fieldRefs.current[field.key] = el }}
                            isFocused={focusedField === field.key}
                            hasInput={hasInput}
                            onDrop={e => {
                              e.preventDefault()
                              const name = dragFieldName.current || e.dataTransfer.getData('text/plain')
                              const expr = `{{${name}}}`
                              const cur = localConfig[field.key] || ''
                              const ref = fieldRefs.current[field.key]
                              if (ref?.selectionStart !== undefined) {
                                const s = ref.selectionStart, en = ref.selectionEnd
                                handleChange(field.key, cur.slice(0,s) + expr + cur.slice(en))
                              } else {
                                handleChange(field.key, cur + expr)
                              }
                              dragFieldName.current = null
                            }}
                            onDragOver={e => { e.preventDefault(); e.dataTransfer.dropEffect = 'copy' }}
                          />
                        )
                      ))}
                    </div>
                  )
                )}

                {stepError && (
                  <div className="ne__step-error">
                    <strong>❌ Error</strong>
                    <p>{stepError}</p>
                  </div>
                )}
              </>
            )}

            {activeTab === 'settings' && (
              <div className="ne__fields">
                <div className="ne__setting-group">
                  <label className="pf__label">Node ID</label>
                  <div className="ne__setting-val">{selectedNode.id}</div>
                </div>
                <div className="ne__setting-group">
                  <label className="pf__label">Node Type</label>
                  <div className="ne__setting-val">{def.type}</div>
                </div>
                <button className="ne__delete-btn" onClick={() => { deleteNode(selectedNode.id); clearSelection() }}>
                  🗑 Delete this node
                </button>
              </div>
            )}
          </div>

          {/* RIGHT: OUTPUT */}
          <div className="ne__panel ne__panel--output">
            <div className="ne__panel-header">
              <span className="ne__panel-title">OUTPUT</span>
              {hasOutput && (
                <button className="ne__copy-btn" onClick={copyOutput}>
                  {copied ? <Check size={11}/> : <Copy size={11}/>}
                </button>
              )}
            </div>
            <div className="ne__panel-tabs">
              {['schema','table','json'].map(t => (
                <button key={t} className={`ne__ptab ${outputTab===t?'ne__ptab--active':''}`} onClick={() => setOutputTab(t)}>{t}</button>
              ))}
            </div>
            {!hasOutput ? (
              <div className="ne__empty-panel">
                <span style={{fontSize:28,opacity:.3}}>|→</span>
                <p>No output data</p>
                <button className="ne__execute-inline" onClick={executeStep} disabled={isExecuting}>
                  {isExecuting ? 'Running…' : 'Execute step'}
                </button>
                <small>or set mock data</small>
              </div>
            ) : (
              <div className="ne__panel-content">
                {outputTab === 'schema' && <SchemaView fields={Object.entries(flatOutput)} readOnly />}
                {outputTab === 'table'  && <TableView data={outputData} />}
                {outputTab === 'json'   && <JsonView  data={outputData} />}
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────
// SET / TRANSFORM Visual Field Builder (n8n style)
// ─────────────────────────────────────────────────────────────────
function SetTransformEditor({ config, onChange, flatInput, dragFieldName, hasInput }) {
  const mode     = config.mode || 'Manual Mapping'
  const includeInput = config.include_input ?? false

  // Parse field_mappings from JSON string or array
  const parseMappings = () => {
    const raw = config.field_mappings
    if (!raw || raw === '[]') return []
    try { return typeof raw === 'string' ? JSON.parse(raw) : raw }
    catch { return [] }
  }

  const mappings = parseMappings()

  const saveMappings = (next) => {
    onChange('field_mappings', JSON.stringify(next))
  }

  const addField = (name = '', value = '', type = 'String') => {
    saveMappings([...mappings, { name, type, value }])
  }

  const updateField = (index, key, val) => {
    const next = mappings.map((m, i) => i === index ? { ...m, [key]: val } : m)
    saveMappings(next)
  }

  const removeField = (index) => {
    saveMappings(mappings.filter((_, i) => i !== index))
  }

  // Drop a field from INPUT into the drop zone → add as new mapping
  const onDropZone = (e) => {
    e.preventDefault()
    const name = dragFieldName.current || e.dataTransfer.getData('text/plain')
    if (name) {
      addField(name, `{{${name}}}`, 'String')
      dragFieldName.current = null
    }
  }

  const onDragOver = (e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'copy' }

  // Drop onto an existing value input
  const onDropValue = (e, index) => {
    e.preventDefault()
    const name = dragFieldName.current || e.dataTransfer.getData('text/plain')
    if (name) {
      const cur = mappings[index]?.value || ''
      updateField(index, 'value', cur + `{{${name}}}`)
      dragFieldName.current = null
    }
  }

  // Infer type from value
  const inferType = (val) => {
    if (val === 'true' || val === 'false') return 'Boolean'
    if (!isNaN(val) && val.trim() !== '') return 'Number'
    return 'String'
  }

  return (
    <div className="ste">
      {/* Mode */}
      <div className="ste__mode">
        <label className="pf__label">Mode</label>
        <select className="pf__input pf__select" value={mode} onChange={e => onChange('mode', e.target.value)}>
          <option>Manual Mapping</option>
          <option>Keep Only Mapped Fields</option>
        </select>
        <p className="pf__help">
          {mode === 'Manual Mapping'
            ? 'Adds/updates the fields you define. All other input fields pass through.'
            : 'Only the fields you define below will appear in the output.'}
        </p>
      </div>

      {/* Fields to Set label */}
      <div className="ste__section-label">Fields to Set</div>

      {/* Field rows */}
      {mappings.length > 0 && (
        <div className="ste__rows">
          {mappings.map((mapping, i) => (
            <FieldRow
              key={i}
              mapping={mapping}
              index={i}
              onUpdate={updateField}
              onRemove={removeField}
              onDropValue={onDropValue}
              onDragOver={onDragOver}
              flatInput={flatInput}
            />
          ))}
        </div>
      )}

      {/* Drop zone */}
      <div
        className="ste__dropzone"
        onDrop={onDropZone}
        onDragOver={onDragOver}
        onClick={() => addField('', '', 'String')}
      >
        <span className="ste__dropzone-icon">+</span>
        <span>Drag input fields here</span>
        <span className="ste__dropzone-or">or</span>
        <button className="ste__add-btn" onClick={e => { e.stopPropagation(); addField('', '', 'String') }}>
          Add Field
        </button>
      </div>

      {/* Include Other Input Fields */}
      <div className="ste__toggle-row">
        <span className="pf__label">Include Other Input Fields</span>
        <label className="pf__toggle">
          <input type="checkbox" checked={!!includeInput} onChange={e => onChange('include_input', e.target.checked)}/>
          <span className="pf__track"><span className="pf__thumb"/></span>
        </label>
      </div>
    </div>
  )
}

// ── Single field row ──────────────────────────────────────────────
function FieldRow({ mapping, index, onUpdate, onRemove, onDropValue, onDragOver }) {
  const [showTypeMenu, setShowTypeMenu] = useState(false)
  const valueRef = useRef(null)

  const resolvedPreview = mapping.value?.replace(/\{\{[^}]+\}\}/g, '…') || ''

  return (
    <div className="fr">
      <GripVertical size={13} className="fr__drag"/>

      <div className="fr__body">
        {/* Row 1: name + type */}
        <div className="fr__row1">
          <input
            className="fr__name"
            value={mapping.name}
            onChange={e => onUpdate(index, 'name', e.target.value)}
            placeholder="Field name"
          />
          <div className="fr__type-wrap">
            <button className="fr__type-btn" onClick={() => setShowTypeMenu(v => !v)}>
              <span className="fr__type-icon">{typeIcon(mapping.type)}</span>
              <span className="fr__type-label">{mapping.type || 'String'}</span>
              <ChevronDown size={11}/>
            </button>
            {showTypeMenu && (
              <div className="fr__type-menu">
                {FIELD_TYPES.map(t => (
                  <button key={t} className="fr__type-opt" onClick={() => { onUpdate(index, 'type', t); setShowTypeMenu(false) }}>
                    <span>{typeIcon(t)}</span> {t}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Row 2: value expression */}
        <div className="fr__row2">
          <div className="fr__expr-wrap">
            <span className="fr__expr-eq">=</span>
            <input
              ref={valueRef}
              className="fr__value"
              value={mapping.value}
              onChange={e => onUpdate(index, 'value', e.target.value)}
              placeholder={`{{fieldName}} or a fixed value`}
              onDrop={e => onDropValue(e, index)}
              onDragOver={onDragOver}
            />
            <button className="fr__reset" title="Clear value" onClick={() => onUpdate(index, 'value', '')}>
              ↺
            </button>
          </div>
          {mapping.value && (
            <div className="fr__preview">{mapping.value}</div>
          )}
        </div>
      </div>

      <button className="fr__remove" onClick={() => onRemove(index)}><Trash2 size={12}/></button>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────
// Generic Param Field
// ─────────────────────────────────────────────────────────────────
function ParamField({ field, value, onChange, onFocus, fieldRef, isFocused, hasInput, onDrop, onDragOver }) {
  const { type, label, placeholder, options, help, min, max, step, required } = field
  if (field.key === 'field_mappings') return null // handled by SetTransformEditor
  if (type === 'conditions') return null
  const cls = `pf__input${isFocused?' pf__input--focused':''}`

  return (
    <div className="pf">
      <div className="pf__header">
        <label className="pf__label">{label}{required && <span className="pf__req">*</span>}</label>
        {help && <span className="pf__hint" title={help}>?</span>}
      </div>
      {hasInput && (type==='text'||type==='textarea') && (
        <div className="pf__drop-hint">⬅ Drag a field from INPUT or click while focused</div>
      )}
      {type==='text' && (
        <input ref={fieldRef} className={cls} value={value}
          onChange={e => onChange(e.target.value)} placeholder={placeholder}
          onFocus={onFocus} onDrop={onDrop} onDragOver={onDragOver}/>
      )}
      {type==='textarea' && (
        <textarea ref={fieldRef} className={`${cls} pf__textarea`} value={value}
          onChange={e => onChange(e.target.value)} placeholder={placeholder}
          rows={4} onFocus={onFocus} onDrop={onDrop} onDragOver={onDragOver}/>
      )}
      {type==='select' && (
        <select className="pf__input pf__select" value={value} onChange={e => onChange(e.target.value)}>
          {options?.map(o => <option key={o} value={o}>{o}</option>)}
        </select>
      )}
      {type==='number' && (
        <input ref={fieldRef} className={cls} type="number" value={value}
          onChange={e => onChange(Number(e.target.value))} min={min} max={max} onFocus={onFocus}/>
      )}
      {type==='boolean' && (
        <label className="pf__toggle">
          <input type="checkbox" checked={!!value} onChange={e => onChange(e.target.checked)}/>
          <span className="pf__track"><span className="pf__thumb"/></span>
          <span className="pf__toggle-label">{value?'Enabled':'Disabled'}</span>
        </label>
      )}
      {type==='slider' && (
        <div className="pf__slider-row">
          <input type="range" className="pf__slider" value={value}
            min={min??0} max={max??1} step={step??0.1} onChange={e => onChange(Number(e.target.value))}/>
          <span className="pf__slider-val">{value}</span>
        </div>
      )}
      {help && <p className="pf__help">{help}</p>}
    </div>
  )
}

function ConditionsEditor({ value, onChange, dragFieldName }) {
  const conditions = Array.isArray(value) ? value : []

  const addCondition = () => {
    onChange([ ...conditions, { value1: '', operation: 'equals', value2: '' } ])
  }

  const updateCondition = (index, key, val) => {
    const next = conditions.map((c, i) => i === index ? { ...c, [key]: val } : c)
    onChange(next)
  }

  const removeCondition = (index) => {
    const next = conditions.filter((_, i) => i !== index)
    onChange(next.length ? next : [])
  }

  const onDropValue = (e, index, key) => {
    e.preventDefault()
    const name = dragFieldName.current || e.dataTransfer.getData('text/plain')
    if (!name) return
    const expr = `{{${name}}}`
    const cur = conditions[index]?.[key] || ''
    updateCondition(index, key, cur ? cur + expr : expr)
    dragFieldName.current = null
  }

  const onDragOver = (e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'copy' }

  return (
    <div className="pf">
      <div className="pf__header">
        <label className="pf__label">Conditions</label>
      </div>
      {conditions.length === 0 && (
        <div className="ne__empty-panel">
          <p>No conditions yet</p>
          <button className="ne__execute-inline" onClick={addCondition}>Add Condition</button>
        </div>
      )}
      {conditions.length > 0 && (
        <div className="ne__fields">
          {conditions.map((c, i) => (
            <div key={i} className="pf__cond-row">
              <input
                className="pf__input"
                placeholder="{{$json.field}} or field.path"
                value={c.value1 || ''}
                onChange={e => updateCondition(i, 'value1', e.target.value)}
                onDrop={e => onDropValue(e, i, 'value1')}
                onDragOver={onDragOver}
              />
              <select
                className="pf__input pf__select"
                value={c.operation || 'equals'}
                onChange={e => updateCondition(i, 'operation', e.target.value)}
              >
                {[
                  'equals','not equals','contains','not contains',
                  'starts with','ends with','greater than','greater than or equal',
                  'less than','less than or equal','is empty','is not empty'
                ].map(op => <option key={op} value={op}>{op}</option>)}
              </select>
              <input
                className="pf__input"
                placeholder="value"
                value={c.value2 || ''}
                onChange={e => updateCondition(i, 'value2', e.target.value)}
                onDrop={e => onDropValue(e, i, 'value2')}
                onDragOver={onDragOver}
              />
              <button className="ne__execute-inline" onClick={() => removeCondition(i)}>Remove</button>
            </div>
          ))}
          <button className="ne__execute-inline" onClick={addCondition}>Add Condition</button>
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────
// Schema / Table / JSON views
// ─────────────────────────────────────────────────────────────────
function SchemaView({ fields, onDragStart, onInsert, readOnly }) {
  return (
    <div className="sv">
      {fields.map(([key, val]) => {
        const type = Array.isArray(val)?'array':val===null?'null':typeof val
        return (
          <div key={key} className="sv__row"
            draggable={!readOnly}
            onDragStart={e => onDragStart?.(e, key)}
            onClick={() => { if (!readOnly) onInsert?.(key) }}
            title={readOnly ? '' : `Drag or click to use "${key}"`}
          >
            <div className="sv__row-main">
              {!readOnly && <GripVertical size={11} className="sv__drag-icon"/>}
              <span className={`sv__type sv__type--${type}`}>{typeIcon(type)}</span>
              <span className="sv__key">{key}</span>
              <span className="sv__val">{truncate(JSON.stringify(val), 30)}</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

function TableView({ data }) {
  if (!data || typeof data !== 'object') return <JsonView data={data}/>
  const rows = Array.isArray(data) ? data : [data]
  const cols = [...new Set(rows.flatMap(r => Object.keys(r||{})))]
  if (!cols.length) return <div className="ne__empty-panel"><p>Empty</p></div>
  return (
    <div className="tv">
      <table className="tv__table">
        <thead><tr>{cols.map(c => <th key={c}>{c}</th>)}</tr></thead>
        <tbody>
          {rows.map((row,i) => (
            <tr key={i}>{cols.map(c => <td key={c}>{row&&row[c]!==undefined?truncate(JSON.stringify(row[c]),40):'—'}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function JsonView({ data }) {
  return <pre className="jv">{JSON.stringify(data, null, 2)}</pre>
}

// ─────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────
function flattenObject(obj, prefix='') {
  if (!obj || typeof obj !== 'object') return prefix ? {[prefix]:obj} : {}
  return Object.entries(obj).reduce((acc,[k,v]) => {
    const key = prefix ? `${prefix}.${k}` : k
    if (v && typeof v==='object' && !Array.isArray(v) && Object.keys(v).length < 10) {
      Object.assign(acc, flattenObject(v, key))
    } else { acc[key] = v }
    return acc
  }, {})
}

function truncate(str, n) { return str&&str.length>n ? str.slice(0,n)+'…' : str }

function typeIcon(type) {
  return {String:'T',string:'T',Number:'#',number:'#',Boolean:'✓',boolean:'✓',Object:'{…}',object:'{…}',Array:'[…]',array:'[…]',null:'∅'}[type]||'?'
}


