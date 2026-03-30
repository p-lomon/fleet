from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from dashboard.api import create_router


def create_app(queue_dir: str | Path) -> FastAPI:
    """Create the dashboard FastAPI application."""
    app = FastAPI(title="Fleet Dashboard", version="0.1.0")
    
    # Mount API routes
    app.include_router(create_router(queue_dir), prefix="/api")
    
    # Mount static files
    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Root route serves the dashboard
    @app.get("/")
    def root() -> FileResponse:
        return FileResponse(static_dir / "index.html")
    
    return app


def run_dashboard(queue_dir: str | Path, host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run the dashboard server."""
    import uvicorn
    app = create_app(queue_dir)
    uvicorn.run(app, host=host, port=port)
