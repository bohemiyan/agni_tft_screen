import hid

print("Listing HID devices:")
for device in hid.enumerate():
    print(f"VID: {device['vendor_id']} (0x{device['vendor_id']:04x}), PID: {device['product_id']} (0x{device['product_id']:04x}), Path: {device['path']}")
