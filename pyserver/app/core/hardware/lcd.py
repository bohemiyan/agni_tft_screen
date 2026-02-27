import logging
try:
    import hid
except Exception as e:
    logger.warning(f"hid library not available ({e}), using dummy HID implementation.")
    class DummyHIDDevice:
        def __init__(self):
            self.opened = False
        def open(self, vendor_id, product_id):
            self.opened = True
            logger.info(f"Dummy HID opened for vendor {vendor_id}, product {product_id}")
        def write(self, data):
            logger.info(f"Dummy HID write called with {len(data)} bytes")
            return len(data)
        def close(self):
            self.opened = False
            logger.info("Dummy HID closed")
    hid = type('hid', (), {'device': DummyHIDDevice})
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
            logger.info("lcd found (real or dummy)")
            logger.info(f"Opened LCD device: {self.vendor_id}:{self.product_id}")
        except Exception as e:
            self.is_open = False
            logger.error(f"Failed to open LCD device: {e}")

    def close(self):
        if self.device:
            self.device.close()
            self.device = None
        self.is_open = False

    def _convert_rgba_to_rgb565(self, image_data):
        """Convert RGB image data to RGB565 format."""
        expected_pixels = 320 * 170
        rgb565_data = bytearray(expected_pixels * 2)
        idx = 0
        
        # Handle both RGB (3 bytes) and RGBA (4 bytes) input
        pixel_stride = 4 if len(image_data) >= expected_pixels * 4 else 3
        
        for i in range(0, len(image_data), pixel_stride):
            if i + 2 >= len(image_data):
                break
            
            r = image_data[i]
            g = image_data[i + 1]
            b = image_data[i + 2]
            
            # Convert to 16-bit RGB565 (R: 5, G: 6, B: 5)
            val = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            
            # Store in big-endian format (matching JS DataView.setUint16 default)
            rgb565_data[idx] = (val >> 8) & 0xFF      # High byte first
            rgb565_data[idx + 1] = val & 0xFF          # Low byte
            idx += 2
            
        return rgb565_data

    async def set_orientation(self, portrait=False):
        """Set LCD orientation to portrait or landscape."""
        if not self.is_open:
            logger.warning("Attempted set_orientation but device not open")
            return

        buffer = bytearray(REPORT_SIZE + BUFFER_SIZE)
        
        buffer[REPORT_SIZE + 0] = LCD_SIGNATURE
        buffer[REPORT_SIZE + 1] = LCD_CONFIG
        buffer[REPORT_SIZE + 2] = LCD_ORIENTATION
        buffer[REPORT_SIZE + 3] = LCD_PORTRAIT if portrait else LCD_LANDSCAPE
        
        buffer[0] = 0x00  # Report ID
        
        try:
            self.device.write(buffer)
            logger.info(f"LCD orientation set to {'portrait' if portrait else 'landscape'}")
        except Exception as e:
            logger.error(f"LCD set_orientation failed: {e}")
            self._attempt_recovery()

    async def heartbeat(self):
        """Send heartbeat/time sync to LCD."""
        if not self.is_open:
            logger.warning("Attempted heartbeat but device not open")
            return

        now = time.localtime()
        
        buffer = bytearray(REPORT_SIZE + BUFFER_SIZE)
        
        buffer[REPORT_SIZE + 0] = LCD_SIGNATURE
        buffer[REPORT_SIZE + 1] = LCD_CONFIG
        buffer[REPORT_SIZE + 2] = LCD_SET_TIME
        buffer[REPORT_SIZE + 3] = now.tm_hour
        buffer[REPORT_SIZE + 4] = now.tm_min
        buffer[REPORT_SIZE + 5] = now.tm_sec
        
        buffer[0] = 0x00  # Report ID
        
        try:
            self.device.write(buffer)
        except Exception as e:
            logger.error(f"LCD heartbeat failed: {e}")
            self._attempt_recovery()

    async def refresh(self, x, y, width, height, image_data):
        """Refresh a partial region of the LCD."""
        if not self.is_open:
            logger.warning("Attempted LCD refresh but device not open")
            return

        rgb565_data = self._convert_rgba_to_rgb565(image_data)
        
        buffer = bytearray(REPORT_SIZE + BUFFER_SIZE)
        
        buffer[REPORT_SIZE + 0] = LCD_SIGNATURE
        buffer[REPORT_SIZE + 1] = LCD_REFRESH
        
        # X coordinate (Uint16 Little-Endian to match JS: true means little-endian)
        buffer[REPORT_SIZE + 2] = x & 0xFF
        buffer[REPORT_SIZE + 3] = (x >> 8) & 0xFF
        
        # Y coordinate (Uint16 Little-Endian)
        buffer[REPORT_SIZE + 4] = y & 0xFF
        buffer[REPORT_SIZE + 5] = (y >> 8) & 0xFF
        
        # Width and Height (Uint8)
        buffer[REPORT_SIZE + 6] = width
        buffer[REPORT_SIZE + 7] = height
        
        # Copy pixel data
        data_length = width * height * 2  # RGB565 = 2 bytes per pixel
        buffer[REPORT_SIZE + HEADER_SIZE: REPORT_SIZE + HEADER_SIZE + data_length] = rgb565_data[:data_length]
        
        buffer[0] = 0x00  # Report ID
        
        try:
            self.device.write(buffer)
        except Exception as e:
            logger.error(f"LCD refresh failed: {e}")
            self._attempt_recovery()

    async def redraw(self, image_data):
        """Perform full screen redraw in chunks."""
        if not self.is_open:
            logger.warning("Attempted LCD redraw but device not open")
            return

        rgb565_data = self._convert_rgba_to_rgb565(image_data)
        
        for index in range(CHUNK_COUNT):
            success = await self._send_chunk(index, rgb565_data)
            if not success:
                logger.error(f"Failed to send chunk {index}, aborting redraw")
                break

    async def _send_chunk(self, index, rgb565_data):
        """Send a single chunk of the redraw."""
        buffer = bytearray(REPORT_SIZE + BUFFER_SIZE)
        
        buffer[REPORT_SIZE + 0] = LCD_SIGNATURE
        buffer[REPORT_SIZE + 1] = LCD_REDRAW
        
        # Set chunk type
        if index == 0:
            buffer[REPORT_SIZE + 2] = LCD_REDRAW_START
        elif index == FINAL_CHUNK_INDEX:
            buffer[REPORT_SIZE + 2] = LCD_REDRAW_END
        else:
            buffer[REPORT_SIZE + 2] = LCD_REDRAW_CONTINUE
        
        # Sequence number
        buffer[REPORT_SIZE + 3] = 1 + index
        
        # Reserved byte (index 4)
        buffer[REPORT_SIZE + 4] = 0
        
        # Offset into image (Uint16 Big-Endian)
        offset = index * DATA_SIZE
        buffer[REPORT_SIZE + 5] = (offset >> 8) & 0xFF
        buffer[REPORT_SIZE + 6] = offset & 0xFF
        
        # Chunk size (Uint16 Big-Endian)
        length = DATA_SIZE if index < FINAL_CHUNK_INDEX else FINAL_CHUNK_SIZE
        buffer[REPORT_SIZE + 7] = (length >> 8) & 0xFF
        buffer[REPORT_SIZE + 8] = length & 0xFF
        
        # Copy pixel data slice
        pixel_start = index * DATA_SIZE
        end_pos = REPORT_SIZE + HEADER_SIZE + length
        buffer[REPORT_SIZE + HEADER_SIZE: end_pos] = rgb565_data[pixel_start: pixel_start + length]
        
        buffer[0] = 0x00  # Report ID
        
        try:
            self.device.write(buffer)
            await asyncio.sleep(0.005)  # 5ms delay between chunks
            return True
        except Exception as e:
            logger.error(f"LCD Write failure on chunk {index}: {e}")
            self._attempt_recovery()
            return False

    def _attempt_recovery(self):
        """Attempt to recover from a write failure."""
        logger.info("Attempting LCD recovery...")
        self.close()
        time.sleep(0.1)
        self.open()