#!/usr/bin/env node
"use strict";
/*!
 * s1panel - main
 * Copyright (c) 2024-2025 Tomasz Jaworski
 * GPL-3 Licensed
 */
const threads = require("worker_threads");
const fs = require("fs");
const path = require("path");
const http = require("http");

const express = require("express");
const { createCanvas, loadImage, GlobalFonts } = require("@napi-rs/canvas");

const logger = require("./logger");
const api = require("./api");

const home_dir = process.env.S1PANEL_CONFIG || __dirname;
const font_root = path.join("usr", "share", "fonts");
const font_dir = process.env.SNAP
  ? path.join(process.env.SNAP, font_root)
  : path.join("/", font_root);

const get_hr_time = () => Math.floor(Number(process.hrtime.bigint()) / 1000000);

const lcd_redraw = (state, imageData) => {
  state.drawing = true;

  const pixelData = new Uint16Array(imageData.data);

  state.lcd_thread.postMessage({ type: "redraw", pixelData }, [
    pixelData.buffer,
  ]);
};

const lcd_update = (state, rect, imageData) => {
  state.drawing = true;

  const pixelData = new Uint16Array(imageData.data);

  state.lcd_thread.postMessage({ type: "update", rect, pixelData }, [
    pixelData.buffer,
  ]);
};

const lcd_orientation = (state, portrait) => {
  state.lcd_thread.postMessage({ type: "orientation", portrait });
};

const lcd_set_time = (state) => {
  state.lcd_thread.postMessage({ type: "heartbeat" });
};

const lcd_set_config = (state, config) => {
  state.lcd_thread.postMessage({
    type: "config",
    poll: config.poll,
    refresh: config.refresh,
    heartbeat: config.heartbeat,
  });
};

const load_config = async (filename) => {
  try {
    const jsonData = await fs.promises.readFile(filename, "utf8");
    return JSON.parse(jsonData);
  } catch (err) {
    logger.error("load_config: " + err);
    throw err;
  }
};

const translate_rect = (portrait, rect, height) =>
  portrait
    ? {
        x: rect.y,
        y: height - (rect.x + rect.width),
        width: rect.height,
        height: rect.width,
      }
    : rect;

const next_update_region = (context, state, config) => {
  while (state.changes.length) {
    const _change = state.changes.shift();
    const _rect = translate_rect(config.portrait, _change, config.canvas.height);
    const _image = context.getImageData(_rect.x, _rect.y, _rect.width, _rect.height);

    if (config.debug_update) {
      _image.data.fill(Math.floor(Math.random() * 65025) + 1);
    }

    state.change_count--;

    lcd_update(state, _rect, _image);
  }
};

const start_update_screen = async (context, state, config) => {
  const _start = get_hr_time();
  const _count = state.change_count;

  next_update_region(context, state, config);

  state.stat_update = get_hr_time() - _start;
  state.stat_count = _count;

  return _count ? true : false;
};

const clear_pending_screen_updates = (state) => {
  while (state.changes.length) {
    state.changes.shift();
    state.change_count--;
  }
};

const update_device_screen = async (context, state, config, theme) => {
  if (state.update_orientation) {
    config.portrait = theme.orientation === 'portrait';

    state.update_orientation = false;

    lcd_orientation(state, config.portrait);

    return;
  }
  else if (!state.drawing) {
    if ('redraw' === theme.refresh || state.pending_redraw(state)) {
      clear_pending_screen_updates(state);

      lcd_redraw(state, context.getImageData(0, 0, config.canvas.width, config.canvas.height));

      return true;
    }
    else if (state.changes.length) {
      // lcd update methods:
      //
      // redraw   : always redraw the whole screen (slowest)
      // update   : update by the widget rect (fastest)
      //
      // row      : update whole screen by drawing strips down x (landscape going down)
      // column   : update whole screen by drawing strips down y (portrait going down)
      // gridx    : update screen by a grid of 32x10 (only changed parts)
      // gridy    : update screen by a grid of 10x32 (only changed parts)
      //
      switch (theme.refresh) {
        case 'update':
          return await start_update_screen(context, state, config);

        case 'row':
        case 'column':
        case 'gridx':
        case 'gridy':
          break;
      }
    }
  }
};

// keep screen at least for 10 seconds
// prevents from fast screen switching...
const has_screen_expired = (elapsed, duration) => {
  const _min_time_ms = 10 * 1000;

  if (duration > _min_time_ms) {
    return elapsed > duration ? true : false;
  }

  return elapsed > _min_time_ms ? true : false;
};

const fetch_screen = (state, config, theme) => {
  const _count = theme.screens.length;
  const _old_index = state.screen_index;

  let _screen = theme.screens[state.screen_index];

  if (_count > 1) {
    const _now = get_hr_time();
    const _diff = _now - state.screen_start;

    if (state.change_screen !== state.screen_index) {
      // jump to change_screen
      if (state.change_screen < _count) {
        state.screen_index = state.change_screen;
      } else {
        state.change_screen = 0;
      }
    } else if (
      _screen.duration &&
      has_screen_expired(_diff, _screen.duration)
    ) {
      if (!state.screen_paused) {
        // move to next screen, or cycle back
        state.screen_index++;

        if (state.screen_index >= _count) {
          state.screen_index = 0;
        }
      } else {
        state.screen_start = get_hr_time();
      }
    }

    // did we change?
    if (_old_index !== state.screen_index) {
      _screen = theme.screens[state.screen_index];

      // does new screen have a wallpaper?
      if (_screen.wallpaper) {
        state.wallpaper_image = null;
      }

      if (_screen.led_config) {
        config.led_config.theme = _screen.led_config.theme || 4;
        config.led_config.intensity = _screen.led_config.intensity || 3;
        config.led_config.speed = _screen.led_config.speed || 3;
        state.update_led = true;
      }

      // sync up everything, and force full screen redraw
      state.change_screen = state.screen_index;
      state.screen_start = get_hr_time();
      state.force_redraw(state);
    }
  } else {
    state.screen_start = get_hr_time();
  }
  return _screen;
};

const calc_update_region = (rect) => {
  const _max_size = 2048; // 4096 buffer limit
  const _totalPixels = rect.width * rect.height;
  const _chunks = [];

  if (_totalPixels > _max_size) {
    const _rows = Math.ceil(rect.height / Math.sqrt(_max_size));
    const _cols = Math.ceil(rect.width / Math.sqrt(_max_size));
    const _area_width = Math.ceil(rect.width / _cols);
    const _area_height = Math.ceil(rect.height / _rows);

    for (let i = 0; i < _rows; i++) {
      for (let j = 0; j < _cols; j++) {
        const _areaX = rect.x + j * _area_width;
        const _areaY = rect.y + i * _area_height;

        _chunks.push({
          x: _areaX,
          y: _areaY,
          width: Math.min(_area_width, rect.width - j * _area_width),
          height: Math.min(_area_height, rect.height - i * _area_height),
        });
      }
    }
  } else {
    _chunks.push(rect);
  }

  return _chunks;
};

const fix_rect_bounds = (config, rect) => {
  let _width = rect.width;
  let _height = rect.height;

  const _total_width = rect.x + _width;
  const _total_height = rect.y + _height;

  const _max_width = config.portrait
    ? config.canvas.height
    : config.canvas.width;
  const _max_height = config.portrait
    ? config.canvas.width
    : config.canvas.height;

  if (_total_width > _max_width) {
    _width -= _total_width - _max_width;
  }

  if (_total_height > _max_height) {
    _height -= _total_height - _max_height;
  }

  return { x: rect.x, y: rect.y, width: _width, height: _height };
};

const next_draw_widgets = async (context, state, config, widgets) => {

    for (let index = 0; index < widgets.length; index++) {
        const _widget_config = widgets[index];

        let sensor = null;

        if (_widget_config.refresh && _widget_config.sensor) {
            const _sensor = state.sensors[_widget_config.value];
            if (_sensor) {
                sensor = await _sensor.sample(_widget_config.refresh, _widget_config.format);
            }
        }

        const _widget = state.widgets[_widget_config.name];
        const _value = sensor ? sensor.value : _widget_config.value;
        const _min = sensor ? sensor.min : 0;
        const _max = sensor ? sensor.max : 0;

        let changed = false;

        if (_widget) {
            changed = await _widget.draw(context, _value, _min, _max, _widget_config);
        }

        if (!state.drawing && changed) {
            calc_update_region(fix_rect_bounds(config, _widget_config.rect)).forEach(each => {
                state.changes.push(each);
                state.change_count++;
            });
        }
    }
};

const load_wallpaper = async (context, state, config, screen) => {

    if (screen.background) {
        context.fillStyle = screen.background;
        context.rect(0, 0, config.canvas.width, config.canvas.height);
        context.fill();
    }

    if (screen.wallpaper) {
        if (state.wallpaper_image) {
            return state.wallpaper_image;
        }

        const image = await loadImage(screen.wallpaper);
        state.wallpaper_image = image;
        return state.wallpaper_image;
    }

    return null;
};

const draw_screen = async (context, state, config, screen) => {

    context.resetTransform();
    context.rotate(0);
    context.clearRect(0, 0, config.canvas.width, config.canvas.height);

    const image = await load_wallpaper(context, state, config, screen);

    if (image) {
        context.drawImage(image, 0, 0, config.canvas.width, config.canvas.height);
    }

    if (config.portrait) {
        context.translate(0, 170);
        context.rotate(-Math.PI / 2);
    }

    await next_draw_widgets(context, state, config, screen.widgets);
};

const update_led_strip = async (state, config) => {

    if (!state.update_led) {
        return;
    }

    // led strip manipulation is done on a seperate thread...
    state.led_thread.postMessage(config.led_config);
    state.update_led = false;
};

const next_sensor = async (state, widgets) => {

    for (let index = 0; index < widgets.length; index++) {
        const _widget_config = widgets[index];

        if (_widget_config.refresh && _widget_config.sensor) {
            const _sensor = state.sensors[_widget_config.value];
            if (_sensor) {
                await _sensor.sample(_widget_config.refresh, '');
            }
        }
    }
};

/*
 * we need to poll each widget/sensor in all the inactive screens or we
 * going to have missed data points. ie: if cpu_usage is only on screen 1
 * and temp is only on screen 2, if we stay on screen 1 too long screen 2
 * temp sensor will have missed data points. we skip the active screen,
 * since its going to be taken care of by the draw_screen.
 */
const poll_inactive_screen_sensors = async (state, screens, active) => {

    for (let index = 0; index < screens.length; index++) {
        const _screen = screens[index];

        if (_screen.id !== active.id) {
            await next_sensor(state, _screen.widgets);
        }
    }
};

const start_draw_canvas = async (state, config, theme) => {

    const _context = state.canvas_context[state.active_context];
    const _active_screen = fetch_screen(state, config, theme);

    await poll_inactive_screen_sensors(state, theme.screens, _active_screen);

    // pick a screen and draw it
    await draw_screen(_context, state, config, _active_screen);

    // update lcd screen
    const device_updated = await update_device_screen(_context, state, config, theme);

    state.output_context.putImageData(_context.getImageData(0, 0, config.canvas.width, config.canvas.height), 0, 0);

    if (device_updated) {
        state.active_context ^= 1;  // flip buffer to use
    }

    await update_led_strip(state, config);

    setTimeout(() => {
        lcd_set_config(state, config);
        start_draw_canvas(state, config, theme);
    }, config.poll);
};

const initialize = async (state, config, theme) => {

    config.widgets.forEach(widget => {

        const _file = './' + widget;    // relative path to install dir ./widget/xyz.js
        const _module = require(_file);

        if (_module) {

            const _name = _module.info().name;

            logger.info('initialize: widget ' + _name + ' loaded...');

            state.widgets[_name] = { name: _name, info: _module.info, draw: _module.draw };
        }
    });

    config.sensors.forEach(sensor => {

        const _file = './' + sensor.module; // relative path to install dir ./sensors/abc.js
        const _module = require(_file);

        if (_module) {

            const _config = sensor.config || {};
            const _name = _module.init(_config);
            const _info = { ..._module.settings(), module: sensor.module };

            logger.info('initialize: sensor ' + _name + ' loaded...');

            state.sensors[_name] = { config: _config, name: _name, info: _info, sample: (rate, format) => {
                return _module.sample(rate, format, _config);
            }, stop: () => {
                return _module.stop(_config);
            }};
        }
    });

    config.portrait = theme.orientation === 'portrait';

    logger.info('initialize: device orientation is ' + theme.orientation);

    // sort screens by id
    theme.screens.sort((a, b) => a.id - b.id);

    lcd_set_time(state);
};

const init_web_gui = async (state, config, theme) => {

    const _web = express();

    const _listen = config.listen.split(':');
    const _ip = _listen[0];
    const _port = Number(_listen[1]);

    _web.use(express.static(path.join(__dirname, 'gui/dist')));
    _web.use(express.json());

    api.init(_web, { state, config, theme });

    await new Promise(resolve => {
        http.createServer(_web).listen(_port, _ip, () => {
            logger.info('initialize: gui started on ' + _ip + ':' + _port);
            resolve();
        });
    });
};

const lcd_thread_status = (state, theme, message) => {

    if (state.drawing && message.complete) {

        if ('redraw' === message.type) {

            state.done_redraw(state);
        }

        state.drawing = false;
    }
};

const file_exists = async (path) => {
    try {
        await fs.promises.stat(path);
        return path;
    } catch (err) {
        return null;
    }
};

const load_panel_font = async (font) => {

    const _full_path = path.join(font_dir, font.path);
    const found = await file_exists(_full_path);

    if (found) {
        logger.info('initialize: register ' + _full_path + ' as ' + font.face.family);
        GlobalFonts.registerFromPath(_full_path, font.face.family);
    }
    else {
        logger.info('initialize: ' + _full_path + ' not available for ' + font.face.family);
    }
};

const register_fonts = async () => {

    const _fonts = [ 
        // Arial → Liberation Sans
        { path: '/truetype/liberation/LiberationSans-Regular.ttf', face: { family: 'Arial', weight: 'normal', style: 'normal' } },
        { path: '/truetype/liberation/LiberationSans-Bold.ttf', face: { family: 'Arial', weight: 'bold', style: 'normal' } },
        { path: '/truetype/liberation/LiberationSans-Italic.ttf', face: { family: 'Arial', weight: 'normal', style: 'italic' } },
        { path: '/truetype/liberation/LiberationSans-BoldItalic.ttf', face: { family: 'Arial', weight: 'bold', style: 'italic' } },

        // Courier New → Liberation Mono
        { path: '/truetype/liberation/LiberationMono-Regular.ttf', face: { family: 'Courier New', weight: 'normal', style: 'normal' } },
        { path: '/truetype/liberation/LiberationMono-Bold.ttf', face: { family: 'Courier New', weight: 'bold', style: 'normal' } },
        { path: '/truetype/liberation/LiberationMono-Italic.ttf', face: { family: 'Courier New', weight: 'normal', style: 'italic' } },
        { path: '/truetype/liberation/LiberationMono-BoldItalic.ttf', face: { family: 'Courier New', weight: 'bold', style: 'italic' } },

        // Times New Roman → Liberation Serif
        { path: '/truetype/liberation/LiberationSerif-Regular.ttf', face: { family: 'Times New Roman', weight: 'normal', style: 'normal' } },
        { path: '/truetype/liberation/LiberationSerif-Bold.ttf', face: { family: 'Times New Roman', weight: 'bold', style: 'normal' } },
        { path: '/truetype/liberation/LiberationSerif-Italic.ttf', face: { family: 'Times New Roman', weight: 'normal', style: 'italic' } },
        { path: '/truetype/liberation/LiberationSerif-BoldItalic.ttf', face: { family: 'Times New Roman', weight: 'bold', style: 'italic' } },

        // Verdana → DejaVu Sans
        { path: '/truetype/dejavu/DejaVuSans.ttf', face: { family: 'Verdana', weight: 'normal', style: 'normal' } },
        { path: '/truetype/dejavu/DejaVuSans-Bold.ttf', face: { family: 'Verdana', weight: 'bold', style: 'normal' } },

        // Georgia → DejaVu Serif
        { path: '/truetype/dejavu/DejaVuSerif.ttf', face: { family: 'Georgia', weight: 'normal', style: 'normal' } },
        { path: '/truetype/dejavu/DejaVuSerif-Bold.ttf', face: { family: 'Georgia', weight: 'bold', style: 'normal' } },

        // Garamond → EB Garamond
        { path: '/opentype/ebgaramond/EBGaramond12-Regular.otf', face: { family: 'Garamond', weight: 'normal', style: 'normal' } },
        { path: '/opentype/ebgaramond/EBGaramond12-Bold.otf', face: { family: 'Garamond', weight: 'bold', style: 'normal' } },
        { path: '/opentype/ebgaramond/EBGaramond12-Italic.otf', face: { family: 'Garamond', weight: 'normal', style: 'italic' } },

        // Helvetica → FreeSans from GNU FreeFont
        { path: '/truetype/freefont/FreeSans.ttf', face: { family: 'Helvetica', weight: 'normal', style: 'normal' } },
        { path: '/truetype/freefont/FreeSans-Bold.ttf', face: { family: 'Helvetica', weight: 'bold', style: 'normal' } }
    ];

    logger.info('initialize: starting fonts registration from ' + font_dir);
    
    for (const font of _fonts) {
        await load_panel_font(font);            
    }
};

const main = async () => {
    try {
        // additional commandline args
        const _args = process.argv.slice(2);
        const _config_file = (_args.length > 0) ? _args[0] : path.join(home_dir, 'config.json'); // {dir}/config.json

        logger.info('config ' + _config_file);
        
        const config = await load_config(_config_file);
        const _theme_file = path.join(home_dir, config.theme); // {dir}/themes/simple_demo/portrait_simple.json
        
        logger.info('theme ' + _theme_file);

        const theme = await load_config(_theme_file);

        const screens_mgr = require('./screens_manager');

        // Load screen files referenced by active_screens (or fall back to inline screens)
        const resolved_screens = theme.active_screens
            ? await screens_mgr.resolve_theme_screens(theme)
            : (theme.screens || []);

        theme.screens = resolved_screens;

        // Apply rotate/rotation_interval from theme to each screen's duration
        if (theme.rotate && theme.rotation_interval) {
            theme.screens.forEach(s => { s.duration = theme.rotation_interval; });
        } else if (theme.rotate === false) {
            // Only first screen (system_status) cycles — set others to 0
            theme.screens.forEach((s, i) => { s.duration = i === 0 ? 0 : 0; });
        }

        await register_fonts();

        const _output_canvas = createCanvas(config.canvas.width, config.canvas.height);
        const _canvas1 = createCanvas(config.canvas.width, config.canvas.height).getContext('2d');
        const _canvas2 = createCanvas(config.canvas.width, config.canvas.height).getContext('2d');

        const _state = {

            config_file        : _config_file,

            widgets            : {},
            sensors            : {},

            redraw_want        : 1,
            redraw_count       : 0,

            drawing            : false,             // drawing in progress
            changes            : [],                // screen update regions
            change_count       : 0,                 // screen update count

            output_canvas      : _output_canvas,
            output_context     : _output_canvas.getContext('2d', { pixelFormat: config.canvas.pixel }),
            active_context     : 0,
            canvas_context     : [ _canvas1, _canvas2 ],

            change_screen      : 0,                 // index of forced screen change
            screen_paused      : false,             // pause screen change
            screen_index       : 0,                 // array index into screens, not screen id
            screen_start       : get_hr_time(),

            update_orientation : true,
            update_led         : true,

            wallpaper_image    : null,

            led_thread         : new threads.Worker('./led_thread.js', { workerData: config.led_config }),
            lcd_thread         : new threads.Worker('./lcd_thread.js', { workerData: { device: config.device, poll: config.poll, refresh: config.refresh, heartbeat: config.heartbeat }}),

            unsaved_changes    : false,

            // helpers to keep things consistant between here and api
            pending_redraw     : (state) => state.redraw_count < state.redraw_want,
            force_redraw       : (state) => state.redraw_want++,
            done_redraw        : (state) => state.redraw_count < state.redraw_want ? state.redraw_count++ : state.redraw_count
        };

        await initialize(_state, config, theme);

        const _screen = theme.screens[_state.screen_index];

        _screen.widgets.sort((a, b) => a.id - b.id);

        if (_screen.led_config) {

            config.led_config.theme = _screen.led_config.theme || 4;    // off by default
            config.led_config.intensity = _screen.led_config.intensity || 3;
            config.led_config.speed = _screen.led_config.speed || 3;
        }

        _state.lcd_thread.on('message', message => {

            lcd_thread_status(_state, theme, message);
        });

        await init_web_gui(_state, config, theme);

        start_draw_canvas(_state, config, theme);

    } catch (err) {
        logger.error('Application startup failed: ' + err);
        process.exit(1);
    }
};

logger.info("starting up " + __filename);

main();
