import json
from core.models.audit_log import AuditLog

class AuditService:

    @staticmethod
    def log(db, model, record_id, action, old_data=None, new_data=None, user=None):
        record = AuditLog( 
            model=model, #type: ignore
            record_id=record_id, #type: ignore
            action=action, #type: ignore
            old_data=json.dumps(old_data, default=str) if old_data else None, #type: ignore
            new_data=json.dumps(new_data, default=str) if new_data else None, #type: ignore
            user=user #type: ignore
        )

        db.add(record)
