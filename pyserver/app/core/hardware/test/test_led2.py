#!/usr/bin/env python3
import asyncio
import hid
from PIL import Image, ImageDraw

# Constants
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
FINAL_CHUNK_INDEX = 26
FINAL_CHUNK_SIZE = 2304

async def send_welcome():
    device = hid.device()
    device.open(1241, 64769)
    print("✅ HID opened")

    # Create image with "WELCOME" text
    img = Image.new("RGB", (320, 170), "black")
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arialbd.ttf", 32)
    except:
        font = ImageFont.load_default()
    
    draw.text((60, 70), "WELCOME", fill=(0, 212, 255))  # Cyan color
    
    # Convert to RGB565
    pixels = list(img.getdata())
    rgb565 = bytearray(320 * 170 * 2)
    
    idx = 0
    for r, g, b in pixels:
        val = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        rgb565[idx] = (val >> 8) & 0xFF      # High byte
        rgb565[idx + 1] = val & 0xFF          # Low byte
        idx += 2

    print(f"Image converted: {len(rgb565)} bytes")

    # Send all 27 chunks
    for index in range(CHUNK_COUNT):
        buf = bytearray(REPORT_SIZE + BUFFER_SIZE)
        buf[0] = 0x00
        
        buf[1] = LCD_SIGNATURE
        buf[2] = LCD_REDRAW
        
        if index == 0:
            buf[3] = LCD_REDRAW_START
        elif index == FINAL_CHUNK_INDEX:
            buf[3] = LCD_REDRAW_END
        else:
            buf[3] = LCD_REDRAW_CONTINUE
            
        buf[4] = index + 1  # Sequence
        
        offset = index * DATA_SIZE
        length = DATA_SIZE if index < FINAL_CHUNK_INDEX else FINAL_CHUNK_SIZE
        
        buf[6] = (offset >> 8) & 0xFF   # Offset high
        buf[7] = offset & 0xFF           # Offset low
        buf[8] = (length >> 8) & 0xFF   # Length high
        buf[9] = length & 0xFF           # Length low
        
        # Copy pixel data
        start = index * DATA_SIZE
        buf[10:10+length] = rgb565[start:start+length]
        
        device.write(buf)
        print(f"Chunk {index+1}/27 sent")
        await asyncio.sleep(0.005)

    print("✅ Welcome displayed")
    await asyncio.sleep(2)
    
    # Clear to black
    black = bytearray(320 * 170 * 2)  # All zeros
    buf = bytearray(REPORT_SIZE + BUFFER_SIZE)
    buf[0] = 0x00
    buf[1] = LCD_SIGNATURE
    buf[2] = LCD_REDRAW
    buf[3] = LCD_REDRAW_START
    buf[4] = 1
    buf[6] = 0
    buf[7] = 0
    buf[8] = 0x10
    buf[9] = 0x00
    buf[10:10+4096] = black[:4096]
    device.write(buf)
    print("Cleared")
    
    device.close()

asyncio.run(send_welcome())