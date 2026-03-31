from fastapi import FastAPI
from core.registry.sync_fields import sync_fields
from core.registry.sync import sync_models
from core.db.connection import engine 
from core.db.session import session
from core.db.base import Base
from core.registry.loader import load_all
from core.logger import setup_logger

setup_logger()

def create_tables():       
    load_all()
    Base.metadata.create_all(bind=engine)
    
    db = session()
    sync_models(db)
    sync_fields(db)
    db.commit()
    db.close() 

def start_application():
    app = FastAPI(title="HRMS",version="0.1")
    create_tables()
    return app


app = start_application()

from api.router import router
app.include_router(router=router, prefix="/api")

@app.get("/docs")
def home():
    return {"msg":"Hello FastAPI🚀"}


