import usb.core
import usb.util
import numpy as np
import cv2
import time

# 장치 찾기
dev = usb.core.find(idVendor=0x04b4, idProduct=0xf7f7)
if dev is None:
    raise ValueError("Mini212G2 device failed to open.")

# 커널 드라이버 분리 및 설정
if dev.is_kernel_driver_active(0):
    dev.detach_kernel_driver(0)
dev.set_configuration()

# Endpoint 설정
cfg = dev.get_active_configuration()
intf = cfg[(0, 0)]
ep = usb.util.find_descriptor(
    intf,
    custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
)

# 해상도 및 프레임 크기 설정
width, height = 256, 192
frame_size = width * height * 2  # Y16 = 2 bytes/pixel
line_offset = 140  # ImageJ로 확인된 wrap 시작 라인

print("📡 Thermal camera streaming started... Press 'q' to quit, 'c' to capture")

while True:
    try:
        # 프레임 수신
        data = dev.read(ep.bEndpointAddress, frame_size, timeout=1000)
        if len(data) != frame_size:
            continue

        # Y16 데이터 → np.uint16로 변환 및 리쉐이프
        raw_frame = np.frombuffer(data, dtype=np.uint16).reshape((height, width))

        # 💡 라인 wrap-around 보정 (138번째 줄부터 시작된 프레임을 원래 순서로 정렬)
        raw_frame = np.vstack((raw_frame[line_offset:], raw_frame[:line_offset]))

        # 정규화 후 8비트 변환
        raw_8bit = cv2.normalize(raw_frame, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        color_frame = cv2.applyColorMap(raw_8bit, cv2.COLORMAP_HOT)

        # 영상 표시
        cv2.imshow("Thermal RAW (Fixed)", color_frame)
        key = cv2.waitKey(1)

        if key == ord('c'):
            cv2.imwrite("captured_fixed.png", color_frame)
            print("📸 Image saved as 'captured_fixed.png'")

        elif key == ord('q'):
            print("🛑 Exiting...")
            break

    except usb.core.USBError as e:
        print("USB Error:", e)
        continue

# 종료 처리
usb.util.dispose_resources(dev)
cv2.destroyAllWindows()
