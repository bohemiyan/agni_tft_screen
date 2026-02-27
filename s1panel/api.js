"use strict";

const node_canvas = require("@napi-rs/canvas");
const { loadImage, createCanvas } = node_canvas;
const logger = require("./logger");
const fs = require("fs");
const path = require("path");
const multer = require("multer");
const upload = multer();
const screens_mgr = require("./screens_manager");

const service = process.env.SERVICE || false;
const home_dir = process.env.S1PANEL_CONFIG || __dirname;

const set_dirty = (context, redraw) => {
  const _state = context.state;

  if (redraw) {
    _state.force_redraw(_state);
  }

  _state.screen_paused = true;
  _state.unsaved_changes = true;
};

const find_theme_screen = (context, id) => {
  const _theme = context.theme;

  return _theme.screens.find((screen) => screen.id === id);
};

const find_screen_widget = (screen, id) => {
  if (screen) {
    return screen.widgets.find((widget) => widget.id === id);
  }
};

const find_widget = (context, screen, widget) => {
  return find_screen_widget(find_theme_screen(context, screen), widget);
};

const get_theme_dir = (context) => {
  const _config = context.config;

  return path.join(home_dir, path.dirname(_config.theme));
};

const get_theme_file_path = (context, file) => {
  return path.join(get_theme_dir(context), file);
};

const get_widget_list = async (context) => {
  const _state = context.state;
  const _list = [];

  Object.getOwnPropertyNames(_state.widgets).forEach((each) => {
    const _widget = _state.widgets[each];
    const _info = _widget.info();

    // standard required fields are added here...
    _info.fields = [].concat(
      [
        { name: "name", value: "string" },
        { name: "rect", value: "rect" },
        { name: "sensor", value: "reserved" },
        { name: "value", value: "image" === _info.name ? "image" : "string" },
        { name: "format", value: "string" },
        { name: "refresh", value: "clock" },
        { name: "debug_frame", value: "reserved" },
      ],
      _info.fields,
    );

    _list.push(_info);
  });

  return _list;
};

const get_config = async (context) => {
  const _state = context.state;

  return { ...context.config, unsaved_changes: _state.unsaved_changes };
};

const get_lcd_screen = async (context) => {
  const _state = context.state;

  return _state.output_canvas.toBuffer("image/png", {
    compressionLevel: 3,
    filters: node_canvas.PNG_FILTER_NONE,
  });
};

const get_sensor_list = async (context) => {
  const _state = context.state;
  const _list = [];

  Object.getOwnPropertyNames(_state.sensors).forEach((each) => {
    _list.push({ name: each, value: each });
  });

  return _list;
};

const get_theme = async (context) => {
  return JSON.parse(
    JSON.stringify(
      context.theme,
      (key, value) => ("_private" === key ? undefined : value),
      3,
    ),
  );
};

const get_active_screen = async (context) => {
  const _theme = context.theme;
  const _state = context.state;
  const _screen = _theme.screens[_state.screen_index];

  return { id: _screen.id };
};

const toggle_debug_rect = async (context, request) => {
  const _widget = find_widget(context, request.screen, request.widget);

  if (_widget) {
    _widget.debug_frame = !_widget.debug_frame;

    set_dirty(context, true);

    return { value: _widget.debug_frame };
  }

  throw new Error("Widget not found");
};

const adjust_rect = async (context, request) => {
  const _widget = find_widget(context, request.screen, request.widget);

  if (_widget) {
    _widget.rect.x = request.rect.x;
    _widget.rect.y = request.rect.y;
    _widget.rect.width = request.rect.width;
    _widget.rect.height = request.rect.height;

    set_dirty(context, true);

    return;
  }

  throw new Error("Widget not found");
};

const update_property = async (context, request) => {
  const _widget = find_widget(context, request.screen, request.widget);

  if (_widget) {
    const _value = (_widget[request.key] = request.value);

    if ("value" === request.key && _value.sensor) {
      _widget.sensor = false;
    }

    set_dirty(context);

    return { value: _value };
  }

  throw new Error("Widget not found");
};

const set_sensor = async (context, request) => {
  const _widget = find_widget(context, request.screen, request.widget);

  if (_widget) {
    _widget.value = request.sensor;
    _widget.sensor = true;

    set_dirty(context);

    return { value: _widget.value };
  }

  throw new Error("Widget not found");
};

const set_background = async (context, request) => {
  const _screen = find_theme_screen(context, request.screen);

  if (_screen) {
    _screen.background = request.value;

    set_dirty(context, true);

    return { value: _screen.background };
  }

  throw new Error("Screen not found");
};

const set_led_settings = (led_config, request) => {
  var _changed = false;

  if (request) {
    if (request.theme !== led_config.theme) {
      led_config.theme = request.theme;
      _changed = true;
    }

    if (request.intensity !== led_config.intensity) {
      led_config.intensity = request.intensity;
      _changed = true;
    }

    if (request.speed !== led_config.speed) {
      led_config.speed = request.speed;
      _changed = true;
    }
  }

  return _changed;
};

const set_led_strip = async (context, request) => {
  const _state = context.state;
  const _config = context.config;
  const _led_config = _config.led_config;

  if (request.screen) {
    const _screen = find_theme_screen(context, request.screen);

    if (_screen) {
      if (!_screen.led_config) {
        _screen.led_config = {};
      }

      set_led_settings(_screen.led_config, request);
      set_dirty(context);
    }
  }

  set_led_settings(_led_config, request);

  _state.update_led = true;

  try {
    const buffer = await read_file(_state.config_file);
    const _file_config = JSON.parse(buffer);

    _file_config.led_config = _led_config;

    await write_file(_state.config_file, JSON.stringify(_file_config, null, 3));
    logger.info("api set_led_strip: config.json updated");

    return {
      theme: _led_config.theme,
      intensity: _led_config.intensity,
      speed: _led_config.speed,
      dirty: true,
    };
  } catch (error) {
    throw error;
  }
};

const get_led_strip = async (context) => {
  const _config = context.config;
  const _led_config = _config.led_config;

  return {
    theme: _led_config.theme,
    intensity: _led_config.intensity,
    speed: _led_config.speed,
  };
};

const set_orientation = async (context, request) => {
  const _theme = context.theme;
  const _state = context.state;

  if (request.orientation !== _theme.orientation) {
    switch (request.orientation) {
      case "portrait":
        _theme.orientation = "portrait";
        break;

      case "landscape":
        _theme.orientation = "landscape";
        break;
    }

    _state.update_orientation = true;

    set_dirty(context, true);
  }

  return { orientation: _theme.orientation };
};

const set_refresh = async (context, request) => {
  const _theme = context.theme;
  const _config = context.config;

  if (request.refresh !== _theme.refresh) {
    switch (request.refresh) {
      case "redraw":
        _config.refresh_method = _theme.refresh = "redraw";
        break;

      case "update":
        _config.refresh_method = _theme.refresh = "update";
        break;
    }

    set_dirty(context);
  }

  return { refresh: _theme.refresh };
};

const set_screen_name = async (context, request) => {
  const _screen = find_theme_screen(context, request.screen);

  if (_screen) {
    _screen.name = request.name;

    set_dirty(context);

    return { name: _screen.name };
  }

  throw new Error("Screen not found");
};

const set_screen_duration = async (context, request) => {
  const _screen = find_theme_screen(context, request.screen);

  if (_screen) {
    _screen.duration = request.duration;

    set_dirty(context);

    return { duration: _screen.duration };
  }

  throw new Error("Screen not found");
};

const get_last_screen_id = (screens) => {
  var _id = 0;

  screens.forEach((each) => {
    _id = Math.max(_id, each.id);
  });

  return _id;
};

const add_screen = async (context, request) => {
  const _theme = context.theme;

  const _screen = {
    id: 1 + get_last_screen_id(_theme.screens),
    name: request.name,
    background: "#000000",
    duartion: 0,
    widgets: [],
  };

  _theme.screens.push(_screen);

  set_dirty(context);

  return _screen;
};

const remove_screen = async (context, request) => {
  const _state = context.state;
  const _theme = context.theme;

  const _current_screen = _theme.screens[_state.screen_index];

  _theme.screens = _theme.screens.filter((each) => each.id !== request.id);

  // adjust screen_index to new array
  for (var i = 0; i < _theme.screens.length; i++) {
    const _screen = _theme.screens[i];

    if (_screen.id === _current_screen.id) {
      _state.change_screen = _state.screen_index = i;
      break;
    }
  }

  set_dirty(context);
};

const get_config_dirty = async (context) => {
  const _state = context.state;

  return { unsaved_changes: _state.unsaved_changes || false };
};

const next_screen = async (context, request) => {
  const _state = context.state;
  const _theme = context.theme;
  const _count = _theme.screens.length;

  // calculate the "next" screen
  var _next_screen_index = _state.screen_index + 1;
  if (_next_screen_index >= _count) {
    _next_screen_index = 0;
  }

  var _id = 0;

  for (var i = 0; i < _theme.screens.length; i++) {
    var _screen = _theme.screens[i];

    if (request.id) {
      // if id was passed, use that
      if (_screen.id === request.id) {
        _id = _screen.id;
        _next_screen_index = i;
        break;
      }
    } else if (i === _next_screen_index) {
      // pick based on next screen
      _id = _screen.id;
      break;
    }
  }

  _state.change_screen = _next_screen_index;

  return { id: _id };
};

const get_random_color = () => {
  const r = Math.floor(Math.random() * 256);
  const g = Math.floor(Math.random() * 256);
  const b = Math.floor(Math.random() * 256);

  const _hex_r = r.toString(16).padStart(2, "0");
  const _hex_g = g.toString(16).padStart(2, "0");
  const _hex_b = b.toString(16).padStart(2, "0");

  return "#" + _hex_r + _hex_g + _hex_b;
};

const get_last_widget_id = (widgets) => {
  var _id = 0;

  widgets.forEach((widget) => {
    _id = Math.max(_id, widget.id);
  });

  return _id;
};

const make_blank_widget = (id, info) => {
  const _obj = {
    id: id,
    group: 1,
    name: info.name,
    rect: { x: 10, y: 10, width: 50, height: 50 },
    sensor: false,
    value: "",
    format: "",
    refresh: 1000,
    debug_frame: true,
  };

  info.fields.forEach((field) => {
    switch (field.value) {
      case "color":
        _obj[field.name] = get_random_color();
        break;

      case "reserved":
      case "boolean":
        _obj[field.name] = false;
        break;

      case "clock":
      case "number":
        _obj[field.name] = 0;
        break;

      case "font":
        _obj[field.name] = "18px Arial";
        break;

      default:
        {
          const _syntax = field.value.split(":");

          if (_syntax.length > 1) {
            if ("list" === _syntax[0]) {
              _obj[field.name] = _syntax[1].split(",")[0];
            }
          } else {
            _obj[field.name] = "";
          }
        }
        break;
    }
  });

  return _obj;
};

const add_widget = async (context, request) => {
  const _state = context.state;

  const _screen = find_theme_screen(context, request.screen);

  if (_screen) {
    const _name = Object.getOwnPropertyNames(_state.widgets).find(
      (name) => name === request.name,
    );

    if (_name) {
      const _widget = _state.widgets[_name];
      const _new_widget = make_blank_widget(
        1 + get_last_widget_id(_screen.widgets),
        _widget.info(),
      );

      _screen.widgets.push(_new_widget);

      set_dirty(context, true);

      return _new_widget;
    }
  }

  throw new Error("Screen or widget type not found");
};

const delete_widget = async (context, request) => {
  const _screen = find_theme_screen(context, request.screen);

  if (_screen) {
    _screen.widgets = _screen.widgets.filter(
      (widget) => widget.id !== request.widget,
    );

    set_dirty(context, true);

    return;
  }

  throw new Error("Screen not found");
};

const read_png = async (file_path) => {
  try {
    const data = await fs.promises.readFile(file_path);
    return data;
  } catch (error) {
    throw error;
  }
};

const get_wallpaper = async (context, request) => {
  const _screen = find_theme_screen(context, Number(request.screen));

  if (_screen) {
    try {
      const data = await read_png(_screen.wallpaper);
      return data;
    } catch (error) {
      throw error;
    }
  }

  throw new Error("Screen not found");
};

const get_image = async (context, request) => {
  const _widget = find_widget(
    context,
    Number(request.screen),
    Number(request.widget),
  );

  if (_widget) {
    try {
      const data = await read_png(_widget.value);
      return data;
    } catch (error) {
      throw error;
    }
  }

  throw new Error("Widget not found");
};

const clear_wallpaper = async (context, request) => {
  const _screen = find_theme_screen(context, Number(request.screen));

  if (_screen) {
    delete _screen.wallpaper;

    set_dirty(context, true);

    return;
  }

  throw new Error("Screen not found");
};

const clear_image = async (context, request) => {
  const _widget = find_widget(
    context,
    Number(request.screen),
    Number(request.widget),
  );

  if (_widget) {
    _widget.value = null;

    set_dirty(context, true);

    return;
  }

  throw new Error("Widget not found");
};

const write_file = async (file_path, buffer) => {
  try {
    await fs.promises.writeFile(file_path, buffer);
  } catch (err) {
    logger.error(
      "api write_file: error saving file " + file_path + " to disk " + err,
    );
    throw err;
  }
};

const read_file = async (file_path) => {
  try {
    const buffer = await fs.promises.readFile(file_path);
    return buffer;
  } catch (err) {
    logger.error(
      "api read_file: error reading file " + file_path + " from disk " + err,
    );
    throw err;
  }
};

const save_config = async (context, request) => {
  const _state = context.state;

  try {
    const buffer = await read_file(_state.config_file);
    const _file_config = JSON.parse(buffer);
    const _live_config = context.config;

    var _changed = false;
    var _restart = false;

    if (
      request.listen &&
      0 !== _live_config.listen.localeCompare(request.listen)
    ) {
      _live_config.listen = _file_config.listen = request.listen;
      _changed = true;
      _restart = true;
    }

    if (request.poll && _live_config.poll !== request.poll) {
      _live_config.poll = _file_config.poll = request.poll;
      _changed = true;
    }

    if (request.refresh && _live_config.refresh !== request.refresh) {
      _live_config.refresh = _file_config.refresh = request.refresh;
      _changed = true;
    }

    if (request.heartbeat && _live_config.heartbeat !== request.heartbeat) {
      _live_config.heartbeat = _file_config.heartbeat = request.heartbeat;
      _changed = true;
    }

    if (_changed) {
      await write_file(
        _state.config_file,
        JSON.stringify(
          _live_config,
          (key, value) => ("_private" === key ? undefined : value),
          3,
        ),
      );
      logger.info("api: config.json updated");

      if (service && _restart) {
        process.exit(1);
      }

      return _live_config;
    }

    return _live_config;
  } catch (error) {
    throw error;
  }
};

const theme_save = async (context) => {
  const _state = context.state;
  const _config = context.config;
  const _theme = context.theme;

  try {
    await write_file(
      path.join(home_dir, _config.theme),
      JSON.stringify(
        _theme,
        (key, value) => ("_private" === key ? undefined : value),
        3,
      ),
    );
    logger.info("api: theme " + _config.theme + " saved");

    _state.screen_paused = false;
    _state.unsaved_changes = false;

    return _theme;
  } catch (error) {
    throw error;
  }
};

const theme_revert = async (context) => {
  const _state = context.state;
  const _config = context.config;

  try {
    const buffer = await read_file(path.join(home_dir, _config.theme));
    const _theme = JSON.parse(buffer);
    const _screen = _theme.screens[0];

    _screen.widgets.sort((a, b) => a.id - b.id);

    _state.update_orientation = true;
    _state.redraw_want++;
    _state.screen_index = _state.change_screen = 0;

    if (_screen.led_config) {
      _config.led_config.theme = _screen.led_config.theme || 4;
      _config.led_config.intensity = _screen.led_config.intensity || 3;
      _config.led_config.speed = _screen.led_config.speed || 3;
      _state.update_led = true;
    }

    context.theme.orientation = _theme.orientation;
    context.theme.refresh = _theme.refresh;
    context.theme.screens = _theme.screens;

    _state.force_redraw(_state);
    _state.unsaved_changes = false;

    logger.info("api: theme reverted back from " + _config.theme);

    return _theme;
  } catch (error) {
    throw error;
  }
};

const up_widget = async (context, request) => {
  const _screen = find_theme_screen(context, request.screen);

  if (_screen) {
    var _previous = null;

    _screen.widgets.find((widget) => {
      if (_previous && widget.id === request.widget) {
        widget.id = [_previous.id, (_previous.id = widget.id)][0];
        return true;
      }

      _previous = widget;
    });

    _screen.widgets.sort((a, b) => a.id - b.id);

    set_dirty(context, true);

    return;
  }
  throw new Error("Screen not found");
};

const down_widget = async (context, request) => {
  const _screen = find_theme_screen(context, request.screen);

  if (_screen) {
    var _previous = null;

    _screen.widgets.find((widget) => {
      if (_previous && _previous.id === request.widget) {
        widget.id = [_previous.id, (_previous.id = widget.id)][0];
        return true;
      }

      _previous = widget;
    });

    _screen.widgets.sort((a, b) => a.id - b.id);

    set_dirty(context, true);

    return;
  }
  throw new Error("Screen not found");
};

const top_widget = async (context, request) => {
  const _screen = find_theme_screen(context, request.screen);

  if (_screen) {
    var _count = 2;

    _screen.widgets.forEach((widget) => {
      widget.id = widget.id === request.widget ? 1 : _count++;
    });

    _screen.widgets.sort((a, b) => a.id - b.id);

    set_dirty(context, true);

    return;
  }

  throw new Error("Screen not found");
};

const bottom_widget = async (context, request) => {
  const _screen = find_theme_screen(context, request.screen);

  if (_screen) {
    var _count = 1;

    _screen.widgets.forEach((widget) => {
      widget.id =
        widget.id === request.widget ? _screen.widgets.length : _count++;
    });

    _screen.widgets.sort((a, b) => a.id - b.id);

    set_dirty(context, true);

    return;
  }

  throw new Error("Screen not found");
};

const upload_image = async (context, req, res) => {
  try {
    const _request = req.query;
    const _file = req.files[0];

    const _widget = find_widget(
      context,
      Number(_request.screen),
      Number(_request.widget),
    );

    if (_widget) {
      const _file_path = get_theme_file_path(context, _file.originalname);

      await write_file(_file_path, _file.buffer);

      _widget.value = _file_path;

      set_dirty(context, true);

      return res
        .type("application/json")
        .status(201)
        .send({ value: _file_path, widget: _widget.id });
    }

    return res.status(404).end();
  } catch (error) {
    logger.error("api: upload_image error " + error);
    res.status(500).end();
  }
};

const upload_wallpaper = async (context, req, res) => {
  try {
    const _state = context.state;

    const _request = req.query;
    const _file = req.files[0];

    const _screen = find_theme_screen(context, Number(_request.screen));

    if (_screen) {
      const _file_path = get_theme_file_path(context, _file.originalname);

      await write_file(_file_path, _file.buffer);

      const image = await node_canvas.loadImage(_file_path);

      _screen.wallpaper = _file_path;
      _state.wallpaper_image = image;

      set_dirty(context, true);

      return res
        .type("application/json")
        .status(201)
        .send({ value: _file_path });
    }

    return res.status(404).end();
  } catch (error) {
    logger.error("api: upload_wallpaper error " + error);
    res.status(500).end();
  }
};

const config_sensor_list = async (context) => {
  const _state = context.state;
  const _list = [];

  Object.getOwnPropertyNames(_state.sensors).forEach((each) => {
    const _info = _state.sensors[each].info || {};
    const _config = JSON.parse(
      JSON.stringify(
        _state.sensors[each].config || {},
        (key, value) => ("_private" === key ? undefined : value),
        3,
      ),
    );

    _list.push({ name: each, info: _info, config: _config });
  });

  return _list;
};

const config_sensor_scan = async () => {
  const _sensor_dir = path.join(__dirname, "sensors");

  try {
    const files = await fs.promises.readdir(_sensor_dir);
    var _list = [];

    files
      .filter((file) => file.endsWith(".js") && !file.includes("thread"))
      .forEach((file) => {
        const _sensor_path = path.join(_sensor_dir, file);

        const _module = require(_sensor_path);

        _list.push({ ..._module.settings(), module: "sensors/" + file });
      });

    return _list;
  } catch (err) {
    logger.error(
      "api: config_sensor_scan open " + _sensor_dir + " err: " + err,
    );
    return [];
  }
};

const config_sensor_add = async (context, request) => {
  const _state = context.state;

  const _sensor = request.module;
  const _config = request.config;
  const _config_copy = { ...request.config };

  const _sensor_path = path.join(__dirname, _sensor);

  const _module = require(_sensor_path);
  const _name = _module.init(_config);

  logger.info("api: config_sensor_add " + _name + " loaded...");

  // check for duplicates first...
  if (
    Object.getOwnPropertyNames(_state.sensors).find(
      (each) => _name.toLowerCase() === each.toLowerCase(),
    )
  ) {
    logger.info("api: config_sensor_add " + _name + " is duplicate...");

    await _module.stop(_config);
    return {
      status: "duplicate",
      error: '"' + _name + '" sensor already exists',
    };
  }

  try {
    const buffer = await read_file(_state.config_file);
    const _file_config = JSON.parse(buffer);
    const _live_config = context.config;

    const _new_sensor = {
      module: _sensor,
      config: _config_copy,
    };

    _file_config.sensors.push(_new_sensor);
    _live_config.sensors.push(_new_sensor);

    await write_file(_state.config_file, JSON.stringify(_file_config, null, 3));
    logger.info("api config_sensor_add: config.json updated");

    _state.sensors[_name] = {
      config: _config,
      name: _name,
      info: { ..._module.settings(), module: _sensor },
      sample: (rate, format) => {
        return _module.sample(rate, format, _config);
      },
      stop: () => {
        return _module.stop(_config);
      },
    };

    return { status: "success", name: _name };
  } catch (error) {
    throw error;
  }
};

function config_match(a, b) {
  return (
    Object.keys(a).every((key) => a[key] === b[key]) &&
    Object.keys(b).every((key) => a[key] === b[key])
  );
}

const config_sensor_remove = async (context, request) => {
  const _state = context.state;
  const _name = request?.name;
  const _module = request?.module;

  if (!_name || !_module) {
    return { status: "invalid parameter" };
  }

  if (
    !Object.getOwnPropertyNames(_state.sensors).find(
      (each) => _name.toLowerCase() === each.toLowerCase(),
    )
  ) {
    return { status: "not found" };
  }

  const _config = JSON.parse(
    JSON.stringify(
      _state.sensors[_name].config || {},
      (key, value) => ("_private" === key ? undefined : value),
      3,
    ),
  );

  try {
    const buffer = await read_file(_state.config_file);
    const _file_config = JSON.parse(buffer);
    const _live_config = context.config;

    _file_config.sensors = _file_config.sensors.filter((each) => {
      return each.module !== _module || !config_match(each.config, _config);
    });

    _live_config.sensors = _file_config.sensors.filter((each) => {
      return each.module !== _module || !config_match(each.config, _config);
    });

    await write_file(_state.config_file, JSON.stringify(_file_config, null, 3));
    logger.info("api config_sensor_remove: config.json updated");

    await _state.sensors[_name].stop();
    delete _state.sensors[_name];
    return { status: "success" };
  } catch (error) {
    throw error;
  }
};

const config_sensor_edit = async (context, request) => {
  const _state = context.state;
  const _name = request?.name;
  const _module = request?.module;
  const _config = request?.config;

  if (!_name || !_module || !_config) {
    return { status: "invalid parameter" };
  }

  if (
    !Object.getOwnPropertyNames(_state.sensors).find(
      (each) => _name.toLowerCase() === each.toLowerCase(),
    )
  ) {
    return { status: "not found" };
  }

  // remove...
  await config_sensor_remove(context, request);

  // add...
  const result2 = await config_sensor_add(context, request);

  return result2;
};

const callback_wrapper = async (
  method,
  url,
  req,
  res,
  callback,
  type,
  context,
) => {
  const _request = method === "get" ? req.query : req.body;

  try {
    const respone = await callback(context, _request);
    res
      .type(type)
      .status(200)
      .send(respone || {});
  } catch (err) {
    logger.error("api: request " + url + " error " + err);
    res.status(500).end();
  }
};

module.exports.init = (web, context) => {
  [
    {
      method: "get",
      url: "/api/config",
      type: "application/json",
      callback: get_config,
    },
    {
      method: "get",
      url: "/api/theme",
      type: "application/json",
      callback: get_theme,
    },
    {
      method: "get",
      url: "/api/screen",
      type: "application/json",
      callback: get_active_screen,
    },
    {
      method: "get",
      url: "/api/lcd_screen",
      type: "image/png",
      callback: get_lcd_screen,
    },
    {
      method: "get",
      url: "/api/image",
      type: "image/png",
      callback: get_image,
    },
    {
      method: "get",
      url: "/api/wallpaper",
      type: "image/png",
      callback: get_wallpaper,
    },
    {
      method: "get",
      url: "/api/widget_list",
      type: "application/json",
      callback: get_widget_list,
    },
    {
      method: "get",
      url: "/api/sensor_list",
      type: "application/json",
      callback: get_sensor_list,
    },
    {
      method: "get",
      url: "/api/config_dirty",
      type: "application/json",
      callback: get_config_dirty,
    },
    {
      method: "post",
      url: "/api/toggle_debug_frame",
      type: "application/json",
      callback: toggle_debug_rect,
    },
    {
      method: "post",
      url: "/api/adjust_rect",
      type: "application/json",
      callback: adjust_rect,
    },
    {
      method: "post",
      url: "/api/update_property",
      type: "application/json",
      callback: update_property,
    },
    {
      method: "post",
      url: "/api/set_background",
      type: "application/json",
      callback: set_background,
    },
    {
      method: "post",
      url: "/api/led_strip",
      type: "application/json",
      callback: set_led_strip,
    },
    {
      method: "get",
      url: "/api/led_strip",
      type: "application/json",
      callback: get_led_strip,
    },
    {
      method: "post",
      url: "/api/set_orientation",
      type: "application/json",
      callback: set_orientation,
    },
    {
      method: "post",
      url: "/api/set_refresh",
      type: "application/json",
      callback: set_refresh,
    },
    {
      method: "post",
      url: "/api/set_screen_name",
      type: "application/json",
      callback: set_screen_name,
    },
    {
      method: "post",
      url: "/api/set_screen_duration",
      type: "application/json",
      callback: set_screen_duration,
    },
    {
      method: "post",
      url: "/api/add_screen",
      type: "application/json",
      callback: add_screen,
    },
    {
      method: "post",
      url: "/api/remove_screen",
      type: "application/json",
      callback: remove_screen,
    },
    {
      method: "post",
      url: "/api/next_screen",
      type: "application/json",
      callback: next_screen,
    },
    {
      method: "post",
      url: "/api/add_widget",
      type: "application/json",
      callback: add_widget,
    },
    {
      method: "post",
      url: "/api/set_sensor",
      type: "application/json",
      callback: set_sensor,
    },
    {
      method: "post",
      url: "/api/delete_widget",
      type: "application/json",
      callback: delete_widget,
    },
    {
      method: "post",
      url: "/api/clear_wallpaper",
      type: "application/json",
      callback: clear_wallpaper,
    },
    {
      method: "post",
      url: "/api/clear_image",
      type: "application/json",
      callback: clear_image,
    },
    {
      method: "post",
      url: "/api/save_config",
      type: "application/json",
      callback: save_config,
    },
    {
      method: "post",
      url: "/api/theme_save",
      type: "application/json",
      callback: theme_save,
    },
    {
      method: "post",
      url: "/api/theme_revert",
      type: "application/json",
      callback: theme_revert,
    },
    {
      method: "post",
      url: "/api/up_widget",
      type: "application/json",
      callback: up_widget,
    },
    {
      method: "post",
      url: "/api/down_widget",
      type: "application/json",
      callback: down_widget,
    },
    {
      method: "post",
      url: "/api/top_widget",
      type: "application/json",
      callback: top_widget,
    },
    {
      method: "post",
      url: "/api/bottom_widget",
      type: "application/json",
      callback: bottom_widget,
    },
    {
      method: "get",
      url: "/api/config_sensor_list",
      type: "application/json",
      callback: config_sensor_list,
    },
    {
      method: "get",
      url: "/api/config_sensor_scan",
      type: "application/json",
      callback: config_sensor_scan,
    },
    {
      method: "post",
      url: "/api/config_sensor_add",
      type: "application/json",
      callback: config_sensor_add,
    },
    {
      method: "post",
      url: "/api/config_sensor_remove",
      type: "application/json",
      callback: config_sensor_remove,
    },
    {
      method: "post",
      url: "/api/config_sensor_edit",
      type: "application/json",
      callback: config_sensor_edit,
    },
  ].forEach((each) => {
    switch (each.method) {
      case "get":
        web.get(
          each.url,
          async (req, res) =>
            await callback_wrapper(
              each.method,
              each.url,
              req,
              res,
              each.callback,
              each.type,
              context,
            ),
        );
        break;

      case "post":
        web.post(
          each.url,
          async (req, res) =>
            await callback_wrapper(
              each.method,
              each.url,
              req,
              res,
              each.callback,
              each.type,
              context,
            ),
        );
        break;
    }
  });

  web.post(
    "/api/upload_image",
    upload.any(),
    async (req, res) => await upload_image(context, req, res),
  );
  web.post(
    "/api/upload_wallpaper",
    upload.any(),
    async (req, res) => await upload_wallpaper(context, req, res),
  );

  // ── Screen Management ────────────────────────────────────────────

  // List all screens (system + user)
  web.get("/api/screens", async (req, res) => {
    try {
      const list = await screens_mgr.list_screens();
      res.json(list);
    } catch (err) {
      res.status(500).json({ error: String(err) });
    }
  });

  // Get one screen
  web.get("/api/screens/:id", async (req, res) => {
    try {
      const data = await screens_mgr.load_screen(req.params.id);
      res.json(data);
    } catch (err) {
      res.status(404).json({ error: "Screen not found" });
    }
  });

  // Create a new user screen
  web.post("/api/screens", async (req, res) => {
    const _data = req.body || {};
    if (!_data.name) return res.status(400).json({ error: "name is required" });
    _data.widgets = _data.widgets || [];
    _data.background = _data.background || "#060a10";
    try {
      const id = await screens_mgr.create_screen(_data);
      res.json({ id });
    } catch (err) {
      res.status(err.code || 500).json({ error: err.message || String(err) });
    }
  });

  // Update a user screen (blocks system screens)
  web.put("/api/screens/:id", async (req, res) => {
    try {
      await screens_mgr.save_screen(req.params.id, req.body);
      res.json({ ok: true });
    } catch (err) {
      res.status(err.code || 500).json({ error: err.message || String(err) });
    }
  });

  // Delete a user screen (blocks system screens)
  web.delete("/api/screens/:id", async (req, res) => {
    try {
      await screens_mgr.delete_screen(req.params.id);
      res.json({ ok: true });
    } catch (err) {
      res.status(err.code || 500).json({ error: err.message || String(err) });
    }
  });

  // Update the active theme's screen rotation config
  web.put("/api/theme/screens", async (req, res) => {
    const { active_screens, rotate, rotation_interval } = req.body;
    const _theme = context.theme;
    const _state = context.state;

    if (!Array.isArray(active_screens)) {
      return res.status(400).json({ error: "active_screens must be an array" });
    }

    // Force system_status to always be first
    const _ids = [
      "system_status",
      ...active_screens.filter((id) => id !== "system_status"),
    ];

    _theme.active_screens = _ids;
    _theme.rotate = rotate !== false;
    _theme.rotation_interval = Number(rotation_interval) || 60000;

    // Reload resolved screens
    try {
      const screens = await screens_mgr.resolve_theme_screens(_theme);
      _theme.screens = screens;
      _state.force_redraw(_state);
      res.json({ ok: true, active_screens: _ids });
    } catch (err) {
      res.status(500).json({ error: String(err) });
    }
  });
};
