from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import workflows, webhooks
from app.nodes.registry import NodeRegistry
from app.scheduler.job_store import start_scheduler, stop_scheduler

app = FastAPI(
    title="AI Automation Platform",
    description="Simple n8n-like workflow automation",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all node plugins on startup
@app.on_event("startup")
async def startup():
    NodeRegistry.discover()
    print(f"✅ Registered nodes: {NodeRegistry.list_nodes()}")
    start_scheduler()

@app.on_event("shutdown")
async def shutdown():
    stop_scheduler()



app.include_router(workflows.router, prefix="/api/workflows", tags=["Workflows"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])

@app.get("/")
def root():
    return {"status": "AI Automation Platform v2 running"}

@app.get("/api/nodes")
def get_available_nodes():
    """Return all registered node types for the frontend palette."""
    return NodeRegistry.get_node_definitions()