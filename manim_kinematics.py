from manim import *
import numpy as np

THAI_FONT = "Loma"

class Step1_VelocityA(MovingCameraScene):
    def construct(self):
        title = Text("ขั้นที่ 1: หาความเร็วของจุด A", font=THAI_FONT).scale(0.8).to_edge(UP)
        self.play(Write(title))

        rack = Line(LEFT*5, RIGHT*5, color=GRAY).shift(DOWN*3)
        rack_teeth = VGroup(*[Line(rack.point_from_proportion(i), rack.point_from_proportion(i) + UP*0.2, color=GRAY) for i in np.linspace(0, 1, 25)])
        self.add(rack, rack_teeth)

        O_pos = ORIGIN
        gear_radius = 3.0
        gear = Circle(radius=gear_radius, color=BLUE, fill_opacity=0.2).move_to(O_pos)
        center_dot = Dot(O_pos)
        label_O = MathTex("O").next_to(center_dot, UR, buff=0.1)
        
        A_pos = O_pos + DOWN*2.0
        A_dot = Dot(A_pos, color=RED)
        label_A = MathTex("A").next_to(A_dot, DR, buff=0.1)

        C_pos = O_pos + DOWN*3.0
        C_dot = Dot(C_pos, color=GREEN)
        label_C = MathTex("IC").next_to(C_dot, DL, buff=0.1)

        self.play(FadeIn(gear, center_dot, label_O, A_dot, label_A, C_dot, label_C))

        arc = Arc(radius=1.5, start_angle=0, angle=PI/2, color=YELLOW).add_tip()
        omega_label = MathTex(r"\omega = 6 \text{ rad/s}").next_to(arc, UR)
        self.play(Create(arc), Write(omega_label))

        r_line = DashedLine(C_pos, A_pos, color=YELLOW)
        r_label = MathTex(r"1 \text{ cm}").next_to(r_line, RIGHT)
        self.play(Create(r_line), Write(r_label))

        vA_vec = Arrow(A_pos, A_pos + LEFT*3, buff=0, color=RED)
        vA_label = MathTex(r"v_A = 6 \text{ cm/s}").next_to(vA_vec, UP)
        self.play(GrowArrow(vA_vec), Write(vA_label))
        
        self.play(self.camera.frame.animate.move_to(A_pos).set(width=8))
        self.wait(2)

class Step2_VelocityB(MovingCameraScene):
    def construct(self):
        title = Text("ขั้นที่ 2: หาความเร็วของจุด B", font=THAI_FONT).scale(0.8).to_edge(UP)
        self.play(Write(title))

        O_pos = ORIGIN
        A_pos = DOWN*2.0
        B_pos = A_pos + RIGHT * 8 * np.cos(60*DEGREES) + UP * 8 * np.sin(60*DEGREES)

        arm = Line(A_pos, B_pos, color=ORANGE, stroke_width=6)
        A_dot = Dot(A_pos, color=RED)
        B_dot = Dot(B_pos, color=BLUE)

        guide = DashedLine(B_pos + LEFT*3, B_pos + RIGHT*3, color=GRAY)
        
        self.play(Create(guide), Create(arm), FadeIn(A_dot, B_dot))

        label_A = MathTex("A").next_to(A_dot, DOWN)
        label_B = MathTex("B").next_to(B_dot, UP)
        self.add(label_A, label_B)

        vA_vec = Arrow(A_pos, A_pos + LEFT*2, buff=0, color=RED)
        vA_label = MathTex("v_A").next_to(vA_vec, DOWN)
        self.play(GrowArrow(vA_vec), Write(vA_label))

        vB_vec = Arrow(B_pos, B_pos + LEFT*2, buff=0, color=BLUE)
        vB_label = MathTex("v_B").next_to(vB_vec, UP)
        self.play(GrowArrow(vB_vec), Write(vB_label))

        text1 = Text("ความเร็วทั้งสองอยู่ในแนวระดับ (แนวนอน)", font=THAI_FONT).scale(0.6).to_edge(DOWN).shift(UP*1)
        self.play(Write(text1))
        self.wait(2)

        omega_label = MathTex(r"\omega_{AB} = 0").scale(1.5).move_to(LEFT*2)
        v_ans = MathTex(r"v_B = v_A = 6 \text{ cm/s } (\leftarrow)").scale(1.5).next_to(omega_label, DOWN)
        
        self.play(Write(omega_label), Write(v_ans))
        self.wait(3)
