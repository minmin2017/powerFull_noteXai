from manim import *
import numpy as np

THAI_FONT = "Loma"

class AngularVelocityRatio(Scene):
    def construct(self):
        A = np.array([0.0, 3.0, 0])
        B = np.array([0.0, -3.0, 0])
        Q = np.array([-1.5, 0.5, 0])
        
        center_line = DashedLine(A, B, color=GRAY)
        dot_A = Dot(A, color=WHITE); label_A = Text("A", font="sans-serif", font_size=24).next_to(A, UP)
        dot_B = Dot(B, color=WHITE); label_B = Text("B", font="sans-serif", font_size=24).next_to(B, DOWN)
        dot_Q = Dot(Q, color=YELLOW); label_Q = Text("Q", font="sans-serif", font_size=24).next_to(Q, LEFT)
        
        title = Text("จุด A, B (จุดหมุน) และ Q (จุดสัมผัส)", font=THAI_FONT, font_size=32).to_edge(UP)
        self.play(Write(title))
        self.play(Create(center_line), FadeIn(dot_A, label_A, dot_B, label_B, dot_Q, label_Q))
        self.wait(1)
        
        theta = -20 * DEGREES
        v_n = np.array([np.cos(theta), np.sin(theta), 0])
        normal_line = Line(Q - 4*v_n, Q + 5*v_n, color=RED)
        normal_label = Text("Contact Normal", font="sans-serif", font_size=24, color=RED).next_to(normal_line.get_end(), DOWN)
        self.play(Transform(title, Text("เส้น Contact Normal ผ่านจุด Q", font=THAI_FONT, font_size=32).to_edge(UP)))
        self.play(Create(normal_line), Write(normal_label))
        
        R = normal_line.get_projection(A)
        S = normal_line.get_projection(B)
        dot_R = Dot(R, color=BLUE); label_R = Text("R", font="sans-serif", font_size=24, color=BLUE).next_to(R, UP)
        dot_S = Dot(S, color=BLUE); label_S = Text("S", font="sans-serif", font_size=24, color=BLUE).next_to(S, DOWN)
        line_AR = Line(A, R, color=BLUE)
        line_BS = Line(B, S, color=BLUE)
        elbow_R = RightAngle(line_AR, normal_line, length=0.2, quadrant=(1,-1))
        elbow_S = RightAngle(line_BS, normal_line, length=0.2, quadrant=(-1,1))
        
        self.play(Transform(title, Text("AR และ BS ตั้งฉากกับ Contact Normal", font=THAI_FONT, font_size=32).to_edge(UP)))
        self.play(Create(line_AR), Create(line_BS), FadeIn(dot_R, label_R, dot_S, label_S, elbow_R, elbow_S))
        
        line_AQ = Line(A, Q, color=WHITE); line_BQ = Line(B, Q, color=WHITE)
        self.play(Create(line_AQ), Create(line_BQ))
        
        P = Q + 2.5 * v_n
        dot_P = Dot(P, color=GREEN); label_P = Text("P", font="sans-serif", font_size=24, color=GREEN).next_to(P, DOWN)
        
        dir_v2 = np.array([-line_AQ.get_vector()[1], line_AQ.get_vector()[0], 0])
        dir_v2 = dir_v2 / np.linalg.norm(dir_v2)
        if dir_v2[0] < 0: dir_v2 = -dir_v2
        
        dir_v3 = np.array([-line_BQ.get_vector()[1], line_BQ.get_vector()[0], 0])
        dir_v3 = dir_v3 / np.linalg.norm(dir_v3)
        if dir_v3[0] < 0: dir_v3 = -dir_v3
        
        dir_perp_n = np.array([-v_n[1], v_n[0], 0])
        E = line_intersection([Q, Q+dir_v2], [P, P+dir_perp_n])
        F = line_intersection([Q, Q+dir_v3], [P, P+dir_perp_n])
        
        dot_E = Dot(E, color=YELLOW); label_E = Text("E", font="sans-serif", font_size=24, color=YELLOW).next_to(E, RIGHT)
        dot_F = Dot(F, color=YELLOW); label_F = Text("F", font="sans-serif", font_size=24, color=YELLOW).next_to(F, RIGHT)
        
        vec_v2 = Arrow(Q, E, buff=0, color=YELLOW); vec_v3 = Arrow(Q, F, buff=0, color=ORANGE)
        label_v2 = MathTex(r"v_{Q2}").next_to(E, UP); label_v3 = MathTex(r"v_{Q3}").next_to(F, DOWN)
        
        self.play(Transform(title, Text("ความเร็ว vQ2 และ vQ3 มีภาพฉายบน Contact Normal เท่ากันที่ P", font=THAI_FONT, font_size=28).to_edge(UP)))
        self.play(GrowArrow(vec_v2), GrowArrow(vec_v3), Write(label_v2), Write(label_v3))
        
        line_EP = DashedLine(E, P, color=GREEN); line_FP = DashedLine(F, P, color=GREEN)
        elbow_P1 = RightAngle(line_EP, Line(Q, P), length=0.2, quadrant=(-1,1))
        elbow_P2 = RightAngle(line_FP, Line(Q, P), length=0.2, quadrant=(1,-1))
        
        self.play(Create(line_EP), Create(line_FP), FadeIn(dot_P, label_P, dot_E, label_E, dot_F, label_F, elbow_P1, elbow_P2))
        
        self.play(Transform(title, Text("พิจารณาสามเหลี่ยมคล้าย AQR และ EQP", font=THAI_FONT, font_size=32).to_edge(UP)))
        tri_AQR = Polygon(A, Q, R, color=BLUE, fill_opacity=0.3)
        tri_EQP = Polygon(E, Q, P, color=YELLOW, fill_opacity=0.3)
        self.play(FadeIn(tri_AQR), FadeIn(tri_EQP))
        
        eq1 = MathTex(r"\Delta AQR \sim \Delta EQP \Rightarrow \frac{EQ}{PQ} = \frac{AQ}{AR}").to_corner(UL).shift(DOWN)
        bg1 = BackgroundRectangle(eq1, color=BLACK, fill_opacity=0.8, buff=0.2)
        self.play(FadeIn(bg1), Write(eq1))
        self.wait(2)
        
        self.play(FadeOut(tri_AQR), FadeOut(tri_EQP), FadeOut(bg1), FadeOut(eq1))
        self.play(Transform(title, Text("พิจารณาสามเหลี่ยมคล้าย BQS และ FQP", font=THAI_FONT, font_size=32).to_edge(UP)))
        tri_BQS = Polygon(B, Q, S, color=BLUE, fill_opacity=0.3)
        tri_FQP = Polygon(F, Q, P, color=ORANGE, fill_opacity=0.3)
        self.play(FadeIn(tri_BQS), FadeIn(tri_FQP))
        
        eq2 = MathTex(r"\Delta BQS \sim \Delta FQP \Rightarrow \frac{FQ}{PQ} = \frac{BQ}{BS}").to_corner(UL).shift(DOWN)
        bg2 = BackgroundRectangle(eq2, color=BLACK, fill_opacity=0.8, buff=0.2)
        self.play(FadeIn(bg2), Write(eq2))
        self.wait(2)
        
        self.play(FadeOut(tri_BQS), FadeOut(tri_FQP), FadeOut(bg2), FadeOut(eq2))
        self.play(Transform(title, Text("สรุปอัตราส่วนความเร็วเชิงมุม", font=THAI_FONT, font_size=32).to_edge(UP)))
        
        eq3 = MathTex(r"\frac{\omega_2}{\omega_3} = \frac{v_{Q2}/AQ}{v_{Q3}/BQ} = \frac{EQ/AQ}{FQ/BQ} = \frac{EQ \cdot BQ}{FQ \cdot AQ}")
        
        text_sub = Text("แทนค่าจากสามเหลี่ยมคล้าย:", font=THAI_FONT, font_size=24)
        eq_sub = MathTex(r"\quad \frac{EQ}{AQ} = \frac{PQ}{AR} \quad \text{and} \quad \frac{BQ}{FQ} = \frac{BS}{PQ}")
        sub_group = VGroup(text_sub, eq_sub).arrange(RIGHT)
        
        eq4 = MathTex(r"\therefore \frac{\omega_2}{\omega_3} = \frac{PQ}{AR} \cdot \frac{BS}{PQ} = \frac{BS}{AR}")
        
        conclusion = VGroup(eq3, sub_group, eq4).arrange(DOWN, buff=0.5).to_edge(LEFT)
        bg3 = BackgroundRectangle(conclusion, color=BLACK, fill_opacity=0.8, buff=0.2)
        self.play(FadeIn(bg3), Write(conclusion))
        self.wait(3)

