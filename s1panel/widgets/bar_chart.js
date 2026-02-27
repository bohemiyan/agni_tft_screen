'use strict';
/*!
 * s1panel - widget/bar_chart (native canvas, zero deps)
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

        const _private   = get_private(config);
        const _rect      = config.rect;
        const _horizontal = config.horizontal || false;

        const _raw   = value.split(',').map(Number);
        const _pts   = config.points || 16;
        const _data  = _raw.slice(Math.max(0, _raw.length - _pts));

        const _has_changed = (_private.last_value !== value);

        const _data_max = max && max > 0 ? max : Math.max(..._data, 1);
        const _data_min = min ?? 0;
        const _range    = _data_max - _data_min || 1;

        const _fill    = config.fill    || '#0077aa';
        const _outline = config.outline || '#00d4ff';

        start_draw(context, _rect);

        if (_horizontal) {
            // Single horizontal progress bar (points=1 mode)
            const _val = _data[_data.length - 1] ?? 0;
            const _pct = Math.max(0, Math.min(1, (_val - _data_min) / _range));
            const _fw  = _rect.width * _pct;

            // background track
            context.fillStyle = 'rgba(255,255,255,0.05)';
            context.fillRect(_rect.x, _rect.y, _rect.width, _rect.height);

            // filled portion with gradient
            if (_fw > 0) {
                const _grad = context.createLinearGradient(_rect.x, 0, _rect.x + _fw, 0);
                _grad.addColorStop(0, _outline);
                _grad.addColorStop(1, _fill);
                context.fillStyle = _grad;
                context.fillRect(_rect.x, _rect.y, _fw, _rect.height);
            }
        }
        else {
            // Vertical bar histogram
            const _bar_gap  = config.gap ?? 1;
            const _total_w  = _rect.width;
            const _bar_w    = Math.max(1, Math.floor((_total_w - (_data.length - 1) * _bar_gap) / _data.length));

            _data.forEach((v, i) => {
                const _pct = Math.max(0, Math.min(1, (v - _data_min) / _range));
                const _bh  = Math.round(_pct * _rect.height);
                const _bx  = _rect.x + i * (_bar_w + _bar_gap);
                const _by  = _rect.y + _rect.height - _bh;

                // gradient per bar
                const _grad = context.createLinearGradient(_bx, _by, _bx, _by + _bh);
                _grad.addColorStop(0, _outline);
                _grad.addColorStop(1, _fill);
                context.fillStyle = _grad;
                context.fillRect(_bx, _by, _bar_w, _bh);
            });
        }

        if (config.debug_frame) debug_rect(context, _rect);
        context.restore();

        if (_has_changed) _private.last_value = value;

        fulfill(_has_changed);
    });
}

function info() {
    return {
        name: 'bar_chart',
        description: 'A bar chart (native canvas)',
        fields: [
            { name: 'outline',    value: 'color'   },
            { name: 'fill',       value: 'color'   },
            { name: 'points',     value: 'number'  },
            { name: 'horizontal', value: 'boolean' },
            { name: 'gap',        value: 'number'  },
        ]
    };
}

module.exports = { info, draw };