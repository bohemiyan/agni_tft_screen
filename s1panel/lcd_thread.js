"use strict";
/*!
 * s1panel - lcd_thread
 * Copyright (c) 2024-2025 Tomasz Jaworski
 * GPL-3 Licensed
 */
const threads = require("worker_threads");
const node_hid = require("node-hid");
const lcd = require("./lcd_device");
const logger = require("./logger");

const usb_hid = node_hid.HIDAsync;

node_hid.setDriverType("libusb");

const START_COOL_DOWN = 1000;
const POLL_TIMEOUT = 10;

// my hid throws way too many of these errors, hide them by default!
const DEBUG_TRACE = false;

const get_hr_time = () => Math.floor(Number(process.hrtime.bigint()) / 1000000);

const start_lcd_redraw = async (handle, state, job) => {
  try {
    await lcd.redraw(handle, job.image);
  } catch (err) {
    if (DEBUG_TRACE) {
      logger.error("lcd_thread: start_lcd_redraw hid error: " + err);
    }
  }
  return { type: "redraw", complete: true };
};

const start_lcd_update = async (handle, state, job) => {
  while (job && "update" === job.type) {
    try {
      await lcd.refresh(
        handle,
        job.rect.x,
        job.rect.y,
        job.rect.width,
        job.rect.height,
        job.image,
      );
    } catch (err) {
      if (DEBUG_TRACE) {
        logger.error("lcd_thread: start_lcd_update hid error: " + err);
      }
    }
    job = state.queue.shift();
  }
  return { type: "update", complete: true };
};

const start_lcd_heartbeat = async (handle, state, job) => {
  try {
    await lcd.heartbeat(handle);
  } catch (err) {
    if (DEBUG_TRACE) {
      logger.error("lcd_thread: start_lcd_heartbeat hid error: " + err);
    }
  }
  return { type: "heartbeat", complete: false };
};

const start_lcd_orientation = async (handle, state, job) => {
  try {
    await lcd.set_orientation(handle, job.portrait);
  } catch (err) {
    if (DEBUG_TRACE) {
      logger.error("lcd_thread: start_lcd_orientation hid error: " + err);
    }
  }
  return { type: "orientation", complete: false };
};

const with_delay = async (handle, state, job, call) => {
  if ("redraw" === state.last_type) {
    await new Promise((resolve) => setTimeout(resolve, state.refresh));
  }
  return await call(handle, state, job);
};

const refresh_device = async (handle, state) => {
  while (true) {
    const _now = get_hr_time();
    let rc = { type: "idle" };

    if (state.queue.length) {
      const _last_heartbeat = _now - state.last_heartbeat;

      if (_last_heartbeat > state.heartbeat) {
        rc = await with_delay(
          handle,
          state,
          { type: "heartbeat" },
          start_lcd_heartbeat,
        );
      } else {
        const _job = state.queue.shift();

        switch (_job.type) {
          case "redraw":
            rc = await start_lcd_redraw(handle, state, _job);
            break;
          case "update":
            rc = await with_delay(handle, state, _job, start_lcd_update);
            break;
          case "orientation":
            rc = await with_delay(handle, state, _job, start_lcd_orientation);
            break;
          case "heartbeat":
            rc = await with_delay(handle, state, _job, start_lcd_heartbeat);
            break;
        }
      }
    } else {
      const _last_activity = _now - state.last_activity;
      if (_last_activity > state.refresh) {
        rc = await with_delay(
          handle,
          state,
          { type: "heartbeat" },
          start_lcd_heartbeat,
        );
      }
    }

    if ("idle" !== rc.type) {
      if ("heartbeat" === rc.type) {
        state.last_heartbeat = get_hr_time();
      } else {
        threads.parentPort.postMessage({
          type: rc.type,
          complete: rc.complete,
        });
      }

      state.last_type = rc.type;
      state.last_activity = get_hr_time();
    }

    await new Promise((resolve) => setTimeout(resolve, POLL_TIMEOUT));
  }
};

const message_handler = (state, message) => {
  switch (message.type) {
    case "orientation":
    case "heartbeat":
      state.queue.push(message);
      break;
    case "redraw":
      state.queue.push({ type: "redraw", image: { data: message.pixelData } });
      break;
    case "update":
      state.queue.push({
        type: "update",
        rect: message.rect,
        image: { data: message.pixelData },
      });
      break;
    case "config":
      state.poll = message.poll || state.poll;
      state.refresh = message.refresh || state.refresh;
      state.heartbeat = message.heartbeat || state.heartbeat;
      break;
    default:
      logger.error("lcd_thread: unknown command type: " + message.type);
      break;
  }
};

const main = async (state) => {
  logger.info("lcd_thread: started...");

  threads.parentPort.on("message", (message) => {
    message_handler(state, message);
  });

  node_hid.devices().find((each) => {
    if (1241 === each.vendorId && 64769 === each.productId) {
      logger.info(JSON.stringify(each, null, 3));
    }
  });

  try {
    const handle = await usb_hid.open(state.device);
    await new Promise((resolve) => setTimeout(resolve, START_COOL_DOWN));
    await refresh_device(handle, state);
  } catch (err) {
    logger.error("lcd_thread: failed to open usbhid " + state.device);
    logger.error(err);
  }
};

main({
  device: threads.workerData.device,
  poll: threads.workerData.poll,
  refresh: threads.workerData.refresh,
  heartbeat: threads.workerData.heartbeat,
  last_heartbeat: get_hr_time(),
  last_activity: get_hr_time(),
  queue: [],
  last_type: "idle",
});

main({
  device: threads.workerData.device,
  poll: threads.workerData.poll,
  refresh: threads.workerData.refresh,
  heartbeat: threads.workerData.heartbeat,
  last_heartbeat: get_hr_time(),
  last_activity: get_hr_time(),
  queue: [],
  last_type: "idle",
});
