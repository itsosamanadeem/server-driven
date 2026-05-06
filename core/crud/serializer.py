def serialize(obj, allowed_fields=None):
    result = {}
    hidden_fields = {"password_hash"}

    for column in obj.__table__.columns:
        if column.name in hidden_fields:
            continue
        if allowed_fields is not None and column.name not in allowed_fields:
            continue
        result[column.name] = getattr(obj, column.name)

    return result
