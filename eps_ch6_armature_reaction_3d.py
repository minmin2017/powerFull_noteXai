# -*- coding: utf-8 -*-
"""
eps_ch6_armature_reaction_3d.py — 3D Armature Reaction & Magnetic Flux Visualization
Pages 2 to 6 of EPS Chapter 6
Scenes:
1. ArmatureCoilsAndSlots3D (3D Rotor with Conductors in Slots & Stator Poles)
2. MagneticFluxDistortion3D (3D Magnetic Fields: Bf, Ba, Btotal and 3D MNP Tilt)
3. CrossAndDemagnetizingAA_BB (Pages 5-6: Conductors AA Cross-magnetize vs BB Demagnetize)
"""

import math
from manim import *
import numpy as np
from mlib import *

class ArmatureCoilsAndSlots3D(SafeThreeDScene):
    """ฉากที่ 1: โครงสร้าง 3D ของขดลวดอาร์เมเจอร์ในร่องสล็อต และขั้วแม่เหล็กสเตเตอร์"""
    def construct(self):
        self.set_camera_orientation(phi=65 * DEGREES, theta=-50 * DEGREES)

        t_title = title("โครงสร้าง 3D: ขดลวดอาร์เมเจอร์ในร่องสล็อต & ขั้วแม่เหล็ก N-S (หน้า 2-4)")
        self.hud(t_title)
        self.play(FadeIn(t_title))

        hud_p = RoundedRectangle(corner_radius=0.18, width=4.5, height=5.5, color="#1E293B", fill_opacity=0.92).move_to([4.8, 0, 0])
        hud_h = Text("ส่วนประกอบ 3 มิติ", font_size=18, color=WHITE).move_to([4.8, 2.3, 0])

        c1 = VGroup(
            Text("1. ขั้วแม่เหล็ก N-S (Stator):", font_size=14, color=FIELD),
            Text("สร้างฟลักซ์หลักแนวนอนคงที่", font_size=12, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.8, 1.4, 0])

        c2 = VGroup(
            Text("2. แกนเหล็กอาร์เมเจอร์:", font_size=14, color=WARN),
            Text("มีร่องสล็อต (Slots) ฝังตัวนำขดลวด", font_size=12, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.8, 0.4, 0])

        c3 = VGroup(
            Text("3. ขดลวดตัวนำ (Conductors):", font_size=14, color=YELLOW),
            Text("ด้านบนจ่ายกระแสออก ด้านล่างรับกระแสเข้า", font_size=12, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.8, -0.6, 0])

        c4 = VGroup(
            Text("4. สนามแม่เหล็กขดลวด:", font_size=14, color=EMF),
            Text("กระแสในขดลวดสร้างสนามวนรอบตัวนำ", font_size=12, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.8, -1.6, 0])

        hud_grp = VGroup(hud_p, hud_h, c1, c2, c3, c4)
        self.hud(hud_grp)
        self.play(FadeIn(hud_grp))

        cx, cy, cz = -1.8, 0.0, 0.0

        # Stator Poles
        pole_n = Prism(dimensions=[1.2, 3.2, 2.4]).move_to([cx - 3.0, cy, cz]).set_color(RED).set_opacity(0.85)
        pole_s = Prism(dimensions=[1.2, 3.2, 2.4]).move_to([cx + 3.0, cy, cz]).set_color(BLUE).set_opacity(0.85)

        lbl_n = Text("ขั้ว N (Stator)", font_size=16, color=WHITE).move_to([cx - 3.0, cy, cz + 1.4])
        lbl_s = Text("ขั้ว S (Stator)", font_size=16, color=WHITE).move_to([cx + 3.0, cy, cz + 1.4])
        self.world_text(lbl_n, lbl_s)

        self.play(FadeIn(pole_n), FadeIn(pole_s), FadeIn(lbl_n), FadeIn(lbl_s))

        # Rotor Core (Cylinder)
        rotor = Cylinder(radius=1.5, height=2.0, direction=[0, 0, 1], color=METAL).move_to([cx, cy, cz]).set_opacity(0.55)
        shaft = Cylinder(radius=0.15, height=3.6, direction=[0, 0, 1], color=GRAY).move_to([cx, cy, cz])
        lbl_rot = Text("แกนเหล็กโรเตอร์", font_size=14, color=METAL).move_to([cx, cy + 1.8, cz])
        self.world_text(lbl_rot)

        self.play(FadeIn(rotor), FadeIn(shaft), FadeIn(lbl_rot))

        # 3D Armature Conductors (Coil rods arranged around rotor surface)
        num_coils = 8
        coils_grp = VGroup()
        for i in range(num_coils):
            angle = i * (2 * PI / num_coils)
            x_pos = cx + 1.45 * math.cos(angle)
            y_pos = cy + 1.45 * math.sin(angle)
            coil_rod = Cylinder(radius=0.09, height=2.1, direction=[0, 0, 1], color=YELLOW).move_to([x_pos, y_pos, cz])
            coils_grp.add(coil_rod)

        cap1 = caption("ตัวนำขดลวดอาร์เมเจอร์ (Armature Conductors) ฝังอยู่ในร่องสล็อตรอบแกนเหล็ก")
        self.hud(cap1)
        self.play(Create(coils_grp), FadeIn(cap1))
        self.wait(1.5)

        # 3D End Turns (Connecting the rods into full coils)
        end_turns = VGroup()
        for i in range(num_coils // 2):
            a1 = i * (2 * PI / num_coils)
            a2 = a1 + PI
            p1_top = np.array([cx + 1.45 * math.cos(a1), cy + 1.45 * math.sin(a1), cz + 1.05])
            p2_top = np.array([cx + 1.45 * math.cos(a2), cy + 1.45 * math.sin(a2), cz + 1.05])
            arch = Line(p1_top, p2_top, color=WARN, stroke_width=3)
            end_turns.add(arch)

        self.play(Create(end_turns))

        # Rotate camera to showcase 3D depth
        self.move_camera(phi=70 * DEGREES, theta=-15 * DEGREES, run_time=3.5)
        self.wait(2.0)


class MagneticFluxDistortion3D(SafeThreeDScene):
    """ฉากที่ 2: การวิ่งของสนาม 3 มิติ: Bf (หลัก) + Ba (ขดลวด) -> รวมเป็น Btotal บิดเบี้ยว"""
    def construct(self):
        self.set_camera_orientation(phi=65 * DEGREES, theta=-55 * DEGREES)

        t_title = title("สนาม 3 มิติ: การรวมตัวของฟลักซ์หลัก & ฟลักซ์อาร์เมเจอร์ (หน้า 3-4)")
        self.hud(t_title)
        self.play(FadeIn(t_title))

        hud_p = RoundedRectangle(corner_radius=0.18, width=4.5, height=5.5, color="#1E293B", fill_opacity=0.92).move_to([4.8, 0, 0])
        hud_h = Text("3 ขั้นตอนการบิดเบี้ยว", font_size=18, color=WHITE).move_to([4.8, 2.3, 0])

        s1 = VGroup(
            Text("1. สนามหลัก Bf (แนวนอน):", font_size=14, color=FIELD),
            Text("พุ่งจาก N ซ้ายไป S ขวาตรงๆ", font_size=12, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.8, 1.4, 0])

        s2 = VGroup(
            Text("2. สนามอาร์เมเจอร์ Ba (แนวดิ่ง):", font_size=14, color=WARN),
            Text("วนรอบตัวนำ เกิดแรงแม่เหล็กขวาง", font_size=12, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.8, 0.4, 0])

        s3 = VGroup(
            Text("3. สนามลัพธ์ Btotal (เอียง):", font_size=14, color=EMF),
            Text("เส้นแรงรวมกันจนบิดเบี้ยวตามทิศหมุน", font_size=12, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.8, -0.6, 0])

        s4 = VGroup(
            Text("4. ระนาบเป็นกลางเลื่อน:", font_size=14, color=OK),
            Text("MNP เอียงทำมุมฉากกับสนามรวมใหม่", font_size=12, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.8, -1.6, 0])

        hud_grp = VGroup(hud_p, hud_h, s1, s2, s3, s4)
        self.hud(hud_grp)
        self.play(FadeIn(hud_grp))

        cx, cy, cz = -1.8, 0.0, 0.0

        # Poles
        pole_n = Prism(dimensions=[1.0, 3.0, 2.2]).move_to([cx - 2.8, cy, cz]).set_color(RED).set_opacity(0.85)
        pole_s = Prism(dimensions=[1.0, 3.0, 2.2]).move_to([cx + 2.8, cy, cz]).set_color(BLUE).set_opacity(0.85)
        rotor = Cylinder(radius=1.3, height=1.8, direction=[0, 0, 1], color=METAL).move_to([cx, cy, cz]).set_opacity(0.4)

        self.play(FadeIn(pole_n), FadeIn(pole_s), FadeIn(rotor))

        # Step 1: Main Flux Lines (Horizontal Straight Lines)
        main_flux = VGroup()
        for y_val in np.linspace(-1.0, 1.0, 5):
            for z_val in np.linspace(-0.6, 0.6, 3):
                l = Line([cx - 2.2, cy + y_val, cz + z_val], [cx + 2.2, cy + y_val, cz + z_val], color=FIELD, stroke_width=2.5).set_opacity(0.7)
                main_flux.add(l)

        plane_orig = Polygon(
            [cx, cy - 1.6, cz - 1.2], [cx, cy + 1.6, cz - 1.2],
            [cx, cy + 1.6, cz + 1.2], [cx, cy - 1.6, cz + 1.2],
            color=OK, fill_color=OK, fill_opacity=0.3, stroke_width=2
        )
        lbl_mnp1 = Text("ระนาบเดิม MNP (90°)", font_size=14, color=OK).move_to([cx, cy + 1.9, cz])
        self.world_text(lbl_mnp1)

        cap1 = caption("ขั้นที่ 1: โนโหลด — มีเฉพาะสนามหลัก Bf วิ่งแนวนอน ➔ ระนาบ MNP ตั้งตรง 90°")
        self.hud(cap1)
        self.play(Create(main_flux), FadeIn(plane_orig), FadeIn(lbl_mnp1), FadeIn(cap1))
        self.wait(2.0)

        # Step 2: 3D Armature Flux Loops (Vertical Cross Field Ba)
        arm_flux = VGroup()
        for rad in [0.7, 1.1]:
            loop_left = Circle(radius=rad, color=WARN, stroke_width=3).rotate(PI/2, axis=RIGHT).move_to([cx - 0.7, cy, cz])
            loop_right = Circle(radius=rad, color=WARN, stroke_width=3).rotate(PI/2, axis=RIGHT).move_to([cx + 0.7, cy, cz])
            arm_flux.add(loop_left, loop_right)

        cap2 = caption("ขั้นที่ 2: จ่ายโหลด — กระแสในขดลวดสร้างสนาม Ba วนรอบตัวนำในแนวตั้งฉาก")
        self.hud(cap2)
        self.play(
            FadeOut(cap1),
            FadeIn(arm_flux),
            FadeIn(cap2)
        )
        self.wait(2.0)

        # Step 3: Combined Distorted 3D Flux & Shifted Neutral Plane
        distorted_flux = VGroup()
        for y_val in np.linspace(-1.0, 1.0, 5):
            for z_val in np.linspace(-0.6, 0.6, 3):
                # S-curve bending
                p_start = np.array([cx - 2.2, cy + y_val + 0.5, cz + z_val])
                p_mid = np.array([cx, cy + y_val, cz + z_val])
                p_end = np.array([cx + 2.2, cy + y_val - 0.5, cz + z_val])
                curve = CubicBezier(p_start, p_start + [0.8, -0.3, 0], p_end + [-0.8, 0.3, 0], p_end, color=EMF, stroke_width=3)
                distorted_flux.add(curve)

        # Shifted Neutral Plane (tilted by 22 degrees)
        angle_tilt = 22 * DEGREES
        plane_shifted = Polygon(
            [cx - 1.6 * math.sin(angle_tilt), cy - 1.6 * math.cos(angle_tilt), cz - 1.2],
            [cx + 1.6 * math.sin(angle_tilt), cy + 1.6 * math.cos(angle_tilt), cz - 1.2],
            [cx + 1.6 * math.sin(angle_tilt), cy + 1.6 * math.cos(angle_tilt), cz + 1.2],
            [cx - 1.6 * math.sin(angle_tilt), cy - 1.6 * math.cos(angle_tilt), cz + 1.2],
            color="#EC4899", fill_color="#EC4899", fill_opacity=0.35, stroke_width=2.5
        )
        lbl_mnp2 = Text("ระนาบใหม่ (เอียงตามทิศหมุน)", font_size=14, color="#EC4899").move_to([cx + 0.8, cy + 1.9, cz])
        self.world_text(lbl_mnp2)

        cap3 = caption("ขั้นที่ 3: เส้นแรงรวมกันตัดกันไม่ได้ ➔ สนามบิดเบี้ยว & ระนาบเป็นกลางเลื่อนตามทิศหมุน!")
        self.hud(cap3)
        self.play(
            FadeOut(cap2),
            FadeOut(main_flux),
            FadeOut(arm_flux),
            FadeOut(plane_orig), FadeOut(lbl_mnp1),
            Create(distorted_flux),
            FadeIn(plane_shifted), FadeIn(lbl_mnp2),
            FadeIn(cap3)
        )

        self.move_camera(phi=70 * DEGREES, theta=-20 * DEGREES, run_time=3.0)
        self.wait(2.5)


class CrossAndDemagnetizingAA_BB(SafeScene):
    """ฉากที่ 3: ทำความเข้าใจหน้า 5-6 (การแบ่งกลุ่มตัวนำ AA ขวางสนาม vs BB ลดทอนสนาม)"""
    def construct(self):
        t_title = title("การแบ่งผลกระทบของอาร์เมเจอร์: แกน AA (บิดเบี้ยว) vs แกน BB (ลดทอน) (หน้า 5-6)")
        self.play(FadeIn(t_title))

        # Panel
        panel = RoundedRectangle(corner_radius=0.18, width=4.6, height=5.6, color="#1E293B", fill_opacity=0.92).move_to([4.7, 0, 0])
        p_head = Text("สรุปแกน AA vs BB", font_size=18, color=WHITE).move_to([4.7, 2.3, 0])

        c1 = VGroup(
            Text("1. ตัวนำแกน AA (Cross):", font_size=14, color=WARN),
            Text("อยู่ใต้ขั้ว N-S สร้างสนามขวาง 90°", font_size=12, color=GRAYTXT),
            Text("➔ ทำให้สนามรวมบิดเบี้ยว (Distortion)", font_size=12, color=WARN)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.7, 1.2, 0])

        c2 = VGroup(
            Text("2. ตัวนำแกน BB (Demag):", font_size=14, color=RED),
            Text("อยู่ระหว่างช่องขั้ว (มุมเลื่อน 2α)", font_size=12, color=GRAYTXT),
            Text("➔ สร้างสนามต้าน/ลดทอนฟลักซ์หลัก", font_size=12, color=RED)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.7, -0.3, 0])

        c3 = VGroup(
            Text("3. ผลลัพธ์สุดท้าย:", font_size=14, color=EMF),
            Text("• เกิดประกายไฟที่แปรงถ่าน (Sparking)", font_size=12, color=GRAYTXT),
            Text("• แรงดันขาออกลดลง (Terminal Volts drop)", font_size=12, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.7, -1.6, 0])

        self.play(FadeIn(panel), FadeIn(p_head), FadeIn(c1), FadeIn(c2), FadeIn(c3))

        cx = -2.2
        # Circle Rotor
        rotor_circle = Circle(radius=1.8, color=METAL, fill_color="#0F172A", fill_opacity=0.9).move_to([cx, 0, 0])
        self.play(Create(rotor_circle))

        # Pole outlines
        pole_left = Rectangle(width=1.2, height=3.0, color=RED, fill_color=RED, fill_opacity=0.3).move_to([cx - 2.5, 0, 0])
        pole_right = Rectangle(width=1.2, height=3.0, color=BLUE, fill_color=BLUE, fill_opacity=0.3).move_to([cx + 2.5, 0, 0])
        lbl_n = Text("N", font_size=24, color=WHITE).move_to([cx - 2.5, 0, 0])
        lbl_s = Text("S", font_size=24, color=WHITE).move_to([cx + 2.5, 0, 0])
        self.play(FadeIn(pole_left), FadeIn(pole_right), FadeIn(lbl_n), FadeIn(lbl_s))

        # Conductors AA (Cross Magnetizing Region)
        aa_dots = VGroup()
        for angle_deg in [60, 75, 90, 105, 120, 240, 255, 270, 285, 300]:
            rad = math.radians(angle_deg)
            dot = Dot(point=[cx + 1.6 * math.cos(rad), 1.6 * math.sin(rad), 0], radius=0.09, color=WARN)
            aa_dots.add(dot)

        lbl_aa = Text("ตัวนำแกน AA (Cross-magnetizing)", font_size=13, color=WARN).move_to([cx, 2.2, 0])

        cap1 = caption("ตัวนำกลุ่ม AA: อยู่ใต้ขั้ว N-S สร้างสนามขวาง 90° ทำให้สนามหลักบิดเบี้ยว")
        self.play(Create(aa_dots), FadeIn(lbl_aa), FadeIn(cap1))
        self.wait(2.0)

        # Conductors BB (Demagnetizing Region in the angle 2*alpha)
        bb_dots = VGroup()
        for angle_deg in [140, 155, 170, 320, 335, 350]:
            rad = math.radians(angle_deg)
            dot = Dot(point=[cx + 1.6 * math.cos(rad), 1.6 * math.sin(rad), 0], radius=0.09, color=RED)
            bb_dots.add(dot)

        lbl_bb = Text("ตัวนำแกน BB (Demagnetizing มุม 2α)", font_size=13, color=RED).move_to([cx, -2.2, 0])

        cap2 = caption("ตัวนำกลุ่ม BB: อยู่ในมุม 2α ระหว่างช่องขั้ว สร้างสนามต้านทำให้ฟลักซ์หลักลดลง!")
        self.play(
            FadeOut(cap1),
            Create(bb_dots),
            FadeIn(lbl_bb),
            FadeIn(cap2)
        )
        self.wait(3.0)
