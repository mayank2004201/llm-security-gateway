from fastapi import FastAPI
from app.api.routes import router
from data.database import Database

def create_app():
    # Initialize Database
    Database.init_db()
    
    app = FastAPI(title="LLM Security Gateway Pro", version="2.0.0")
    
    # Register Routes
    app.include_router(router)
    
    return app

app = create_app()
