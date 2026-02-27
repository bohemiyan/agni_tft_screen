const set_poll_time = (ms) => {
  _poll_time = ms;
};

const api_fetch_config = async () => {
  const response = await fetch("/api/config");
  return await response.json();
};

const api_fetch_theme = async () => {
  const response = await fetch("/api/theme");
  return await response.json();
};

const api_fetch_screen = async () => {
  const response = await fetch("/api/screen");
  return await response.json();
};

const api_fetch_widgets = async () => {
  const response = await fetch("/api/widget_list");
  return await response.json();
};

const api_fetch_sensors = async () => {
  const response = await fetch("/api/sensor_list");
  return await response.json();
};

const api_load_image = async () => {
  const response = await fetch("/api/lcd_screen?r" + new Date().getTime());
  return await response.json();
};

const api_toggle_debug_frame = async (screen, id) => {
  const response = await fetch("/api/toggle_debug_frame", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ screen: screen, widget: id }),
  });
  return await response.json();
};

const api_adjust_rect = async (screen, id, rect) => {
  const response = await fetch("/api/adjust_rect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ screen: screen, widget: id, rect: rect }),
  });
  return await response.json();
};

const api_update_property = async (screen, id, key, value) => {
  const response = await fetch("/api/update_property", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      screen: screen,
      widget: id,
      key: key,
      value: value,
    }),
  });
  return await response.json();
};

const api_set_background = async (screen, value) => {
  const response = await fetch("/api/set_background", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ screen, value }),
  });
  return await response.json();
};

const api_set_sensor = async (screen, id, value) => {
  const response = await fetch("/api/set_sensor", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ screen: screen, widget: id, sensor: value }),
  });
  return await response.json();
};

const api_set_orientation = async (value) => {
  const response = await fetch("/api/set_orientation", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ orientation: value }),
  });
  return await response.json();
};

const api_set_refresh = async (value) => {
  const response = await fetch("/api/set_refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: value }),
  });
  return await response.json();
};

const api_fetch_config_dirty = async () => {
  const response = await fetch("/api/config_dirty");
  return await response.json();
};

const api_set_screen_name = async (screen, name) => {
  const response = await fetch("/api/set_screen_name", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ screen, name }),
  });
  return await response.json();
};

const api_set_screen_duration = async (screen, duration) => {
  const response = await fetch("/api/set_screen_duration", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ screen, duration }),
  });
  return await response.json();
};

const api_add_screen = async (name) => {
  const response = await fetch("/api/add_screen", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  return await response.json();
};

const api_remove_screen = async (id) => {
  const response = await fetch("/api/remove_screen", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id }),
  });
  return await response.json();
};

const api_next_screen = async (id) => {
  const response = await fetch("/api/next_screen", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id }),
  });
  return await response.json();
};

const api_add_widget = async (screen, name) => {
  const response = await fetch("/api/add_widget", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ screen, name }),
  });
  return await response.json();
};

const api_delete_widget = async (screen, widget) => {
  const response = await fetch("/api/delete_widget", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ screen, widget }),
  });
  return await response.json();
};

const api_clear_wallpaper = async (screen) => {
  const response = await fetch("/api/clear_wallpaper", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ screen }),
  });
  return await response.json();
};

const api_clear_image = async (screen, widget) => {
  const response = await fetch("/api/clear_image", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ screen, widget }),
  });
  return await response.json();
};

const api_save_config = async (config) => {
  const response = await fetch("/api/save_config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  return await response.json();
};

const api_theme_save = async () => {
  const response = await fetch("/api/theme_save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });
  return await response.json();
};

const api_theme_revert = async () => {
  const response = await fetch("/api/theme_revert", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });
  return await response.json();
};

const api_set_led_strip = async (theme, intensity, speed, screen) => {
  const response = await fetch("/api/led_strip", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ theme, intensity, speed, screen }),
  });
  return await response.json();
};

const api_get_led_strip = async () => {
  const response = await fetch("/api/led_strip");
  return await response.json();
};

const api_up_widget = async (screen, widget) => {
  const response = await fetch("/api/up_widget", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ screen, widget }),
  });
  return await response.json();
};

const api_down_widget = async (screen, widget) => {
  const response = await fetch("/api/down_widget", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ screen, widget }),
  });
  return await response.json();
};

const api_top_widget = async (screen, widget) => {
  const response = await fetch("/api/top_widget", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ screen, widget }),
  });
  return await response.json();
};

const api_bottom_widget = async (screen, widget) => {
  const response = await fetch("/api/bottom_widget", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ screen, widget }),
  });
  return await response.json();
};

const api_config_sensor_list = async () => {
  const response = await fetch("/api/config_sensor_list");
  return await response.json();
};

const api_config_sensor_scan = async () => {
  const response = await fetch("/api/config_sensor_scan");
  return await response.json();
};

const api_config_sensor_add = async (module, config) => {
  const response = await fetch("/api/config_sensor_add", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ module, config }),
  });
  return await response.json();
};

const api_config_sensor_remove = async (name, module) => {
  const response = await fetch("/api/config_sensor_remove", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, module }),
  });
  return await response.json();
};

const api_config_sensor_edit = async (name, module, config) => {
  const response = await fetch("/api/config_sensor_edit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, module, config }),
  });
  return await response.json();
};

export default {
  set_poll_time: set_poll_time,
  fetch_config: api_fetch_config,
  fetch_theme: api_fetch_theme,
  fetch_screen: api_fetch_screen,
  fetch_widgets: api_fetch_widgets,
  fetch_sensors: api_fetch_sensors,
  load_image: api_load_image,
  toggle_debug_frame: api_toggle_debug_frame,
  adjust_rect: api_adjust_rect,
  update_property: api_update_property,
  set_background: api_set_background,
  set_sensor: api_set_sensor,
  set_orientation: api_set_orientation,
  set_refresh: api_set_refresh,
  fetch_config_dirty: api_fetch_config_dirty,
  set_screen_name: api_set_screen_name,
  set_screen_duration: api_set_screen_duration,
  add_screen: api_add_screen,
  remove_screen: api_remove_screen,
  next_screen: api_next_screen,
  add_widget: api_add_widget,
  delete_widget: api_delete_widget,
  clear_wallpaper: api_clear_wallpaper,
  clear_image: api_clear_image,
  save_config: api_save_config,
  theme_save: api_theme_save,
  theme_revert: api_theme_revert,
  set_led_strip: api_set_led_strip,
  get_led_strip: api_get_led_strip,
  up_widget: api_up_widget,
  down_widget: api_down_widget,
  top_widget: api_top_widget,
  bottom_widget: api_bottom_widget,
  config_sensor_list: api_config_sensor_list,
  config_sensor_scan: api_config_sensor_scan,
  config_sensor_add: api_config_sensor_add,
  config_sensor_remove: api_config_sensor_remove,
  config_sensor_edit: api_config_sensor_edit,
};
