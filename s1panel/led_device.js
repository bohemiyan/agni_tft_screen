"use strict";
/*!
 * s1panel - led_device
 * Copyright (c) 2024-2025 Tomasz Jaworski
 * GPL-3 Licensed
 */
const fs = require("fs");
const { SerialPort } = require("serialport");

const BUFFER_SIZE = 5;
const HEADER_SIZE = 5;

const SIGNATURE_BYTE = 0xfa;

const THEME_RAINBOW = 0x01;
const THEME_BREATHING = 0x02;
const THEME_COLORS = 0x03;
const THEME_OFF = 0x04;
const THEME_AUTO = 0x05;

const MAX_VALUE = 0x05;
const MIN_VALUE = 0x01;

const DELAY = 5; // 0.005 second

var _port_cache;

const printBytesInHex = (array) => {
  let _hexString = "";

  for (let i = 0; i < Math.min(array.length, HEADER_SIZE); i++) {
    _hexString += ("0" + array[i].toString(16)).slice(-2) + " ";
  }

  console.log(_hexString);
};

const fix_value = (num) => Math.min(MAX_VALUE, Math.max(6 - num, MIN_VALUE));

const checksum = (dv) => {
  let _crc = 0x00;

  for (let i = 0; i < 4; i++) {
    _crc += dv.getUint8(i);
  }

  return _crc;
};

const open_device = (device) => {
  return new Promise((fulfill, reject) => {
    if (_port_cache && _port_cache.isOpen) {
      return fulfill(_port_cache);
    }

    // Reset cache in case of a stale/closed port
    _port_cache = null;

    const _port = new SerialPort({
      path: device,
      baudRate: 115200,
      autoOpen: false,
    });

    _port.open((err) => {
      if (err) {
        console.log(
          "led_device: error opening port " + device + " - " + err.message,
        );
        console.log(
          "led_device: check device exists with: ls -la /dev/ttyUSB*",
        );
        return reject();
      }

      _port_cache = _port;

      // Clear cache if port closes unexpectedly
      _port.on("close", () => {
        _port_cache = null;
      });
      _port.on("error", (e) => {
        console.log("led_device: port error: " + e.message);
        _port_cache = null;
      });

      fulfill(_port);
    });
  });
};

const port_byte_write = async (port, buffer, index, size) => {
  for (let i = index; i < size; i++) {
    const _one_byte = Buffer.from([buffer[i]]);

    await new Promise((resolve) => {
      port.write(_one_byte, (err) => {
        if (err) {
          console.log("led_device: " + err);
        }
        setTimeout(resolve, DELAY);
      });
    });
  }
};

const set_rainbow = async (device, intensity, speed) => {
  const _buffer = new Uint8ClampedArray(BUFFER_SIZE);
  const _header = new DataView(_buffer.buffer);

  _header.setUint8(0, SIGNATURE_BYTE);
  _header.setUint8(1, THEME_RAINBOW);
  _header.setUint8(2, fix_value(intensity));
  _header.setUint8(3, fix_value(speed));
  _header.setUint8(4, checksum(_header));

  try {
    const port = await open_device(device);
    await port_byte_write(port, _buffer, 0, BUFFER_SIZE);
  } catch (err) {
    // ignore errors from open_device
  }
};

const set_breathing = async (device, intensity, speed) => {
  const _buffer = new Uint8ClampedArray(BUFFER_SIZE);
  const _header = new DataView(_buffer.buffer);

  _header.setUint8(0, SIGNATURE_BYTE);
  _header.setUint8(1, THEME_BREATHING);
  _header.setUint8(2, fix_value(intensity));
  _header.setUint8(3, fix_value(speed));
  _header.setUint8(4, checksum(_header));

  try {
    const port = await open_device(device);
    await port_byte_write(port, _buffer, 0, BUFFER_SIZE);
  } catch (err) {
    // ignore
  }
};

const set_color = async (device, intensity, speed) => {
  const _buffer = new Uint8ClampedArray(BUFFER_SIZE);
  const _header = new DataView(_buffer.buffer);

  _header.setUint8(0, SIGNATURE_BYTE);
  _header.setUint8(1, THEME_COLORS);
  _header.setUint8(2, fix_value(intensity));
  _header.setUint8(3, fix_value(speed));
  _header.setUint8(4, checksum(_header));

  try {
    const port = await open_device(device);
    await port_byte_write(port, _buffer, 0, BUFFER_SIZE);
  } catch (err) {
    // ignore
  }
};

const set_automatic = async (device, intensity, speed) => {
  const _buffer = new Uint8ClampedArray(BUFFER_SIZE);
  const _header = new DataView(_buffer.buffer);

  _header.setUint8(0, SIGNATURE_BYTE);
  _header.setUint8(1, THEME_AUTO);
  _header.setUint8(2, fix_value(intensity));
  _header.setUint8(3, fix_value(speed));
  _header.setUint8(4, checksum(_header));

  try {
    const port = await open_device(device);
    await port_byte_write(port, _buffer, 0, BUFFER_SIZE);
  } catch (err) {
    // ignore
  }
};

const set_off = async (device) => {
  const _buffer = new Uint8ClampedArray(BUFFER_SIZE);
  const _header = new DataView(_buffer.buffer);

  _header.setUint8(0, SIGNATURE_BYTE);
  _header.setUint8(1, THEME_OFF);
  _header.setUint8(2, 0x05);
  _header.setUint8(3, 0x05);
  _header.setUint8(4, checksum(_header));

  try {
    const port = await open_device(device);
    await port_byte_write(port, _buffer, 0, BUFFER_SIZE);
  } catch (err) {
    // ignore
  }
};

module.exports = {
  set_rainbow,
  set_breathing,
  set_color,
  set_automatic,
  set_off,
};
