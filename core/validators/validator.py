from core.registry import registry

class Validator:

    @staticmethod
    def validate(db, model_name: str, data: dict):
        fields = registry.field_cache.get_fields(model_name)

        field_map = {f.name: f for f in fields}

        # 🔹 1. Required fields
        # for field in fields:
        #     if field.required and field.name not in data:
        #         if field.name == 'id':
        #             continue
        #         raise ValueError(f"Field '{field.name}' is required")

        # 🔹 2. Field validation
        for key, value in data.items():

            if key not in field_map:
                raise ValueError(f"Unknown field '{key}'")

            field = field_map[key]

            # 🔹 Type validation
            Validator._validate_type(field, value)

            # 🔹 Relationship validation
            if field.field_type == "many2one":
                Validator._validate_many2one(db, field, value)

            elif field.field_type == "many2many":
                Validator._validate_many2many(db, field, value)

            elif field.field_type == "one2many":
                if not isinstance(value, list):
                    raise TypeError(f"{key} must be a list")

    # -----------------------
    # 🔧 TYPE VALIDATION
    # -----------------------
    @staticmethod
    def _validate_type(field, value):
        type_map = {
            "integer": int,
            "float": float,
            "string": str,
            "boolean": bool,
        }

        expected = type_map.get(field.field_type)

        if expected and value is not None and not isinstance(value, expected):
            raise TypeError(
                f"Field '{field.name}' expects {expected.__name__}, got {type(value).__name__}"
            )

    # -----------------------
    # 🔧 MANY2ONE
    # -----------------------
    @staticmethod
    def _validate_many2one(db, field, value):
        model = registry.get_model(field.relation)

        if not db.get(model, value):
            raise ValueError(
                f"{field.name}: related record {value} not found in {field.relation}"
            )

    # -----------------------
    # 🔧 MANY2MANY
    # -----------------------
    @staticmethod
    def _validate_many2many(db, field, value):
        if not isinstance(value, list):
            raise TypeError(f"{field.name} must be a list of IDs")

        model = registry.get_model(field.relation)

        records = db.query(model).filter(model.id.in_(value)).all() # type: ignore

        if len(records) != len(value):
            raise ValueError(f"{field.name}: some related records not found")