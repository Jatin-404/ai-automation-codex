import BaseNode from './BaseNode'

const wrap = (props) => <BaseNode {...props} />

const nodeTypes = {
  // Triggers
  manual_trigger:  wrap,
  webhook_trigger: wrap,
  scheduler:       wrap,
  // Actions
  http_request:    wrap,
  set_transform:   wrap,
  code_node:       wrap,
  notification:    wrap,
  whatsapp:        wrap,
  // Logic
  filter_items:    wrap,
  limit_items:     wrap,
  // AI
  ai_node:         wrap,
}

export default nodeTypes
