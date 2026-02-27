'use strict';
/*!
 * s1panel - widget/progress_bar
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
    context.strokeStyle = "red";
    context.rect(rect.x, rect.y, rect.width, rect.height);
    context.stroke();
}

function get_private(config) {
    if (!config._private) {
        config._private = {};
    }
    return config._private;
}

function draw(context, value, min, max, config) {

    return new Promise((fulfill, reject) => {

        const _private = get_private(config);
        const _rect = config.rect;
        
        // Convert string value to number 
        let _numValue = Number(value);
        if (isNaN(_numValue)) _numValue = 0;

        // Determine percentage based on min/max if provided, else assume 0-100
        let _percentage = _numValue;
        if (max > min) {
            _percentage = ((_numValue - min) / (max - min)) * 100;
        }
        
        // Clamp between 0 and 100
        _percentage = Math.max(0, Math.min(100, _percentage));
        
        const _has_changed = (_private.last_value !== _percentage) ? true : false;
        
        const _barWidth = _rect.width; 
        const _barHeight = _rect.height; 
        
        start_draw(context, _rect);
        
        const _bg_color = config.background_color || '#333333';
        const _fg_color = config.color || '#00ff00';
        const _is_vertical = config.vertical === 'true' || config.vertical === true;

        // Draw background
        context.fillStyle = _bg_color;
        context.fillRect(_rect.x, _rect.y, _barWidth, _barHeight);

        // Draw foreground
        context.fillStyle = _fg_color;
        
        if (_is_vertical) {
            const _fillHeight = (_barHeight * _percentage) / 100;
            context.fillRect(_rect.x, _rect.y + (_barHeight - _fillHeight), _barWidth, _fillHeight);
        } else {
            const _fillWidth = (_barWidth * _percentage) / 100;
            context.fillRect(_rect.x, _rect.y, _fillWidth, _barHeight);
        }

        if (config.debug_frame) {
            debug_rect(context, _rect);
        }
        
        context.restore();

        if (_has_changed) {
            _private.last_value = _percentage;
        }
        
        fulfill(_has_changed);
    }); 
}

function info() {
    return {
        name: 'progress_bar',
        description: 'A visual progress bar for percentages and limits',
        fields: [
            { name: 'color', type: 'color', value: '#00ff00' },
            { name: 'background_color', type: 'color', value: '#333333' },
            { name: 'vertical', type: 'boolean', value: 'false' }
        ]
    };
}

module.exports = {
    info,
    draw
};
