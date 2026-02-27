import psutil
from .base import BaseSensor

class MemorySensor(BaseSensor):
    async def sample(self) -> float:
        memory = psutil.virtual_memory()
        usage = memory.percent
        self.last_value = usage
        return usage

    def settings(self) -> dict:
        settings = super().settings()
        settings.update({
            "unit": "%",
            "min": 0,
            "max": 100
        })
        return settings
