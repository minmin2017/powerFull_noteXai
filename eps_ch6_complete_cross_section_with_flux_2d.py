# -*- coding: utf-8 -*-
"""
eps_ch6_complete_cross_section_with_flux_2d.py — Complete DC Assembly with Magnetic Flux Lines & Distortion
(1080p Full HD @ 25fps)
Scene: CompleteDCAssemblyWithFluxLines
"""

import math
from manim import *
import numpy as np
from mlib import *

class CompleteDCAssemblyWithFluxLines(SafeScene):
    def construct(self):
        t_title = title("แผนผัง 2D สมบูรณ์แบบ: โครงสร้างครบชุด + เส้นแรงแม่เหล็ก & การบิดเบี้ยว")
        fit_width(t_title, 12.2)
        self.play(FadeIn(t_title))

        # Right Summary HUD
        panel = RoundedRectangle(corner_radius=0.18, width=4.6, height=5.6, color="#1E293B", fill_opacity=0.92).move_to([4.7, 0, 0])
        p_head = Text("เส้นแรงแม่เหล็กในเครื่องจักร", font_size=18, color=WHITE).move_to([4.7, 2.3, 0])

        c1 = VGroup(
            Text("1. สนามหลัก Bf (เส้นฟ้า):", font_size=13, color=FIELD),
            Text("พุ่งแนวนอนตรงจาก N ซ้ายไป S ขวา", font_size=11, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.03).move_to([4.7, 1.4, 0])

        c2 = VGroup(
            Text("2. สนามอาร์เมเจอร์ Ba (เส้นส้ม):", font_size=13, color=WARN),
            Text("วนรอบตัวนำในร่องสล็อต (กฎมือขวา)", font_size=11, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.03).move_to([4.7, 0.5, 0])

        c3 = VGroup(
            Text("3. สนามรวมบิดเบี้ยว Btotal (เส้นม่วง):", font_size=13, color=EMF),
            Text("เส้นแรงรวมกันจนบิดเป็นรูปตัว S", font_size=11, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.03).move_to([4.7, -0.4, 0])

        c4 = VGroup(
            Text("4. ระนาบเป็นกลางเลื่อน (MNP):", font_size=13, color="#EC4899"),
            Text("ระนาบเอียงตาม ➔ ต้องย้ายแปรงถ่าน", font_size=11, color=GRAYTXT),
            Text("เพื่อให้อยู่ตรงจุด emf=0V ไร้สปาร์ค!", font_size=11, color="#EC4899")
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.03).move_to([4.7, -1.5, 0])

        hud_grp = VGroup(panel, p_head, c1, c2, c3, c4)
        self.play(FadeIn(hud_grp))

        cx = -2.2
        # 1. Stator Poles (N Left Red, S Right Blue)
        pole_n = ArcPolygon(
            [cx - 2.8, -1.6, 0], [cx - 2.8, 1.6, 0],
            [cx - 2.1, 1.3, 0], [cx - 2.1, -1.3, 0],
            color=RED, fill_color="#991B1B", fill_opacity=0.7
        )
        lbl_n = Text("N", font_size=24, color=WHITE).move_to([cx - 2.5, 0, 0])

        pole_s = ArcPolygon(
            [cx + 2.8, 1.6, 0], [cx + 2.8, -1.6, 0],
            [cx + 2.1, -1.3, 0], [cx + 2.1, 1.3, 0],
            color=BLUE, fill_color="#1E3A8A", fill_opacity=0.7
        )
        lbl_s = Text("S", font_size=24, color=WHITE).move_to([cx + 2.5, 0, 0])

        # 2. Rotor Slotted Core (Outer Grey Ring)
        rotor_outer = Annulus(inner_radius=1.2, outer_radius=1.85, color=METAL, fill_color="#0F172A", fill_opacity=0.9).move_to([cx, 0, 0])

        # 3. Commutator Hub & Segments (Inner Bronze Ring)
        comm_ring = Annulus(inner_radius=0.45, outer_radius=0.85, color="#F59E0B", fill_color="#B45309", fill_opacity=0.9).move_to([cx, 0, 0])
        shaft_dot = Dot([cx, 0, 0], radius=0.25, color=GRAY)
        lbl_shaft = Text("เพลา", font_size=10, color=WHITE).move_to([cx, 0, 0])

        comm_lines = VGroup()
        for deg in [0, 45, 90, 135, 180, 225, 270, 315]:
            rad = math.radians(deg)
            p1 = np.array([cx + 0.45 * math.cos(rad), 0.45 * math.sin(rad), 0])
            p2 = np.array([cx + 0.85 * math.cos(rad), 0.85 * math.sin(rad), 0])
            comm_lines.add(Line(p1, p2, color=BLACK, stroke_width=2))

        # 4. Armature Conductor Coils in Slots + Tap Wires
        num_slots = 8
        coils_grp = VGroup()
        taps_grp = VGroup()

        for i in range(num_slots):
            deg = i * (360.0 / num_slots)
            rad = math.radians(deg)
            r_slot = 1.55
            p_slot = np.array([cx + r_slot * math.cos(rad), r_slot * math.sin(rad), 0])
            p_comm = np.array([cx + 0.85 * math.cos(rad), 0.85 * math.sin(rad), 0])

            is_left = (90 < deg < 270)
            c_color = YELLOW if is_left else WARN
            dot_slot = Circle(radius=0.14, color=c_color, fill_color="#0F172A", fill_opacity=1.0).move_to(p_slot)
            
            if is_left:
                sym = Dot(p_slot, radius=0.04, color=WHITE)
            else:
                sym = VGroup(
                    Line(p_slot + [-0.05, -0.05, 0], p_slot + [0.05, 0.05, 0], color=WHITE, stroke_width=1.5),
                    Line(p_slot + [-0.05, 0.05, 0], p_slot + [0.05, -0.05, 0], color=WHITE, stroke_width=1.5)
                )

            tap_line = Line(p_slot, p_comm, color=YELLOW, stroke_width=2.0)
            coils_grp.add(dot_slot, sym)
            taps_grp.add(tap_line)

        # 5. Carbon Brushes (+) Top, (-) Bottom & External Circuit
        brush_top = Rectangle(width=0.45, height=0.35, color=WHITE, fill_color="#334155", fill_opacity=0.95).move_to([cx, 1.05, 0])
        lbl_bt = Text("(+)", font_size=11, color=WHITE).move_to(brush_top.get_center())

        brush_bot = Rectangle(width=0.45, height=0.35, color=WHITE, fill_color="#334155", fill_opacity=0.95).move_to([cx, -1.05, 0])
        lbl_bb = Text("(-)", font_size=11, color=WHITE).move_to(brush_bot.get_center())

        self.play(
            Create(pole_n), FadeIn(lbl_n),
            Create(pole_s), FadeIn(lbl_s),
            Create(rotor_outer),
            Create(comm_ring), Create(comm_lines), FadeIn(shaft_dot), FadeIn(lbl_shaft),
            Create(coils_grp), Create(taps_grp),
            FadeIn(brush_top), FadeIn(lbl_bt),
            FadeIn(brush_bot), FadeIn(lbl_bb)
        )
        self.wait(1.5)

        # -------------------------------------------------------------
        # STEP 1: Main Magnetic Field (Bf - Cyan Horizontal Lines)
        # -------------------------------------------------------------
        main_flux = VGroup()
        for y_pos in [-1.0, -0.5, 0.0, 0.5, 1.0]:
            arrow_f = Arrow(start=[cx - 2.1, y_pos, 0], end=[cx + 2.1, y_pos, 0], color=FIELD, stroke_width=2.5, buff=0)
            main_flux.add(arrow_f)

        cap1 = caption("1. เส้นแรงสนามหลัก Bf (สีฟ้า): พุ่งข้ามจากขั้ว N ไปยังขั้ว S ในแนวนอนตรงๆ")
        self.play(Create(main_flux), FadeIn(cap1))
        self.wait(2.0)

        # -------------------------------------------------------------
        # STEP 2: Armature Flux Loops (Ba - Orange Circles around conductors)
        # -------------------------------------------------------------
        arm_loops = VGroup()
        for deg in [45, 135, 225, 315]:
            rad = math.radians(deg)
            p_center = np.array([cx + 1.55 * math.cos(rad), 1.55 * math.sin(rad), 0])
            c_loop = Circle(radius=0.4, color=WARN, stroke_width=2.5).move_to(p_center)
            arm_loops.add(c_loop)

        cap2 = caption("2. เส้นแรงสนามอาร์เมเจอร์ Ba (วงกลมสีส้ม): กระแสในขดลวดสร้างฟลักซ์หมุนวนรอบตัวนำ")
        self.play(FadeOut(cap1), Create(arm_loops), FadeIn(cap2))
        self.wait(2.0)

        # -------------------------------------------------------------
        # STEP 3: Combined Distorted Flux (Btotal S-curves) + Shifted Neutral Plane
        # -------------------------------------------------------------
        distorted_flux = VGroup()
        for y_pos in [-1.0, -0.5, 0.0, 0.5, 1.0]:
            p_start = np.array([cx - 2.1, y_pos + 0.35, 0])
            p_end = np.array([cx + 2.1, y_pos - 0.35, 0])
            curve = CubicBezier(p_start, p_start + [0.8, -0.3, 0], p_end + [-0.8, 0.3, 0], p_end, color=EMF, stroke_width=3.2)
            distorted_flux.add(curve)

        tilt_rad = math.radians(20)
        mnp_line = DashedLine([cx - 2.2 * math.sin(tilt_rad), -2.2 * math.cos(tilt_rad), 0], [cx + 2.2 * math.sin(tilt_rad), 2.2 * math.cos(tilt_rad), 0], color="#EC4899", stroke_width=3)
        lbl_mnp = Text("ระนาบเป็นกลางใหม่ (MNP)", font_size=13, color="#EC4899").move_to([cx + 0.9, 2.3, 0])

        cap3 = caption("3. เส้นแรงรวมบิดเบี้ยว Btotal (สีม่วง): เส้นแรง 2 สนามรวมกัน ➔ บิดเบี้ยวเป็นรูปตัว S และระนาบเป็นกลางเลื่อนตาม!")
        self.play(
            FadeOut(cap2),
            FadeOut(main_flux),
            FadeOut(arm_loops),
            Create(distorted_flux),
            Create(mnp_line), FadeIn(lbl_mnp),
            FadeIn(cap3)
        )
        self.wait(3.5)
