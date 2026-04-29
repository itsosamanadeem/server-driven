def to_dict(obj):
    data = {}
    hidden_fields = {"password_hash"}

    for column in obj.__table__.columns:
        if column.name in hidden_fields:
            continue
        data[column.name] = getattr(obj, column.name)

    return data
