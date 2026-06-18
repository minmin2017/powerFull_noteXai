"""
AC Motor Predictive-Maintenance Simulation
สร้างข้อมูลเซนเซอร์มอเตอร์ AC จากสภาพ Healthy ไปจนถึง Failed
แกน x = เวลา (ชั่วโมง), แกน y = ค่าเซนเซอร์ (vibration, temperature, current, speed)

ตัวขับการเสื่อม (degradation driver) คือ "bearing wear" ซึ่งเป็นสาเหตุพังอันดับ 1
ของมอเตอร์ AC ในความเป็นจริง — wear โต 0 -> 1 ตามเวลา แล้วไปกระทบเซนเซอร์ทุกตัว
"""

import numpy as np
import pandas as pd

# ---------- พารามิเตอร์มอเตอร์ (ปรับให้ตรงกับมอเตอร์จริงของมินได้) ----------
RATED_SPEED_RPM = 1500.0      # ความเร็วรอบปกติ (motor 4-pole, 50Hz)
RATED_CURRENT_A = 5.0         # กระแสพิกัดปกติ
AMBIENT_TEMP_C = 30.0         # อุณหภูมิห้อง
BASE_VIBRATION_RMS = 0.15     # mm/s, ตอน healthy
T_FAIL_HOURS = 1000.0         # อายุจนพังสนิทใน simulation นี้ (ปรับได้)
SAMPLE_RATE_HOURS = 0.5       # เก็บข้อมูลทุกกี่ชม.
DEGRADATION_EXPONENT = 3.0    # >1 = เสื่อมช้าตอนแรก เร่งไวตอนใกล้พัง (ของจริงเป็นแบบนี้)

# ความถี่ defect ของแบริ่ง (ตัวอย่างค่าทั่วไป หน่วย x เท่าของรอบเพลา)
BPFO_ORDER = 3.5   # Ball Pass Frequency Outer race
BPFI_ORDER = 5.4   # Ball Pass Frequency Inner race

RNG = np.random.default_rng(42)


def wear_curve(t_hours: np.ndarray) -> np.ndarray:
    """0 (healthy) -> 1 (failed) ตามเวลา เร่งความเร็วใกล้จุดพัง"""
    frac = np.clip(t_hours / T_FAIL_HOURS, 0, 1)
    return frac ** DEGRADATION_EXPONENT


def simulate(t_fail_hours: float = T_FAIL_HOURS,
             sample_rate_hours: float = SAMPLE_RATE_HOURS) -> pd.DataFrame:
    t = np.arange(0, t_fail_hours + sample_rate_hours, sample_rate_hours)
    wear = wear_curve(t)

    shaft_hz = RATED_SPEED_RPM / 60.0

    # --- Vibration: baseline + harmonic จาก bearing defect ที่แอมพลิจูดโตตาม wear ---
    defect_amp = wear ** 2 * 4.0  # โตเร็วตอนใกล้พัง (ไม่ใช่เส้นตรง)
    vib_signal = (
        BASE_VIBRATION_RMS
        + defect_amp * np.abs(np.sin(2 * np.pi * BPFO_ORDER * shaft_hz * t / 1000))
        + defect_amp * 0.6 * np.abs(np.sin(2 * np.pi * BPFI_ORDER * shaft_hz * t / 1000))
    )
    vibration_rms = vib_signal + RNG.normal(0, 0.03, size=t.shape)
    vibration_rms = np.clip(vibration_rms, 0, None)

    # --- Temperature: friction ที่แบริ่งสึกทำให้ร้อนขึ้น (ไม่เป็นเส้นตรง, โตไวตอนปลาย) ---
    temperature_c = (
        AMBIENT_TEMP_C
        + 35.0 * wear ** 1.5
        + RNG.normal(0, 0.8, size=t.shape)
    )

    # --- Current: แบริ่งฝืดทำให้มอเตอร์กินกระแสเพิ่ม (overload เพื่อรักษารอบ) ---
    current_a = (
        RATED_CURRENT_A * (1 + 0.4 * wear ** 2)
        + RNG.normal(0, 0.05, size=t.shape)
    )

    # --- Speed: slip เพิ่มขึ้นเมื่อโหลด/แรงเสียดทานเพิ่ม รอบตกเล็กน้อยใกล้พัง ---
    speed_rpm = (
        RATED_SPEED_RPM * (1 - 0.05 * wear ** 2)
        + RNG.normal(0, 2.0, size=t.shape)
    )

    rul_hours = t_fail_hours - t
    label = np.select(
        [wear < 0.3, wear < 0.7, wear < 0.95],
        ["healthy", "degrading", "critical"],
        default="failed",
    )

    return pd.DataFrame({
        "time_hr": t,
        "wear_pct": (wear * 100).round(2),
        "vibration_rms_mm_s": vibration_rms.round(4),
        "temperature_c": temperature_c.round(2),
        "current_a": current_a.round(3),
        "speed_rpm": speed_rpm.round(1),
        "rul_hr": rul_hours.round(1),
        "label": label,
    })


if __name__ == "__main__":
    df = simulate()
    out_path = "ac_motor_sim_data.csv"
    df.to_csv(out_path, index=False)
    print(f"สร้างข้อมูลแล้ว {len(df)} แถว -> {out_path}")
    print(df.iloc[[0, len(df)//4, len(df)//2, -1]])

    # กราฟ time-axis เทียบกับค่าเซนเซอร์ (ถ้ามี matplotlib)
    try:
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(4, 1, figsize=(9, 10), sharex=True)
        axes[0].plot(df.time_hr, df.vibration_rms_mm_s); axes[0].set_ylabel("Vibration (mm/s)")
        axes[1].plot(df.time_hr, df.temperature_c); axes[1].set_ylabel("Temp (°C)")
        axes[2].plot(df.time_hr, df.current_a); axes[2].set_ylabel("Current (A)")
        axes[3].plot(df.time_hr, df.speed_rpm); axes[3].set_ylabel("Speed (RPM)")
        axes[3].set_xlabel("Time (hours)")
        fig.suptitle("AC Motor Degradation Simulation: Healthy -> Failed")
        plt.tight_layout()
        plt.savefig("ac_motor_sim_plot.png", dpi=120)
        print("บันทึกกราฟ -> ac_motor_sim_plot.png")
    except ImportError:
        print("(ไม่มี matplotlib ข้ามการวาดกราฟ — pip install matplotlib ถ้าต้องการ)")
