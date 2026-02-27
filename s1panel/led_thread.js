"use strict";
/*!
 * s1panel - led_thread
 * Copyright (c) 2024-2025 Tomasz Jaworski
 * GPL-3 Licensed
 */
const threads = require("worker_threads");
const led = require("./led_device");
const logger = require("./logger");

threads.parentPort.on("message", async (message) => {
  switch (message.theme) {
    case 1:
      await led.set_rainbow(message.device, message.intensity, message.speed);
      break;

    case 2:
      await led.set_breathing(message.device, message.intensity, message.speed);
      break;

    case 3:
      await led.set_color(message.device, message.intensity, message.speed);
      break;

    case 4:
      await led.set_off(message.device);
      break;

    case 5:
      await led.set_automatic(message.device, message.intensity, message.speed);
      break;

    case 6:
      // ignore
      logger.info("led_thread: ignore");
      break;
  }
});

logger.info("led_thread: started...");
