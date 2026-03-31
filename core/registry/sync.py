from sqlalchemy.orm import Session
from core.registry import registry
from core.models.ir_model import IrModel
import logging
logger = logging.getLogger(__name__)

def sync_models(session: Session):
    """
    Sync registry models into ir_model table
    """

    for model_name, meta in registry.model_meta.items():

        existing = session.query(IrModel).filter_by(model=model_name).first()

        if not existing:
            record = IrModel(
                model=meta["model"],
                name=meta["name"],
                table_name=meta["table_name"],
                module=meta["module"]
            )
            session.add(record)
            logger.info(f"✅ Registered model in DB: {model_name}")