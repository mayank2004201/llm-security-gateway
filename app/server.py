from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.routes import router
from data.database import Database
import os

def create_app():
    # Initialize Database
    Database.init_db()
    
    app = FastAPI(title="LLM Security Gateway Pro", version="2.0.0")
    
    # Register Routes
    app.include_router(router)
    
    # Serve Static Files
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    os.makedirs(static_dir, exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(static_dir, "index.html"))
    
    return app

app = create_app()
