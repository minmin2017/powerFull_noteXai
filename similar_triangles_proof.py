"""
similar_triangles_proof.py — Manim Animation for Fundamental Law of Gearing
Focuses strictly on the 3 pairs of similar triangles (Pages 5-6).
High resolution, 60fps, slow and detailed point-by-point explanation.
"""

import sys
import os
import numpy as np
from manim import *

THAI_FONT = "Loma" if sys.platform.startswith("linux") else "Leelawadee UI"
Text.set_default(font=THAI_FONT)

# Colors
GEAR_IN  = "#4FC3F7"   # Body 2 (A)
GEAR_OUT = "#FFB74D"   # Body 3 (B)
FORCE    = "#66BB6A"   # Velocity / Normal
WARN     = "#FF7043"   # Highlights
OK       = "#26C6DA"   # Pitch Point / Result
GRAYTXT  = "#B0BEC5"   
BASE_COL = "#AB47BC"   
WHITE    = "#FFFFFF"

class SimilarTrianglesProof(Scene):
    def construct(self):
        # ---------------------------------------------------------
        # INTRO
        # ---------------------------------------------------------
        title = Text("บทพิสูจน์กฎการขบ: เจาะลึกสามเหลี่ยมคล้าย 3 คู่", font_size=32, color=WHITE).to_edge(UP)
        self.play(Write(title))

        intro_text = Text("เราจะมาดูกันว่าอัตราทดคงที่ มาจากสามเหลี่ยมคล้ายคู่ไหนบ้าง (ทีละจุด)", font_size=20, color=GRAYTXT).next_to(title, DOWN)
        self.play(FadeIn(intro_text))
        self.wait(2)
        self.play(FadeOut(intro_text))

        # ---------------------------------------------------------
        # SETUP GEOMETRY
        # ---------------------------------------------------------
        A = np.array([-4.0, -1.5, 0])
        B = np.array([-0.0, 2.0, 0])
        Q = np.array([-2.5, 0.5, 0])

        dotA = Dot(A, color=GEAR_IN)
        dotB = Dot(B, color=GEAR_OUT)
        dotQ = Dot(Q, color=WHITE)
        
        lblA = Text("A", font_size=24, color=GEAR_IN).next_to(dotA, DOWN)
        lblB = Text("B", font_size=24, color=GEAR_OUT).next_to(dotB, UP)
        lblQ = Text("Q (จุดสัมผัส)", font_size=20, color=WHITE).next_to(dotQ, UL)

        lineAQ = Line(A, Q, color=GEAR_IN, stroke_width=2)
        lineBQ = Line(B, Q, color=GEAR_OUT, stroke_width=2)

        self.play(
            Create(dotA), FadeIn(lblA),
            Create(dotB), FadeIn(lblB),
            Create(dotQ), FadeIn(lblQ),
            Create(lineAQ), Create(lineBQ)
        )

        # Contact Normal n-n
        # Let's say normal line passes through Q with some angle
        n_angle = 35 * DEGREES
        n_dir = np.array([np.cos(n_angle), np.sin(n_angle), 0])
        n_start = Q - n_dir * 5
        n_end = Q + n_dir * 5
        line_nn = DashedLine(n_start, n_end, color=FORCE)
        lbl_nn = Text("Contact Normal (n-n')", font_size=16, color=FORCE).next_to(n_end, DOWN).shift(LEFT*1.5)

        self.play(Create(line_nn), FadeIn(lbl_nn))
        
        # ---------------------------------------------------------
        # PAIR 1: Velocity VQ2 and Triangle ARQ
        # ---------------------------------------------------------
        txt_pair1 = Text("คู่ที่ 1: สามเหลี่ยมคล้ายฝั่งชิ้นที่ 2 (จุด A)", font_size=24, color=GEAR_IN).to_edge(UP).shift(DOWN*0.8)
        self.play(FadeIn(txt_pair1))

        # Velocity VQ2 is perpendicular to AQ
        v2_angle = lineAQ.get_angle() + PI/2
        v2_len = 2.5
        v2_end = Q + np.array([np.cos(v2_angle), np.sin(v2_angle), 0]) * v2_len
        vec_v2 = Arrow(Q, v2_end, buff=0, color=GEAR_IN)
        lbl_v2 = MathTex(r"v_{Q2}", font_size=24, color=GEAR_IN).next_to(vec_v2.get_end(), UL, buff=0.1)
        
        # Right angle AQ and VQ2
        ra_v2 = RightAngle(lineAQ, vec_v2, length=0.2, color=GEAR_IN)

        self.play(GrowArrow(vec_v2), FadeIn(lbl_v2), Create(ra_v2))

        # Projection of VQ2 onto n-n
        # Dot product to find projection length
        v2_vec = v2_end - Q
        vn_len = np.dot(v2_vec, n_dir)
        vn_end = Q + n_dir * vn_len
        vec_vn = Arrow(Q, vn_end, buff=0, color=OK)
        lbl_vn = MathTex(r"v_n", font_size=24, color=OK).next_to(vec_vn.get_end(), DR, buff=0.1)
        
        proj_line2 = DashedLine(v2_end, vn_end, color=GRAYTXT)
        ra_proj2 = RightAngle(line_nn, proj_line2, length=0.2, color=GRAYTXT, quadrant=(1,-1))

        self.play(Create(proj_line2), Create(ra_proj2), GrowArrow(vec_vn), FadeIn(lbl_vn))

        # Point R
        # R is foot of perpendicular from A to n-n
        AR_vec = A - Q
        AR_proj_len = np.dot(AR_vec, n_dir)
        R = Q + n_dir * AR_proj_len
        lineAR = Line(A, R, color=GEAR_IN)
        dotR = Dot(R, color=GEAR_IN)
        lblR = Text("R", font_size=20, color=GEAR_IN).next_to(dotR, DR, buff=0.1)
        ra_R = RightAngle(line_nn, lineAR, length=0.2, color=GEAR_IN, quadrant=(-1,1))

        self.play(Create(lineAR), Create(dotR), FadeIn(lblR), Create(ra_R))

        # Highlight similarity
        angle_alpha_1 = Angle(line_nn, lineAQ, radius=0.6, color=WARN)
        angle_alpha_2 = Angle(proj_line2, vec_v2, radius=0.6, color=WARN)
        
        # The angle between AQ and n-n is same as angle between vQ2 and proj_line2
        self.play(Create(angle_alpha_1))
        self.play(Create(angle_alpha_2))

        panel_1 = VGroup(
            Text("1) เนื่องจาก AQ ⊥ vQ2 และ AR ⊥ n-n'", font_size=18, color=WHITE),
            Text("   ทำให้มุมระหว่างพวกมันมีค่าเท่ากัน (สีส้ม)", font_size=18, color=WARN),
            VGroup(
                Text("2) ดังนั้น สามเหลี่ยมความเร็ว คล้ายกับ", font_size=18, color=WHITE),
                MathTex(r"\Delta ARQ", font_size=20, color=GEAR_IN)
            ).arrange(RIGHT, buff=0.1),
            MathTex(r"\cos(\alpha) = \frac{v_n}{v_{Q2}} = \frac{AR}{AQ}", font_size=22, color=OK),
            MathTex(r"v_n = v_{Q2}\frac{AR}{AQ} = (\omega_2 AQ)\frac{AR}{AQ} = \omega_2 AR", font_size=22, color=GEAR_IN)
        ).arrange(DOWN, aligned_edge=LEFT).to_corner(DR)
        
        bg_panel1 = BackgroundRectangle(panel_1, color=BLACK, fill_opacity=0.8, buff=0.2)
        self.play(FadeIn(bg_panel1), FadeIn(panel_1))
        self.wait(5)
        
        self.play(FadeOut(bg_panel1), FadeOut(panel_1), FadeOut(txt_pair1), FadeOut(angle_alpha_1), FadeOut(angle_alpha_2), FadeOut(lbl_v2), FadeOut(vec_v2), FadeOut(proj_line2), FadeOut(ra_proj2), FadeOut(ra_v2))

        # ---------------------------------------------------------
        # PAIR 2: Velocity VQ3 and Triangle BSQ
        # ---------------------------------------------------------
        txt_pair2 = Text("คู่ที่ 2: สามเหลี่ยมคล้ายฝั่งชิ้นที่ 3 (จุด B)", font_size=24, color=GEAR_OUT).to_edge(UP).shift(DOWN*0.8)
        self.play(FadeIn(txt_pair2))

        v3_angle = lineBQ.get_angle() + PI/2
        # v3 must project to the EXACT SAME vn
        # vn_len = v3_len * cos(beta) => v3_len = vn_len / cos(beta)
        v3_vec_dir = np.array([np.cos(v3_angle), np.sin(v3_angle), 0])
        beta = np.arccos(np.dot(v3_vec_dir, n_dir))
        v3_len = vn_len / np.cos(beta)
        v3_end = Q + v3_vec_dir * v3_len
        
        vec_v3 = Arrow(Q, v3_end, buff=0, color=GEAR_OUT)
        lbl_v3 = MathTex(r"v_{Q3}", font_size=24, color=GEAR_OUT).next_to(vec_v3.get_end(), UP, buff=0.1)
        ra_v3 = RightAngle(lineBQ, vec_v3, length=0.2, color=GEAR_OUT)

        self.play(GrowArrow(vec_v3), FadeIn(lbl_v3), Create(ra_v3))
        
        proj_line3 = DashedLine(v3_end, vn_end, color=GRAYTXT)
        ra_proj3 = RightAngle(line_nn, proj_line3, length=0.2, color=GRAYTXT, quadrant=(1,1))
        self.play(Create(proj_line3), Create(ra_proj3))

        # Point S
        BS_vec = B - Q
        BS_proj_len = np.dot(BS_vec, n_dir)
        S = Q + n_dir * BS_proj_len
        lineBS = Line(B, S, color=GEAR_OUT)
        dotS = Dot(S, color=GEAR_OUT)
        lblS = Text("S", font_size=20, color=GEAR_OUT).next_to(dotS, UP, buff=0.1)
        ra_S = RightAngle(line_nn, lineBS, length=0.2, color=GEAR_OUT, quadrant=(1,-1))

        self.play(Create(lineBS), Create(dotS), FadeIn(lblS), Create(ra_S))

        panel_2 = VGroup(
            Text("ในทำนองเดียวกัน ชิ้นที่ 3 มีสามเหลี่ยมคล้าย", font_size=18, color=WHITE),
            VGroup(
                Text("สามเหลี่ยมความเร็ว คล้ายกับ", font_size=18, color=WHITE),
                MathTex(r"\Delta BSQ", font_size=20, color=GEAR_OUT)
            ).arrange(RIGHT, buff=0.1),
            MathTex(r"v_n = \omega_3 BS", font_size=22, color=GEAR_OUT),
            Text("จับสมการความเร็ว vn ของ 2 ชิ้นมาเท่ากัน:", font_size=18, color=WARN),
            MathTex(r"\omega_2 AR = \omega_3 BS", font_size=22, color=OK),
            MathTex(r"\frac{\omega_2}{\omega_3} = \frac{BS}{AR}", font_size=24, color=OK)
        ).arrange(DOWN, aligned_edge=LEFT).to_corner(DR)

        bg_panel2 = BackgroundRectangle(panel_2, color=BLACK, fill_opacity=0.8, buff=0.2)
        self.play(FadeIn(bg_panel2), FadeIn(panel_2))
        self.wait(5)

        self.play(FadeOut(bg_panel2), FadeOut(panel_2), FadeOut(txt_pair2), FadeOut(lbl_v3), FadeOut(vec_v3), FadeOut(proj_line3), FadeOut(ra_proj3), FadeOut(ra_v3), FadeOut(vec_vn), FadeOut(lbl_vn))

        # ---------------------------------------------------------
        # PAIR 3: Triangle ARP and BSP (Pitch Point)
        # ---------------------------------------------------------
        txt_pair3 = Text("คู่ที่ 3: เส้น Line of Centers ตัดกับ Contact Normal (จุด P)", font_size=24, color=OK).to_edge(UP).shift(DOWN*0.8)
        self.play(FadeIn(txt_pair3))

        line_centers = Line(A, B, color=WHITE, stroke_width=2)
        lbl_centers = Text("Line of Centers", font_size=16, color=WHITE).next_to(line_centers.get_center(), LEFT, buff=0.1)
        
        # Intersection P
        # Solving intersection A+t(B-A) = n_start + u(n_dir)
        # Simple math:
        P = line_intersection((A, B), (n_start, n_end))
        dotP = Dot(P, color=OK, radius=0.1)
        lblP = Text("Pitch Point P", font_size=22, color=OK).next_to(dotP, DR, buff=0.1)

        self.play(Create(line_centers), FadeIn(lbl_centers), Create(dotP), FadeIn(lblP))

        # Triangles ARP and BSP
        tri_ARP = Polygon(A, R, P, color=GEAR_IN, fill_opacity=0.3, stroke_width=0)
        tri_BSP = Polygon(B, S, P, color=GEAR_OUT, fill_opacity=0.3, stroke_width=0)

        self.play(FadeIn(tri_ARP), FadeIn(tri_BSP))

        # Vertically opposite angles at P
        ang_P1 = Angle(line_centers, line_nn, quadrant=(1,-1), other_angle=True, radius=0.4, color=WARN)
        ang_P2 = Angle(line_centers, line_nn, quadrant=(-1,1), other_angle=True, radius=0.4, color=WARN)
        
        self.play(Create(ang_P1), Create(ang_P2))

        panel_3 = VGroup(
            VGroup(
                Text("ดูที่", font_size=18, color=WHITE),
                MathTex(r"\Delta ARP", font_size=20, color=GEAR_IN),
                Text("และ", font_size=18, color=WHITE),
                MathTex(r"\Delta BSP", font_size=20, color=GEAR_OUT)
            ).arrange(RIGHT, buff=0.1),
            Text("1) มีมุมฉากเหมือนกันที่ R และ S", font_size=18, color=WHITE),
            Text("2) มุมตรงข้ามที่จุด P เท่ากัน (สีส้ม)", font_size=18, color=WARN),
            Text("ดัวนั้น สามเหลี่ยมสองรูปนี้คล้ายกัน!", font_size=18, color=OK),
            MathTex(r"\frac{BS}{AR} = \frac{BP}{AP}", font_size=24, color=OK),
            Text("สรุปกฎการขบ:", font_size=20, color=WHITE),
            MathTex(r"\frac{\omega_2}{\omega_3} = \frac{BS}{AR} = \frac{BP}{AP}", font_size=28, color=OK)
        ).arrange(DOWN, aligned_edge=LEFT).to_corner(DL)

        bg_panel3 = BackgroundRectangle(panel_3, color=BLACK, fill_opacity=0.8, buff=0.2)
        self.play(FadeIn(bg_panel3), FadeIn(panel_3))
        
        conclude = Text("นี่คือที่มาว่าทำไมอัตราทด ถึงขึ้นอยู่กับจุด P ล้วนๆ!", font_size=24, color=WARN).to_edge(BOTTOM).shift(UP*0.5)
        self.play(Write(conclude))
        
        self.wait(8)
