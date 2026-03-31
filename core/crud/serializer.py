def serialize(obj):
    result = {}

    for column in obj.__table__.columns:
        result[column.name] = getattr(obj, column.name)

    return result