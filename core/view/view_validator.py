from core.registry import registry
from core.registry.fields_cache import FieldCache


class ViewValidationError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"View validation failed: {errors}")


class ViewValidator:

    def __init__(self, db, field_cache: FieldCache):
        self.db = db
        self.field_cache = field_cache
        self.errors = []

    def validate(self, model: str, view_type: str, arch_json: dict):
        self.errors = []

        # Check model exists in registry
        if not registry.get_model(model):
            self.errors.append(f"Model '{model}' does not exist in registry")
            raise ViewValidationError(self.errors)

        # Build a fast lookup of valid fields for this model
        self.valid_fields = {
            f.name: f
            for f in self.field_cache.get_fields(model)
        }
        
        self.model = model
        # Validate each section
        self._validate_components(arch_json.get("components", []))
        self._validate_actions(arch_json.get("actions", []))

        if view_type == "list":
            self._validate_columns(arch_json.get("columns", []))
            self._validate_filters(arch_json.get("filters", []))

        if self.errors:
            raise ViewValidationError(self.errors)

    # ─────────────────────────────────────────
    # COMPONENTS (recursive)
    # ─────────────────────────────────────────

    def _validate_components(self, components: list):
        for component in components:
            ctype = component.get("type")

            if ctype == "field":
                self._validate_field_component(component)

            elif ctype in ("group", "tab", "notebook"):
                # Recurse into children
                self._validate_components(component.get("children", []))

            elif ctype == "tabs":
                for child in component.get("children", []):
                    if child.get("type") != "tab":
                        self.errors.append(
                            f"'tabs' children must all be type 'tab', got '{child.get('type')}'"
                        )
                    self._validate_components(child.get("children", []))

            elif ctype in ("separator", "html"):
                pass  # No field references, nothing to validate

            else:
                self.errors.append(f"Unknown component type: '{ctype}'")

    def _validate_field_component(self, component: dict):
        name = component.get("name")
        widget = component.get("widget")

        if not name:
            self.errors.append("A 'field' component is missing 'name'")
            return

        # ── Does field exist on this model? ──
        field_meta = self.valid_fields.get(name)
        if not field_meta:
            self.errors.append(
                f"Field '{name}' does not exist on model '{self.model}'"
            )
            return

        # ── Does widget match field type? ──
        if widget:
            self._validate_widget_match(name, widget, field_meta)

        # ── Relational field checks ──
        if field_meta.field_type in ("many2one", "many2many", "one2many") or \
           widget in ("many2one", "many2many", "one2many"):
            self._validate_relational_field(component, field_meta)

    def _validate_widget_match(self, name, widget, field_meta):
        """
        Loose check — widget must be compatible with the field's storage type.
        E.g. you can't put a 'date' widget on an integer field.
        """
        incompatible = {
            "INTEGER":  {"date", "datetime", "many2one", "one2many", "many2many", "boolean"},
            "BOOLEAN":  {"date", "datetime", "many2one", "one2many", "many2many", "integer", "float"},
            "many2one":  {"date", "datetime", "integer", "float", "boolean", "text"},
            "one2many":  {"date", "datetime", "integer", "float", "boolean", "text", "char"},
            "many2many": {"date", "datetime", "integer", "float", "boolean", "text", "char"},
        }
        bad_widgets = incompatible.get(field_meta.field_type, set())
        if widget in bad_widgets:
            self.errors.append(
                f"Field '{name}': widget '{widget}' is incompatible "
                f"with field type '{field_meta.field_type}'"
            )

    def _validate_relational_field(self, component: dict, field_meta):
        name = component.get("name")
        widget = component.get("widget") or field_meta.field_type

        # relation model must exist
        relation = component.get("relation") or field_meta.relation
        if not relation:
            self.errors.append(
                f"Field '{name}': relational field must have a 'relation'"
            )
            return

        if not registry.get_model(relation):
            self.errors.append(
                f"Field '{name}': relation model '{relation}' "
                f"does not exist in registry"
            )

        # one2many must have inline_view
        if widget == "one2many":
            inline_view = component.get("inline_view")
            if not inline_view:
                self.errors.append(
                    f"Field '{name}': one2many widget requires 'inline_view'"
                )
            else:
                self._validate_inline_view_exists(name, inline_view)

    def _validate_inline_view_exists(self, field_name: str, inline_view: str):
        from modules.base.models.views import IrView
        exists = (
            self.db.query(IrView)
            .filter(IrView.name == inline_view, IrView.type == "list")
            .first()
        )
        if not exists:
            self.errors.append(
                f"Field '{field_name}': inline_view '{inline_view}' "
                f"not found in ir_view (must be a list view)"
            )

    # ─────────────────────────────────────────
    # ACTIONS
    # ─────────────────────────────────────────

    def _validate_actions(self, actions: list):
        known_types = {"submit", "delete", "rpc", "redirect", "wizard"}

        for action in actions:
            name = action.get("name", "<unnamed>")
            atype = action.get("type")

            if not atype:
                self.errors.append(f"Action '{name}' is missing 'type'")
                continue

            if atype not in known_types:
                self.errors.append(
                    f"Action '{name}': unknown type '{atype}'. "
                    f"Must be one of {known_types}"
                )

            if atype == "rpc" and not action.get("endpoint"):
                self.errors.append(
                    f"Action '{name}': type 'rpc' requires 'endpoint'"
                )

    # ─────────────────────────────────────────
    # COLUMNS (list views only)
    # ─────────────────────────────────────────

    def _validate_columns(self, columns: list):
        for col in columns:
            field_name = col.get("field")
            if not field_name:
                self.errors.append("A column entry is missing 'field'")
                continue
            if field_name not in self.valid_fields:
                self.errors.append(
                    f"Column field '{field_name}' does not exist "
                    f"on model '{self.model}'"
                )

    # ─────────────────────────────────────────
    # FILTERS (list views only)
    # ─────────────────────────────────────────

    def _validate_filters(self, filters: list):
        valid_operators = {
            "=", "!=", "ilike", "like", ">", "<", ">=", "<=",
            "in", "not_in", "is_null", "is_not_null"
        }

        for f in filters:
            field_name = f.get("field")
            operator = f.get("operator")

            if not field_name:
                self.errors.append("A filter entry is missing 'field'")
                continue

            if field_name not in self.valid_fields:
                self.errors.append(
                    f"Filter field '{field_name}' does not exist "
                    f"on model '{self.model}'"
                )

            if operator and operator not in valid_operators:
                self.errors.append(
                    f"Filter on '{field_name}': unknown operator '{operator}'"
                )