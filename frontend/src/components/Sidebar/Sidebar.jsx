import useWorkflowStore from '../../store/workflowStore'
import './Sidebar.css'

const CATEGORY_ORDER = ['trigger', 'action', 'ai', 'logic']
const CATEGORY_LABELS = {
  trigger: '⚡ Triggers',
  action:  '🔧 Actions',
  ai:      '🤖 AI',
  logic:   '🔀 Logic',
}

export default function Sidebar() {
  const { availableNodes } = useWorkflowStore()

  const grouped = CATEGORY_ORDER.reduce((acc, cat) => {
    acc[cat] = availableNodes.filter(n => n.category === cat)
    return acc
  }, {})

  const onDragStart = (e, nodeType, definition) => {
    e.dataTransfer.setData('application/reactflow-type', nodeType)
    e.dataTransfer.setData('application/reactflow-def', JSON.stringify(definition))
    e.dataTransfer.effectAllowed = 'move'
  }

  return (
    <aside className="sidebar">
      <div className="sidebar__header">
        <h2 className="sidebar__title">Nodes</h2>
        <p className="sidebar__hint">Drag onto canvas</p>
      </div>

      <div className="sidebar__groups">
        {CATEGORY_ORDER.map(cat => {
          const nodes = grouped[cat]
          if (!nodes?.length) return null
          return (
            <div key={cat} className="sidebar__group">
              <div className="sidebar__group-label">{CATEGORY_LABELS[cat]}</div>
              {nodes.map(def => (
                <div
                  key={def.type}
                  className="sidebar__node-card"
                  style={{ '--card-color': getCategoryColor(def.category) }}
                  draggable
                  onDragStart={(e) => onDragStart(e, def.type, def)}
                  title={def.description}
                >
                  <span className="card-icon">{def.icon}</span>
                  <div className="card-text">
                    <span className="card-label">{def.label}</span>
                    <span className="card-desc">{def.description}</span>
                  </div>
                </div>
              ))}
            </div>
          )
        })}
      </div>
    </aside>
  )
}

function getCategoryColor(cat) {
  return { trigger: '#3b82f6', action: '#10b981', ai: '#8b5cf6', logic: '#ef4444' }[cat] || '#6366f1'
}