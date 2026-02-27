# Automatically generated Python theme
# Screens are imported from the app/screens/ folder

from app.screens.system_status import SCREEN as system_status
from app.screens.network_charts import SCREEN as network_charts
from app.screens.clock_date import SCREEN as clock_date
from app.screens.storage_power import SCREEN as storage_power
from app.screens.performance_dashboard import SCREEN as performance_dashboard
from app.screens.zen_weather_time import SCREEN as zen_weather_time

THEME = {
    'orientation': 'portrait',
    'refresh': 'update',
    'screens': [
        system_status,
        network_charts,
        clock_date,
        storage_power,
        performance_dashboard,
        zen_weather_time
    ]
}
