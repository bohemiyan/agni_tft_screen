from datetime import datetime
from app.sensors.base import BaseSensor

class CalendarSensor(BaseSensor):
    def _get_ordinal(self, n: int) -> str:
        if 11 <= (n % 100) <= 13:
            return f"{n}th"
        if n % 10 == 1: return f"{n}st"
        if n % 10 == 2: return f"{n}nd"
        if n % 10 == 3: return f"{n}rd"
        return f"{n}th"

    async def sample(self) -> tuple:
        now = datetime.now()
        
        month = now.month
        day = now.day
        year = now.year
        short_year = str(year)[2:]
        
        weekday = now.strftime("%A")
        weekday_short = now.strftime("%a")
        month_name = now.strftime("%B")
        month_short = now.strftime("%b")
        
        val0 = f"{month}/{day}/{short_year}"
        val1 = f"{year}-{month}-{day}"
        val2 = f"{day}"
        val3 = self._get_ordinal(day)
        val4 = weekday
        val5 = weekday_short
        val6 = month_name
        val7 = month_short
        val8 = f"{year}"
        val9 = f"{month}"
        val10 = short_year
        val11 = f"{year}.{month}.{day}"
        
        self._last_value = (val0, val1, val2, val3, val4, val5, val6, val7, val8, val9, val10, val11)
        return self._last_value

    @classmethod
    def info(cls) -> dict:
        return {
            "name": 'calendar',
            "description": 'current date info',
            "icon": 'pi-calendar',        
            "multiple": False,
            "ident": [],
            "fields": []
        }
