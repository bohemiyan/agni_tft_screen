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
THEME_IGNORE = 0x06  # Theme 6 = ignore/no-op

MAX_VALUE = 0x05
MIN_VALUE = 0x01


class LEDDevice:
    def __init__(self):
        self.port = None
        self.device_path = None

    def _fix_value(self, num):
        """Fix value to valid range (inverted logic: higher input = lower output)."""
        return min(MAX_VALUE, max(6 - num, MIN_VALUE))

    def _checksum(self, buffer):
        """Calculate checksum (sum of first 4 bytes)."""
        crc = 0
        for i in range(4):
            crc += buffer[i]
        return crc & 0xFF

    def _connect(self, path):
        """Open serial connection to LED device."""
        # Close existing port if different path or stale
        if self.port:
            try:
                if not self.port.is_open or self.device_path != path:
                    self.port.close()
                    self.port = None
            except Exception:
                self.port = None
        
        self.device_path = path
        
        # Check if we need to open new connection
        if not self.port:
            try:
                self.port = serial.Serial(
                    self.device_path, 
                    115200, 
                    timeout=1,
                    write_timeout=1
                )
                logger.info("led found")
                logger.info(f"Opened LED Serial: {self.device_path}")
                
            except Exception as e:
                self.port = None
                logger.warning(f"Could not open LED Serial {self.device_path}: Is the USB plugged in?")

    def _ensure_connected(self, device_path):
        """Ensure connection is active, reconnect if necessary."""
        need_reconnect = False
        
        if not self.port:
            need_reconnect = True
        elif self.device_path != device_path:
            need_reconnect = True
        else:
            # Check if port is still open (like JS isOpen check)
            try:
                if not self.port.is_open:
                    need_reconnect = True
            except Exception:
                need_reconnect = True
        
        if need_reconnect:
            self._connect(device_path)

    async def set_strip(self, theme, intensity, speed, device_path="/dev/ttyUSB0"):
        """Set LED strip theme and parameters."""
        theme = int(theme)
        
        # Theme 6 = ignore (matching led_thread.js behavior)
        if theme == 6:
            logger.info('led_thread: ignore')
            return
        
        self._ensure_connected(device_path)
        
        if not self.port or not self.port.is_open:
            return  # Silent fail if device doesn't exist

        buffer = bytearray(5)
        buffer[0] = SIGNATURE_BYTE
        
        # Map theme id to constants
        theme_map = {
            1: THEME_RAINBOW,
            2: THEME_BREATHING, 
            3: THEME_COLORS,
            4: THEME_OFF,
            5: THEME_AUTO
        }
        buffer[1] = theme_map.get(theme, THEME_AUTO)
        buffer[2] = self._fix_value(int(intensity))
        buffer[3] = self._fix_value(int(speed))
        buffer[4] = self._checksum(buffer)

        try:
            # Write byte by byte with delay (matching JS implementation)
            for b in buffer:
                self.port.write(bytes([b]))
                await asyncio.sleep(0.005)  # 5ms delay per byte
                
        except Exception as e:
            logger.error(f"LED Write Failure: {e}")
            # Try reconnecting for next run (clear cache like JS)
            try:
                self.port.close()
            except:
                pass
            self.port = None
            self._connect(device_path)

    async def set_rainbow(self, intensity, speed, device_path="/dev/ttyUSB0"):
        """Convenience method for rainbow theme."""
        await self.set_strip(1, intensity, speed, device_path)

    async def set_breathing(self, intensity, speed, device_path="/dev/ttyUSB0"):
        """Convenience method for breathing theme."""
        await self.set_strip(2, intensity, speed, device_path)

    async def set_color(self, intensity, speed, device_path="/dev/ttyUSB0"):
        """Convenience method for solid color theme."""
        await self.set_strip(3, intensity, speed, device_path)

    async def set_off(self, device_path="/dev/ttyUSB0"):
        """Convenience method to turn off LEDs."""
        await self.set_strip(4, 5, 5, device_path)

    async def set_automatic(self, intensity, speed, device_path="/dev/ttyUSB0"):
        """Convenience method for automatic theme."""
        await self.set_strip(5, intensity, speed, device_path)

    def close(self):
        """Close serial port."""
        if self.port:
            try:
                self.port.close()
            except:
                pass
            self.port = None