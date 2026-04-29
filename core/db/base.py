from sqlalchemy.orm import as_declarative, declared_attr
import os

if os.getenv('ENV') == "production":
    def forbidden_create_all(*args, **kwargs):
        raise Exception("❌ create_all is forbidden in production")
    Base.metadata.create_all = forbidden_create_all  # type: ignore
    
@as_declarative()
class Base:
    id: any #type: ignore
    __name__: str

    @declared_attr  # type: ignore
    def __tablename__(cls):
        return cls.__name__.lower()

    def __init_subclass__(cls, **kwargs):
        """
        AUTO register every model
        """
        super().__init_subclass__(**kwargs)

        # if hasattr(cls, "__tablename__"):
        #     registry.register_model(cls.__tablename__, cls)