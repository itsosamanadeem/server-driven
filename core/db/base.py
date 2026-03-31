from sqlalchemy.orm import as_declarative, declared_attr
from core.registry import registry

@as_declarative()
class Base:
    id: any
    __name__: str

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def __init_subclass__(cls, **kwargs):
        """
        AUTO register every model
        """
        super().__init_subclass__(**kwargs)

        if hasattr(cls, "__tablename__"):
            registry.register_model(cls.__tablename__, cls)