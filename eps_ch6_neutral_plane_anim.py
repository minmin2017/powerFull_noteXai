# -*- coding: utf-8 -*-
"""
eps_ch6_neutral_plane_anim.py — Manim Teaching Animation for EPS Chapter 6
Scenes:
1. DCMachineComponents3D (3D Exploded / Assembled View of Stator, Armature, Commutator, Brushes)
2. NeutralPlane3DView (3D View of Neutral Plane MNP, 3D Coil Rotation & Faraday Induction)
3. ArmatureReactionDistortion (สนามแม่เหล็ก 2 สนามรวมกัน -> บิดเบี้ยว -> ระนาบเลื่อน หน้า 2-4)
4. MagneticVectorField2D (Vector Field / Calculus of Main Field, Armature Reaction & Distorted Field)
"""

import sys
import os
import math
from manim import *
import numpy as np

from mlib import *

class DCMachineComponents3D(SafeThreeDScene):
    def construct(self):
        self.set_camera_orientation(phi=65 * DEGREES, theta=-55 * DEGREES)

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

        self.move_camera(phi=70 * DEGREES, theta=-20 * DEGREES, run_time=3.5)
        self.wait(2.0)


class NeutralPlane3DView(SafeThreeDScene):
    def construct(self):
        self.set_camera_orientation(phi=65 * DEGREES, theta=-55 * DEGREES)

        t_title = title("มุมมอง 3D: ระนาบเป็นกลาง (Neutral Plane) & การตัดเส้นแรงแม่เหล็ก")
        self.hud(t_title)
        self.play(FadeIn(t_title))

        hud_panel = RoundedRectangle(corner_radius=0.18, width=4.4, height=5.4, color="#1E293B", fill_opacity=0.92).move_to([4.8, 0, 0])
        hud_head = Text("การเหนี่ยวนำแรงดัน (EMF)", font_size=18, color=WHITE).move_to([4.8, 2.2, 0])
        hud_form = MathTex(r"e = B \cdot l \cdot v \cdot \sin(\theta)", font_size=23, color=CURRENT).next_to(hud_head, DOWN, buff=0.15)

        hud_c1 = VGroup(
            Text("• ระนาบเป็นกลาง (MNP):", font_size=14, color=OK),
            Text("ขดลวดอยู่บน-ล่าง ขนานกับสนาม B", font_size=13, color=GRAYTXT),
            MathTex(r"\theta = 0^\circ \;\rightarrow\; e = 0 \text{ V}", font_size=17, color=OK)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.06).move_to([4.8, 0.5, 0])

        hud_c2 = VGroup(
            Text("• ระนาบตัดเต็มที่ (90°):", font_size=14, color=EMF),
            Text("ขดลวดอยู่ซ้าย-ขวา ตั้งฉากกับ B", font_size=13, color=GRAYTXT),
            MathTex(r"\theta = 90^\circ \;\rightarrow\; e = \text{Max}", font_size=17, color=EMF)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.06).move_to([4.8, -1.3, 0])

        hud_grp = VGroup(hud_panel, hud_head, hud_form, hud_c1, hud_c2)
        self.hud(hud_grp)
        self.play(FadeIn(hud_grp))

        cx, cy, cz = -1.8, 0.0, 0.0

        pole_n = Prism(dimensions=[1.2, 3.2, 2.5]).move_to([cx - 3.0, cy, cz]).set_color(RED).set_opacity(0.85)
        pole_s = Prism(dimensions=[1.2, 3.2, 2.5]).move_to([cx + 3.0, cy, cz]).set_color(BLUE).set_opacity(0.85)

        lbl_n_txt = Text("ขั้ว N", font_size=20, color=WHITE).move_to([cx - 3.0, cy, cz + 1.4])
        lbl_s_txt = Text("ขั้ว S", font_size=20, color=WHITE).move_to([cx + 3.0, cy, cz + 1.4])
        self.world_text(lbl_n_txt, lbl_s_txt)

        self.play(FadeIn(pole_n), FadeIn(pole_s), FadeIn(lbl_n_txt), FadeIn(lbl_s_txt))

        flux_lines = VGroup()
        for y_off in [-1.0, 0.0, 1.0]:
            for z_off in [-0.8, 0.0, 0.8]:
                p_start = np.array([cx - 2.3, cy + y_off, cz + z_off])
                p_end = np.array([cx + 2.3, cy + y_off, cz + z_off])
                l = Line(p_start, p_end, color=FIELD, stroke_width=2.5).set_opacity(0.6)
                flux_lines.add(l)

        self.play(Create(flux_lines))

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

        shaft = Cylinder(radius=0.15, height=3.0, direction=[0, 0, 1], color=METAL).move_to([cx, cy, cz])
        self.play(FadeIn(shaft))

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
            run_time=2.5
        )
        self.move_camera(phi=60 * DEGREES, theta=-25 * DEGREES, run_time=2.0)
        self.wait(1.5)

        coil_full = make_coil(5 * PI / 2)
        self.play(
            Transform(coil, coil_full),
            run_time=3.0
        )
        self.move_camera(phi=70 * DEGREES, theta=-65 * DEGREES, run_time=2.5)
        self.wait(2.0)


class ArmatureReactionDistortion(SafeScene):
    """ทำความเข้าใจหน้า 2-4: ทำไมสนามแม่เหล็กถึงบิดเบี้ยวและระนาบเลื่อนตามทิศหมุน"""
    def construct(self):
        t_title = title("อาร์เมเจอร์รีแอคชั่น: สนามแม่เหล็กบิดเบี้ยว & ระนาบเลื่อน (หน้า 2-4)")
        self.play(FadeIn(t_title))

        # Panel on the right
        panel = RoundedRectangle(corner_radius=0.18, width=4.6, height=5.6, color="#1E293B", fill_opacity=0.92).move_to([4.7, 0, 0])
        p_head = Text("ลำดับเหตุผล 4 ขั้น", font_size=18, color=WHITE).move_to([4.7, 2.3, 0])

        s1 = VGroup(
            Text("1. สนามหลัก (Bf):", font_size=14, color=FIELD),
            Text("เกิดจากขั้วหลัก N->S แนวนอน", font_size=12, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.7, 1.4, 0])

        s2 = VGroup(
            Text("2. สนามอาร์เมเจอร์ (Ba):", font_size=14, color=WARN),
            Text("เกิดจากกระแสโหลด Ia ในแนวตั้งฉาก", font_size=12, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.7, 0.4, 0])

        s3 = VGroup(
            Text("3. สนามรวมบิดเบี้ยว (Btotal):", font_size=14, color=EMF),
            Text("เส้นแรงตัดกันไม่ได้ จึงรวมกันเอียงไป", font_size=12, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.7, -0.6, 0])

        s4 = VGroup(
            Text("4. ระนาบเป็นกลางเลื่อน:", font_size=14, color=OK),
            Text("เลื่อนตามทิศทางการหมุนของอาร์เมเจอร์", font_size=12, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.7, -1.6, 0])

        self.play(FadeIn(panel), FadeIn(p_head), FadeIn(s1), FadeIn(s2), FadeIn(s3), FadeIn(s4))

        # Visual Stage on Left (x centered around -2.2)
        cx = -2.2

        # Step 1: Main Field Only (รูป 6-2 ก)
        v_bf = Arrow(start=[cx - 2.2, 0, 0], end=[cx + 1.2, 0, 0], buff=0, color=FIELD, stroke_width=4)
        lbl_bf = MathTex(r"\vec{B}_f \text{ (สนามหลัก)}", color=FIELD, font_size=20).next_to(v_bf, UP, buff=0.1)

        mnp_original = DashedLine(start=[cx - 0.5, -2.4, 0], end=[cx - 0.5, 2.4, 0], color=OK, stroke_width=3)
        lbl_mnp1 = Text("ระนาบเดิม (ตั้งตรง 90°)", font_size=14, color=OK).next_to(mnp_original, UP, buff=0.1)

        cap1 = caption("รูป (ก): มีเฉพาะสนามหลัก Bf -> ระนาบเป็นกลาง MNP ตั้งตรง 90°")
        self.play(Create(v_bf), FadeIn(lbl_bf), Create(mnp_original), FadeIn(lbl_mnp1), FadeIn(cap1))
        self.wait(1.5)

        # Step 2: Armature Cross Field (รูป 6-2 ข)
        v_ba = Arrow(start=[cx - 0.5, 1.6, 0], end=[cx - 0.5, -1.6, 0], buff=0, color=WARN, stroke_width=4)
        lbl_ba = MathTex(r"\vec{B}_a \text{ (สนามอาร์เมเจอร์)}", color=WARN, font_size=20).next_to(v_ba, RIGHT, buff=0.1)

        cap2 = caption("รูป (ข): เมื่อจ่ายโหลด กระแส Ia สร้างสนาม Ba ตั้งฉาก 90° กับสนามหลัก")
        self.play(
            FadeOut(cap1),
            Create(v_ba),
            FadeIn(lbl_ba),
            FadeIn(cap2)
        )
        self.wait(1.5)

        # Step 3: Combined Distorted Field & Neutral Plane Shift (รูป 6-2 ค)
        v_total = Arrow(start=[cx - 2.2, 1.2, 0], end=[cx + 1.2, -1.2, 0], buff=0, color=EMF, stroke_width=5)
        lbl_total = MathTex(r"\vec{B}_{\text{total}} = \vec{B}_f + \vec{B}_a", color=EMF, font_size=22).next_to(v_total, DOWN, buff=0.15)

        mnp_shifted = Line(start=[cx + 0.6, 2.2, 0], end=[cx - 1.6, -2.2, 0], color="#EC4899", stroke_width=3.5)
        lbl_mnp2 = Text("ระนาบใหม่ (เอียงตามทิศหมุน)", font_size=14, color="#EC4899").next_to(mnp_shifted, UP, buff=0.1)

        rot_arrow = CurvedArrow(start_point=[cx - 1.8, 1.8, 0], end_point=[cx + 0.8, 1.8, 0], color=YELLOW)
        lbl_rot = Text("ทิศทางการหมุน", font_size=13, color=YELLOW).next_to(rot_arrow, UP, buff=0.05)

        cap3 = caption("รูป (ค): สนามรวมเอียงไป ทำให้ระนาบเป็นกลางเลื่อนตามทิศการหมุนเสมอ!")
        self.play(
            FadeOut(cap2),
            FadeOut(v_bf), FadeOut(lbl_bf),
            FadeOut(v_ba), FadeOut(lbl_ba),
            Create(v_total), FadeIn(lbl_total),
            Create(mnp_shifted), FadeIn(lbl_mnp2),
            Create(rot_arrow), FadeIn(lbl_rot),
            FadeIn(cap3)
        )
        self.wait(3.0)


class MagneticVectorField2D(SafeScene):
    def construct(self):
        t_title = title("สนามเวกเตอร์แม่เหล็ก (Magnetic Vector Field & StreamLines)")
        self.play(FadeIn(t_title))

        def field_main(p):
            return np.array([1.8, 0.0, 0.0])

        vf_main = ArrowVectorField(
            field_main,
            x_range=[-6.0, 2.0, 1.0],
            y_range=[-2.5, 2.5, 0.8],
            length_func=lambda norm: 0.5,
            colors=[FIELD]
        )

        p_info = RoundedRectangle(corner_radius=0.18, width=4.5, height=5.5, color="#1E293B", fill_opacity=0.92).move_to([4.8, 0, 0])
        p_head = Text("Vector Calculus", font_size=18, color=WHITE).move_to([4.8, 2.3, 0])
        
        eq1 = MathTex(r"\vec{B}_f = B_0 \hat{i}", font_size=24, color=FIELD).move_to([4.8, 1.4, 0])
        eq2 = MathTex(r"\vec{B}_a = -B_a \hat{j}", font_size=24, color=WARN).move_to([4.8, 0.4, 0])
        eq3 = MathTex(r"\vec{B}_{\text{total}} = \vec{B}_f + \vec{B}_a", font_size=22, color=EMF).move_to([4.8, -0.6, 0])
        eq4 = MathTex(r"\alpha = \tan^{-1}\left(\frac{B_a}{B_0}\right)", font_size=22, color=OK).move_to([4.8, -1.6, 0])

        self.play(Create(vf_main), FadeIn(p_info), FadeIn(p_head), Write(eq1), Write(eq2), Write(eq3), Write(eq4))
        
        cap1 = caption("1. สนามแม่เหล็กหลักสม่ำเสมอ พุ่งจากขั้ว N ไปขั้ว S (เวกเตอร์แนวนอน)")
        self.play(FadeIn(cap1))
        self.wait(2.0)

        def field_distorted(p):
            x, y = p[0] + 2.0, p[1]
            r = math.sqrt(x*x + y*y) + 0.1
            bx = 1.8 - 0.4 * y / r
            by = -1.2 + 0.4 * x / r
            return np.array([bx, by, 0.0])

        vf_distorted = ArrowVectorField(
            field_distorted,
            x_range=[-6.0, 2.0, 1.0],
            y_range=[-2.5, 2.5, 0.8],
            length_func=lambda norm: 0.55,
            colors=[WARN, EMF]
        )

        cap2 = caption("2. เมื่อจ่ายโหลด: สนามอาร์เมเจอร์รวมกับสนามหลัก ทำให้เวกเตอร์สนามบิดเบี้ยวเอียงลง")
        self.play(
            FadeOut(cap1),
            Transform(vf_main, vf_distorted),
            FadeIn(cap2)
        )
        self.wait(3.0)
