import usb.core
import usb.util
import time
import numpy as np
import cv2

# XOR 계산 함수
def calc_xor(data):
    xor = 0
    for b in data:
        xor ^= b
    return xor

# 명령 전송 함수
def send_full_command(dev, ep_out, full_command):
    dev.write(ep_out.bEndpointAddress, full_command)

# ACK 수신 함수
def wait_for_ack(ep_ack_in):
    try:
        response = ep_ack_in.read(8, timeout=500)
        if response[:6].tolist() == [0x55, 0xAA, 0x01, 0x00, 0x01, 0xF0]:
            print("✅ ACK received")
            return True
        else:
            print("❓ Unexpected response:", list(response[:6]))
            return False
    except usb.core.USBError as e:
        print(f"⚠️ ACK read error: {e}")
        return False

# 장치 찾기
dev = usb.core.find(idVendor=0x04b4, idProduct=0xf7f7)
if dev is None:
    raise ValueError("❌ Device not found")

if dev.is_kernel_driver_active(0):
    dev.detach_kernel_driver(0)

dev.set_configuration()
dev.set_interface_altsetting(interface=0, alternate_setting=0)

cfg = dev.get_active_configuration()
intf = cfg[(0, 0)]

# Endpoint 지정
def get_ep(addr):
    return usb.util.find_descriptor(intf, custom_match=lambda e: e.bEndpointAddress == addr)

ep_image_in = get_ep(0x81)     # EP1: 영상 수신
ep_out = get_ep(0x02)          # EP2: 명령 전송
ep_ack_in = get_ep(0x83)       # EP3: ACK 수신

if not (ep_image_in and ep_out and ep_ack_in):
    raise RuntimeError("❌ Endpoint 설정 실패")

# 명령 전송: 55 AA 07 02 01 03 00 00 00 02 05 F0
# 이 명령은 이미 XOR 계산이 포함되어 있음 (0x05)
full_command = [0x55, 0xAA, 0x07, 0x02, 0x01, 0x03,
                0x00, 0x00, 0x00, 0x02, 0x05, 0xF0]
send_full_command(dev, ep_out, full_command)

# ACK 수신 확인
if not wait_for_ack(ep_ack_in):
    raise RuntimeError("❌ ACK 수신 실패")

input()
# 영상 수신 루프 시작
width, height = 256, 192
frame_size = width * height * 2  # Y16

print("📡 Thermal stream 시작. 'q' 키를 눌러 종료하세요.")

while True:
    try:
        data = dev.read(0x81, frame_size, timeout=2000)

        if len(data) != frame_size:
            print(f"⚠️ Incomplete frame: {len(data)} bytes")
            continue

        raw_frame = np.frombuffer(data, dtype=np.uint16).reshape((height, width))
        raw_8bit = cv2.normalize(raw_frame, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        color_frame = cv2.applyColorMap(raw_8bit, cv2.COLORMAP_HOT)
        resized = cv2.resize(color_frame, (640, 480))
        cv2.imshow("Thermal Camera", resized)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    except usb.core.USBError as e:
        print("❗ USB Error:", e)
        continue

cv2.destroyAllWindows()
