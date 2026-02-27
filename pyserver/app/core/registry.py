import json
import os
import uuid
from typing import Dict, Any, List
from .modular_models import SensorNode, WidgetNode, ScreenNode, ThemeNode

class Registry:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.sensors: Dict[str, SensorNode] = {}
        self.widgets: Dict[str, WidgetNode] = {}
        self.screens: Dict[str, ScreenNode] = {}
        self.themes: Dict[str, ThemeNode] = {}
        self.active_theme_id: str = None
        self.load()

    def generate_id(self) -> str:
        return uuid.uuid4().hex[:8]

    def load(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                data = json.load(f)
            
            for k, v in data.get("sensors", {}).items():
                self.sensors[k] = SensorNode(**v)
            for k, v in data.get("widgets", {}).items():
                self.widgets[k] = WidgetNode(**v)
            for k, v in data.get("screens", {}).items():
                self.screens[k] = ScreenNode(**v)
            for k, v in data.get("themes", {}).items():
                self.themes[k] = ThemeNode(**v)
                
            self.active_theme_id = data.get("active_theme_id")
        else:
            self.seed_defaults()
            self.save()

    def seed_defaults(self):
        # 1. Sensors (9 basic system sensors)
        s_cpu = SensorNode(id="s_cpu", type="cpu_usage", name="CPU Usage", protected=True)
        s_temp = SensorNode(id="s_temp", type="cpu_temp", name="CPU Temp", protected=True)
        s_pwr = SensorNode(id="s_pwr", type="cpu_power", name="CPU Power", protected=True)
        s_mem = SensorNode(id="s_mem", type="memory", name="Memory", protected=True)
        s_clk = SensorNode(id="s_clk", type="clock", name="Clock", protected=True)
        s_cal = SensorNode(id="s_cal", type="calendar", name="Calendar", protected=True)
        s_net = SensorNode(id="s_net", type="network", name="Network", protected=True)
        s_spc = SensorNode(id="s_spc", type="space", name="Storage Space", protected=True)
        s_wth = SensorNode(id="s_wth", type="weather", name="Weather", protected=True)
        
        self.sensors = {s.id: s for s in [s_cpu, s_temp, s_pwr, s_mem, s_clk, s_cal, s_net, s_spc, s_wth]}

        # 2. Widgets (8 basic widget references)
        w_clk = WidgetNode(id="w_clk", type="text", name="Clock Text", sensor_id="s_clk", rect={"x": 0, "y": 3, "width": 170, "height": 14}, properties={"color": "#00d4ff", "font": "bold 12px Arial", "align": "center", "format": "{1} {3}"}, protected=True)
        w_cal = WidgetNode(id="w_cal", type="text", name="Date Text", sensor_id="s_cal", rect={"x": 0, "y": 3, "width": 170, "height": 12}, properties={"color": "#4a6080", "font": "10px Arial", "align": "right", "format": "{6} {9}/{2}/{10}"}, protected=True)
        w_cpu_ring = WidgetNode(id="w_cpu_ring", type="doughnut_chart", name="CPU Ring", sensor_id="s_cpu", rect={"x": 10, "y": 20, "width": 80, "height": 80}, properties={"used": "#00d4ff", "free": "#0d1e2d", "format": "{0}"}, protected=True)
        w_cpu_text = WidgetNode(id="w_cpu_text", type="text", name="CPU Text", sensor_id="s_cpu", rect={"x": 10, "y": 55, "width": 80, "height": 16}, properties={"color": "#00d4ff", "font": "bold 14px Arial", "align": "center", "format": "{0}%"}, protected=True)
        w_mem_ring = WidgetNode(id="w_mem_ring", type="doughnut_chart", name="Memory Ring", sensor_id="s_mem", rect={"x": 90, "y": 20, "width": 80, "height": 80}, properties={"used": "#a855f7", "free": "#1a0d2e", "format": "{2}"}, protected=True)
        w_mem_text = WidgetNode(id="w_mem_text", type="text", name="Memory Text", sensor_id="s_mem", rect={"x": 90, "y": 55, "width": 80, "height": 16}, properties={"color": "#a855f7", "font": "bold 14px Arial", "align": "center", "format": "{2}%"}, protected=True)
        w_net_line = WidgetNode(id="w_net_line", type="line_chart", name="Network Chart", sensor_id="s_net", rect={"x": 0, "y": 200, "width": 170, "height": 40}, properties={"outline": "#00d4ff"}, protected=True)
        w_spc_bar = WidgetNode(id="w_spc_bar", type="bar_chart", name="Storage Bar", sensor_id="s_spc", rect={"x": 10, "y": 150, "width": 150, "height": 20}, properties={"used": "#10b981"}, protected=True)
        
        self.widgets = {w.id: w for w in [w_clk, w_cal, w_cpu_ring, w_cpu_text, w_mem_ring, w_mem_text, w_net_line, w_spc_bar]}

        # 3. Screens (6 typical system screens)
        sc_sys = ScreenNode(id="sc_sys", name="System Status", background="#060a10", widget_ids=["w_clk", "w_cal", "w_cpu_ring", "w_cpu_text", "w_mem_ring", "w_mem_text"], protected=True)
        sc_net = ScreenNode(id="sc_net", name="Network Charts", background="#060a10", widget_ids=["w_clk", "w_net_line"], protected=True)
        sc_clk = ScreenNode(id="sc_clk", name="Clock Date", background="#060a10", widget_ids=["w_clk", "w_cal"], protected=True)
        sc_sto = ScreenNode(id="sc_sto", name="Storage Power", background="#060a10", widget_ids=["w_spc_bar"], protected=True)
        sc_prf = ScreenNode(id="sc_prf", name="Performance Dashboard", background="#060a10", widget_ids=["w_cpu_ring", "w_mem_ring"], protected=True)
        sc_zen = ScreenNode(id="sc_zen", name="Zen Weather Time", background="#060a10", widget_ids=["w_clk"], protected=True)
        
        self.screens = {s.id: s for s in [sc_sys, sc_net, sc_clk, sc_sto, sc_prf, sc_zen]}

        # 4. Theme
        th_agni = ThemeNode(id="th_agni", name="Agni Dark Modules", orientation="portrait", refresh="update", rotation_interval=60000, screen_ids=["sc_sys", "sc_net", "sc_clk", "sc_sto", "sc_prf", "sc_zen"], protected=True)
        self.themes = {"th_agni": th_agni}
        self.active_theme_id = "th_agni"

    def save(self):
        data = {
            "sensors": {k: v.model_dump() for k, v in self.sensors.items()},
            "widgets": {k: v.model_dump() for k, v in self.widgets.items()},
            "screens": {k: v.model_dump() for k, v in self.screens.items()},
            "themes": {k: v.model_dump() for k, v in self.themes.items()},
            "active_theme_id": self.active_theme_id
        }
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=4)
            
    # CRUD - Sensors
    def add_sensor(self, s: SensorNode) -> SensorNode:
        if not s.id: s.id = self.generate_id()
        self.sensors[s.id] = s
        self.save()
        return s
        
    def delete_sensor(self, s_id: str):
        if s_id in self.sensors:
            del self.sensors[s_id]
            for w in self.widgets.values():
                if w.sensor_id == s_id:
                    w.sensor_id = None
            self.save()

    # CRUD - Widgets
    def add_widget(self, w: WidgetNode) -> WidgetNode:
        if not w.id: w.id = self.generate_id()
        self.widgets[w.id] = w
        self.save()
        return w

    def delete_widget(self, w_id: str):
        if w_id in self.widgets:
            del self.widgets[w_id]
            for s in self.screens.values():
                if w_id in s.widget_ids:
                    s.widget_ids.remove(w_id)
            self.save()

    # CRUD - Screens
    def add_screen(self, s: ScreenNode) -> ScreenNode:
        if not s.id: s.id = self.generate_id()
        self.screens[s.id] = s
        self.save()
        return s
        
    def delete_screen(self, s_id: str):
        if s_id in self.screens:
            del self.screens[s_id]
            for t in self.themes.values():
                if s_id in t.screen_ids:
                    t.screen_ids.remove(s_id)
            self.save()

    # CRUD - Themes
    def add_theme(self, t: ThemeNode) -> ThemeNode:
        if not t.id: t.id = self.generate_id()
        self.themes[t.id] = t
        self.save()
        return t
        
    def delete_theme(self, t_id: str):
        if t_id in self.themes:
            del self.themes[t_id]
            if self.active_theme_id == t_id:
                self.active_theme_id = None
            self.save()
