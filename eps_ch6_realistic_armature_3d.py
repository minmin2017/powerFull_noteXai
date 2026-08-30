# -*- coding: utf-8 -*-
"""
eps_ch6_realistic_armature_3d.py — Realistic 3D Sculpted Armature Windings & Commutation (1080p)
Pages 6 to 9 of EPS Chapter 6
Scenes:
1. RealisticArmatureWinding3D (True 3D Coils wound around Rotor Core connected to Commutator)
2. CommutationCurrentSplit3D (Pages 7-8: Current path 50A/50A -> 100A through Brushes & Neutral Plane)
"""

import math
from manim import *
import numpy as np
from mlib import *

class RealisticArmatureWinding3D(SafeThreeDScene):
    """ฉากที่ 1: ปั้นโมเดล 3D ขดลวดอาร์เมเจอร์ของจริงที่พันรอบแกนเหล็กและเชื่อมเข้าคอมมิวเตเตอร์"""
    def construct(self):
        self.set_camera_orientation(phi=65 * DEGREES, theta=-55 * DEGREES)

        t_title = title("โมเดล 3D แท้: ขดลวดอาร์เมเจอร์พันรอบแกนเหล็ก & เชื่อมคอมมิวเตเตอร์ (หน้า 6-8)")
        self.hud(t_title)
        self.play(FadeIn(t_title))

        # HUD Panel on Right
        hud_p = RoundedRectangle(corner_radius=0.18, width=4.6, height=5.6, color="#1E293B", fill_opacity=0.92).move_to([4.7, 0, 0])
        hud_h = Text("โครงสร้างขดลวด 3D", font_size=18, color=WHITE).move_to([4.7, 2.3, 0])

        c1 = VGroup(
            Text("1. ขดลวดอาร์เมเจอร์ 3D:", font_size=14, color=WARN),
            Text("ขดลวดทองแดงร้อยผ่านร่องสล็อต", font_size=12, color=GRAYTXT),
            Text("พันรอบแกนเหล็กเป็นวงรอบปิด", font_size=12, color=WARN)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.7, 1.3, 0])

        c2 = VGroup(
            Text("2. จุดเชื่อมต่อ (Tap Wires):", font_size=14, color=YELLOW),
            Text("ปลายขดลวดแต่ละชุดดึงออกมา", font_size=12, color=GRAYTXT),
            Text("บัดกรีเชื่อมเข้าซี่คอมมิวเตเตอร์", font_size=12, color=YELLOW)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.7, 0.2, 0])

        c3 = VGroup(
            Text("3. รูปเส้นโค้งย้วยๆ ในหนังสือ:", font_size=14, color=OK),
            Text("คือภาพ 2D คลี่ของขดลวดชุดนี้!", font_size=12, color=GRAYTXT),
            Text("เพื่อให้เห็นกระแสแบ่ง 2 สาย 50A+50A", font_size=12, color=OK)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.7, -1.0, 0])

        c4 = VGroup(
            Text("4. แปรงถ่าน (Brushes):", font_size=14, color=WHITE),
            Text("กดรับกระแสรวม 100A ที่ระนาบ MNP", font_size=12, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.7, -2.0, 0])

        hud_grp = VGroup(hud_p, hud_h, c1, c2, c3, c4)
        self.hud(hud_grp)
        self.play(FadeIn(hud_grp))

        cx, cy, cz = -1.8, 0.0, 0.0

        # Stator Poles (N on Left Red, S on Right Blue)
        pole_n = Prism(dimensions=[1.0, 3.2, 2.6]).move_to([cx - 3.2, cy, cz]).set_color(RED).set_opacity(0.85)
        pole_s = Prism(dimensions=[1.0, 3.2, 2.6]).move_to([cx + 3.2, cy, cz]).set_color(BLUE).set_opacity(0.85)
        lbl_n = Text("N (Stator)", font_size=16, color=WHITE).move_to([cx - 3.2, cy, cz + 1.6])
        lbl_s = Text("S (Stator)", font_size=16, color=WHITE).move_to([cx + 3.2, cy, cz + 1.6])
        self.world_text(lbl_n, lbl_s)

        self.play(FadeIn(pole_n), FadeIn(pole_s), FadeIn(lbl_n), FadeIn(lbl_s))

        # Rotor Cylinder
        rotor_core = Cylinder(radius=1.5, height=2.2, direction=[0, 0, 1], color=METAL).move_to([cx, cy, cz]).set_opacity(0.5)
        shaft = Cylinder(radius=0.15, height=4.2, direction=[0, 0, 1], color=GRAY).move_to([cx, cy, cz])
        self.play(FadeIn(rotor_core), FadeIn(shaft))

        # Commutator Segments in front (+z direction)
        comm_z = cz + 1.4
        comm_hub = Cylinder(radius=0.55, height=0.6, direction=[0, 0, 1], color="#B45309").move_to([cx, cy, comm_z])
        self.play(FadeIn(comm_hub))

        # 3D Sculpted Copper Coils (12 winding loops around the rotor body)
        num_coils = 12
        windings = VGroup()
        tap_wires = VGroup()

        for i in range(num_coils):
            ang = i * (2 * PI / num_coils)
            r_out = 1.55
            # Outer conductor rod along rotor slot
            p_back = np.array([cx + r_out * math.cos(ang), cy + r_out * math.sin(ang), cz - 1.1])
            p_front = np.array([cx + r_out * math.cos(ang), cy + r_out * math.sin(ang), cz + 1.1])
            rod = Line(p_back, p_front, color=WARN, stroke_width=4.5)
            
            # Back end-turn connection (arch)
            ang_next = (i + num_coils // 2) * (2 * PI / num_coils)
            p_back_next = np.array([cx + r_out * math.cos(ang_next), cy + r_out * math.sin(ang_next), cz - 1.1])
            arch_back = Line(p_back, p_back_next, color="#D97706", stroke_width=3)
            
            # Front tap wire to commutator segment
            p_comm = np.array([cx + 0.55 * math.cos(ang), cy + 0.55 * math.sin(ang), comm_z])
            tap = Line(p_front, p_comm, color=YELLOW, stroke_width=3)

            windings.add(rod, arch_back)
            tap_wires.add(tap)

        cap1 = caption("1. ขดลวดอาร์เมเจอร์ 3D แท้: ร้อยผ่านร่องสล็อตและต่อปลายเข้าซี่คอมมิวเตเตอร์")
        self.hud(cap1)
        self.play(Create(windings), Create(tap_wires), FadeIn(cap1))
        self.wait(2.0)

        # Brushes (Top Brush + at Neutral Plane, Bottom Brush -)
        brush_top = Prism(dimensions=[0.3, 0.4, 0.4]).move_to([cx, cy + 0.7, comm_z]).set_color(WHITE).set_opacity(0.95)
        brush_bot = Prism(dimensions=[0.3, 0.4, 0.4]).move_to([cx, cy - 0.7, comm_z]).set_color(WHITE).set_opacity(0.95)
        lbl_bp = Text("แปรงถ่าน (+)", font_size=13, color=WHITE).move_to([cx + 0.9, cy + 0.7, comm_z])
        lbl_bm = Text("แปรงถ่าน (-)", font_size=13, color=WHITE).move_to([cx + 0.9, cy - 0.7, comm_z])
        self.world_text(lbl_bp, lbl_bm)

        cap2 = caption("2. แปรงถ่าน (+) และ (-) สัมผัสที่คอมมิวเตเตอร์ตรงระนาบเป็นกลาง เพื่อรับกระแสรวมออกสู่วงจร")
        self.hud(cap2)
        self.play(
            FadeOut(cap1),
            FadeIn(brush_top), FadeIn(brush_bot),
            FadeIn(lbl_bp), FadeIn(lbl_bm),
            FadeIn(cap2)
        )
        self.wait(1.5)

        # 3D Camera Sweep to inspect all angles in high detail
        self.move_camera(phi=75 * DEGREES, theta=-15 * DEGREES, run_time=3.5)
        self.wait(1.5)
        self.move_camera(phi=60 * DEGREES, theta=-85 * DEGREES, run_time=3.5)
        self.wait(2.5)


class CommutationCurrentSplit3D(SafeScene):
    """ฉากที่ 2: อธิบายรูปที่ 6-4 และ 6-5 (การแบ่งกระแส 50A + 50A = 100A และการกลับทิศทางในขดลวด)"""
    def construct(self):
        t_title = title("กลไกคอมมิวเตชั่น: กระแสแบ่ง 2 วงจรขนาน 50A + 50A ➔ 100A (หน้า 8-9)")
        self.play(FadeIn(t_title))

        panel = RoundedRectangle(corner_radius=0.18, width=4.6, height=5.6, color="#1E293B", fill_opacity=0.92).move_to([4.7, 0, 0])
        p_head = Text("หลักการคอมมิวเตชั่น", font_size=18, color=WHITE).move_to([4.7, 2.3, 0])

        c1 = VGroup(
            Text("1. กระแสแบ่ง 2 สาย (50A + 50A):", font_size=14, color=FIELD),
            Text("ขดลวดซีกซ้ายจ่าย 50A ขึ้นบน", font_size=12, color=GRAYTXT),
            Text("ขดลวดซีกขวาจ่าย 50A ขึ้นบน", font_size=12, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.7, 1.3, 0])

        c2 = VGroup(
            Text("2. รวมที่แปรงถ่าน (+):", font_size=14, color=EMF),
            MathTex(r"I_{\text{load}} = 50\text{A} + 50\text{A} = 100\text{A}", font_size=18, color=EMF),
            Text("ส่งกระแสตรง 100A ออกสู่โหลด", font_size=12, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.7, 0.2, 0])

        c3 = VGroup(
            Text("3. การส่งไม้ผลัด (Commutation):", font_size=14, color=WARN),
            Text("ขด B ถูกลัดวงจรชั่วขณะ", font_size=12, color=GRAYTXT),
            Text("กระแสในขด B ต้องกลับทิศจาก +50 ➔ -50A", font_size=12, color=WARN)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.7, -0.9, 0])

        c4 = VGroup(
            Text("4. กฎเลนซ์สร้าง Self-induced emf:", font_size=14, color=RED),
            Text("ขดลวดต้านการเปลี่ยนกระแส ➔ สปาร์ค!", font_size=12, color=RED)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05).move_to([4.7, -1.9, 0])

        self.play(FadeIn(panel), FadeIn(p_head), FadeIn(c1), FadeIn(c2), FadeIn(c3), FadeIn(c4))

        cx = -2.2
        # Ring Core
        ring = Annulus(inner_radius=1.2, outer_radius=1.7, color=METAL, fill_color="#0F172A", fill_opacity=0.9).move_to([cx, 0, 0])
        self.play(Create(ring))

        # Current arrows on left and right branches
        arr_left = Arrow(start=[cx - 1.45, -1.2, 0], end=[cx - 1.45, 1.2, 0], color=FIELD, stroke_width=4)
        lbl_left = Text("50 A (ซีกซ้าย)", font_size=13, color=FIELD).next_to(arr_left, LEFT, buff=0.1)

        arr_right = Arrow(start=[cx + 1.45, -1.2, 0], end=[cx + 1.45, 1.2, 0], color=FIELD, stroke_width=4)
        lbl_right = Text("50 A (ซีกขวา)", font_size=13, color=FIELD).next_to(arr_right, RIGHT, buff=0.1)

        # Top brush output
        arr_top_out = Arrow(start=[cx, 1.8, 0], end=[cx, 2.8, 0], color=EMF, stroke_width=5)
        lbl_top_out = Text("100 A ออกสู่โหลด", font_size=15, color=EMF).next_to(arr_top_out, UP, buff=0.1)

        # Bottom brush input
        arr_bot_in = Arrow(start=[cx, -2.8, 0], end=[cx, -1.8, 0], color=EMF, stroke_width=5)
        lbl_bot_in = Text("100 A ไหลกลับ", font_size=15, color=EMF).next_to(arr_bot_in, DOWN, buff=0.1)

        cap = caption("ขดลวดอาร์เมเจอร์แบ่งเป็น 2 วงจรขนาน: 50A ซ้าย + 50A ขวา รวมกันที่แปรงถ่านเป็น 100A")
        self.play(
            Create(arr_left), FadeIn(lbl_left),
            Create(arr_right), FadeIn(lbl_right),
            Create(arr_top_out), FadeIn(lbl_top_out),
            Create(arr_bot_in), FadeIn(lbl_bot_in),
            FadeIn(cap)
        )
        self.wait(3.5)
