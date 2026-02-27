'use strict';
/*!
 * s1panel - screens_manager
 * Manages system and user screens stored as individual JSON files.
 * System screens (screens/system/) are read-only.
 * User screens (screens/user/) support full CRUD.
 */
const fs   = require('fs');
const path = require('path');

const logger = require('./logger');

const home_dir    = process.env.S1PANEL_CONFIG || __dirname;
const SYSTEM_DIR  = path.join(home_dir, 'screens', 'system');
const USER_DIR    = path.join(home_dir, 'screens', 'user');

// System screen IDs that can never be deleted or overwritten
const SYSTEM_IDS = new Set(['system_status', 'network_charts', 'clock_date', 'storage_power']);

function ensure_user_dir() {
    if (!fs.existsSync(USER_DIR)) {
        fs.mkdirSync(USER_DIR, { recursive: true });
    }
}

function read_json(filepath) {
    return new Promise((fulfill, reject) => {
        fs.readFile(filepath, 'utf8', (err, data) => {
            if (err) return reject(err);
            try { fulfill(JSON.parse(data)); }
            catch (e) { reject(e); }
        });
    });
}

function write_json(filepath, data) {
    return new Promise((fulfill, reject) => {
        fs.writeFile(filepath, JSON.stringify(data, null, 3), 'utf8', err => {
            if (err) return reject(err);
            fulfill();
        });
    });
}

function list_dir(dir, is_system) {
    return new Promise(fulfill => {
        fs.readdir(dir, (err, files) => {
            if (err) return fulfill([]);
            const _json = files.filter(f => f.endsWith('.json'));
            const _promises = _json.map(f => read_json(path.join(dir, f)).then(data => ({
                id:     data.id || path.basename(f, '.json'),
                name:   data.name || data.id,
                system: is_system,
            })).catch(() => null));
            Promise.all(_promises).then(results => fulfill(results.filter(Boolean)));
        });
    });
}

/* ──────────────────────────── Public API ──────────────────────────── */

function list_screens() {
    return Promise.all([
        list_dir(SYSTEM_DIR, true),
        list_dir(USER_DIR, false),
    ]).then(([sys, usr]) => [...sys, ...usr]);
}

function load_screen(id) {
    // Try system first, then user
    const _sys_path  = path.join(SYSTEM_DIR, id + '.json');
    const _user_path = path.join(USER_DIR,   id + '.json');

    return read_json(_sys_path).catch(() => read_json(_user_path));
}

function save_screen(id, data) {
    if (SYSTEM_IDS.has(id)) {
        return Promise.reject({ code: 403, message: 'Cannot modify a system screen.' });
    }
    ensure_user_dir();
    data.id = id;
    data.system = false;
    return write_json(path.join(USER_DIR, id + '.json'), data);
}

function create_screen(data) {
    const _id = 'user_' + Date.now();
    return save_screen(_id, { ...data, id: _id }).then(() => _id);
}

function delete_screen(id) {
    if (SYSTEM_IDS.has(id)) {
        return Promise.reject({ code: 403, message: 'Cannot delete a system screen.' });
    }
    return new Promise((fulfill, reject) => {
        const _p = path.join(USER_DIR, id + '.json');
        fs.unlink(_p, err => {
            if (err) return reject({ code: 404, message: 'Screen not found.' });
            fulfill();
        });
    });
}

/**
 * Given a theme object with active_screens (array of IDs), loads each
 * screen file and returns an array of screen objects. system_status is
 * always prepended even if not listed.
 */
function resolve_theme_screens(theme) {
    let _ids = Array.isArray(theme.active_screens) ? [...theme.active_screens] : [];

    // Always ensure system_status is first
    _ids = _ids.filter(id => id !== 'system_status');
    _ids.unshift('system_status');

    return Promise.all(_ids.map(id =>
        load_screen(id).catch(err => {
            logger.error('screens_manager: failed to load screen ' + id + ' - ' + err);
            return null;
        })
    )).then(screens => screens.filter(Boolean));
}

module.exports = {
    list_screens,
    load_screen,
    save_screen,
    create_screen,
    delete_screen,
    resolve_theme_screens,
    SYSTEM_IDS,
};
