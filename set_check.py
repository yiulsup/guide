import usb.core
import usb.util
import time

# ========================
# Endpoint 설정 도우미
# ========================
def get_ep(interface, addr):
    return usb.util.find_descriptor(interface, custom_match=lambda e: e.bEndpointAddress == addr)

# ========================
# USB 장치 연결
# ========================
dev = usb.core.find(idVendor=0x04b4, idProduct=0xf7f7)
if dev is None:
    raise ValueError("❌ USB 장치를 찾을 수 없습니다.")

if dev.is_kernel_driver_active(0):
    dev.detach_kernel_driver(0)

dev.set_configuration()
dev.set_interface_altsetting(interface=0, alternate_setting=0)
cfg = dev.get_active_configuration()
intf = cfg[(0, 0)]

ep_out = get_ep(intf, 0x02)   # 명령 전송
ep_in  = get_ep(intf, 0x83)   # 응답 수신

# ========================
# Digital Video Page Query 명령
# ========================
query_cmd = [0x55, 0xAA, 0x07, 0x02, 0x01, 0x80,
             0x00, 0x00, 0x00, 0x00, 0x84, 0xF0]  # XOR = 0x84

print("📤 명령 전송 중...")
dev.write(ep_out.bEndpointAddress, query_cmd)
time.sleep(0.05)  # 응답 대기

# ========================
# 응답 1: ACK 확인
# ========================
try:
    ack = dev.read(ep_in.bEndpointAddress, 6, timeout=500)
    if ack[:6].tolist() == [0x55, 0xAA, 0x01, 0x00, 0x01, 0xF0]:
        print("✅ ACK 수신 완료:", list(ack))
    else:
        print("⚠️ 예상치 못한 ACK:", list(ack))
except usb.core.USBError as e:
    print("❌ ACK 수신 실패:", e)

# ========================
# 응답 2: 설정 정보 수신
# ========================
while True:
    try:
        response = dev.read(ep_in.bEndpointAddress, 24, timeout=1000)
        print("✅ 설정 정보 수신 완료:", list(response))

        if response[0] == 0x55 and response[1] == 0xAA and response[3] == 0x02 and response[4] == 0x01:
            sync_mode    = response[5]
            output_port  = response[6]
            video_format = response[7]
            cmos_mode    = response[8]
            frame_rate   = response[9]
            clock_edge   = response[11]

            # 설명 매핑
            sync_modes = ["Shutdown", "Slave", "Master"]
            port_types = [
                "Parallel Closed", "USB2.0", "CMOS", "BT1120", "BT656",
                "USB2.0+UART", "LCD", "LVDS", "LCD+DVP", "UVC+CDC"
            ]
            format_types = [
                "YUV422", "YUV422+Param", "Y16", "Y16+Param", "Y16+YUV422",
                "Y16+Param+YUV422", "", "", "TMP", "TMP+Param", "TMP+YUV422", "TMP+Param+YUV422"
            ]
            cmos_types = ["CMOS16", "CMOS8(MSB)", "CMOS8(LSB)"]
            frame_rates = ["30Hz", "25Hz", "9Hz", "50Hz"]
            clock_edges = ["Rising Edge", "Falling Edge"]

            print("🔍 현재 디지털 비디오 설정:")
            print(f"  📡 External Sync Mode : {sync_mode} ({sync_modes[sync_mode] if sync_mode < len(sync_modes) else 'Unknown'})")
            print(f"  🔌 Output Port        : {output_port} ({port_types[output_port] if output_port < len(port_types) else 'Unknown'})")
            print(f"  🎥 Video Format       : {video_format} ({format_types[video_format] if video_format < len(format_types) else 'Unknown'})")
            print(f"  🧠 CMOS Mode          : {cmos_mode} ({cmos_types[cmos_mode] if cmos_mode < len(cmos_types) else 'Unknown'})")
            print(f"  ⏱ Frame Rate         : {frame_rate} ({frame_rates[frame_rate] if frame_rate < len(frame_rates) else 'Unknown'})")
            print(f"  ⏰ Clock Edge         : {clock_edge} ({clock_edges[clock_edge] if clock_edge < len(clock_edges) else 'Unknown'})")

        else:
            print("⚠️ 응답 포맷이 예상과 다릅니다.")

    except usb.core.USBError as e:
        print(f"❌ 설정 정보 수신 실패: {e}")
