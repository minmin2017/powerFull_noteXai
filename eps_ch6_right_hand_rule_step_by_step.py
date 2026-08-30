# -*- coding: utf-8 -*-
"""
eps_ch6_right_hand_rule_step_by_step.py — Step-by-Step Right Hand Thumb Rule & Armature Flux Construction
(1080p Full HD @ 25fps)
Scene: RightHandRuleStepByStep
"""

import math
from manim import *
import numpy as np
from mlib import *

class RightHandRuleStepByStep(SafeScene):
    def construct(self):
        t_title = title("ฟิสิกส์ทีละเส้น: กฎมือขวา (Right-Hand Rule) สร้างสนามอาร์เมเจอร์ Ba")
        fit_width(t_title, 12.2)
        self.play(FadeIn(t_title))

        # Right Summary HUD
        panel = RoundedRectangle(corner_radius=0.18, width=4.6, height=5.6, color="#1E293B", fill_opacity=0.92).move_to([4.7, 0, 0])
        p_head = Text("กฎมือขวาของแอมแปร์", font_size=18, color=WHITE).move_to([4.7, 2.3, 0])

        c1 = VGroup(
            Text("1. ตัวนำซีกบน (⊙ พุ่งออก):", font_size=13, color=YELLOW),
            Text("• นิ้วโป้งชี้พุ่งออกจากจอ", font_size=11, color=GRAYTXT),
            Text("• 4 นิ้วกำวน 'ทวนเข็ม' ↺", font_size=11, color=YELLOW),
            Text("➔ ด้านล่างของวงกลมชี้ลง ⬇", font_size=11, color=OK)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.04).move_to([4.7, 1.3, 0])

        c2 = VGroup(
            Text("2. ตัวนำซีกล่าง (⊗ พุ่งเข้า):", font_size=13, color=WARN),
            Text("• นิ้วโป้งชี้พุ่งเข้าสู่จอ", font_size=11, color=GRAYTXT),
            Text("• 4 นิ้วกำวน 'ตามเข็ม' ↻", font_size=11, color=WARN),
            Text("➔ ด้านบนของวงกลมชี้ลง ⬇", font_size=11, color=OK)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.04).move_to([4.7, 0.1, 0])

        c3 = VGroup(
            Text("3. การรวมสนาม (Superposition):", font_size=13, color=EMF),
            Text("ตรงกลางแกนเหล็ก เส้นแรงชี้ลงเหมือนกัน", font_size=11, color=GRAYTXT),
            Text("➔ เสริมแรงเป็นสนามดิ่ง Ba ⬇ (90°)", font_size=11, color=EMF)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.04).move_to([4.7, -1.2, 0])

        hud_grp = VGroup(panel, p_head, c1, c2, c3)
        self.play(FadeIn(hud_grp))

        cx = -2.2
        # Rotor Outer Ring (Core cross-section)
        rotor_ring = Circle(radius=1.8, color=METAL, stroke_width=4).move_to([cx, 0, 0])
        self.play(Create(rotor_ring))

        # -------------------------------------------------------------
        # STEP 1: Top Conductor (Dot)
        # -------------------------------------------------------------
        p_top = np.array([cx, 1.4, 0])
        c_top = Circle(radius=0.22, color=YELLOW, fill_color="#B45309", fill_opacity=0.9).move_to(p_top)
        dot_sym = Dot(p_top, radius=0.06, color=WHITE)
        lbl_top = Text("ตัวนำซีกบน: กระแสพุ่งออก (⊙)", font_size=13, color=YELLOW).next_to(c_top, UP, buff=0.15)

        cap1 = caption("ขั้นที่ 1: ตัวนำซีกบน (⊙) ➔ นิ้วโป้งชี้ออก ➔ สนามแม่เหล็กวนทวนเข็มนาฬิกา ↺")
        self.play(Create(c_top), FadeIn(dot_sym), FadeIn(lbl_top), FadeIn(cap1))
        self.wait(1.5)

        # Concentric CCW circles for top conductor
        top_flux1 = Circle(radius=0.55, color=YELLOW, stroke_width=2.5).move_to(p_top)
        top_flux2 = Circle(radius=0.95, color=YELLOW, stroke_width=2.5).move_to(p_top)
        arr_top_ccw = CurvedArrow(p_top + [0.55, 0, 0], p_top + [0, 0.55, 0], radius=0.55, color=YELLOW)
        vec_top_down = Arrow(start=[cx, 0.45, 0], end=[cx, -0.05, 0], color=OK, stroke_width=4)
        lbl_vtop = Text("ทิศชี้ลง ⬇", font_size=11, color=OK).next_to(vec_top_down, LEFT, buff=0.1)

        self.play(Create(top_flux1), Create(top_flux2), Create(arr_top_ccw), Create(vec_top_down), FadeIn(lbl_vtop))
        self.wait(2.0)

        # -------------------------------------------------------------
        # STEP 2: Bottom Conductor (Cross)
        # -------------------------------------------------------------
        p_bot = np.array([cx, -1.4, 0])
        c_bot = Circle(radius=0.22, color=WARN, fill_color="#991B1B", fill_opacity=0.9).move_to(p_bot)
        cross_sym = VGroup(
            Line(p_bot + [-0.08, -0.08, 0], p_bot + [0.08, 0.08, 0], color=WHITE, stroke_width=2),
            Line(p_bot + [-0.08, 0.08, 0], p_bot + [0.08, -0.08, 0], color=WHITE, stroke_width=2)
        )
        lbl_bot = Text("ตัวนำซีกล่าง: กระแสพุ่งเข้า (⊗)", font_size=13, color=WARN).next_to(c_bot, DOWN, buff=0.15)

        cap2 = caption("ขั้นที่ 2: ตัวนำซีกล่าง (⊗) ➔ นิ้วโป้งชี้เข้า ➔ สนามแม่เหล็กวนตามเข็มนาฬิกา ↻")
        self.play(FadeOut(cap1), Create(c_bot), FadeIn(cross_sym), FadeIn(lbl_bot), FadeIn(cap2))
        self.wait(1.5)

        # Concentric CW circles for bottom conductor
        bot_flux1 = Circle(radius=0.55, color=WARN, stroke_width=2.5).move_to(p_bot)
        bot_flux2 = Circle(radius=0.95, color=WARN, stroke_width=2.5).move_to(p_bot)
        arr_bot_cw = CurvedArrow(p_bot + [0, 0.55, 0], p_bot + [0.55, 0, 0], radius=0.55, color=WARN)
        vec_bot_down = Arrow(start=[cx, -0.45, 0], end=[cx, -0.95, 0], color=OK, stroke_width=4)
        lbl_vbot = Text("ทิศชี้ลง ⬇", font_size=11, color=OK).next_to(vec_bot_down, LEFT, buff=0.1)

        self.play(Create(bot_flux1), Create(bot_flux2), Create(arr_bot_cw), Create(vec_bot_down), FadeIn(lbl_vbot))
        self.wait(2.0)

        # -------------------------------------------------------------
        # STEP 3: Superposition inside core
        # -------------------------------------------------------------
        cap3 = caption("ขั้นที่ 3: ตรงกลางแกนโรเตอร์ เส้นแรงทั้งสองชี้ลงเหมือนกัน ➔ รวมกันเป็นสนามอาร์เมเจอร์ Ba แนวดิ่ง!")
        vec_ba_total = Arrow(start=[cx, 1.2, 0], end=[cx, -1.2, 0], color=EMF, stroke_width=6)
        lbl_ba_math = MathTex(r"\vec{B}_a", font_size=20, color=EMF)
        lbl_ba_txt = Text("(พุ่งลงแนวดิ่ง 90°)", font_size=13, color=EMF)
        lbl_ba_total = VGroup(lbl_ba_math, lbl_ba_txt).arrange(RIGHT, buff=0.1).next_to(vec_ba_total, RIGHT, buff=0.15)

        self.play(
            FadeOut(cap2),
            FadeOut(lbl_vtop), FadeOut(lbl_vbot),
            Create(vec_ba_total), FadeIn(lbl_ba_total),
            FadeIn(cap3)
        )
        self.wait(3.5)
