import logging
import serial
import asyncio

logger = logging.getLogger(__name__)

BUFFER_SIZE = 5
HEADER_SIZE = 5

SIGNATURE_BYTE = 0xFA

THEME_RAINBOW = 0x01
THEME_BREATHING = 0x02
THEME_COLORS = 0x03
THEME_OFF = 0x04
THEME_AUTO = 0x05

MAX_VALUE = 0x05
MIN_VALUE = 0x01

DELAY = 0.005  # 0.005 second = 5ms matching JS


class LEDDevice:
    def __init__(self):
        self.port = None
        self.device_path = None

    def _fix_value(self, num):
        """Fix value to valid range matching JS exactly."""
        # JS: return Math.min(MAX_VALUE, Math.max(6 - num, MIN_VALUE));
        return min(MAX_VALUE, max(6 - num, MIN_VALUE))

    def _checksum(self, dv):
        """Calculate checksum matching JS exactly."""
        # JS: var _crc = 0x00; for (var i = 0; i < 4; i++) { _crc += dv.getUint8(i); }
        crc = 0
        for i in range(4):
            crc += dv[i]
        return crc & 0xFF

    def _open_device(self, device):
        """Open serial port matching JS open_device exactly."""
        # JS: if (_port_cache && _port_cache.isOpen) { return fulfill(_port_cache); }
        if self.port and self.port.is_open:
            return True
        
        # JS: _port_cache = null;
        self.port = None
        
        # JS: const _port = new SerialPort({ path: device, baudRate: 115200, autoOpen: false });
        try:
            self.port = serial.Serial(
                port=device,
                baudrate=115200,
                timeout=1,
                write_timeout=1,
                exclusive=True
            )
            
            # JS: _port.on('close', () => { _port_cache = null; });
            # JS: _port.on('error', (e) => { ... _port_cache = null; });
            # Python serial doesn't have callbacks, we check is_open instead
            
            logger.info("led found")
            logger.info(f"Opened LED Serial: {device}")
            self.device_path = device
            return True
            
        except Exception as e:
            logger.error(f"led_device: error opening port {device} - {e}")
            logger.error("led_device: check device exists with: ls -la /dev/ttyUSB*")
            self.port = None
            return False

    async def _port_byte_write(self, buffer):
        """Write byte by byte with delay matching JS port_byte_write exactly."""
        # JS: function port_byte_write(port, buffer, index, size, fulfill)
        for i in range(len(buffer)):
            # JS: const _one_byte = Buffer.from( [ buffer[index] ] );
            one_byte = bytes([buffer[i]])
            
            try:
                # JS: port.write(_one_byte, err => { ... });
                self.port.write(one_byte)
            except Exception as e:
                logger.error(f"led_device: {e}")
                return False
            
            # JS: setTimeout(() => { ... }, DELAY);
            await asyncio.sleep(DELAY)
        
        return True

    async def set_strip(self, theme, intensity, speed, device_path="/dev/ttyUSB0"):
        """Set LED strip theme matching JS set_rainbow/set_breathing/etc exactly."""
        theme = int(theme)
        
        # Theme 6 = ignore (matching led_thread.js)
        if theme == 6:
            logger.info('led_thread: ignore')
            return
        
        # Map theme to constant like JS
        theme_map = {
            1: THEME_RAINBOW,
            2: THEME_BREATHING,
            3: THEME_COLORS,
            4: THEME_OFF,
            5: THEME_AUTO
        }
        theme_const = theme_map.get(theme, THEME_AUTO)
        
        # JS: const _buffer = new Uint8ClampedArray(BUFFER_SIZE);
        buffer = bytearray(BUFFER_SIZE)
        
        # JS: _header.setUint8(0, SIGNATURE_BYTE);
        buffer[0] = SIGNATURE_BYTE
        # JS: _header.setUint8(1, THEME_RAINBOW/THEME_BREATHING/etc);
        buffer[1] = theme_const
        # JS: _header.setUint8(2, fix_value(intensity));
        buffer[2] = self._fix_value(int(intensity))
        # JS: _header.setUint8(3, fix_value(speed));
        buffer[3] = self._fix_value(int(speed))
        # JS: _header.setUint8(4, checksum(_header));
        buffer[4] = self._checksum(buffer)
        
        # JS: open_device(device).then(port => { port_byte_write(...).then(fulfill); }, fulfill);
        if not self._open_device(device_path):
            return  # Silent fail like JS
        
        if not self.port or not self.port.is_open:
            return
        
        # JS: port_byte_write(port, _buffer, 0, BUFFER_SIZE, () => { fulfill(); });
        await self._port_byte_write(buffer)

    async def set_rainbow(self, intensity, speed, device_path="/dev/ttyUSB0"):
        """Convenience method matching JS set_rainbow."""
        await self.set_strip(1, intensity, speed, device_path)

    async def set_breathing(self, intensity, speed, device_path="/dev/ttyUSB0"):
        """Convenience method matching JS set_breathing."""
        await self.set_strip(2, intensity, speed, device_path)

    async def set_color(self, intensity, speed, device_path="/dev/ttyUSB0"):
        """Convenience method matching JS set_color."""
        await self.set_strip(3, intensity, speed, device_path)

    async def set_off(self, device_path="/dev/ttyUSB0"):
        """Convenience method matching JS set_off."""
        await self.set_strip(4, 5, 5, device_path)

    async def set_automatic(self, intensity, speed, device_path="/dev/ttyUSB0"):
        """Convenience method matching JS set_automatic."""
        await self.set_strip(5, intensity, speed, device_path)

    def close(self):
        """Close serial port."""
        if self.port:
            try:
                self.port.close()
            except:
                pass
            self.port = None
            self.device_path = None