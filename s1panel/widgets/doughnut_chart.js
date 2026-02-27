'use strict';
/*!
 * s1panel - widget/doughnut_chart (native canvas, zero deps)
 * Copyright (c) 2024-2025 Tomasz Jaworski
 * GPL-3 Licensed
 */

function start_draw(context, rect) {
    context.save();
    context.beginPath();
    context.rect(rect.x, rect.y, rect.width, rect.height);
    context.clip();
}

function debug_rect(context, rect) {
    context.lineWidth = 1;
    context.strokeStyle = 'red';
    context.strokeRect(rect.x, rect.y, rect.width, rect.height);
}

function get_private(config) {
    if (!config._private) config._private = {};
    return config._private;
}

function draw(context, value, min, max, config) {

    return new Promise(fulfill => {

        const _private = get_private(config);
        const _rect    = config.rect;
        const _has_changed = (_private.last_value !== value);

        // Geometry
        const _cx = _rect.x + _rect.width  / 2;
        const _cy = _rect.y + _rect.height / 2;
        const _r  = (Math.min(_rect.width, _rect.height) / 2) - 2;

        // Cutout as fraction (default 80% → 0.80)
        const _cutout_str = String(config.cutout || '80%');
        const _cutout = _cutout_str.endsWith('%')
            ? parseFloat(_cutout_str) / 100
            : parseFloat(_cutout_str);
        const _inner_r = _r * _cutout;

        // Arc sweep: circumference degrees → radians, default 270°
        const _sweep_deg   = config.circumference ?? 270;
        const _sweep_rad   = (_sweep_deg / 360) * Math.PI * 2;

        // Start angle: rotation places the arc start, default 225° → 5π/4
        const _start_deg   = config.rotation ?? 225;
        const _start_rad   = (_start_deg / 180) * Math.PI;

        // Percentage
        const _val = Number(value);
        const _pct = Math.max(0, Math.min(1, (_val - (min ?? 0)) / ((max && max > 0 ? max : 100) - (min ?? 0))));

        const _used_sweep = _sweep_rad * _pct;
        const _free_sweep = _sweep_rad * (1 - _pct);
        const _end_used   = _start_rad + _used_sweep;

        const _used_color = config.used || '#00d4ff';
        const _free_color = config.free || '#0d1e2d';

        const _line_w = _r - _inner_r;

        start_draw(context, _rect);

        // Background (free) arc
        context.beginPath();
        context.arc(_cx, _cy, _r - _line_w / 2, _start_rad, _start_rad + _sweep_rad);
        context.strokeStyle = _free_color;
        context.lineWidth   = _line_w;
        context.lineCap     = 'round';
        context.stroke();

        // Foreground (used) arc with subtle glow
        if (_pct > 0) {
            context.beginPath();
            context.arc(_cx, _cy, _r - _line_w / 2, _start_rad, _end_used);
            context.strokeStyle = _used_color;
            context.lineWidth   = _line_w;
            context.lineCap     = 'round';

            // glow effect
            context.shadowColor   = _used_color;
            context.shadowBlur    = 6;
            context.stroke();
            context.shadowBlur    = 0;
        }

        if (config.debug_frame) debug_rect(context, _rect);
        context.restore();

        if (_has_changed) _private.last_value = value;

        fulfill(_has_changed);
    });
}

function info() {
    return {
        name: 'doughnut_chart',
        description: 'A doughnut/arc gauge (native canvas)',
        fields: [
            { name: 'used',          value: 'color'  },
            { name: 'free',          value: 'color'  },
            { name: 'rotation',      value: 'number' },
            { name: 'cutout',        value: 'string' },
            { name: 'circumference', value: 'number' },
        ]
    };
}

module.exports = { info, draw };
