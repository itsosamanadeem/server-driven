from pydantic import RootModel
from typing import Dict, Any

class DynamicModel(RootModel[Dict[str,Any]]):
    ...