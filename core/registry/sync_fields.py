from sqlalchemy.orm import Session
from core.models.ir_fields import IrField
from core.registry.fields.fields_extractor import extract_fields
import logging
logger = logging.getLogger(__name__)

def sync_fields(session: Session):
    fields = extract_fields()
    
    for field in fields:
        exists = session.query(IrField).filter_by(
            model=field["model"],
            name=field["name"]
        ).first()
        logger.info(f"🚀 Fields already registered in ir_fields field name: {field}")
        if not exists:
            record = IrField(
                model=field["model"],
                name=field["name"],
                field_type=field["field_type"],
                required=field["required"],
                relation=field["relation"]
            )
            session.add(record)
            logger.info("🚀 Registring Fields in ir_fields")