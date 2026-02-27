#!/usr/bin/env python3
import hid
import time

d = hid.device()
d.open(1241, 64769)
print("Opened HID device")

# Fill screen with RED (RGB565: 0xF800)
buffer = bytearray(4105)  # REPORT_SIZE(1) + BUFFER_SIZE(4104)
buffer[0] = 0x00  # Report ID
buffer[1] = 0x55  # Signature
buffer[2] = 0xA3  # REDRAW command
buffer[3] = 0xF0  # START
buffer[4] = 1     # Sequence
buffer[6] = 0     # Offset high
buffer[7] = 0     # Offset low  
buffer[8] = 0x10  # Length high (4096)
buffer[9] = 0x00  # Length low

# Fill data with red (0xF8, 0x00 repeated)
for i in range(4096):
    buffer[10 + i] = 0xF8 if i % 2 == 0 else 0x00

print("Sending RED...")
d.write(buffer)
time.sleep(2)

# Send BLACK (all zeros)
buffer2 = bytearray(4105)
buffer2[0] = 0x00
buffer2[1] = 0x55
buffer2[2] = 0xA3
buffer2[3] = 0xF0
buffer2[4] = 1
buffer2[6] = 0
buffer2[7] = 0
buffer2[8] = 0x10
buffer2[9] = 0x00
# rest is already 0 = black

print("Sending BLACK...")
d.write(buffer2)

d.close()
print("Done")