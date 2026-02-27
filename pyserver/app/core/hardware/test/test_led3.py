#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, '.')

from app.core.hardware.lcd import LCDDevice
from PIL import Image, ImageDraw

async def debug():
    lcd = LCDDevice()
    lcd.open()
    
    print(f"is_open: {lcd.is_open}")
    print(f"device: {lcd.device}")
    
    # Test heartbeat
    print("Sending heartbeat...")
    await lcd.heartbeat()
    print("Heartbeat done")
    
    # Create simple image
    canvas = Image.new("RGB", (320, 170), "black")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([50, 50, 270, 120], fill="blue")
    draw.text((100, 80), "TEST", fill="white")
    
    raw = canvas.tobytes()
    print(f"Raw bytes: {len(raw)}")
    
    # Check what _convert_rgba_to_rgb565 produces
    rgb565 = lcd._convert_rgba_to_rgb565(raw)
    print(f"RGB565 bytes: {len(rgb565)} (expected 108800)")
    
    print("Sending redraw...")
    await lcd.redraw(raw)
    print("Redraw done")
    
    await asyncio.sleep(2)
    lcd.close()

asyncio.run(debug())