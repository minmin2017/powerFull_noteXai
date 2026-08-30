# -*- coding: utf-8 -*-
"""
eps_ch6_self_inductance_sparking_physics.py — Self-Inductance & Reactance Voltage Sparking (Page 9)
(1080p Full HD @ 25fps)
Scene: SelfInductanceSparkingPhysics
Shows:
1. Coil A moving towards Commutation (50A -> 0A)
2. Flux collapse -> Lenz's Law generates Self-Induced EMF e = L(di/dt)
3. Current forced to continue flowing -> Residual emf != 0V
4. Segment disconnecting from Brush -> High Voltage Sparking Arc!
"""

import math
from manim import *
import numpy as np
from mlib import *

class SelfInductanceSparkingPhysics(SafeScene):
    def construct(self):
        t_title = title("ฟิสิกส์หน้า 9: การเหนี่ยวนำในตัวเอง (Lenz's Law) & แรงดันเหนี่ยวนำตกค้างทำให้เกิดสปาร์ค")
        fit_width(t_title, 12.2)
        self.play(FadeIn(t_title))

        # Right Summary HUD
        panel = RoundedRectangle(corner_radius=0.18, width=4.7, height=5.6, color="#1E293B", fill_opacity=0.92).move_to([4.65, 0, 0])
        p_head = Text("ฟิสิกส์หน้า 9: การเหนี่ยวนำตนเอง", font_size=17, color=WHITE).move_to([4.65, 2.3, 0])

        c1 = VGroup(
            Text("1. กระแสลดลงฉับพลัน (50A ➔ 0A):", font_size=12, color=WARN),
            Text("เกิดในเวลาสั้นมาก dt เล็กมาก", font_size=11, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.03).move_to([4.65, 1.4, 0])

        c2 = VGroup(
            Text("2. ฟลักซ์ยุบตัว ➔ กฎของเลนซ์:", font_size=12, color=EMF),
            Text("ขดลวดสร้างแรงดัน e = L(di/dt)", font_size=11, color=GRAYTXT),
            Text("พยายามรั้งกระแสเดิมให้ไหลต่อ!", font_size=11, color=EMF)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.03).move_to([4.65, 0.45, 0])

        c3 = VGroup(
            Text("3. emf ตกค้าง (ไม่เป็น 0V จริง):", font_size=12, color=RED),
            Text("แม้จะอยู่ที่ระนาบเป็นกลางแล้ว", font_size=11, color=GRAYTXT),
            Text("ก็ยังมีแรงดันค้างอยู่ระหว่างซี่!", font_size=11, color=RED)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.03).move_to([4.65, -0.5, 0])

        c4 = VGroup(
            Text("4. จังหวะซี่หลุด ➔ เกิดสปาร์ค!", font_size=12, color=YELLOW),
            Text("แรงดันค้างกระโดดข้ามอากาศ", font_size=11, color=GRAYTXT),
            Text("เกิดประกายไฟอาร์คที่แปรงถ่าน", font_size=11, color=YELLOW)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.03).move_to([4.65, -1.5, 0])

        hud_grp = VGroup(panel, p_head, c1, c2, c3, c4)
        self.play(FadeIn(hud_grp))

        cx = -2.2
        # -------------------------------------------------------------
        # STAGE 1: Linear Armature Unrolled (Coils A, B, C & Commutator Segments 1, 2)
        # -------------------------------------------------------------
        # Coils A, B, C
        box_a = Rectangle(width=1.6, height=1.1, color=FIELD, fill_color="#0284C7", fill_opacity=0.85).move_to([cx - 1.8, 1.2, 0])
        t_a = Text("ขดลวด A", font_size=14, color=WHITE).move_to(box_a.get_center())

        box_b = Rectangle(width=1.6, height=1.1, color=WARN, fill_color="#D97706", fill_opacity=0.85).move_to([cx + 0.0, 1.2, 0])
        t_b = Text("ขดลวด B\n(กำลังสลับ)", font_size=13, color=WHITE).move_to(box_b.get_center())

        box_c = Rectangle(width=1.6, height=1.1, color=EMF, fill_color="#7C3AED", fill_opacity=0.85).move_to([cx + 1.8, 1.2, 0])
        t_c = Text("ขดลวด C", font_size=14, color=WHITE).move_to(box_c.get_center())

        # Commutator Segments 1 & 2
        seg1 = Rectangle(width=1.5, height=0.7, color=WARN, fill_color="#B45309", fill_opacity=0.9).move_to([cx - 0.85, -0.3, 0])
        t_s1 = Text("ซี่ที่ 1", font_size=13, color=WHITE).move_to(seg1.get_center())

        seg2 = Rectangle(width=1.5, height=0.7, color=WARN, fill_color="#B45309", fill_opacity=0.9).move_to([cx + 0.85, -0.3, 0])
        t_s2 = Text("ซี่ที่ 2", font_size=13, color=WHITE).move_to(seg2.get_center())

        # Taps
        tap_a = Line(box_a.get_bottom(), seg1.get_top(), color=YELLOW, stroke_width=2.5)
        tap_b1 = Line(box_b.get_bottom() + [-0.3, 0, 0], seg1.get_top(), color=YELLOW, stroke_width=2.5)
        tap_b2 = Line(box_b.get_bottom() + [0.3, 0, 0], seg2.get_top(), color=YELLOW, stroke_width=2.5)
        tap_c = Line(box_c.get_bottom(), seg2.get_top(), color=YELLOW, stroke_width=2.5)

        # Carbon Brush (+)
        brush = Rectangle(width=1.4, height=0.7, color=WHITE, fill_color="#334155", fill_opacity=0.95).move_to([cx - 0.4, -1.2, 0])
        t_br = Text("แปรงถ่าน (+)", font_size=13, color=WHITE).move_to(brush.get_center())

        cap1 = caption("ขั้น 1: ขด B เคลื่อนเข้าสู่คอมมิวเตชั่น กระแสเดิม 50A พยายามลดลงเป็น 0A ในเวลาสั้นมาก")
        self.play(
            FadeIn(box_a), FadeIn(t_a),
            FadeIn(box_b), FadeIn(t_b),
            FadeIn(box_c), FadeIn(t_c),
            FadeIn(seg1), FadeIn(t_s1),
            FadeIn(seg2), FadeIn(t_s2),
            Create(tap_a), Create(tap_b1), Create(tap_b2), Create(tap_c),
            FadeIn(brush), FadeIn(t_br),
            FadeIn(cap1)
        )
        self.wait(2.0)

        # -------------------------------------------------------------
        # STAGE 2: Lenz's Law & Self-Induced EMF e = L(di/dt)
        # -------------------------------------------------------------
        # Collapsing flux rings
        flux_ring1 = Circle(radius=0.5, color=YELLOW, stroke_width=2.5).move_to(box_b.get_center())
        flux_ring2 = Circle(radius=0.7, color=YELLOW, stroke_width=2.0).move_to(box_b.get_center())
        
        eq_lenz = VGroup(
            MathTex(r"e_L = -L \frac{di}{dt}", color=RED, font_size=32),
            Text("แรงดันต้านการเปลี่ยนแปลง (กฎเลนซ์)", font_size=13, color=RED)
        ).arrange(DOWN, buff=0.1).move_to([cx, 2.5, 0])

        arrow_force = Arrow(start=[cx - 0.7, 1.2, 0], end=[cx + 0.7, 1.2, 0], color=RED, stroke_width=4.5)
        lbl_force = Text("พยายามรั้งกระแสเดิมไว้!", font_size=12, color=RED).move_to([cx, 0.7, 0])

        cap2 = caption("ขั้น 2: ฟลักซ์ยุบตัว ➔ ขดลวดสร้างแรงดัน e = -L(di/dt) พยายามรั้งกระแสเดิมให้ไหลต่อ!")
        self.play(
            FadeOut(cap1),
            Create(flux_ring1), Create(flux_ring2),
            FadeIn(eq_lenz),
            Create(arrow_force), FadeIn(lbl_force),
            FadeIn(cap2)
        )
        self.wait(2.5)

        # -------------------------------------------------------------
        # STAGE 3: Commutator Segment 2 Breaks Contact -> SPARKING ARC!
        # -------------------------------------------------------------
        # Move brush slightly left so it disconnects from segment 2
        spark_star = Star(n=8, outer_radius=0.35, inner_radius=0.15, color=YELLOW, fill_color="#FBBF24", fill_opacity=1.0).move_to([cx + 0.45, -0.75, 0])
        lbl_spark = Text("⚡ อาร์ค / สปาร์ค!", font_size=13, color=YELLOW).move_to([cx + 1.8, -0.75, 0])

        cap3 = caption("ขั้น 3: เมื่อซี่ 2 หลุดออกจากแปรงถ่าน ➔ แรงดันเหนี่ยวนำตกค้างกระโดดข้ามช่องว่างกลายเป็นสปาร์ค!")
        self.play(
            FadeOut(cap2),
            brush.animate.move_to([cx - 0.85, -1.2, 0]),
            t_br.animate.move_to([cx - 0.85, -1.2, 0]),
            FadeIn(spark_star), FadeIn(lbl_spark),
            FadeIn(cap3)
        )
        self.wait(3.5)
