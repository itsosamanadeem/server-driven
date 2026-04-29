def to_dict(obj):
    data = {}

    for column in obj.__table__.columns:
        data[column.name] = getattr(obj, column.name)

    return data