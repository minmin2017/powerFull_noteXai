# -*- coding: utf-8 -*-
"""
eps_ch6_commutation_baton_handoff.py — Ultra-Clear Commutation "Baton Handoff" (1080p Full HD @ 25fps)
Pages 7-9 & Figures 6-4, 6-5 of EPS Chapter 6
Scene: CommutationBatonHandoff
"""

import math
from manim import *
import numpy as np
from mlib import *

class CommutationBatonHandoff(SafeScene):
    def construct(self):
        t_title = title("กลไกคอมมิวเตชั่น: การส่งไม้ผลัดกระแส (+50A ➔ 0A ➔ -50A) (หน้า 7-9)")
        fit_width(t_title, 12.2)
        self.play(FadeIn(t_title))

        # Right Summary HUD
        panel = RoundedRectangle(corner_radius=0.18, width=4.6, height=5.6, color="#1E293B", fill_opacity=0.92).move_to([4.7, 0, 0])
        p_head = Text("3 ขั้นตอนการส่งไม้ผลัด", font_size=18, color=WHITE).move_to([4.7, 2.3, 0])

        c1 = VGroup(
            Text("ขั้น 1: ก่อนคอมมิวเตชั่น", font_size=13, color=FIELD),
            Text("• แปรงถ่านแตะซี่ที่ 1 เต็มแผ่น", font_size=11, color=GRAYTXT),
            Text("• ขด B มีกระแส +50A (ไหลซ้าย)", font_size=11, color=FIELD),
            Text("• ซี่ 1 รับ 100A, ซี่ 2 = 0A", font_size=11, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.03).move_to([4.7, 1.3, 0])

        c2 = VGroup(
            Text("ขั้น 2: จังหวะลัดวงจร (ขด B)", font_size=13, color=WARN),
            Text("• แปรงถ่านแตะคร่อมซี่ 1 & 2", font_size=11, color=GRAYTXT),
            Text("• ขด B อยู่ที่ MNP ➔ emf=0V", font_size=11, color=WARN),
            Text("• กระแสในขด B ลดลงเป็น 0A", font_size=11, color=OK)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.03).move_to([4.7, 0.1, 0])

        c3 = VGroup(
            Text("ขั้น 3: ส่งไม้ผลัดสมบูรณ์", font_size=13, color=EMF),
            Text("• แปรงถ่านแตะซี่ที่ 2 เต็มแผ่น", font_size=11, color=GRAYTXT),
            Text("• ขด B กลับทิศเป็น -50A (ไหลขวา)", font_size=11, color=EMF),
            Text("• ซี่ 2 รับ 100A ➔ ไม่สปาร์ค!", font_size=11, color=EMF)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.03).move_to([4.7, -1.2, 0])

        hud_grp = VGroup(panel, p_head, c1, c2, c3)
        self.play(FadeIn(hud_grp))

        cx = -2.2
        # Rotor Structure: 3 Coils (Coil A, Coil B, Coil C) in a row
        y_coil = 1.0
        coil_a = Rectangle(width=1.4, height=0.7, color=FIELD, fill_color="#0284C7", fill_opacity=0.4).move_to([cx - 2.0, y_coil, 0])
        lbl_ca = Text("ขดลวด A", font_size=13, color=WHITE).move_to(coil_a.get_center())

        coil_b = Rectangle(width=1.4, height=0.7, color=WARN, fill_color="#D97706", fill_opacity=0.4).move_to([cx, y_coil, 0])
        lbl_cb = Text("ขดลวด B", font_size=13, color=WHITE).move_to(coil_b.get_center())

        coil_c = Rectangle(width=1.4, height=0.7, color=EMF, fill_color="#9333EA", fill_opacity=0.4).move_to([cx + 2.0, y_coil, 0])
        lbl_cc = Text("ขดลวด C", font_size=13, color=WHITE).move_to(coil_c.get_center())

        # Commutator Segments (Segment 1 and Segment 2)
        y_seg = -0.5
        seg_1 = Rectangle(width=1.8, height=0.6, color="#F59E0B", fill_color="#B45309", fill_opacity=0.8).move_to([cx - 1.0, y_seg, 0])
        lbl_s1 = Text("ซี่ที่ 1", font_size=14, color=WHITE).move_to(seg_1.get_center())

        seg_2 = Rectangle(width=1.8, height=0.6, color="#F59E0B", fill_color="#B45309", fill_opacity=0.8).move_to([cx + 1.0, y_seg, 0])
        lbl_s2 = Text("ซี่ที่ 2", font_size=14, color=WHITE).move_to(seg_2.get_center())

        # Carbon Brush (+) at Bottom
        y_brush = -1.4
        brush = Rectangle(width=1.8, height=0.7, color=WHITE, fill_color="#334155", fill_opacity=0.95).move_to([cx - 1.0, y_brush, 0])
        lbl_brush = Text("แปรงถ่าน (+)", font_size=14, color=WHITE).move_to(brush.get_center())
        out_arrow = Arrow(start=[cx - 1.0, y_brush - 0.35, 0], end=[cx - 1.0, y_brush - 1.1, 0], color=EMF, stroke_width=5)
        lbl_out = Text("100A สู่โหลด", font_size=13, color=EMF).next_to(out_arrow, DOWN, buff=0.1)

        # Connection Wires from coils to commutator segments
        wire_1 = Line([cx - 2.0, y_coil - 0.35, 0], [cx - 1.0, y_seg + 0.3, 0], color=YELLOW, stroke_width=3)
        wire_2 = Line([cx, y_coil - 0.35, 0], [cx - 1.0, y_seg + 0.3, 0], color=YELLOW, stroke_width=3)
        wire_3 = Line([cx, y_coil - 0.35, 0], [cx + 1.0, y_seg + 0.3, 0], color=YELLOW, stroke_width=3)
        wire_4 = Line([cx + 2.0, y_coil - 0.35, 0], [cx + 1.0, y_seg + 0.3, 0], color=YELLOW, stroke_width=3)

        self.play(
            FadeIn(coil_a), FadeIn(lbl_ca),
            FadeIn(coil_b), FadeIn(lbl_cb),
            FadeIn(coil_c), FadeIn(lbl_cc),
            FadeIn(seg_1), FadeIn(lbl_s1),
            FadeIn(seg_2), FadeIn(lbl_s2),
            Create(wire_1), Create(wire_2), Create(wire_3), Create(wire_4),
            FadeIn(brush), FadeIn(lbl_brush),
            Create(out_arrow), FadeIn(lbl_out)
        )
        self.wait(1.5)

        # -------------------------------------------------------------
        # STAGE 1: Before Commutation
        # -------------------------------------------------------------
        cap1 = caption("ขั้นที่ 1 (ก่อนส่งไม้ผลัด): แปรงถ่านแตะซี่ที่ 1 เต็มแผ่น ➔ กระแส 50A (ขด A) + 50A (ขด B) = 100A เข้าซี่ 1")
        arr_b_left = Arrow(start=[cx + 0.5, y_coil, 0], end=[cx - 0.5, y_coil, 0], color=FIELD, stroke_width=4)
        lbl_curr_b1 = Text("+50A (ซ้าย)", font_size=11, color=FIELD).next_to(arr_b_left, UP, buff=0.1)

        self.play(Create(arr_b_left), FadeIn(lbl_curr_b1), FadeIn(cap1))
        self.wait(2.5)

        # -------------------------------------------------------------
        # STAGE 2: During Commutation (Short Circuit at MNP)
        # -------------------------------------------------------------
        cap2 = caption("ขั้นที่ 2 (จังหวะส่งไม้ผลัด): แปรงถ่านแตะคร่อมซี่ 1 และซี่ 2 ➔ ขด B ถูกลัดวงจรที่ MNP (emf=0V, กระแส=0A)")
        
        # Move brush to center bridging segment 1 and 2
        self.play(
            FadeOut(cap1),
            FadeOut(arr_b_left), FadeOut(lbl_curr_b1),
            brush.animate.move_to([cx, y_brush, 0]),
            lbl_brush.animate.move_to([cx, y_brush, 0]),
            out_arrow.animate.move_to([cx, y_brush - 0.72, 0]),
            lbl_out.animate.next_to(out_arrow, DOWN, buff=0.1),
            FadeIn(cap2)
        )
        self.wait(2.5)

        # -------------------------------------------------------------
        # STAGE 3: After Commutation (Complete Transfer, -50A)
        # -------------------------------------------------------------
        cap3 = caption("ขั้นที่ 3 (ส่งไม้ผลัดสำเร็จ): แปรงถ่านแตะซี่ 2 เต็มแผ่น ➔ กระแสในขด B กลับทิศสมบูรณ์เป็น -50A (ไหลขวา) ไร้สปาร์ค!")
        arr_b_right = Arrow(start=[cx - 0.5, y_coil, 0], end=[cx + 0.5, y_coil, 0], color=EMF, stroke_width=4)
        lbl_curr_b2 = Text("-50A (กลับทิศไปขวา)", font_size=11, color=EMF).next_to(arr_b_right, UP, buff=0.1)

        # Move brush to segment 2 fully
        self.play(
            FadeOut(cap2),
            brush.animate.move_to([cx + 1.0, y_brush, 0]),
            lbl_brush.animate.move_to([cx + 1.0, y_brush, 0]),
            out_arrow.animate.move_to([cx + 1.0, y_brush - 0.72, 0]),
            lbl_out.animate.next_to(out_arrow, DOWN, buff=0.1),
            Create(arr_b_right), FadeIn(lbl_curr_b2),
            FadeIn(cap3)
        )
        self.wait(3.5)
