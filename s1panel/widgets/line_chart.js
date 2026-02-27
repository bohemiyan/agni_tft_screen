'use strict';
/*!
 * s1panel - widget/line_chart (native canvas, zero deps)
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

        const _raw   = value.split(',').map(Number);
        const _count = Math.min(config.points || 60, _raw.length);
        const _data  = _raw.slice(_raw.length - _count);

        const _has_changed = (_private.last_value !== value);

        const _data_min = min ?? 0;
        const _data_max = max && max > 0 ? max : Math.max(..._data, 1);
        const _range    = _data_max - _data_min || 1;

        const scaleX = i  => _rect.x + (i / (_data.length - 1)) * _rect.width;
        const scaleY = v  => _rect.y + _rect.height - ((v - _data_min) / _range) * _rect.height;

        start_draw(context, _rect);

        // fill area beneath line
        if (config.area) {
            context.beginPath();
            _data.forEach((v, i) => {
                const x = scaleX(i), y = scaleY(v);
                i === 0 ? context.moveTo(x, y) : context.lineTo(x, y);
            });
            context.lineTo(scaleX(_data.length - 1), _rect.y + _rect.height);
            context.lineTo(scaleX(0), _rect.y + _rect.height);
            context.closePath();
            context.fillStyle = config.fill || 'rgba(0,212,255,0.15)';
            context.fill();
        }

        // draw the line
        context.beginPath();
        _data.forEach((v, i) => {
            const x = scaleX(i), y = scaleY(v);
            i === 0 ? context.moveTo(x, y) : context.lineTo(x, y);
        });
        context.strokeStyle = config.outline || '#00d4ff';
        context.lineWidth   = config.line_width || 1.5;
        context.lineJoin    = 'round';
        context.stroke();

        if (config.debug_frame) debug_rect(context, _rect);
        context.restore();

        if (_has_changed) _private.last_value = value;

        fulfill(_has_changed);
    });
}

function info() {
    return {
        name: 'line_chart',
        description: 'A smooth line/area chart (native canvas)',
        fields: [
            { name: 'outline',    value: 'color'   },
            { name: 'fill',       value: 'color'   },
            { name: 'points',     value: 'number'  },
            { name: 'area',       value: 'boolean' },
            { name: 'line_width', value: 'number'  },
        ]
    };
}

module.exports = { info, draw };