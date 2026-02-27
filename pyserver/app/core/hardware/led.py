import logging
import serial
import asyncio

logger = logging.getLogger(__name__)

SIGNATURE_BYTE = 0xFA

THEME_RAINBOW = 0x01
THEME_BREATHING = 0x02
THEME_COLORS = 0x03
THEME_OFF = 0x04
THEME_AUTO = 0x05

MAX_VALUE = 0x05
MIN_VALUE = 0x01

class LEDDevice:
    def __init__(self):
        self.port = None
        self.device_path = None

    def _fix_value(self, num):
        return min(MAX_VALUE, max(6 - num, MIN_VALUE))

    def _checksum(self, buffer):
        crc = 0
        for i in range(4):
            crc += buffer[i]
        return crc & 0xFF

    async def set_strip(self, theme, intensity, speed, device_path="/dev/ttyUSB0"):
        if self.device_path != device_path or not self.port:
            self._connect(device_path)

        if not self.port:
            return # Silent fail if device doesn't exist

        buffer = bytearray(5)
        buffer[0] = SIGNATURE_BYTE
        
        # map theme id logic somewhat based on legacy params
        theme_map = {1: THEME_RAINBOW, 2: THEME_BREATHING, 3: THEME_COLORS, 4: THEME_OFF, 5: THEME_AUTO}
        buffer[1] = theme_map.get(int(theme), THEME_AUTO)
        buffer[2] = self._fix_value(int(intensity))
        buffer[3] = self._fix_value(int(speed))
        buffer[4] = self._checksum(buffer)

        try:
            for b in buffer:
                self.port.write(bytes([b]))
                await asyncio.sleep(0.005) # 5ms delay per byte
        except Exception as e:
            logger.error(f"LED Write Failure: {e}")
            self._connect(device_path) # Try reconnecting for next run

    def _connect(self, path):
        if self.port:
            try: self.port.close()
            except: pass
            self.port = None

        self.device_path = path
        try:
            self.port = serial.Serial(self.device_path, 115200, timeout=1)
            logger.info(f"Opened LED Serial: {self.device_path}")
        except Exception as e:
            logger.warning(f"Could not open LED Serial {self.device_path}: Is the USB plugged in?")
