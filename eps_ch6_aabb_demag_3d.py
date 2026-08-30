# -*- coding: utf-8 -*-
"""
eps_ch6_aabb_demag_3d.py — True 3D Visualization of AA (Cross) vs BB (Demagnetizing) Conductors
Pages 5 to 7 of EPS Chapter 6 (1080p Full HD)
"""

import math
from manim import *
import numpy as np
from mlib import *

class AABBConductors3D(SafeThreeDScene):
    """โมเดล 3D แสดงการแบ่งกลุ่มตัวนำ AA (สนามขวาง) vs BB (สนามต่อต้าน) และการเอียงใน 3 มิติ"""
    def construct(self):
        self.set_camera_orientation(phi=65 * DEGREES, theta=-50 * DEGREES)

        t_title = title("มุมมอง 3D แท้: การแบ่งแกนตัวนำ AA (สนามขวาง) vs BB (สนามต่อต้าน) (หน้า 5-7)")
        self.hud(t_title)
        self.play(FadeIn(t_title))

        # HUD Summary Panel on Right
        hud_p = RoundedRectangle(corner_radius=0.18, width=4.6, height=5.6, color="#1E293B", fill_opacity=0.92).move_to([4.7, 0, 0])
        hud_h = Text("การแยกผลเสีย 2 ส่วน", font_size=18, color=WHITE).move_to([4.7, 2.3, 0])

        c1 = VGroup(
            Text("1. ตัวนำกลุ่ม AA (สีส้ม):", font_size=14, color=WARN),
            Text("อยู่ใต้ขั้ว N และ S", font_size=12, color=GRAYTXT),
            Text("➔ สร้างสนามขวาง 90° (สนามบิดเบี้ยว)", font_size=12, color=WARN)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.7, 1.3, 0])

        c2 = VGroup(
            Text("2. ตัวนำกลุ่ม BB (สีแดง):", font_size=14, color=RED),
            Text("อยู่ในมุมเลื่อน 2α ระหว่างขั้ว", font_size=12, color=GRAYTXT),
            Text("➔ สร้างสนามสวนทิศต้านสนามหลัก", font_size=12, color=RED)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.7, 0.2, 0])

        c3 = VGroup(
            Text("3. ผลลัพธ์ต่อเครื่องกำเนิด:", font_size=14, color=EMF),
            Text("• กลุ่ม AA ➔ เกิดสปาร์คที่แปรงถ่าน", font_size=12, color=GRAYTXT),
            Text("• กลุ่ม BB ➔ แรงดันขั้วลดลง (V drop)", font_size=12, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.7, -1.0, 0])

        c4 = VGroup(
            Text("4. ทิศทางการหมุน 3D:", font_size=14, color=YELLOW),
            Text("มุม 2α กวาดตามเข็มนาฬิกา", font_size=12, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.7, -2.0, 0])

        hud_grp = VGroup(hud_p, hud_h, c1, c2, c3, c4)
        self.hud(hud_grp)
        self.play(FadeIn(hud_grp))

        cx, cy, cz = -1.8, 0.0, 0.0

        # Stator Poles
        pole_n = Prism(dimensions=[1.0, 3.2, 2.5]).move_to([cx - 3.2, cy, cz]).set_color(RED).set_opacity(0.85)
        pole_s = Prism(dimensions=[1.0, 3.2, 2.5]).move_to([cx + 3.2, cy, cz]).set_color(BLUE).set_opacity(0.85)
        lbl_n = Text("ขั้ว N (Stator)", font_size=16, color=WHITE).move_to([cx - 3.2, cy, cz + 1.6])
        lbl_s = Text("ขั้ว S (Stator)", font_size=16, color=WHITE).move_to([cx + 3.2, cy, cz + 1.6])
        self.world_text(lbl_n, lbl_s)

        self.play(FadeIn(pole_n), FadeIn(pole_s), FadeIn(lbl_n), FadeIn(lbl_s))

        # Rotor Cylinder
        rotor = Cylinder(radius=1.5, height=2.2, direction=[0, 0, 1], color=METAL).move_to([cx, cy, cz]).set_opacity(0.45)
        shaft = Cylinder(radius=0.15, height=4.0, direction=[0, 0, 1], color=GRAY).move_to([cx, cy, cz])
        self.play(FadeIn(rotor), FadeIn(shaft))

        # 3D Conductors: Divided into Group AA (Orange) and Group BB (Red)
        num_slots = 16
        alpha_deg = 22.5  # shift angle
        coils_aa = VGroup()
        coils_bb = VGroup()

        for i in range(num_slots):
            deg = i * (360.0 / num_slots)
            rad = math.radians(deg)
            x_c = cx + 1.52 * math.cos(rad)
            y_c = cy + 1.52 * math.sin(rad)

            # Determine if this conductor belongs to BB (demagnetizing sector near neutral planes: within +/- 2*alpha)
            is_bb = False
            # Top neutral zone (around 90 deg + alpha) and Bottom neutral zone (around 270 deg + alpha)
            if (65 <= deg <= 115) or (245 <= deg <= 295):
                is_bb = True

            rod = Cylinder(radius=0.08, height=2.2, direction=[0, 0, 1], color=RED if is_bb else WARN).move_to([x_c, y_c, cz])
            if is_bb:
                coils_bb.add(rod)
            else:
                coils_aa.add(rod)

        cap1 = caption("1. ตัวนำกลุ่ม AA (สีส้ม): อยู่ใต้ขั้ว N-S สร้างสนามแม่เหล็กขวาง (Cross-magnetizing)")
        self.hud(cap1)
        self.play(Create(coils_aa), FadeIn(cap1))
        self.wait(2.0)

        # Show Cross-magnetizing 3D Flux (Vertical Arrow)
        vec_cross = Arrow3D(start=[cx, cy + 1.4, cz], end=[cx, cy - 1.4, cz], color=WARN)
        lbl_vec_cross = Text("สนามขวาง AA", font_size=13, color=WARN).move_to([cx + 0.9, cy, cz])
        self.world_text(lbl_vec_cross)
        self.play(Create(vec_cross), FadeIn(lbl_vec_cross))
        self.wait(1.5)

        cap2 = caption("2. ตัวนำกลุ่ม BB (สีแดง): อยู่ในมุม 2α ระหว่างช่องขั้ว สร้างสนามต่อต้าน (Demagnetizing)")
        self.hud(cap2)
        self.play(
            FadeOut(cap1),
            Create(coils_bb),
            FadeIn(cap2)
        )
        self.wait(2.0)

        # Show Demagnetizing 3D Flux (Horizontal arrow pointing Left, OPPOSING Main field N->S)
        vec_demag = Arrow3D(start=[cx + 1.4, cy, cz], end=[cx - 1.4, cy, cz], color=RED)
        lbl_vec_demag = Text("สนามต้าน BB (สวนทิศ N->S)", font_size=13, color=RED).move_to([cx, cy - 1.8, cz])
        self.world_text(lbl_vec_demag)
        self.play(Create(vec_demag), FadeIn(lbl_vec_demag))
        self.wait(2.0)

        # 3D Tilt & Sweep Camera to reveal full 3D spatial alignment
        self.move_camera(phi=75 * DEGREES, theta=-15 * DEGREES, run_time=3.5)
        self.wait(1.5)
        self.move_camera(phi=60 * DEGREES, theta=-75 * DEGREES, run_time=3.5)
        self.wait(2.5)
