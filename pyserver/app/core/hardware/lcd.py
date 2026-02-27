import logging
import hid  # Will fail immediately if not available
import time
import asyncio

logger = logging.getLogger(__name__)

BUFFER_SIZE = 4104
HEADER_SIZE = 8
DATA_SIZE = 4096
REPORT_SIZE = 1

LCD_SIGNATURE = 0x55
LCD_CONFIG = 0xA1
LCD_REFRESH = 0xA2
LCD_REDRAW = 0xA3

LCD_ORIENTATION = 0xF1
LCD_SET_TIME = 0xF2

LCD_LANDSCAPE = 0x01
LCD_PORTRAIT = 0x02

LCD_REDRAW_START = 0xF0
LCD_REDRAW_CONTINUE = 0xF1
LCD_REDRAW_END = 0xF2

CHUNK_COUNT = 27
FINAL_CHUNK_INDEX = CHUNK_COUNT - 1
FINAL_CHUNK_SIZE = 2304


class LCDDevice:
    def __init__(self, vendor_id=1241, product_id=64769):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.device = None
        self.is_open = False

    def open(self):
        try:
            self.device = hid.device()
            self.device.open(self.vendor_id, self.product_id)
            self.is_open = True
            logger.info(f"LCD opened: {self.vendor_id}:{self.product_id}")
        except Exception as e:
            self.is_open = False
            logger.error(f"Failed to open LCD: {e}")
            raise  # Fail loudly - no dummy

    def close(self):
        if self.device:
            self.device.close()
            self.device = None
        self.is_open = False

    def _convert_rgb_to_rgb565(self, image_data):
        """Convert RGB bytes to RGB565 values like JS."""
        rgb565_values = []
        for i in range(0, len(image_data), 3):
            if i + 2 >= len(image_data):
                break
            r, g, b = image_data[i], image_data[i+1], image_data[i+2]
            val = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            rgb565_values.append(val)
        return rgb565_values

    async def set_orientation(self, portrait=False):
        if not self.is_open:
            return
        buffer = bytearray(REPORT_SIZE + BUFFER_SIZE)
        buffer[REPORT_SIZE + 0] = LCD_SIGNATURE
        buffer[REPORT_SIZE + 1] = LCD_CONFIG
        buffer[REPORT_SIZE + 2] = LCD_ORIENTATION
        buffer[REPORT_SIZE + 3] = LCD_PORTRAIT if portrait else LCD_LANDSCAPE
        buffer[0] = 0x00
        try:
            self.device.write(buffer)
        except Exception as e:
            logger.error(f"set_orientation failed: {e}")

    async def heartbeat(self):
        if not self.is_open:
            return
        now = time.localtime()
        buffer = bytearray(REPORT_SIZE + BUFFER_SIZE)
        buffer[REPORT_SIZE + 0] = LCD_SIGNATURE
        buffer[REPORT_SIZE + 1] = LCD_CONFIG
        buffer[REPORT_SIZE + 2] = LCD_SET_TIME
        buffer[REPORT_SIZE + 3] = now.tm_hour
        buffer[REPORT_SIZE + 4] = now.tm_min
        buffer[REPORT_SIZE + 5] = now.tm_sec
        buffer[0] = 0x00
        try:
            self.device.write(buffer)
        except Exception as e:
            logger.error(f"heartbeat failed: {e}")

    async def refresh(self, x, y, width, height, image_data):
        if not self.is_open:
            return
        rgb565_values = self._convert_rgb_to_rgb565(image_data)
        buffer = bytearray(REPORT_SIZE + BUFFER_SIZE)
        buffer[REPORT_SIZE + 0] = LCD_SIGNATURE
        buffer[REPORT_SIZE + 1] = LCD_REFRESH
        buffer[REPORT_SIZE + 2] = x & 0xFF
        buffer[REPORT_SIZE + 3] = (x >> 8) & 0xFF
        buffer[REPORT_SIZE + 4] = y & 0xFF
        buffer[REPORT_SIZE + 5] = (y >> 8) & 0xFF
        buffer[REPORT_SIZE + 6] = width
        buffer[REPORT_SIZE + 7] = height
        
        data_offset = REPORT_SIZE + HEADER_SIZE
        for i in range(width * height):
            val = rgb565_values[i]
            buffer[data_offset + (i * 2)] = (val >> 8) & 0xFF
            buffer[data_offset + (i * 2) + 1] = val & 0xFF
        
        buffer[0] = 0x00
        try:
            self.device.write(buffer)
        except Exception as e:
            logger.error(f"refresh failed: {e}")

    async def redraw(self, image_data):
        if not self.is_open:
            return
        rgb565_values = self._convert_rgb_to_rgb565(image_data)
        for index in range(CHUNK_COUNT):
            success = await self._send_chunk(index, rgb565_values)
            if not success:
                break

    async def _send_chunk(self, index, rgb565_values):
        buffer = bytearray(REPORT_SIZE + BUFFER_SIZE)
        buffer[REPORT_SIZE + 0] = LCD_SIGNATURE
        buffer[REPORT_SIZE + 1] = LCD_REDRAW
        
        if index == 0:
            buffer[REPORT_SIZE + 2] = LCD_REDRAW_START
        elif index == FINAL_CHUNK_INDEX:
            buffer[REPORT_SIZE + 2] = LCD_REDRAW_END
        else:
            buffer[REPORT_SIZE + 2] = LCD_REDRAW_CONTINUE
        
        buffer[REPORT_SIZE + 3] = 1 + index
        
        offset = index * DATA_SIZE
        length = DATA_SIZE if index < FINAL_CHUNK_INDEX else FINAL_CHUNK_SIZE
        
        buffer[REPORT_SIZE + 5] = (offset >> 8) & 0xFF
        buffer[REPORT_SIZE + 6] = offset & 0xFF
        buffer[REPORT_SIZE + 7] = (length >> 8) & 0xFF
        buffer[REPORT_SIZE + 8] = length & 0xFF
        
        pixel_start = (index * DATA_SIZE) // 2
        pixel_length = length // 2
        data_offset = REPORT_SIZE + HEADER_SIZE
        
        for i in range(pixel_length):
            val = rgb565_values[pixel_start + i]
            buffer[data_offset + (i * 2)] = (val >> 8) & 0xFF
            buffer[data_offset + (i * 2) + 1] = val & 0xFF
        
        buffer[0] = 0x00
        
        try:
            self.device.write(buffer)
            await asyncio.sleep(0.005)
            return True
        except Exception as e:
            logger.error(f"Chunk {index} failed: {e}")
            return False