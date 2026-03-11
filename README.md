# AI Automation Tool (n8n-style)

A simplified, n8n-inspired automation engine with a node-based workflow editor. The backend executes workflows as a directed graph and passes **items** between nodes. Each item is a dict shaped like:

```
{ "json": { ... } }
```

## Architecture

- `backend/app/engine` - workflow execution engine (graph, context, executor)
- `backend/app/nodes` - built-in node implementations + registry
- `backend/app/api` - REST API for running, scheduling, and webhook triggering
- `frontend` - React Flow UI for building and running workflows

## Execution Model

- Nodes receive `inputs: List[List[Item]]` (one list per input handle)
- Nodes return `outputs: List[List[Item]]` (one list per output handle)
- Branching is handled by emitting items to different outputs
- Nodes with no input items are skipped unless they are triggers

## API

- `POST /api/workflows/run` - run a workflow
- `POST /api/workflows/run-node` - execute up to a specific node
- `POST /api/workflows/validate` - basic graph validation
- `POST /api/workflows/schedule` - schedule a workflow
- `POST /api/workflows/webhook/register` - register a webhook workflow

## Data Notes

- Use `{{field.path}}` in node configs to reference input item fields.
- Outputs are returned as:
  - `node_items`: full per-node items (all outputs)
  - `node_outputs`: preview for quick UI schema rendering
  - `final_output`: list of JSON outputs from the last executed node
