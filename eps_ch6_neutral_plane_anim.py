# -*- coding: utf-8 -*-
"""
eps_ch6_neutral_plane_anim.py — Manim 3D Teaching Animation for EPS Chapter 6
Scenes:
1. DCMachineComponents3D (3D Exploded / Assembled View of Stator, Armature, Commutator, Brushes)
2. NeutralPlane3DView (3D View of Neutral Plane MNP, 3D Coil Rotation & Faraday Induction)
"""

import sys
import os
import math
from manim import *
import numpy as np

from mlib import *

class DCMachineComponents3D(SafeThreeDScene):
    def construct(self):
        # 1. 3D Camera Setup
        self.set_camera_orientation(phi=65 * DEGREES, theta=-55 * DEGREES)

        # 2. HUD Header & Info
        t_title = title("โครงสร้าง 3 มิติ: ชิ้นส่วนหลักของเครื่องกลไฟฟ้ากระแสตรง (DC Machine)")
        self.hud(t_title)
        self.play(FadeIn(t_title))

        hud_panel = RoundedRectangle(corner_radius=0.18, width=4.5, height=5.5, color="#1E293B", fill_opacity=0.92).move_to([4.8, 0, 0])
        hud_head = Text("4 ชิ้นส่วนหัวใจสำคัญ", font_size=18, color=WHITE).move_to([4.8, 2.3, 0])

        c1 = VGroup(
            Text("1. สเตเตอร์ (Stator):", font_size=14, color=METAL),
            Text("โครงและขั้วแม่เหล็ก N-S อยู่กับที่", font_size=12, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.8, 1.4, 0])

        c2 = VGroup(
            Text("2. อาร์เมเจอร์ (Armature):", font_size=14, color=WARN),
            Text("แกนเหล็ก & ขดลวดหมุนตัดสนาม", font_size=12, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.8, 0.4, 0])

        c3 = VGroup(
            Text("3. คอมมิวเตเตอร์ (Commutator):", font_size=14, color="#F59E0B"),
            Text("ซี่ทองแดงหมุนสลับขั้วแปลง AC->DC", font_size=12, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.8, -0.6, 0])

        c4 = VGroup(
            Text("4. แปรงถ่าน (Brushes):", font_size=14, color=WHITE),
            Text("แท่งคาร์บอนรับไฟส่งออกสู่โหลด", font_size=12, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.8, -1.6, 0])

        hud_grp = VGroup(hud_panel, hud_head, c1, c2, c3, c4)
        self.hud(hud_grp)
        self.play(FadeIn(hud_grp))

        cx, cy, cz = -1.8, 0.0, 0.0

        # 3. Component 1: Stator (Outer Frame & N-S Poles)
        stator_yoke = Cylinder(radius=2.4, height=2.2, direction=[0, 0, 1], color=METAL).move_to([cx, cy, cz]).set_opacity(0.25)
        pole_n = Prism(dimensions=[0.8, 1.8, 2.0]).move_to([cx - 2.0, cy, cz]).set_color(RED).set_opacity(0.85)
        pole_s = Prism(dimensions=[0.8, 1.8, 2.0]).move_to([cx + 2.0, cy, cz]).set_color(BLUE).set_opacity(0.85)

        lbl_n = Text("ขั้ว N (Stator)", font_size=16, color=WHITE).move_to([cx - 2.0, cy, cz + 1.3])
        lbl_s = Text("ขั้ว S (Stator)", font_size=16, color=WHITE).move_to([cx + 2.0, cy, cz + 1.3])
        self.world_text(lbl_n, lbl_s)

        cap = caption("1. สเตเตอร์ (Stator) คือส่วนที่อยู่กับที่ ทำหน้าที่สร้างสนามแม่เหล็กหลัก N-S")
        self.hud(cap)
        self.play(FadeIn(stator_yoke), FadeIn(pole_n), FadeIn(pole_s), FadeIn(lbl_n), FadeIn(lbl_s), FadeIn(cap))
        self.wait(1.5)

        # 4. Component 2: Armature Rotor Core along Z-axis
        armature_core = Cylinder(radius=1.3, height=1.8, direction=[0, 0, 1], color=WARN).move_to([cx, cy, cz]).set_opacity(0.6)
        shaft = Cylinder(radius=0.15, height=3.4, direction=[0, 0, 1], color=GRAY).move_to([cx, cy, cz])

        lbl_arm = Text("แกนอาร์เมเจอร์", font_size=15, color=WARN).move_to([cx, cy + 1.6, cz])
        self.world_text(lbl_arm)

        self.play(
            FadeOut(cap),
            FadeIn(armature_core),
            FadeIn(shaft),
            FadeIn(lbl_arm)
        )
        cap2 = caption("2. อาร์เมเจอร์ (Armature) คือส่วนที่หมุน มีขดลวดเหนี่ยวนำแรงดันไฟฟ้า")
        self.hud(cap2)
        self.play(FadeIn(cap2))
        self.wait(1.5)

        # 5. Component 3: Commutator (on the shaft in front)
        commutator = Cylinder(radius=0.45, height=0.6, direction=[0, 0, 1], color="#F59E0B").move_to([cx, cy, cz + 1.2])
        lbl_comm = Text("คอมมิวเตเตอร์", font_size=14, color="#F59E0B").move_to([cx, cy - 0.7, cz + 1.2])
        self.world_text(lbl_comm)

        self.play(
            FadeOut(cap2),
            FadeIn(commutator),
            FadeIn(lbl_comm)
        )
        cap3 = caption("3. คอมมิวเตเตอร์ (Commutator) หมุนไปพร้อมเพลา แปลงกระแสสลับ AC ให้เป็น DC")
        self.hud(cap3)
        self.play(FadeIn(cap3))
        self.wait(1.5)

        # 6. Component 4: Carbon Brushes (Pressing top and bottom on commutator)
        brush_top = Prism(dimensions=[0.25, 0.35, 0.3]).move_to([cx, cy + 0.55, cz + 1.2]).set_color(WHITE).set_opacity(0.95)
        brush_bot = Prism(dimensions=[0.25, 0.35, 0.3]).move_to([cx, cy - 0.55, cz + 1.2]).set_color(WHITE).set_opacity(0.95)
        lbl_br = Text("แปรงถ่าน (Brushes)", font_size=14, color=WHITE).move_to([cx + 0.9, cy + 0.55, cz + 1.2])
        self.world_text(lbl_br)

        self.play(
            FadeOut(cap3),
            FadeIn(brush_top),
            FadeIn(brush_bot),
            FadeIn(lbl_br)
        )
        cap4 = caption("4. แปรงถ่าน (Brushes) อยู่กับที่ กดแนบกับคอมมิวเตเตอร์ที่ระนาบเป็นกลางเพื่อรับไฟออก")
        self.hud(cap4)
        self.play(FadeIn(cap4))

        # Rotate camera for full 3D assembly perspective
        self.play(
            self.camera.animate.set_euler_angles(phi=70 * DEGREES, theta=-20 * DEGREES),
            run_time=4.0
        )
        self.wait(2.0)


class NeutralPlane3DView(SafeThreeDScene):
    def construct(self):
        # 1. 3D Camera Setup
        self.set_camera_orientation(phi=65 * DEGREES, theta=-55 * DEGREES)

        # 2. HUD Elements (Fixed on screen)
        t_title = title("มุมมอง 3D: ระนาบเป็นกลาง (Neutral Plane) & การตัดเส้นแรงแม่เหล็ก")
        self.hud(t_title)
        self.play(FadeIn(t_title))

        hud_panel = RoundedRectangle(corner_radius=0.18, width=4.4, height=5.4, color="#1E293B", fill_opacity=0.92).move_to([4.8, 0, 0])
        hud_head = Text("การเหนี่ยวนำแรงดัน (EMF)", font_size=18, color=WHITE).move_to([4.8, 2.2, 0])
        hud_form = MathTex(r"e = B \cdot l \cdot v \cdot \sin(	heta)", font_size=23, color=CURRENT).next_to(hud_head, DOWN, buff=0.15)

        hud_c1 = VGroup(
            Text("• ระนาบเป็นกลาง (MNP):", font_size=14, color=OK),
            Text("ขดลวดอยู่บน-ล่าง ขนานกับสนาม B", font_size=13, color=GRAYTXT),
            MathTex(r"	heta = 0^\circ \;ightarrow\; e = 0 	ext{ V}", font_size=17, color=OK)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.06).move_to([4.8, 0.5, 0])

        hud_c2 = VGroup(
            Text("• ระนาบตัดเต็มที่ (90°):", font_size=14, color=EMF),
            Text("ขดลวดอยู่ซ้าย-ขวา ตั้งฉากกับ B", font_size=13, color=GRAYTXT),
            MathTex(r"	heta = 90^\circ \;ightarrow\; e = 	ext{Max}", font_size=17, color=EMF)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.06).move_to([4.8, -1.3, 0])

        hud_grp = VGroup(hud_panel, hud_head, hud_form, hud_c1, hud_c2)
        self.hud(hud_grp)
        self.play(FadeIn(hud_grp))

        cx, cy, cz = -1.8, 0.0, 0.0

        # 3. 3D Magnetic Poles
        pole_n = Prism(dimensions=[1.2, 3.2, 2.5]).move_to([cx - 3.0, cy, cz]).set_color(RED).set_opacity(0.85)
        pole_s = Prism(dimensions=[1.2, 3.2, 2.5]).move_to([cx + 3.0, cy, cz]).set_color(BLUE).set_opacity(0.85)

        lbl_n_txt = Text("ขั้ว N", font_size=20, color=WHITE).move_to([cx - 3.0, cy, cz + 1.4])
        lbl_s_txt = Text("ขั้ว S", font_size=20, color=WHITE).move_to([cx + 3.0, cy, cz + 1.4])
        self.world_text(lbl_n_txt, lbl_s_txt)

        self.play(FadeIn(pole_n), FadeIn(pole_s), FadeIn(lbl_n_txt), FadeIn(lbl_s_txt))

        # 4. 3D Magnetic Flux Lines
        flux_lines = VGroup()
        for y_off in [-1.0, 0.0, 1.0]:
            for z_off in [-0.8, 0.0, 0.8]:
                p_start = np.array([cx - 2.3, cy + y_off, cz + z_off])
                p_end = np.array([cx + 2.3, cy + y_off, cz + z_off])
                l = Line(p_start, p_end, color=FIELD, stroke_width=2.5).set_opacity(0.6)
                flux_lines.add(l)

        self.play(Create(flux_lines))

        # 5. 3D Neutral Plane (Translucent Green Sheet on Y-Z plane at x = cx)
        np_plane = Polygon(
            [cx, cy - 1.8, cz - 1.4],
            [cx, cy + 1.8, cz - 1.4],
            [cx, cy + 1.8, cz + 1.4],
            [cx, cy - 1.8, cz + 1.4],
            color=OK,
            fill_color=OK,
            fill_opacity=0.3,
            stroke_width=2
        )
        lbl_np_3d = Text("ระนาบเป็นกลาง (MNP)", font_size=15, color=OK).move_to([cx, cy + 2.1, cz])
        self.world_text(lbl_np_3d)

        self.play(FadeIn(np_plane), FadeIn(lbl_np_3d))

        # 6. Central Rotor Shaft along Z axis
        shaft = Cylinder(radius=0.15, height=3.0, direction=[0, 0, 1], color=METAL).move_to([cx, cy, cz])
        self.play(FadeIn(shaft))

        # 7. 3D Rotating Armature Coil
        r = 1.3
        L = 2.0

        def make_coil(angle_rad):
            cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
            p1_front = np.array([cx + r * cos_a, cy + r * sin_a, cz + L/2])
            p1_back = np.array([cx + r * cos_a, cy + r * sin_a, cz - L/2])
            p2_back = np.array([cx - r * cos_a, cy - r * sin_a, cz - L/2])
            p2_front = np.array([cx - r * cos_a, cy - r * sin_a, cz + L/2])

            loop = Polygon(p1_front, p1_back, p2_back, p2_front, color=WARN, stroke_width=4, fill_opacity=0.0)
            dot1 = Dot3D(point=p1_front, radius=0.08, color=YELLOW)
            dot2 = Dot3D(point=p2_front, radius=0.08, color=YELLOW)
            return VGroup(loop, dot1, dot2)

        coil = make_coil(0)
        self.play(Create(coil))

        cap = caption("เมื่อขดลวดหมุนถึงระนาบเป็นกลาง (MNP) ตัวนำจะวิ่งขนานเส้นแรง B ทำให้ EMF = 0")
        self.hud(cap)
        self.play(FadeIn(cap))

        coil_vertical = make_coil(PI / 2)
        self.play(
            Transform(coil, coil_vertical),
            self.camera.animate.set_euler_angles(phi=60 * DEGREES, theta=-25 * DEGREES),
            run_time=3.5
        )
        self.wait(2.0)

        coil_full = make_coil(5 * PI / 2)
        self.play(
            Transform(coil, coil_full),
            self.camera.animate.set_euler_angles(phi=70 * DEGREES, theta=-65 * DEGREES),
            run_time=4.0
        )
        self.wait(3.0)
