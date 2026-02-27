#!/usr/bin/env python3
import hid
import time
from PIL import Image, ImageDraw

# Match JS constants exactly
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

def print_bytes(arr, name):
    """Debug helper like JS printBytesInHex"""
    hex_str = " ".join(f"{b:02x}" for b in arr[:16])
    print(f"{name}: {hex_str}...")

# Open device like JS: vendorId=1241, productId=64769
print("Opening HID device...")
device = hid.device()
device.open(1241, 64769)
print("✅ Device opened")

# Create image (320x170 like JS)
print("Creating image...")
img = Image.new("RGB", (320, 170), "black")
draw = ImageDraw.Draw(img)

# Draw "WELCOME" text
try:
    font = ImageFont.truetype("arialbd.ttf", 28)
except:
    font = ImageFont.load_default()

draw.text((60, 70), "WELCOME", fill=(0, 212, 255))  # Cyan

# Convert to RGB565 exactly like JS
pixels = list(img.getdata())
image_data = []  # This is the image.data array in JS

for r, g, b in pixels:
    # JS: _data.setUint16(_offset, image.data[_pixel_start + i])
    # Where image.data contains RGB565 values
    val = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    image_data.append(val)

print(f"Image data: {len(image_data)} pixels")

# Send redraw exactly like JS redraw() function
print("Sending redraw...")

for index in range(CHUNK_COUNT):
    # Create buffer like JS: new Uint8ClampedArray(REPORT_SIZE + BUFFER_SIZE)
    buffer = bytearray(REPORT_SIZE + BUFFER_SIZE)
    
    # Header like JS: new DataView(_buffer.buffer, REPORT_SIZE)
    # Byte 0: Report ID (for HID)
    buffer[0] = 0x00
    
    # JS: _header.setUint8(0, LCD_SIGNATURE)
    buffer[REPORT_SIZE + 0] = LCD_SIGNATURE
    
    # JS: _header.setUint8(1, LCD_REDRAW)
    buffer[REPORT_SIZE + 1] = LCD_REDRAW
    
    # JS: switch(index) for chunk type
    if index == 0:
        buffer[REPORT_SIZE + 2] = LCD_REDRAW_START  # 0xF0
    elif index == FINAL_CHUNK_INDEX:
        buffer[REPORT_SIZE + 2] = LCD_REDRAW_END    # 0xF2
    else:
        buffer[REPORT_SIZE + 2] = LCD_REDRAW_CONTINUE  # 0xF1
    
    # JS: _header.setUint8(3, 1 + index)
    buffer[REPORT_SIZE + 3] = 1 + index
    
    # JS: _header.setUint16(5, index * DATA_SIZE)  -- offset at bytes 5-6
    offset = index * DATA_SIZE
    buffer[REPORT_SIZE + 5] = (offset >> 8) & 0xFF   # High byte
    buffer[REPORT_SIZE + 6] = offset & 0xFF          # Low byte
    
    # JS: _header.setUint16(7, _length)  -- length at bytes 7-8
    length = DATA_SIZE if index < FINAL_CHUNK_INDEX else FINAL_CHUNK_SIZE
    buffer[REPORT_SIZE + 7] = (length >> 8) & 0xFF   # High byte
    buffer[REPORT_SIZE + 8] = length & 0xFF          # Low byte
    
    # JS: Copy pixel data
    # const _data = new DataView(_buffer.buffer, REPORT_SIZE + HEADER_SIZE);
    # const _pixel_start = (index * DATA_SIZE) / 2;
    # const _pixel_length = _length / 2;
    pixel_start = (index * DATA_SIZE) // 2
    pixel_length = length // 2
    
    data_offset = REPORT_SIZE + HEADER_SIZE
    for i in range(pixel_length):
        val = image_data[pixel_start + i]
        # JS: _data.setUint16(_offset, image.data[...])
        # Big endian like JS DataView
        buffer[data_offset + (i * 2)] = (val >> 8) & 0xFF      # High byte
        buffer[data_offset + (i * 2) + 1] = val & 0xFF          # Low byte
    
    # Debug first chunk
    if index == 0:
        print_bytes(buffer, "Chunk 0 header")
    
    # JS: handle.write(_buffer).then(...)
    try:
        device.write(buffer)
        print(f"Chunk {index + 1}/{CHUNK_COUNT} sent")
    except Exception as e:
        print(f"❌ Chunk {index} failed: {e}")
        break
    
    # JS delay between chunks
    time.sleep(0.005)

print("✅ All chunks sent")

# Hold for 2 seconds
print("Holding 2 seconds...")
time.sleep(2)

# Clear screen - send black
print("Clearing...")
black_img = Image.new("RGB", (320, 170), "black")
black_pixels = list(black_img.getdata())
black_data = []

for r, g, b in black_pixels:
    val = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    black_data.append(val)

# Send first chunk black
buffer = bytearray(REPORT_SIZE + BUFFER_SIZE)
buffer[0] = 0x00
buffer[REPORT_SIZE + 0] = LCD_SIGNATURE
buffer[REPORT_SIZE + 1] = LCD_REDRAW
buffer[REPORT_SIZE + 2] = LCD_REDRAW_START
buffer[REPORT_SIZE + 3] = 1
buffer[REPORT_SIZE + 5] = 0
buffer[REPORT_SIZE + 6] = 0
buffer[REPORT_SIZE + 7] = (DATA_SIZE >> 8) & 0xFF
buffer[REPORT_SIZE + 8] = DATA_SIZE & 0xFF

for i in range(DATA_SIZE // 2):
    val = black_data[i]
    buffer[REPORT_SIZE + HEADER_SIZE + (i * 2)] = (val >> 8) & 0xFF
    buffer[REPORT_SIZE + HEADER_SIZE + (i * 2) + 1] = val & 0xFF

device.write(buffer)

device.close()
print("✅ Done")