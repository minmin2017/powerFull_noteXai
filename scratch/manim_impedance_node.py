"""
scratch/manim_impedance_node.py
Fast render explaining Node Force Balance & Mass Inertia (D'Alembert & Impedance)
"""
from manim import *
import numpy as np

THAI_FONT = "Loma"
FORCE = "#66BB6A"
WARN  = "#FF7043"
OK    = "#26C6DA"
BLUE_M = "#42A5F5"
GRAYTXT = "#B0BEC5"

class NodePhysics(Scene):
    def construct(self):
        # 1. Title
        title = Text("ทำไมสมดุลแรงที่มวล M จึงเกิดการเคลื่อนที่ (F = Ma)?", font=THAI_FONT, font_size=26, color=WHITE).to_edge(UP, buff=0.5)
        self.play(FadeIn(title))

        # 2. 3D-like Mass on Plane
        plane = Rectangle(width=6.0, height=0.3, color=GRAY, fill_opacity=0.3).move_to([-2.5, -1.8, 0])
        ground_lines = VGroup(*[Line([-5.5 + i*0.5, -1.95, 0], [-5.2 + i*0.5, -2.25, 0], color=GRAY) for i in range(12)])
        
        # Mass block
        mass = RoundedRectangle(corner_radius=0.1, width=1.8, height=1.4, color=BLUE_M, fill_opacity=0.8).move_to([-2.5, -0.9, 0])
        lbl_m = Text("มวล M", font=THAI_FONT, font_size=20, color=WHITE).move_to(mass.get_center())

        # Spring & Damper from Wall
        wall = Line([-5.5, -0.2, 0], [-5.5, -1.8, 0], color=GRAY, stroke_width=6)
        spring = Line([-5.5, -0.5, 0], [-3.4, -0.5, 0], color=WARN, stroke_width=4)
        damper = Line([-5.5, -1.3, 0], [-3.4, -1.3, 0], color=OK, stroke_width=4)
        
        lbl_k = Text("Spring K", font_size=14, color=WARN).next_to(spring, UP, buff=0.1)
        lbl_b = Text("Damper B", font_size=14, color=OK).next_to(damper, UP, buff=0.1)

        self.play(Create(plane), Create(ground_lines), Create(wall), FadeIn(mass), FadeIn(lbl_m), Create(spring), Create(damper), FadeIn(lbl_k), FadeIn(lbl_b))

        # 3. Applied Force vs Reaction Forces
        f_in = Arrow([-1.6, -0.9, 0], [0.2, -0.9, 0], color=FORCE, stroke_width=7)
        lbl_fin = Text("แรงภายนอก F(t)", font=THAI_FONT, font_size=16, color=FORCE).next_to(f_in, UP, buff=0.1)

        f_react_k = Arrow([-3.4, -0.5, 0], [-4.8, -0.5, 0], color=WARN, stroke_width=5)
        f_react_b = Arrow([-3.4, -1.3, 0], [-4.8, -1.3, 0], color=OK, stroke_width=5)

        self.play(GrowArrow(f_in), FadeIn(lbl_fin), GrowArrow(f_react_k), GrowArrow(f_react_b))

        # 4. Right Explanation Panel
        p_box = RoundedRectangle(corner_radius=0.15, width=5.2, height=4.2, color=GRAYTXT, fill_opacity=0.15).move_to([3.6, -0.2, 0])
        p_t = Text("หลักการสมดุลแรง (D'Alembert)", font=THAI_FONT, font_size=20, color=OK).move_to([3.6, 1.5, 0])
        
        eq1 = MathTex(r"\Sigma F = F(t) - F_K - F_B = M a", font_size=26, color=WHITE).move_to([3.6, 0.8, 0])
        eq2 = MathTex(r"F_{net} = M \left(\frac{d^2 x}{dt^2}\right) = M D^2 x", font_size=26, color=FORCE).move_to([3.6, 0.1, 0])
        
        exp1 = Text("• แรงสุทธิไม่เป็นศูนย์ → มวลมีความเร่ง", font=THAI_FONT, font_size=15, color=WHITE).move_to([3.6, -0.6, 0])
        exp2 = Text("• อิมพีแดนซ์มวล: Z_M = 1 / (M D²)", font=THAI_FONT, font_size=16, color=OK).move_to([3.6, -1.1, 0])
        exp3 = Text("• ใน Block Diagram มวลทำหน้าที่อินทิเกรต", font=THAI_FONT, font_size=15, color=GRAYTXT).move_to([3.6, -1.6, 0])

        self.play(Create(p_box), FadeIn(p_t), FadeIn(eq1), FadeIn(eq2), FadeIn(exp1), FadeIn(exp2), FadeIn(exp3))
        self.wait(2.5)

        # Move Mass
        self.play(
            mass.animate.shift(RIGHT*0.6),
            lbl_m.animate.shift(RIGHT*0.6),
            f_in.animate.shift(RIGHT*0.6),
            lbl_fin.animate.shift(RIGHT*0.6),
            spring.animate.put_start_and_end_on([-5.5, -0.5, 0], [-2.8, -0.5, 0]),
            damper.animate.put_start_and_end_on([-5.5, -1.3, 0], [-2.8, -1.3, 0]),
            run_time=1.5
        )
        self.wait(2.0)
