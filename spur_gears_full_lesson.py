"""
spur_gears_full_lesson.py — Manim Animation for Spur Gears (Mechanics of Machinery Chapter 4 / W06)
Covers all 39 slides across 7 modular, high-impact educational scenes.
Follows mlib.py standards, Mayer signaling principle, and cross-platform font rendering.
"""

import sys
import os
import numpy as np
from manim import *

# ---------------------------------------------------------------- Font & Palette
THAI_FONT = "Loma" if sys.platform.startswith("linux") else "Leelawadee UI"
Text.set_default(font=THAI_FONT)

# Palette (Mayer Signaling Principle)
GEAR_IN  = "#4FC3F7"   # Pinion / Input / First (ฟ้า)
GEAR_OUT = "#FFB74D"   # Gear / Output / Last (ส้มทอง)
GEAR_MID = "#81C784"   # Idler / Contact / Green (เขียว)
FIELD    = "#29B6F6"   # Pitch Circle / Geometry Line (ฟ้าสด)
FORCE    = "#66BB6A"   # Action Line / Force Vector (เขียว)
WARN     = "#FF7043"   # Interference / Limit / Red-Orange (ส้มแดง)
OK       = "#26C6DA"   # Correct / Result (เขียวอมฟ้า)
GRAYTXT  = "#B0BEC5"   # Secondary text (เทา)
METAL    = "#90A4AE"   # Mechanical bodies (เทาเมทัลลิก)
BASE_COL = "#AB47BC"   # Base Circle (ม่วง)

TITLE_Y = 3.45
CAP_Y = -3.45
STAGE_C = np.array([-2.2, 0.15, 0])
PANEL_X = 4.15
PANEL_TOP = 2.45


def make_title(txt):
    return Text(txt, font_size=28, color=WHITE).move_to([0, TITLE_Y, 0])


def make_caption(txt, color=GRAYTXT):
    return Text(txt, font_size=21, color=color).move_to([0, CAP_Y, 0])


# ================================================================ Scene 1: Fundamental Law & Pitch Point P
class SG01_FundamentalLaw(Scene):
    """Slides 1–8: Fundamental Law of Gearing & Pitch Point P"""

    def construct(self):
        title = make_title("บทที่ 4: กฎการขบของเฟือง & จุด Pitch Point (P) (หน้า 1–8)")
        self.play(Write(title))

        cap1 = make_caption("อัตราทดเฉลี่ยขึ้นกับจำนวนฟัน แต่อัตราทดขณะใดขณะหนึ่งขึ้นกับ 'รูปร่างฟัน'")
        self.play(FadeIn(cap1))

        # Two bodies in contact
        A = np.array([-4.2, -0.5, 0])
        B = np.array([-0.2, 1.2, 0])
        Q = np.array([-2.2, 0.35, 0])

        dotA = Dot(A, color=GEAR_IN, radius=0.1)
        dotB = Dot(B, color=GEAR_OUT, radius=0.1)
        lblA = Text("จุดหมุน A (ชิ้น 2)", font_size=18, color=GEAR_IN).next_to(dotA, DOWN)
        lblB = Text("จุดหมุน B (ชิ้น 3)", font_size=18, color=GEAR_OUT).next_to(dotB, UP)

        line_AB = DashedLine(A, B, color=GRAYTXT, stroke_width=2)
        lbl_center_line = Text("Line of Centers", font_size=16, color=GRAYTXT).next_to(line_AB.get_center(), UP, buff=0.1).rotate(line_AB.get_angle())

        body2 = Circle(radius=2.1, color=GEAR_IN, fill_opacity=0.15, stroke_width=2).move_to(A)
        body3 = Circle(radius=2.05, color=GEAR_OUT, fill_opacity=0.15, stroke_width=2).move_to(B)

        self.play(Create(dotA), Create(dotB), FadeIn(lblA), FadeIn(lblB), Create(line_AB), Create(body2), Create(body3))

        # Contact Normal & Pitch point P
        normal_dir = np.array([0.7, 0.714, 0])
        normal_dir = normal_dir / np.linalg.norm(normal_dir)
        normal_line = Line(Q - normal_dir * 2.6, Q + normal_dir * 2.6, color=FORCE, stroke_width=3)
        dotQ = Dot(Q, color=WARN, radius=0.11)
        lblQ = Text("จุดสัมผัส Q", font_size=18, color=WARN).next_to(dotQ, DR, buff=0.1)

        # Intersection with Line of Centers -> Pitch point P
        P = np.array([-2.35, 0.30, 0])
        dotP = Dot(P, color=OK, radius=0.12)
        lblP = Text("Pitch Point P (IC₂₃)", font_size=20, color=OK).next_to(dotP, UL, buff=0.1)

        self.play(Create(normal_line), Create(dotQ), FadeIn(lblQ), Create(dotP), FadeIn(lblP))

        # Right side panel explanation
        panel = VGroup(
            Text("กฎหลักของการส่งกำลัง:", font_size=20, color=OK),
            VGroup(
                Text("อัตราส่วนความเร็วเชิงมุม:", font_size=17, color=WHITE),
                VGroup(
                    MathTex(r"\frac{\omega_2}{\omega_3} = \frac{BP}{AP} = ", font_size=22, color=OK),
                    Text("คงที่", font_size=17, color=OK)
                ).arrange(RIGHT, buff=0.1)
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.08),
            Text("• ถ้าจุด P อยู่นิ่งตลอดเวลา", font_size=17, color=GRAYTXT),
            Text("  การส่งกำลังจะเรียบเหมือนลูกกลิ้ง", font_size=17, color=GRAYTXT),
            Text("• คู่ผิวสัมผัสนี้เรียกว่า", font_size=17, color=WHITE),
            Text("  'Conjugate Profiles'", font_size=19, color=GEAR_IN),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([PANEL_X, 0.2, 0])

        self.play(FadeIn(panel))
        self.wait(2)

        cap2 = make_caption("Conjugate Teeth ทำให้ Common Normal ผ่านจุด Pitch Point P คงที่เสมอ")
        self.play(Transform(cap1, cap2))
        self.wait(2)


# ================================================================ Scene 2: Involute & Involutometry
class SG02_InvoluteGeometry(Scene):
    """Slides 9–13: Involute Curve Generation & Involutometry"""

    def construct(self):
        title = make_title("กำเนิดเส้นโค้ง Involute & Involutometry (หน้า 9–13)")
        self.play(Write(title))

        cap = make_caption("Involute คือเส้นทางเดินของปลายสายพานที่คลี่ออกจาก Base Circle")
        self.play(FadeIn(cap))

        # Center and Base Circle
        O = np.array([-2.6, -0.6, 0])
        Rb = 1.8
        base_circ = Circle(radius=Rb, color=BASE_COL, stroke_width=3).move_to(O)
        lbl_base = Text("Base Circle (Rb)", font_size=18, color=BASE_COL).next_to(base_circ, LEFT)
        dotO = Dot(O, color=WHITE, radius=0.08)

        self.play(Create(dotO), Create(base_circ), FadeIn(lbl_base))

        # Unwrapping cord curve
        angles = np.linspace(0, 1.25, 40)
        involute_pts = [
            O + np.array([
                Rb * (np.cos(a) + a * np.sin(a)),
                Rb * (np.sin(a) - a * np.cos(a)),
                0
            ]) for a in angles
        ]
        involute_curve = VMobject(color=GEAR_IN, stroke_width=4)
        involute_curve.set_points_smoothly(involute_pts)

        tangent_line = Line(
            O + np.array([Rb * np.cos(1.2), Rb * np.sin(1.2), 0]),
            involute_pts[-1],
            color=FORCE, stroke_width=3
        )
        dot_tip = Dot(involute_pts[-1], color=WARN, radius=0.1)
        lbl_cord = Text("สายพานที่คลี่ออก", font_size=16, color=FORCE).next_to(tangent_line, UR, buff=0.05)

        self.play(Create(tangent_line), FadeIn(lbl_cord), Create(involute_curve), Create(dot_tip), run_time=2.0)

        # Involute equation on panel
        panel = VGroup(
            Text("Involute Function (สำคัญ):", font_size=20, color=OK),
            VGroup(
                Text("ความสัมพันธ์มุมอินโวลูท:", font_size=16, color=GRAYTXT),
                MathTex(r"\operatorname{inv}\phi = \tan\phi - \phi", font_size=24, color=OK),
                Text("(ต้องใส่ φ เป็นเรเดียน)", font_size=15, color=WARN),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.08),
            VGroup(
                Text("การหารัศมี Base Circle:", font_size=16, color=GRAYTXT),
                MathTex(r"R_b = R\cos\phi", font_size=22, color=BASE_COL),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.08),
            Text("ข้อได้เปรียบเอกอุ:", font_size=18, color=WHITE),
            Text("อัตราทดยังคงที่แม้ระยะศูนย์กลาง (C)", font_size=16, color=GEAR_IN),
            Text("เปลี่ยนไปจากการประกอบหรือแบริ่งสึก", font_size=16, color=GEAR_IN),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16).move_to([PANEL_X, 0.1, 0])

        self.play(FadeIn(panel))
        self.wait(2)


# ================================================================ Scene 3: Nomenclature & Circles
class SG03_NomenclatureCircles(Scene):
    """Slides 14–18: Gear Circles & Geometry Nomenclature"""

    def construct(self):
        title = make_title("ศัพท์เรขาคณิต & วงกลมหลัก 4 วงของเฟือง (หน้า 14–18)")
        self.play(Write(title))

        cap = make_caption("วงกลม 4 วงเรียงจากในออกนอก: Dedendum < Base < Pitch < Addendum")
        self.play(FadeIn(cap))

        O = np.array([-2.5, -0.4, 0])
        Ri, Rb, R, Ro = 1.3, 1.65, 1.9, 2.3

        c_ded = Circle(radius=Ri, color=WARN, stroke_width=2, stroke_opacity=0.7).move_to(O)
        c_base = Circle(radius=Rb, color=BASE_COL, stroke_width=2.5).move_to(O)
        c_pitch = Circle(radius=R, color=FIELD, stroke_width=3.5).move_to(O)
        c_add = Circle(radius=Ro, color=OK, stroke_width=2).move_to(O)

        lbl_ded = Text("Dedendum (Ri)", font_size=14, color=WARN).next_to(c_ded.point_at_angle(PI*0.75), UL, buff=0.05)
        lbl_base = Text("Base (Rb)", font_size=14, color=BASE_COL).next_to(c_base.point_at_angle(PI*0.6), UL, buff=0.05)
        lbl_pitch = Text("Pitch (R)", font_size=16, color=FIELD).next_to(c_pitch.point_at_angle(PI*0.45), UR, buff=0.05)
        lbl_add = Text("Addendum (Ro)", font_size=14, color=OK).next_to(c_add.point_at_angle(PI*0.3), UR, buff=0.05)

        self.play(
            Create(c_ded), FadeIn(lbl_ded),
            Create(c_base), FadeIn(lbl_base),
            Create(c_pitch), FadeIn(lbl_pitch),
            Create(c_add), FadeIn(lbl_add),
            run_time=1.8
        )

        # Panel Formulas
        panel = VGroup(
            Text("สูตรหลักประจำ 4 วงกลม:", font_size=20, color=OK),
            MathTex(r"R = \frac{mN}{2} = \frac{pN}{2\pi}", font_size=20, color=FIELD),
            MathTex(r"R_b = R\cos\phi", font_size=20, color=BASE_COL),
            MathTex(r"R_o = R + a\quad (a = 1.0m)", font_size=20, color=OK),
            MathTex(r"R_i = R - b\quad (b = 1.25m)", font_size=20, color=WARN),
            VGroup(
                Text("Base Pitch (ระยะพิตช์บน Base):", font_size=16, color=GRAYTXT),
                MathTex(r"p_b = p\cos\phi = \frac{2\pi R_b}{N}", font_size=20, color=WHITE),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.05),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.14).move_to([PANEL_X, 0.1, 0])

        self.play(FadeIn(panel))
        self.wait(2.5)


# ================================================================ Scene 4: Length of Action & Contact Ratio
class SG04_LengthOfAction(Scene):
    """Slides 19–25: Length of Action Z & Contact Ratio mp"""

    def construct(self):
        title = make_title("Length of Action (Z) & Contact Ratio (mp) (หน้า 19–25)")
        self.play(Write(title))

        cap = make_caption("Contact Ratio mp = Z / pb ต้องมากกว่า 1.40 เพื่อให้เฟืองหมุนเรียบไร้เสียงดัง")
        self.play(FadeIn(cap))

        # Line of action and contact points A, B, P
        O1 = np.array([-4.2, -1.2, 0])
        O2 = np.array([-0.6, 1.8, 0])

        b1 = Circle(radius=1.3, color=BASE_COL, stroke_width=2).move_to(O1)
        b2 = Circle(radius=1.3, color=BASE_COL, stroke_width=2).move_to(O2)

        # Common tangent line
        E1 = O1 + np.array([0.9, 0.93, 0])
        E2 = O2 - np.array([0.9, 0.93, 0])
        action_line = Line(E1 - (E2-E1)*0.3, E2 + (E2-E1)*0.3, color=FORCE, stroke_width=3)

        P = (E1 + E2) / 2
        A = P - (E2-E1)*0.32
        B = P + (E2-E1)*0.32

        dotA = Dot(A, color=WARN, radius=0.1)
        dotB = Dot(B, color=WARN, radius=0.1)
        dotP = Dot(P, color=OK, radius=0.1)

        lblA = Text("A (เริ่มขบ)", font_size=15, color=WARN).next_to(dotA, DL, buff=0.08)
        lblB = Text("B (หลุดขบ)", font_size=15, color=WARN).next_to(dotB, UR, buff=0.08)
        lblP = Text("P (Pitch Point)", font_size=15, color=OK).next_to(dotP, UL, buff=0.08)

        z_brace = BraceBetweenPoints(A, B, color=FIELD)
        lbl_z = Text("Z (Length of Action)", font_size=16, color=FIELD).next_to(z_brace, DR, buff=0.1)

        self.play(Create(b1), Create(b2), Create(action_line), Create(dotA), Create(dotB), Create(dotP),
                  FadeIn(lblA), FadeIn(lblB), FadeIn(lblP), Create(z_brace), FadeIn(lbl_z))

        # Side Panel
        panel = VGroup(
            Text("สูตรคำนวณ Z:", font_size=19, color=OK),
            MathTex(r"Z = \sqrt{R_{o1}^2-R_{b1}^2} + \sqrt{R_{o2}^2-R_{b2}^2} - C\sin\phi", font_size=17, color=WHITE),
            Text("นิยาม Contact Ratio:", font_size=19, color=OK),
            MathTex(r"m_p = \frac{Z}{p_b}", font_size=23, color=GEAR_IN),
            VGroup(
                Text("• mp > 1.0  : ใช้งานได้", font_size=16, color=GRAYTXT),
                Text("• mp > 1.40 : เดินเรียบ (Smooth)", font_size=17, color=OK),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.06),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([PANEL_X, 0.1, 0])

        self.play(FadeIn(panel))
        self.wait(2.5)


# ================================================================ Scene 5: Standard Gears & Manufacturing
class SG05_StandardGears(Scene):
    """Slides 26–33: Standard Tooth Systems, Module & Hobbing vs Fellows"""

    def construct(self):
        title = make_title("มาตรฐานขนาดฟัน (Module) & กรรมวิธีผลิต (หน้า 26–33)")
        self.play(Write(title))

        cap = make_caption("เงื่อนไขการขบกันได้: Module (m) และ Pressure Angle (φ) ต้องเท่ากัน")
        self.play(FadeIn(cap))

        # Table comparison of Manufacturing
        box_hob = RoundedRectangle(corner_radius=0.15, width=3.3, height=2.4, color=GEAR_IN, fill_opacity=0.1).move_to([-3.6, 0.4, 0])
        hob_title = Text("1. Hobbing (ฮอบ)", font_size=19, color=GEAR_IN).next_to(box_hob.get_top(), DOWN, buff=0.15)
        hob_desc = VGroup(
            Text("• มีดตัดรูปร่างเหมือน Rack", font_size=15, color=WHITE),
            Text("• ฟันมีดเป็นเส้นตรง", font_size=15, color=GRAYTXT),
            Text("• ผลิตเร็ว แม่นยำสูง", font_size=15, color=GRAYTXT),
            Text("• ตัดได้เฉพาะเฟืองนอก", font_size=15, color=WARN),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to(box_hob.get_center() + DOWN*0.2)

        box_fel = RoundedRectangle(corner_radius=0.15, width=3.3, height=2.4, color=GEAR_OUT, fill_opacity=0.1).move_to([-0.1, 0.4, 0])
        fel_title = Text("2. Fellows Shaper", font_size=19, color=GEAR_OUT).next_to(box_fel.get_top(), DOWN, buff=0.15)
        fel_desc = VGroup(
            Text("• มีดตัดรูปร่างเหมือน Gear", font_size=15, color=WHITE),
            Text("• ชักมีดขึ้น-ลง (Shaping)", font_size=15, color=GRAYTXT),
            Text("• ตัดเฟืองใน (Internal) ได้!", font_size=15, color=OK),
            Text("• ผลิตชิ้นงานในที่แคบได้", font_size=15, color=GRAYTXT),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to(box_fel.get_center() + DOWN*0.2)

        self.play(
            Create(box_hob), FadeIn(hob_title), FadeIn(hob_desc),
            Create(box_fel), FadeIn(fel_title), FadeIn(fel_desc)
        )

        # Right panel: Standard definitions
        panel = VGroup(
            Text("มาตรฐานฟัน British Standard:", font_size=19, color=OK),
            VGroup(
                Text("Module (ขนาดฟัน):", font_size=16, color=GRAYTXT),
                VGroup(
                    MathTex(r"m = \frac{D}{N} = \frac{p}{\pi}", font_size=20, color=WHITE),
                    Text("(mm)", font_size=15, color=WHITE)
                ).arrange(RIGHT, buff=0.1)
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.06),
            VGroup(
                Text("สัดส่วนฟันมาตรฐาน:", font_size=16, color=GRAYTXT),
                MathTex(r"a = 1.000\,m,\quad b = 1.250\,m", font_size=19, color=FIELD),
                MathTex(r"\phi = 20^\circ,\quad t = p/2", font_size=19, color=FIELD),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.06),
            Text("ระบบ US: Pd = N / D (นิ้ว)", font_size=16, color=WARN),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.14).move_to([PANEL_X, 0.1, 0])

        self.play(FadeIn(panel))
        self.wait(2.5)


# ================================================================ Scene 6: Interference & Undercutting
class SG06_InterferenceUndercut(Scene):
    """Slides 34–37: Involute Interference & Minimum Teeth Formula"""

    def construct(self):
        title = make_title("Interference & Undercutting (หน้า 34–37)")
        self.play(Write(title))

        cap = make_caption("Interference เกิดเมื่อการสัมผัสเลยจุด E ออกไป ทำให้มีด Hob กินโคนฟัน (Undercut)")
        self.play(FadeIn(cap))

        # Visual showing undercut tooth vs normal tooth
        base_line = Line([-4.8, -1.5, 0], [-0.5, -1.5, 0], color=BASE_COL, stroke_width=3)
        lbl_base = Text("Base Circle", font_size=15, color=BASE_COL).next_to(base_line, DOWN)

        # Undercut tooth outline
        normal_tooth = Polygon(
            [-4.2, -1.5, 0], [-3.8, 1.2, 0], [-3.2, 1.2, 0], [-2.8, -1.5, 0],
            color=OK, fill_opacity=0.3, stroke_width=3
        )
        lbl_normal = Text("ฟันปกติ (N >= Nmin)", font_size=16, color=OK).next_to(normal_tooth, UP)

        undercut_tooth = Polygon(
            [-1.9, -1.5, 0], [-1.7, -0.6, 0], [-2.2, -0.6, 0], [-1.8, 1.2, 0],
            [-1.2, 1.2, 0], [-0.8, -0.6, 0], [-1.3, -0.6, 0], [-1.1, -1.5, 0],
            color=WARN, fill_opacity=0.3, stroke_width=3
        )
        lbl_undercut = Text("โคนคอด! (Undercut)", font_size=16, color=WARN).next_to(undercut_tooth, UP)

        self.play(Create(base_line), FadeIn(lbl_base),
                  Create(normal_tooth), FadeIn(lbl_normal),
                  Create(undercut_tooth), FadeIn(lbl_undercut))

        # Panel Formulas
        panel = VGroup(
            Text("สูตรจำนวนฟันน้อยสุด (N_min):", font_size=19, color=OK),
            MathTex(r"N_{min} = \frac{2k}{\sin^2\phi}", font_size=23, color=WARN),
            VGroup(
                Text("ที่ φ = 20° (Full-depth k=1):", font_size=16, color=WHITE),
                VGroup(
                    MathTex(r"N_{min} = \frac{2}{\sin^2 20^\circ} = 17.09 \rightarrow \mathbf{18}", font_size=19, color=OK),
                    Text("ฟัน", font_size=15, color=OK)
                ).arrange(RIGHT, buff=0.1)
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.06),
            VGroup(
                Text("วิธีแก้ Undercutting:", font_size=17, color=WHITE),
                Text("1. เพิ่ม φ เป็น 25° (Nmin = 12 ฟัน)", font_size=15, color=GEAR_IN),
                Text("2. ใช้ฟันสั้น Stub (k=0.8, Nmin=14)", font_size=15, color=GEAR_IN),
                Text("3. Profile Shift (เลื่อนหัวคัตเตอร์)", font_size=15, color=GEAR_IN),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.06),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([PANEL_X, 0.1, 0])

        self.play(FadeIn(panel))
        self.wait(2.5)


# ================================================================ Scene 7: Master Exam Calculation
class SG07_MasterCalculation(Scene):
    """Slides 38–39: Master Problem 5-Step Protocol (24T/60T, m=3, φ=20°)"""

    def construct(self):
        title = make_title("Master Problem: ข้อสอบคำนวณ 5 ขั้นตอน (หน้า 38–39)")
        self.play(Write(title))

        cap = make_caption("โจทย์: Pinion 24T ขับ Gear 60T, Module 3 mm, φ = 20° — จงหา Z และ Contact Ratio")
        self.play(FadeIn(cap))

        # 5-step problem solving card
        steps = VGroup(
            VGroup(
                Text("ขั้น 1: ดึงค่ามาตรฐาน", font_size=17, color=OK),
                Text("a = 1.0m = 3 mm, b = 1.25m = 3.75 mm", font_size=15, color=GRAYTXT)
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.04),
            VGroup(
                Text("ขั้น 2: คำนวณรัศมี Pinion (1) & Gear (2)", font_size=17, color=OK),
                VGroup(
                    MathTex(r"R_1 = 36", font_size=16, color=WHITE), Text("mm", font_size=13, color=WHITE), MathTex(r",\quad R_{b1} = 33.829", font_size=16, color=WHITE), Text("mm", font_size=13, color=WHITE), MathTex(r",\quad R_{o1} = 39", font_size=16, color=WHITE), Text("mm", font_size=13, color=WHITE)
                ).arrange(RIGHT, buff=0.05),
                VGroup(
                    MathTex(r"R_2 = 90", font_size=16, color=WHITE), Text("mm", font_size=13, color=WHITE), MathTex(r",\quad R_{b2} = 84.572", font_size=16, color=WHITE), Text("mm", font_size=13, color=WHITE), MathTex(r",\quad R_{o2} = 93", font_size=16, color=WHITE), Text("mm", font_size=13, color=WHITE)
                ).arrange(RIGHT, buff=0.05),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.04),
            VGroup(
                Text("ขั้น 3: ระยะศูนย์กลาง C", font_size=17, color=OK),
                VGroup(
                    MathTex(r"C = R_1 + R_2 = 36 + 90 = 126.000", font_size=16, color=FIELD), Text("mm", font_size=13, color=FIELD)
                ).arrange(RIGHT, buff=0.05)
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.04),
            VGroup(
                Text("ขั้น 4: คำนวณ Z, pb และ mp", font_size=17, color=OK),
                VGroup(
                    MathTex(r"Z = \sqrt{39^2-33.829^2} + \sqrt{93^2-84.572^2} - 126\sin20^\circ = \mathbf{14.997}", font_size=16, color=WARN), Text("mm", font_size=13, color=WARN)
                ).arrange(RIGHT, buff=0.05),
                VGroup(
                    MathTex(r"p_b = \frac{2\pi(33.829)}{24} = \mathbf{8.8564}", font_size=16, color=WHITE), Text("mm", font_size=13, color=WHITE)
                ).arrange(RIGHT, buff=0.05),
                VGroup(
                    MathTex(r"m_p = \frac{Z}{p_b} = \frac{14.997}{8.8564} = \mathbf{1.693}", font_size=17, color=OK),
                    Text("(> 1.40 เดินเรียบ ผ่าน!)", font_size=15, color=OK)
                ).arrange(RIGHT, buff=0.1)
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.04),
            VGroup(
                Text("ขั้น 5: เช็ค Undercutting", font_size=17, color=OK),
                VGroup(
                    MathTex(r"N_1 = 24 > N_{min}(17.09)\ \rightarrow", font_size=16, color=OK),
                    Text("ปลอดภัย ไม่เกิด Undercut", font_size=15, color=OK)
                ).arrange(RIGHT, buff=0.1)
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.04)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.14).move_to([-1.2, -0.1, 0])

        self.play(FadeIn(steps, shift=UP*0.2), run_time=2.0)
        self.wait(3.0)
