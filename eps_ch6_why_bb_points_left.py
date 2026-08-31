# -*- coding: utf-8 -*-
"""
eps_ch6_why_bb_points_left.py — Why BB Armature Field Points Left (Pages 5-7, Fig 6-3)
(1080p Full HD @ 25fps)
Scene: WhyBBPointsLeftExplanation
"""

import math
from manim import *
import numpy as np
from mlib import *

class WhyBBPointsLeftExplanation(SafeScene):
    def construct(self):
        t_title = title("ฟิสิกส์เชิงลึก: ทำไมสนามของตัวนำกลุ่ม BB ถึงชี้ไปทางซ้าย (สนามต่อต้าน)?")
        fit_width(t_title, 12.2)
        self.play(FadeIn(t_title))

        # Right Summary HUD
        panel = RoundedRectangle(corner_radius=0.18, width=4.7, height=5.6, color="#1E293B", fill_opacity=0.92).move_to([4.65, 0, 0])
        p_head = Text("ที่มาของสนามชี้ไปทางซ้าย", font_size=17, color=WHITE).move_to([4.65, 2.3, 0])

        c1 = VGroup(
            Text("1. ตอนแรก (แกนตั้ง 90°):", font_size=12, color=FIELD),
            Text("สนามอาร์เมเจอร์ชี้ลงดิ่งตรงๆ 90°", font_size=11, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.03).move_to([4.65, 1.4, 0])

        c2 = VGroup(
            Text("2. เมื่อเลื่อนแปรงถ่านตามมุม α:", font_size=12, color=WARN),
            Text("แกนสนามอาร์เมเจอร์เอียงตาม (swarrow)", font_size=11, color=GRAYTXT),
            Text("ทำให้เวกเตอร์ไม่ได้อยู่แนวตั้งอีกต่อไป!", font_size=11, color=WARN)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.03).move_to([4.65, 0.45, 0])

        c3 = VGroup(
            Text("3. แตกเวกเตอร์เป็น 2 ส่วน:", font_size=12, color=EMF),
            Text("• เวกเตอร์ชี้ลง (AA) = สนามขวาง", font_size=11, color=EMF),
            Text("• เวกเตอร์ชี้ไปซ้าย (BB) = สนามต่อต้าน!", font_size=11, color=RED)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.03).move_to([4.65, -0.5, 0])

        c4 = VGroup(
            Text("4. ชี้ซ้าย ➔ สวนสนามหลัก (N->S):", font_size=12, color=RED),
            Text("สนามหลักชี้ขวา (N->S)", font_size=11, color=GRAYTXT),
            Text("BB ชี้ซ้าย ➔ หักล้าง ➔ แรงดันตก!", font_size=11, color=RED)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.03).move_to([4.65, -1.5, 0])

        hud_grp = VGroup(panel, p_head, c1, c2, c3, c4)
        self.play(FadeIn(hud_grp))

        cx = -2.2
        # 1. Main Field Vector (Right ->)
        arr_main = Arrow(start=[cx - 2.2, 2.3, 0], end=[cx + 2.2, 2.3, 0], color=FIELD, stroke_width=4.5)
        lbl_main = Text("สนามแม่เหล็กหลัก Bf (พุ่งจาก N ซ้าย ➔ S ขวา)", font_size=13, color=FIELD).move_to([cx, 2.7, 0])

        # Rotor Circle
        rotor = Circle(radius=1.6, color=METAL, fill_color="#0F172A", fill_opacity=0.9).move_to([cx, -0.3, 0])

        # -------------------------------------------------------------
        # STEP 1: Original Vertical Armature Field (90 degrees downward)
        # -------------------------------------------------------------
        arr_vert = Arrow(start=[cx, 1.0, 0], end=[cx, -1.6, 0], color=YELLOW, stroke_width=4.5)
        lbl_vert = Text("สนามอาร์เมเจอร์เดิม (ตั้งฉาก 90° แนวดิ่ง)", font_size=13, color=YELLOW).move_to([cx, -2.1, 0])

        cap1 = caption("ขั้น 1: ก่อนเลื่อนแปรงถ่าน ➔ สนามอาร์เมเจอร์ชี้ลงในแนวดิ่ง 90° ตรงๆ")
        self.play(
            Create(arr_main), FadeIn(lbl_main),
            Create(rotor),
            Create(arr_vert), FadeIn(lbl_vert),
            FadeIn(cap1)
        )
        self.wait(2.0)

        # -------------------------------------------------------------
        # STEP 2: Tilted Armature Field due to Brush Shift
        # -------------------------------------------------------------
        tilt_rad = math.radians(25)
        arr_tilted = Arrow(
            start=[cx + 1.3 * math.sin(tilt_rad), -0.3 + 1.3 * math.cos(tilt_rad), 0],
            end=[cx - 1.3 * math.sin(tilt_rad), -0.3 - 1.3 * math.cos(tilt_rad), 0],
            color=WARN, stroke_width=4.5
        )
        lbl_tilted = Text("แกนสนามอาร์เมเจอร์เอียงตามมุม α", font_size=13, color=WARN).move_to([cx + 1.5, 0.8, 0])

        cap2 = caption("ขั้น 2: เมื่อเลื่อนแปรงถ่านตามระนาบเป็นกลาง ➔ แกนสนามอาร์เมเจอร์ทั้งหมดจะเอียงเฉียงไปทางซ้ายล่าง!")
        self.play(
            FadeOut(cap1),
            FadeOut(arr_vert), FadeOut(lbl_vert),
            Create(arr_tilted), FadeIn(lbl_tilted),
            FadeIn(cap2)
        )
        self.wait(2.5)

        # -------------------------------------------------------------
        # STEP 3: Vector Decomposition into AA (Down) and BB (Left)
        # -------------------------------------------------------------
        # AA: Vector Down
        arr_aa = Arrow(start=[cx, -0.3, 0], end=[cx, -1.6, 0], color=EMF, stroke_width=4.5)
        lbl_aa = Text("AA: สนามขวาง (ชี้ลง)", font_size=12, color=EMF).move_to([cx + 1.1, -1.2, 0])

        # BB: Vector Left
        arr_bb = Arrow(start=[cx, -0.3, 0], end=[cx - 1.6, -0.3, 0], color=RED, stroke_width=5.0)
        lbl_bb = Text("BB: สนามต่อต้าน (ชี้ไปทางซ้าย!)", font_size=13, color=RED).move_to([cx - 1.2, 0.1, 0])

        cap3 = caption("ขั้น 3: แตกเวกเตอร์เฉียง ➔ ได้เวกเตอร์ BB ชี้ไปทางซ้าย (สวนทาง 180° กับสนามหลัก ทำให้แรงดันตก!)")
        self.play(
            FadeOut(cap2),
            Create(arr_aa), FadeIn(lbl_aa),
            Create(arr_bb), FadeIn(lbl_bb),
            FadeIn(cap3)
        )
        self.wait(3.5)
