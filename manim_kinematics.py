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

        # Draw IC (Instantaneous Center)
        C_pos = O_pos + DOWN*3.0
        C_dot = Dot(C_pos, color=GREEN)
        label_C = MathTex("IC").next_to(C_dot, DL, buff=0.1)

        self.play(FadeIn(gear, center_dot, label_O, A_dot, label_A, C_dot, label_C))
        
        ic_text = Text("จุดที่สัมผัสพื้นคือจุดหมุนชั่วขณะ (IC)", font=THAI_FONT).scale(0.5).to_edge(DOWN)
        self.play(Write(ic_text))
        self.wait(1)

        arc = Arc(radius=1.5, start_angle=0, angle=PI/2, color=YELLOW).add_tip()
        omega_label = MathTex(r"\omega = 6 \text{ rad/s}").next_to(arc, UR)
        self.play(Create(arc), Write(omega_label))

        # Show distance
        r_line = DashedLine(C_pos, A_pos, color=YELLOW)
        r_label = MathTex(r"r_{A/IC} = 1 \text{ cm}").next_to(r_line, RIGHT)
        self.play(Create(r_line), Write(r_label))
        
        self.play(FadeOut(ic_text))

        # Show derivation
        eq1 = MathTex(r"v_A = \omega \cdot r_{A/IC}").to_edge(LEFT).shift(UP*1)
        eq2 = MathTex(r"v_A = 6 \cdot 1").next_to(eq1, DOWN, aligned_edge=LEFT)
        eq3 = MathTex(r"v_A = 6 \text{ cm/s (\leftarrow)}").next_to(eq2, DOWN, aligned_edge=LEFT)
        
        self.play(Write(eq1))
        self.wait(1)
        self.play(Write(eq2))
        self.wait(1)
        self.play(Write(eq3))
        
        vA_vec = Arrow(A_pos, A_pos + LEFT*3, buff=0, color=RED)
        vA_label = MathTex(r"v_A").next_to(vA_vec, UP)
        self.play(GrowArrow(vA_vec), Write(vA_label))
        
        self.wait(2)

class Step2_VelocityB(MovingCameraScene):
    def construct(self):
        title = Text("ขั้นที่ 2: หาความเร็วของจุด B", font=THAI_FONT).scale(0.8).to_edge(UP)
        self.play(Write(title))

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
        
        eq_rel = MathTex(r"\vec{v}_B = \vec{v}_A + \vec{v}_{B/A}").to_edge(LEFT).shift(UP*2)
        self.play(Write(eq_rel))
        self.wait(1)

        text1 = Text("เนื่องจาก v_A และ v_B อยู่ในแนวนอนทั้งคู่", font=THAI_FONT).scale(0.5).next_to(eq_rel, DOWN, aligned_edge=LEFT)
        text2 = Text("v_{B/A} จึงต้องเป็นแนวนอนด้วยเพื่อให้สมการเป็นจริง", font=THAI_FONT).scale(0.5).next_to(text1, DOWN, aligned_edge=LEFT)
        self.play(Write(text1))
        self.play(Write(text2))
        self.wait(1)
        
        # Show v_{B/A} perpendicular constraint
        perp_line = DashedLine(B_pos + LEFT + UP*np.sqrt(3), B_pos + RIGHT + DOWN*np.sqrt(3), color=YELLOW)
        perp_label = MathTex(r"\vec{v}_{B/A} \perp AB").next_to(perp_line, UR)
        self.play(Create(perp_line), Write(perp_label))
        
        text3 = Text("แต่ v_{B/A} ต้องตั้งฉากกับแขน AB (เอียง 60°)", font=THAI_FONT).scale(0.5).next_to(text2, DOWN, aligned_edge=LEFT)
        text4 = Text("จึงเป็นไปไม่ได้ที่ v_{B/A} จะเป็นแนวนอน นอกจาก v_{B/A} = 0", font=THAI_FONT).scale(0.5).next_to(text3, DOWN, aligned_edge=LEFT)
        
        self.play(Write(text3))
        self.wait(1)
        self.play(Write(text4))
        self.wait(1)
        
        eq_vba = MathTex(r"\vec{v}_{B/A} = 0 \implies \omega_{AB} = 0").next_to(text4, DOWN, aligned_edge=LEFT).set_color(YELLOW)
        self.play(Write(eq_vba))
        self.wait(1)

        v_ans = MathTex(r"v_B = v_A = 6 \text{ cm/s } (\leftarrow)").next_to(eq_vba, DOWN, aligned_edge=LEFT).set_color(GREEN)
        self.play(Write(v_ans))
        self.wait(3)
