import json
import logging
from pathlib import Path
from core.registry import registry
from core.view.view_validator import ViewValidator, ViewValidationError
from core.registry.manifest import load_manifest
from modules.base.models.groups import Group
from modules.base.models.views import IrView

logger = logging.getLogger(__name__)


def _normalize_data_entries(data_entries):
    if not data_entries:
        return []
    if isinstance(data_entries, (list, tuple, set)):
        return list(data_entries)
    logger.warning("Manifest data key must be list/tuple/set; got %s", type(data_entries).__name__)
    return []


def _load_json_file(path: Path) -> dict | None:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("View file not found: %s", path)
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON in view file %s: %s", path, exc)
    return None


def _upsert_view(db, payload: dict):
    name = payload.get("name")
    model = payload.get("model")
    view_type = payload.get("type")
    arch_json = payload.get("arch_json")

    if not all([name, model, view_type, isinstance(arch_json, dict)]):
        logger.error("Invalid view payload. Required: name, model, type, arch_json(dict). Payload=%s", payload)
        return
    
    validator = ViewValidator(db, registry.field_cache)
    try:
        validator.validate(model, view_type, arch_json) #type: ignore
    except ViewValidationError as e:
        logger.error(
            "View '%s' failed validation — skipping. Errors: %s",
            name, e.errors
        )
        return

    existing = db.query(IrView).filter(IrView.name == name).first()

    if existing:
        existing.model = model
        existing.type = view_type
        existing.arch_json = arch_json
        existing.priority = int(payload.get("priority", 100))
        existing.active = bool(payload.get("active", True))
        view_record = existing
    else:
        view_record = IrView(
            name=name, #type: ignore
            model=model, #type: ignore
            type=view_type, #type: ignore
            arch_json=arch_json, #type: ignore
            priority=int(payload.get("priority", 100)), #type: ignore
            active=bool(payload.get("active", True)), #type: ignore
        )
        db.add(view_record)
        db.flush()

    group_names = payload.get("groups", []) or []
    if not isinstance(group_names, list):
        logger.warning("groups must be a list in view %s", name)
        group_names = []

    view_record.groups.clear()
    for group_name in group_names:
        group = db.query(Group).filter(Group.name == group_name).first()
        if not group:
            logger.warning("Group '%s' not found for view '%s'. Skipping relation.", group_name, name)
            continue
        view_record.groups.append(group)


def sync_views(db, modules: list[str]):
    for module in modules:
        manifest = load_manifest(module)
        data_entries = _normalize_data_entries(manifest.get("data"))

        for rel_path in data_entries:
            if not str(rel_path).endswith(".json"):
                continue

            full_path = Path("modules") / module / str(rel_path)
            payload = _load_json_file(full_path)
            if not payload:
                continue

            _upsert_view(db, payload)
            logger.info("Loaded view data from %s", full_path)
