import subprocess
import os

raw_video = r"D:\unity_project\delta_academy\Recordings\C_HardwareIntro_RAW_v4_25690914_204049.mp4"
output_video = r"D:\unity_project\delta_academy\Recordings\FINAL_DELIVERABLES\C_HardwareIntro_TITLED.mp4"
font = "C\\:/Windows/Fonts/leelawdb.ttf"
font_regular = "C\\:/Windows/Fonts/leelawad.ttf"

filters = [
    # Shot 0: DELTA AUTOMATION STACK
    f"drawtext=fontfile='{font}':text='DELTA AUTOMATION STACK':enable='between(t,0.5,4.5)':fontcolor=white:fontsize=32:x=60:y=h-130:box=1:boxcolor=black@0.65:boxborderw=10",
    f"drawtext=fontfile='{font_regular}':text='Hardware Architecture & Control Infrastructure':enable='between(t,0.5,4.5)':fontcolor=#00D8FF:fontsize=22:x=60:y=h-80:box=1:boxcolor=black@0.65:boxborderw=8",

    # Shot 1: PLC
    f"drawtext=fontfile='{font}':text='PLC — DELTA AS320T-B':enable='between(t,5.0,13.5)':fontcolor=white:fontsize=32:x=60:y=h-130:box=1:boxcolor=black@0.65:boxborderw=10",
    f"drawtext=fontfile='{font_regular}':text='Recipe Controller · 5-Parameter Table · High-Speed Counter':enable='between(t,5.0,13.5)':fontcolor=#00D8FF:fontsize=22:x=60:y=h-80:box=1:boxcolor=black@0.65:boxborderw=8",

    # Shot 2: HMI (Updated to DOP-107WV)
    f"drawtext=fontfile='{font}':text='HMI — DELTA DOP-107WV (หรือ DOP-103WQ)':enable='between(t,14.0,22.5)':fontcolor=white:fontsize=32:x=60:y=h-130:box=1:boxcolor=black@0.65:boxborderw=10",
    f"drawtext=fontfile='{font_regular}':text='One-Touch Changeover · จอ 7\" Widescreen · CIP Verification Checklist':enable='between(t,14.0,22.5)':fontcolor=#00D8FF:fontsize=22:x=60:y=h-80:box=1:boxcolor=black@0.65:boxborderw=8",

    # Shot 3: VFD in cabinet -> Conveyor Motor on machine
    f"drawtext=fontfile='{font}':text='VFD — DELTA MS300 (ในตู้ควบคุม)':enable='between(t,23.0,27.5)':fontcolor=white:fontsize=32:x=60:y=h-130:box=1:boxcolor=black@0.65:boxborderw=10",
    f"drawtext=fontfile='{font_regular}':text='อินเวอร์เตอร์ควบคุมความเร็วสายพาน · S-Curve Anti-Tipping Ramp':enable='between(t,23.0,27.5)':fontcolor=#00D8FF:fontsize=22:x=60:y=h-80:box=1:boxcolor=black@0.65:boxborderw=8",
    f"drawtext=fontfile='{font}':text='CONVEYOR DRIVE MOTOR — มอเตอร์เกียร์ต้นกำลัง':enable='between(t,27.5,31.5)':fontcolor=white:fontsize=32:x=60:y=h-130:box=1:boxcolor=black@0.65:boxborderw=10",
    f"drawtext=fontfile='{font_regular}':text='ติดตั้งที่ปลายสายพาน รับคำสั่งความเร็วจาก MS300 เพื่อขับเคลื่อนสายพานลำเลียง':enable='between(t,27.5,31.5)':fontcolor=#00D8FF:fontsize=22:x=60:y=h-80:box=1:boxcolor=black@0.65:boxborderw=8",

    # Shot 4: SERVO DRIVES in cabinet -> SERVO MOTORS on machine
    f"drawtext=fontfile='{font}':text='SERVO DRIVES — DELTA ASD-A3 (ในตู้ควบคุม)':enable='between(t,32.0,37.0)':fontcolor=white:fontsize=32:x=60:y=h-130:box=1:boxcolor=black@0.65:boxborderw=10",
    f"drawtext=fontfile='{font_regular}':text='ไดรฟ์ควบคุม 2 ชุด รับคำสั่งพัลส์จาก PLC จ่ายกำลังไฟขับมอเตอร์':enable='between(t,32.0,37.0)':fontcolor=#00D8FF:fontsize=22:x=60:y=h-80:box=1:boxcolor=black@0.65:boxborderw=8",
    f"drawtext=fontfile='{font}':text='SERVO MOTORS — DELTA ECMA SERIES (ต้นกำลังบนเครื่อง)':enable='between(t,37.0,42.5)':fontcolor=white:fontsize=32:x=60:y=h-130:box=1:boxcolor=black@0.65:boxborderw=10",
    f"drawtext=fontfile='{font_regular}':text='แกน X\\: มอเตอร์ขับ Lead Screw ปรับราง · แกน Z\\: มอเตอร์ขับ Ball Screw หัวจ่ายเติม':enable='between(t,37.0,42.5)':fontcolor=#00D8FF:fontsize=22:x=60:y=h-80:box=1:boxcolor=black@0.65:boxborderw=8",

    # Shot 5: Closing
    f"drawtext=fontfile='{font}':text='DELTA AUTOMATION ECOSYSTEM':enable='between(t,43.0,49.5)':fontcolor=white:fontsize=32:x=60:y=h-130:box=1:boxcolor=black@0.65:boxborderw=10",
    f"drawtext=fontfile='{font_regular}':text='Integrated Motion & Control · Zero-Downtime Architecture':enable='between(t,43.0,49.5)':fontcolor=#00D8FF:fontsize=22:x=60:y=h-80:box=1:boxcolor=black@0.65:boxborderw=8"
]

vf_chain = ",".join(filters)

cmd = [
    "ffmpeg", "-y",
    "-i", raw_video,
    "-vf", vf_chain,
    "-c:v", "libx264", "-crf", "18", "-preset", "fast",
    "-pix_fmt", "yuv420p",
    output_video
]

print("Running FFmpeg text overlay...")
subprocess.run(cmd, check=True)
print("Finished:", output_video)
