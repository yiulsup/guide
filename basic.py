import usb.core
import usb.util
import numpy as np
import cv2
import time

dev = usb.core.find(idVendor=0x04b4, idProduct=0xf7f7)
if dev is None:
    raise ValueError("Mini212G2 device failed to open.")

if dev.is_kernel_driver_active(0):
    dev.detach_kernel_driver(0)
dev.set_configuration()

cfg = dev.get_active_configuration()
intf = cfg[(0, 0)]
ep = usb.util.find_descriptor(
    intf,
    custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
)

width, height = 256, 192  
frame_size = width * height * 2 # RAW16 + YUV422
while True:
    try:
        data = dev.read(ep.bEndpointAddress, frame_size, timeout=1000)
        if len(data) != frame_size:
            continue

        print(len(data))
        raw_bytes = data[:width * height * 2]
        #raw_frame = np.frombuffer(raw_bytes, dtype=np.uint16).reshape((height, width))[:192]
        raw_frame = np.frombuffer(raw_bytes, dtype=np.uint16).reshape((height, width))
        raw_8bit = cv2.normalize(raw_frame, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        #raw_colored = cv2.applyColorMap(raw_8bit, cv2.COLORMAP_HOT)
        #raw_colored = cv2.applyColorMap(raw_8bit, cv2.COLORMAP_INFERNO)
        
        cv2.imshow("Thermal RAW", raw_8bit)
        key = cv2.waitKey(1)

        if key == ord('c'):
            cv2.imwrite(f"captured.png", raw_8bit)
         
        if key == ord('q'):
            break
                 
    except usb.core.USBError as e:
        print("USB Error:", e)
        continue

usb.util.dispose_resources(dev)
cv2.destroyAllWindows()
