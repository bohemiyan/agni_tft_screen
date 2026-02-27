from datetime import datetime
from app.sensors.base import BaseSensor

class ClockSensor(BaseSensor):
    async def sample(self) -> tuple:
        now = datetime.now()
        
        # 0: 24h:mm
        val0 = f"{now.hour}:{now.minute:02d}"
        
        # 1: 12h:mm
        hour12 = now.hour % 12
        if hour12 == 0:
            hour12 = 12
        val1 = f"{hour12}:{now.minute:02d}"
        
        # 2: ss
        val2 = f"{now.second:02d}"
        
        # 3: am/pm
        val3 = "am" if now.hour < 12 else "pm"
        
        self._last_value = (val0, val1, val2, val3)
        return self._last_value

    @classmethod
    def info(cls) -> dict:
        return {
            "name": 'clock',
            "description": 'current time info',
            "icon": 'pi-clock',
            "multiple": False,
            "ident": [],
            "fields": []
        }
