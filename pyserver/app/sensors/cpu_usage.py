import psutil
from .base import BaseSensor

class CPUUsageSensor(BaseSensor):
    async def sample(self) -> float:
        usage = psutil.cpu_percent(interval=None)
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
