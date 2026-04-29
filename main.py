from fastapi import FastAPI
from core.registry import registry
from core.registry.sync_fields import sync_fields
from core.registry.sync import sync_models
from core.registry.sync_permissions import sync_permissions
from core.db.connection import engine 
from core.db.session import session
from core.db.base import Base
from core.registry.loader import load_all
from core.logger import setup_logger
from sqlalchemy import exc
import logging
logger = logging.getLogger(__name__)


setup_logger()

def init_metadata():       
    load_all()
    
    db = session()
    
    sync_models(db)
    sync_fields(db)
    sync_permissions(db, registry)
    
    try:
        db.commit()
    except exc.SQLAlchemyError as e:
        db.rollback()
        logger.error(f"{e}")
        raise
        
    registry.field_cache.load(db)
    db.close() 

def start_application():
    app = FastAPI(title="HRMS",version="0.1")
    init_metadata()
    return app


app = start_application()

from api.router import router
from api.auth_router import router as auth_router
from api.access_router import router as access_router
app.include_router(router=auth_router, prefix="/api")
app.include_router(router=access_router, prefix="/api")
app.include_router(router=router, prefix="/api")

@app.get("/docs")
def home():
    return {"msg":"Hello FastAPI🚀"}


