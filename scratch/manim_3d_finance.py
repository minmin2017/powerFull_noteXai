"""
scratch/manim_3d_finance.py
3D Finance: Compound Interest & Portfolio Asset Growth in 3D Space
"""
from manim import *
import numpy as np

THAI_FONT = "Loma"
GOLD = "#FFD700"
GREEN_UP = "#00E676"
BLUE_3D = "#29B6F6"
PURPLE_3D = "#AB47BC"
GRAYTXT = "#B0BEC5"

class Finance3D(ThreeDScene):
    def construct(self):
        # 1. 2D Fixed Title Frame
        self.set_camera_orientation(phi=0, theta=-90*DEGREES)
        title = Text("กลไกการเติบโตทางการเงิน 3 มิติ (3D Financial Growth)", font=THAI_FONT, font_size=28, color=GOLD).to_edge(UP, buff=0.4)
        sub = Text("พลังของดอกเบี้ยทบต้น (Compound Interest) • Portfolio Frontier", font=THAI_FONT, font_size=18, color=GRAYTXT).next_to(title, DOWN, buff=0.2)
        
        self.add_fixed_in_frame_mobjects(title, sub)
        self.play(FadeIn(title), FadeIn(sub))
        self.wait(1.0)

        # 2. 3D Setup: Axes & Camera Rotation
        axes = ThreeDAxes(
            x_range=[0, 10, 2],
            y_range=[0, 10, 2],
            z_range=[0, 10, 2],
            x_length=5.5,
            y_length=5.5,
            z_length=4.5
        ).shift(DOWN*0.5 + LEFT*0.5)

        x_lbl = Text("เวลา (ปี)", font=THAI_FONT, font_size=16, color=WHITE).next_to(axes.x_axis, RIGHT, buff=0.2)
        y_lbl = Text("ความเสี่ยง (Risk)", font=THAI_FONT, font_size=16, color=WHITE).next_to(axes.y_axis, UP, buff=0.2)
        z_lbl = Text("ผลตอบแทน (Return)", font=THAI_FONT, font_size=16, color=GOLD).next_to(axes.z_axis, OUT, buff=0.2)

        self.play(Create(axes), FadeIn(x_lbl), FadeIn(y_lbl), FadeIn(z_lbl))
        self.move_camera(phi=65*DEGREES, theta=-45*DEGREES, run_time=2.0)

        # 3. 3D Exponential Growth Curve (Compound Interest)
        curve1 = ParametricFunction(
            lambda t: axes.c2p(t, 0.2*t, 0.1 * np.exp(0.48*t)),
            t_range=[0, 9.5],
            color=GREEN_UP,
            stroke_width=6
        )

        # 3D Linear Growth Curve (Simple Savings)
        curve2 = ParametricFunction(
            lambda t: axes.c2p(t, 0.1*t, 0.6*t),
            t_range=[0, 9.5],
            color=GRAYTXT,
            stroke_width=4
        )

        lbl_c1 = Text("พอร์ตทบต้นแบบก้าวกระโดด", font=THAI_FONT, font_size=16, color=GREEN_UP)
        lbl_c2 = Text("เงินออมแบบเส้นตรง (Linear)", font=THAI_FONT, font_size=16, color=GRAYTXT)
        
        self.play(Create(curve2), Create(curve1), run_time=2.5)

        # 4. 3D Pillars (Asset Allocation Bars)
        pillars = VGroup()
        heights = [1.5, 3.2, 5.8, 8.5]
        colors = [BLUE_3D, PURPLE_3D, GREEN_UP, GOLD]
        for i, (h, c) in enumerate(zip(heights, colors)):
            x_pos = 2.0 + i*2.2
            y_pos = 1.0 + i*1.2
            p = Prism(dimensions=[0.6, 0.6, h*0.4], fill_opacity=0.85, fill_color=c, stroke_width=1)
            p.move_to(axes.c2p(x_pos, y_pos, h*0.2))
            pillars.add(p)

        self.play(FadeIn(pillars, shift=UP*0.5), run_time=1.5)

        # Rotate camera around 3D financial landscape
        self.begin_ambient_camera_rotation(rate=0.25)
        self.wait(3.0)
        self.stop_ambient_camera_rotation()

        # 5. Fixed Summary Card
        card = RoundedRectangle(corner_radius=0.15, width=6.5, height=2.2, color=GOLD, fill_opacity=0.85, stroke_width=2).to_edge(DOWN, buff=0.5)
        c_eq = MathTex(r"A = P \left(1 + \frac{r}{n}\right)^{nt}", font_size=28, color=BLACK).move_to(card.get_center() + UP*0.4)
        c_txt = Text(""Compound interest is the eighth wonder of the world"", font_size=16, color=BLACK).move_to(card.get_center() + DOWN*0.4)
        
        card_grp = VGroup(card, c_eq, c_txt)
        self.add_fixed_in_frame_mobjects(card_grp)
        self.play(FadeIn(card_grp, shift=UP*0.3))
        self.wait(2.5)
