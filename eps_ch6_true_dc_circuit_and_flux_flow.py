# -*- coding: utf-8 -*-
"""
eps_ch6_true_dc_circuit_and_flux_flow.py — True 2-Pole Closed-Circuit DC Machine with Animated Current Flow & Flux
(1080p Full HD @ 25fps)
Scene: TrueDCCircuitAndFluxFlow
Shows:
1. Exact 1 Pair of Brushes ((+) Top, (-) Bottom)
2. Complete Closed Loop Current Flow: Coils -> Brush(+) -> Load -> Brush(-) -> Coils
3. Dual Magnetic Fields & S-Curve Distortion with Tilted MNP
"""

import math
from manim import *
import numpy as np
from mlib import *

class TrueDCCircuitAndFluxFlow(SafeScene):
    def construct(self):
        t_title = title("วงจรจริง 100%: แปรงถ่าน 1 คู่ (+ / -) & เส้นทางกระแสครบวงจรปิดสู่โหลด")
        fit_width(t_title, 12.2)
        self.play(FadeIn(t_title))

        # Right Summary HUD
        panel = RoundedRectangle(corner_radius=0.18, width=4.6, height=5.6, color="#1E293B", fill_opacity=0.92).move_to([4.7, 0, 0])
        p_head = Text("การไหลของกระแสครบวงจร", font_size=18, color=WHITE).move_to([4.7, 2.3, 0])

        c1 = VGroup(
            Text("1. แปรงถ่านมีเพียง 1 คู่:", font_size=13, color=WHITE),
            Text("• แปรงถ่าน (+) ด้านบน (ส่งกระแสออก)", font_size=11, color=EMF),
            Text("• แปรงถ่าน (-) ด้านล่าง (รับกระแสกลับ)", font_size=11, color=FIELD)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.03).move_to([4.7, 1.4, 0])

        c2 = VGroup(
            Text("2. เส้นทางเดินกระแสภายนอก:", font_size=13, color=YELLOW),
            Text("แปรงถ่าน(+) ➔ วิ่งผ่านสายไฟ ➔ เข้า LOAD", font_size=11, color=GRAYTXT),
            Text("➔ ไหลกลับเข้าสู่ แปรงถ่าน(-) ด้านล่าง", font_size=11, color=YELLOW)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.03).move_to([4.7, 0.4, 0])

        c3 = VGroup(
            Text("3. เส้นทางเดินกระแสภายใน:", font_size=13, color=OK),
            Text("แบ่ง 2 ทางขนาน: ซ้าย 50A + ขวา 50A", font_size=11, color=GRAYTXT),
            Text("ดันกระแสขึ้นบนรวมกันเป็น 100A", font_size=11, color=OK)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.03).move_to([4.7, -0.6, 0])

        c4 = VGroup(
            Text("4. สนามแม่เหล็กรวมบิดเบี้ยว:", font_size=13, color=WARN),
            Text("สนามหลัก + สนามอาร์เมเจอร์ ➔ Btotal", font_size=11, color=GRAYTXT),
            Text("ระนาบ MNP เอียงตาม ➔ ต้องวางแปรงถ่านตรงนี้", font_size=11, color=WARN)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.03).move_to([4.7, -1.6, 0])

        hud_grp = VGroup(panel, p_head, c1, c2, c3, c4)
        self.play(FadeIn(hud_grp))

        cx = -2.2
        # 1. Stator Poles (N Left Red, S Right Blue)
        pole_n = ArcPolygon(
            [cx - 2.8, -1.6, 0], [cx - 2.8, 1.6, 0],
            [cx - 2.1, 1.3, 0], [cx - 2.1, -1.3, 0],
            color=RED, fill_color="#991B1B", fill_opacity=0.7
        )
        lbl_n = Text("ขั้ว N", font_size=20, color=WHITE).move_to([cx - 2.5, 0, 0])

        pole_s = ArcPolygon(
            [cx + 2.8, 1.6, 0], [cx + 2.8, -1.6, 0],
            [cx + 2.1, -1.3, 0], [cx + 2.1, 1.3, 0],
            color=BLUE, fill_color="#1E3A8A", fill_opacity=0.7
        )
        lbl_s = Text("ขั้ว S", font_size=20, color=WHITE).move_to([cx + 2.5, 0, 0])

        # 2. Rotor Core Ring
        rotor_ring = Annulus(inner_radius=1.2, outer_radius=1.85, color=METAL, fill_color="#0F172A", fill_opacity=0.9).move_to([cx, 0, 0])

        # 3. Commutator Hub & Segments around shaft
        comm_hub = Annulus(inner_radius=0.45, outer_radius=0.85, color="#F59E0B", fill_color="#B45309", fill_opacity=0.9).move_to([cx, 0, 0])
        shaft_dot = Dot([cx, 0, 0], radius=0.25, color=GRAY)
        lbl_shaft = Text("เพลา", font_size=10, color=WHITE).move_to([cx, 0, 0])

        # 4. Armature Coils (8 slots) + Tap Wires
        num_slots = 8
        coils_grp = VGroup()
        taps_grp = VGroup()

        for i in range(num_slots):
            deg = i * (360.0 / num_slots)
            rad = math.radians(deg)
            p_slot = np.array([cx + 1.55 * math.cos(rad), 1.55 * math.sin(rad), 0])
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

        # 5. Exactly 1 PAIR of Brushes: Top (+) and Bottom (-)
        brush_top = Rectangle(width=0.45, height=0.35, color=WHITE, fill_color="#334155", fill_opacity=0.95).move_to([cx, 1.05, 0])
        lbl_bt = Text("(+)", font_size=12, color=WHITE).move_to(brush_top.get_center())

        brush_bot = Rectangle(width=0.45, height=0.35, color=WHITE, fill_color="#334155", fill_opacity=0.95).move_to([cx, -1.05, 0])
        lbl_bb = Text("(-)", font_size=12, color=WHITE).move_to(brush_bot.get_center())

        # 6. Complete Closed-Circuit External Wiring + Load Resistor
        wire_top = Line([cx, 1.22, 0], [cx, 2.4, 0], color=EMF, stroke_width=3.5)
        wire_top_right = Line([cx, 2.4, 0], [cx + 3.2, 2.4, 0], color=EMF, stroke_width=3.5)
        wire_load_in = Line([cx + 3.2, 2.4, 0], [cx + 3.2, 0.8, 0], color=EMF, stroke_width=3.5)

        load_box = Rectangle(width=0.9, height=1.6, color=EMF, fill_color="#581C87", fill_opacity=0.85).move_to([cx + 3.2, 0, 0])
        lbl_load = Text("LOAD\n(ภาระ)\n100 A", font_size=12, color=WHITE).move_to(load_box.get_center())

        wire_load_out = Line([cx + 3.2, -0.8, 0], [cx + 3.2, -2.4, 0], color=FIELD, stroke_width=3.5)
        wire_bot_left = Line([cx + 3.2, -2.4, 0], [cx, -2.4, 0], color=FIELD, stroke_width=3.5)
        wire_bot = Line([cx, -2.4, 0], [cx, -1.22, 0], color=FIELD, stroke_width=3.5)

        circuit = VGroup(
            brush_top, lbl_bt, brush_bot, lbl_bb,
            wire_top, wire_top_right, wire_load_in,
            load_box, lbl_load,
            wire_load_out, wire_bot_left, wire_bot
        )

        self.play(
            Create(pole_n), FadeIn(lbl_n),
            Create(pole_s), FadeIn(lbl_s),
            Create(rotor_ring), Create(comm_hub), FadeIn(shaft_dot), FadeIn(lbl_shaft),
            Create(coils_grp), Create(taps_grp),
            FadeIn(circuit)
        )
        self.wait(1.5)

        # -------------------------------------------------------------
        # STEP 1: Animated Current Flow Loop (Dots flowing through full closed circuit)
        # -------------------------------------------------------------
        cap1 = caption("1. กระแสไหลครบวงจรปิด: ขดลวดซ้าย(50A)+ขวา(50A) ➔ แปรงถ่าน(+) ➔ โหลด 100A ➔ ไหลกลับเข้าแปรงถ่าน(-)")
        
        # Flow arrows on external wires
        arr_ext1 = Arrow(start=[cx, 1.4, 0], end=[cx, 2.3, 0], color=EMF, stroke_width=4)
        arr_ext2 = Arrow(start=[cx + 0.5, 2.4, 0], end=[cx + 2.5, 2.4, 0], color=EMF, stroke_width=4)
        arr_ext3 = Arrow(start=[cx + 3.2, 2.0, 0], end=[cx + 3.2, 1.0, 0], color=EMF, stroke_width=4)
        
        arr_ret1 = Arrow(start=[cx + 3.2, -1.0, 0], end=[cx + 3.2, -2.0, 0], color=FIELD, stroke_width=4)
        arr_ret2 = Arrow(start=[cx + 2.5, -2.4, 0], end=[cx + 0.5, -2.4, 0], color=FIELD, stroke_width=4)
        arr_ret3 = Arrow(start=[cx, -2.3, 0], end=[cx, -1.4, 0], color=FIELD, stroke_width=4)

        flow_arrows = VGroup(arr_ext1, arr_ext2, arr_ext3, arr_ret1, arr_ret2, arr_ret3)

        self.play(Create(flow_arrows), FadeIn(cap1))
        self.wait(3.0)

        # -------------------------------------------------------------
        # STEP 2: Main Flux + Armature Loops + S-Curve Distorted Flux
        # -------------------------------------------------------------
        distorted_flux = VGroup()
        for y_pos in [-1.0, -0.5, 0.0, 0.5, 1.0]:
            p_start = np.array([cx - 2.1, y_pos + 0.35, 0])
            p_end = np.array([cx + 2.1, y_pos - 0.35, 0])
            curve = CubicBezier(p_start, p_start + [0.8, -0.3, 0], p_end + [-0.8, 0.3, 0], p_end, color=EMF, stroke_width=3.0)
            distorted_flux.add(curve)

        tilt_rad = math.radians(20)
        mnp_line = DashedLine([cx - 2.2 * math.sin(tilt_rad), -2.2 * math.cos(tilt_rad), 0], [cx + 2.2 * math.sin(tilt_rad), 2.2 * math.cos(tilt_rad), 0], color="#EC4899", stroke_width=3)
        lbl_mnp = Text("ระนาบเป็นกลางใหม่ (MNP)", font_size=13, color="#EC4899").move_to([cx + 0.9, 2.3, 0])

        cap2 = caption("2. สนามรวมบิดเบี้ยว Btotal: เส้นแรงรวมกันบิดเป็นรูปตัว S ➔ ระนาบ MNP เอียงตาม 20°")
        self.play(
            FadeOut(cap1),
            Create(distorted_flux),
            Create(mnp_line), FadeIn(lbl_mnp),
            FadeIn(cap2)
        )
        self.wait(3.5)
