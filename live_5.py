import usb.core
import usb.util
import numpy as np
import cv2

# 초기값
split_line = 140
resize_dims = None  # (width, height)
colormap_mode = 0   # 0=gray

print(f"📌 Starting with split_line: {split_line}")

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

# 이전 프레임 저장용
prev_bottom = None

print("📡 Streaming... Press 'q' to quit, 'c' to capture, 's' to set split_line, 'r' to resize, 'm' to change colormap")
cnt = 0
while True:
    try:
        # 프레임 수신
        data = dev.read(ep.bEndpointAddress, frame_size, timeout=1000)
        if len(data) != frame_size:
            continue

        frame = np.frombuffer(data, dtype=np.uint16).reshape((height, width))

        if prev_bottom is None:
            prev_bottom = frame[split_line:]
            continue

        current_top = frame[:split_line]
        corrected_frame = np.vstack((prev_bottom, current_top))
        prev_bottom = frame[split_line:]

        # 정규화
        raw_8bit = cv2.normalize(corrected_frame, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        # 컬러맵
        if colormap_mode == 1:
            display_frame = cv2.applyColorMap(raw_8bit, cv2.COLORMAP_HOT)
        elif colormap_mode == 2:
            display_frame = cv2.applyColorMap(raw_8bit, cv2.COLORMAP_JET)
        elif colormap_mode == 3:
            display_frame = cv2.applyColorMap(raw_8bit, cv2.COLORMAP_INFERNO)
        elif colormap_mode == 4:
            display_frame = cv2.applyColorMap(raw_8bit, cv2.COLORMAP_OCEAN)
        elif colormap_mode == 5:
            display_frame = cv2.applyColorMap(raw_8bit, cv2.COLORMAP_SPRING)
        elif colormap_mode == 6:
            display_frame = cv2.applyColorMap(raw_8bit, cv2.COLORMAP_SUMMER)
        elif colormap_mode == 7:
            display_frame = cv2.applyColorMap(raw_8bit, cv2.COLORMAP_AUTUMN)
        elif colormap_mode == 8:
            display_frame = cv2.applyColorMap(raw_8bit, cv2.COLORMAP_WINTER)
        elif colormap_mode == 9:
            display_frame = cv2.applyColorMap(raw_8bit, cv2.COLORMAP_RAINBOW)
        elif colormap_mode == 10:
            display_frame = cv2.applyColorMap(raw_8bit, cv2.COLORMAP_BONE)
        elif colormap_mode == 11:
            display_frame = cv2.applyColorMap(raw_8bit, cv2.COLORMAP_PINK)
        else:
            display_frame = cv2.cvtColor(raw_8bit, cv2.COLOR_GRAY2BGR)

        # 리사이즈
        if resize_dims is not None:
            display_frame = cv2.resize(display_frame, resize_dims, interpolation=cv2.INTER_NEAREST)

        # 표시
        cv2.imshow("Thermal Camera", display_frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('c'):
            cv2.imwrite(f"./data/captured_{cnt}.png", display_frame)
            cnt += 1
            print(f"📸 Image saved as 'captured_{cnt}.png'")

        elif key == ord('s'):
            try:
                new_split = int(input("🔧 Enter new split_line: "))
                if 0 < new_split < height:
                    split_line = new_split
                    print(f"✅ Updated split_line to: {split_line}")
                else:
                    print("⚠️ Invalid split_line. Must be between 1 and height.")
            except ValueError:
                print("⚠️ Invalid input. Please enter an integer.")

        elif key == ord('r'):
            try:
                dims_input = input("🔧 Enter resize width height (example: 640 480), or 0 0 to reset: ")
                w, h = map(int, dims_input.strip().split())
                if w > 0 and h > 0:
                    resize_dims = (w, h)
                    print(f"✅ Resize set to: {resize_dims}")
                else:
                    resize_dims = None
                    print("🔄 Resize reset to original size.")
            except ValueError:
                print("⚠️ Invalid input. Please enter two integers like '640 480'.")

        elif key == ord('m'):
            try:
                new_map = int(input(
                    "🎨 Enter colormap (0=GRAY, 1=HOT, 2=JET, 3=INFERNO, 4=OCEAN, 5=SPRING, "
                    "6=SUMMER, 7=AUTUMN, 8=WINTER, 9=RAINBOW, 10=BONE, 11=PINK): "
                ))
                if new_map in list(range(0,12)):
                    colormap_mode = new_map
                    print(f"✅ Colormap mode set to: {colormap_mode}")
                else:
                    print("⚠️ Invalid colormap. Use 0-11.")
            except ValueError:
                print("⚠️ Invalid input. Please enter an integer.")

        elif key == ord('q'):
            print("🛑 Exiting...")
            break

    except usb.core.USBError as e:
        print("USB Error:", e)
        continue

usb.util.dispose_resources(dev)
cv2.destroyAllWindows()
