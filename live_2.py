import usb.core
import usb.util
import numpy as np
import cv2
import time

# 장치 찾기
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

# 해상도 및 설정
width, height = 256, 192
frame_size = width * height * 2
split_line = 20  # 줄 기준

# 이전 프레임 저장용
prev_bottom = None
<<<<<<< HEAD
cnt = 0
print("📡 Streaming... Press 'q' to quit, 'c' to capture")
=======

print("📡 Streaming... Press 'q' to quit, 'c' to capture")
cnt = 80
>>>>>>> facc6f2 (first)
while True:
    try:
        # 프레임 수신
        data = dev.read(ep.bEndpointAddress, frame_size, timeout=1000)
        if len(data) != frame_size:
            continue

        frame = np.frombuffer(data, dtype=np.uint16).reshape((height, width))

        if prev_bottom is None:
            # 처음 프레임은 일부만 보관, 사용하지 않음
            prev_bottom = frame[split_line:]
            continue

        # 현재 프레임에서 상단 부분 추출
        current_top = frame[:split_line]

        # 보정된 전체 프레임 조합
        corrected_frame = np.vstack((prev_bottom, current_top))

        # 다음 반복을 위해 하단 보관
        prev_bottom = frame[split_line:]

        # 정규화 후 컬러맵 적용
        raw_8bit = cv2.normalize(corrected_frame, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        #color_frame = cv2.applyColorMap(raw_8bit, cv2.COLORMAP_HOT)

        # 표시
        cv2.imshow("Thermal RAW (Reassembled)", raw_8bit)
        key = cv2.waitKey(1)

        if key == ord('c'):
            cv2.imwrite(f"./data/captured_{cnt}.png", raw_8bit)
            cnt += 1
            print("📸 Image saved as 'captured_cnt.png'")
        elif key == ord('q'):
            print("🛑 Exiting...")
            break

    except usb.core.USBError as e:
        print("USB Error:", e)
        continue

# 종료 처리
usb.util.dispose_resources(dev)
cv2.destroyAllWindows()
