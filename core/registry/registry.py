import logging
logger = logging.getLogger(__name__)

class Registry:
    def __init__(self):
        self.models = {}
        self.modules = []
        self.model_meta = {}
        self.loaded = False

    def register_model(self, name, model_class):
        if name in self.models:
            raise Exception(f"Model already registered: {name}")

        self.models[name] = model_class
        
        self.model_meta[name] = {
            "model": name,
            "name": model_class.__name__,
            "table_name": model_class.__tablename__,
            "module": model_class.__module__.split(".")[1],
            "columns": {},
            "relationships": {}
        }

    def get_model(self, name):
        return self.models.get(name)

    def load_modules(self, modules):
        """
        modules = ordered list of module names
        """
        for module in modules:
            try:
                __import__(f"modules.{module}.models")
                logger.info(f"✅ Loaded module: {module}")
            except Exception as e:
                logger.error(f"Failed to load module {module}: {e}")
                raise

    def setup_models(self):
        """
        Hook point for future:
        - resolve relationships
        - apply inheritance
        - validate fields
        """
        logger.info("🔧 Setting up models...")

    def finalize(self):
        self.loaded = True
        logger.info("🚀 Registry ready")