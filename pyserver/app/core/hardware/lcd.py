import logging
import hid
import time
import asyncio

logger = logging.getLogger(__name__)

BUFFER_SIZE = 4104
HEADER_SIZE = 8
DATA_SIZE = 4096
REPORT_SIZE = 1

LCD_SIGNATURE = 0x55
LCD_REDRAW = 0xA3
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

    def open(self):
        try:
            self.device = hid.device()
            self.device.open(self.vendor_id, self.product_id)
            logger.info(f"Opened LCD device: {self.vendor_id}:{self.product_id}")
        except Exception as e:
            logger.error(f"Failed to open LCD device: {e}")

    def close(self):
        if self.device:
            self.device.close()
            self.device = None

    def _convert_rgba_to_rgb565(self, image_data):
        # Already comes in as raw Pillow RGB buffer in worker
        # Let's assume the worker gave us an RGB pixel_data bytestring
        rgb565_data = bytearray(320 * 170 * 2)
        idx = 0
        for i in range(0, len(image_data), 3):
            # Read RGB
            if i + 2 >= len(image_data): break
            r, g, b = image_data[i], image_data[i+1], image_data[i+2]
            
            # Convert to 16-bit RGB565 (R: 5, G: 6, B: 5)
            val = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            
            # Store in big-endian (or whichever endianness the device expects)
            # The JS code did: _data.setUint16(_offset, image.data[...]) so big-endian.
            rgb565_data[idx] = (val >> 8) & 0xFF
            rgb565_data[idx+1] = val & 0xFF
            idx += 2
            
        return rgb565_data

    async def redraw(self, image_data):
        if not self.device:
            return

        rgb565_data = self._convert_rgba_to_rgb565(image_data)

        for index in range(CHUNK_COUNT):
            buffer = bytearray(REPORT_SIZE + BUFFER_SIZE)
            
            buffer[REPORT_SIZE + 0] = LCD_SIGNATURE
            buffer[REPORT_SIZE + 1] = LCD_REDRAW

            if index == 0:
                buffer[REPORT_SIZE + 2] = LCD_REDRAW_START
            elif index == FINAL_CHUNK_INDEX:
                buffer[REPORT_SIZE + 2] = LCD_REDRAW_END
            else:
                buffer[REPORT_SIZE + 2] = LCD_REDRAW_CONTINUE

            length = DATA_SIZE if index < FINAL_CHUNK_INDEX else FINAL_CHUNK_SIZE

            buffer[REPORT_SIZE + 3] = 1 + index
            
            # Offset (Uint16 Big-Endian)
            offset = index * DATA_SIZE
            buffer[REPORT_SIZE + 5] = (offset >> 8) & 0xFF
            buffer[REPORT_SIZE + 6] = offset & 0xFF
            
            # Length (Uint16 Big-Endian)
            buffer[REPORT_SIZE + 7] = (length >> 8) & 0xFF
            buffer[REPORT_SIZE + 8] = length & 0xFF

            # Copy pixel data slice
            pixel_start = index * DATA_SIZE
            buffer[(REPORT_SIZE + HEADER_SIZE): (REPORT_SIZE + HEADER_SIZE + length)] = rgb565_data[pixel_start: pixel_start + length]

            try:
                # the write format expects report ID as first byte for HID devices (usually 0x00)
                buffer[0] = 0x00 
                self.device.write(buffer)
                # Small delay to let device digest
                await asyncio.sleep(0.005)
            except Exception as e:
                logger.error(f"LCD Write failure on chunk {index}: {e}")
                self.close()
                self.open() # attempt recovery
                break
