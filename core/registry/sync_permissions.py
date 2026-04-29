import logging

from modules.base.models.rbac import Permission

logger = logging.getLogger(__name__)

ACTIONS = ("create", "read", "write", "delete")


def sync_permissions(db, registry):
    for model_name in registry.models.keys():
        for action in ACTIONS:
            code = f"{model_name}.{action}"
            existing = db.query(Permission).filter(Permission.code == code).first()
            if existing:
                continue

            db.add(
                Permission(
                    code=code, #type:ignore
                    name=f"{model_name} {action}", #type:ignore
                    model=model_name, #type:ignore
                    action=action, #type:ignore
                )
            )
            logger.info(f"Created permission: {code}")
