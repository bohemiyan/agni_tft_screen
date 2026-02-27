'use strict';
/*!
 * s1panel - sensor/system_info
 * Copyright (c) 2024-2025 Tomasz Jaworski
 * GPL-3 Licensed
 */
const os = require('os');
const logger = require('../logger');

var _last_sampled = 0;

function format_uptime(seconds) {
    const d = Math.floor(seconds / (3600*24));
    const h = Math.floor(seconds % (3600*24) / 3600);
    const m = Math.floor(seconds % 3600 / 60);
    const s = Math.floor(seconds % 60);

    const dDisplay = d > 0 ? d + (d == 1 ? " day, " : " days, ") : "";
    const hDisplay = h > 0 ? h + (h == 1 ? " hr, " : " hrs, ") : "";
    const mDisplay = m > 0 ? m + (m == 1 ? " min, " : " mins, ") : "";
    const sDisplay = s > 0 ? s + (s == 1 ? " sec" : " secs") : "";
    return dDisplay + hDisplay + mDisplay + sDisplay;
}

function sample(rate, format) {

    return new Promise(fulfill => {

        const _diff = Math.floor(Number(process.hrtime.bigint()) / 1000000) - _last_sampled;

        if (!_last_sampled || _diff > rate) {
            _last_sampled = Math.floor(Number(process.hrtime.bigint()) / 1000000);
            // Time to sample
        }

        const _hostname = os.hostname();
        const _platform = os.platform() + ' ' + os.release();
        const _uptime_raw = os.uptime();
        const _uptime = format_uptime(_uptime_raw);
        const _loadavg = os.loadavg();

        const _output = format.replace(/{(\d+)}/g, function (match, number) { 
    
            switch (number) {
                case '0': return _hostname;
                case '1': return _platform;
                case '2': return _uptime;
                case '3': return _loadavg[0].toFixed(2);
                case '4': return _loadavg[1].toFixed(2);
                case '5': return _loadavg[2].toFixed(2);
                default:
                    return 'null';
            }
        }); 

        fulfill({ value: _output, min: 0, max: 0 });
    });
}

function init(config) {
    logger.info('initialize: system_info sensor');
    return 'system_info';
}

function stop() {
    return Promise.resolve();
}

/* this will only be used for GUI configuration */
function settings() {
    return {
        name: 'system_info',
        description: 'system information monitor',
        icon: 'pi-desktop',        
        multiple: false,
        ident: [],        
        fields: []
    };
}

module.exports = {
    init,
    settings,
    sample,
    stop
};
