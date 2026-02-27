from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseSensor(ABC):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.last_value = None

    @abstractmethod
    async def sample(self) -> Any:
        pass

    def settings(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "config": self.config
        }
