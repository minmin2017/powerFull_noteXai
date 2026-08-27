from manim import *

THAI_FONT = "Loma"

class Part7_ExampleProblem(Scene):
    def construct(self):
        # ---------------- Title ----------------
        title = Text("Part 7: โจทย์ปัญหา Planetary (หน้า 74)", font=THAI_FONT, font_size=40, color=BLUE)
        subtitle = Text("การประยุกต์ใช้ Tabular Method แก้โจทย์จริง", font=THAI_FONT, font_size=30, color=YELLOW)
        header = VGroup(title, subtitle).arrange(DOWN, buff=0.2).to_edge(UP)
        self.play(Write(header))
        self.wait(1)

        # ---------------- Problem Statement ----------------
        prob_text = Text("ให้: N2=20, N4=56, N5=24, N6=35, N7=76\nเฟือง 7 ตรึง (Y=-X), อินพุต ω2 = 100 rpm\nจงหาความเร็วเอาต์พุต ω6", font=THAI_FONT, font_size=24)
        prob_text.next_to(header, DOWN, buff=0.5)
        self.play(Write(prob_text))
        self.wait(2)

        # ---------------- Table Solution ----------------
        t_head = Text("ตารางสมการบรรทัดสุดท้าย (Total):", font=THAI_FONT, font_size=24, color=WHITE)
        t_head.next_to(prob_text, DOWN, buff=0.5).align_to(prob_text, LEFT)
        
        eq1 = MathTex(r"\text{Arm } (3): \omega_3 = X")
        eq2 = MathTex(r"\text{Gear } (2): \omega_2 = X - 3.8Y")
        eq3 = MathTex(r"\text{Gear } (7): \omega_7 = X + Y = 0 \Rightarrow Y = -X")
        eq4 = MathTex(r"\text{Gear } (6): \omega_6 = X + 0.93Y")
        
        eqs = VGroup(eq1, eq2, eq3, eq4).arrange(DOWN, aligned_edge=LEFT).next_to(t_head, DOWN, buff=0.3)
        eqs.align_to(prob_text, LEFT)

        self.play(Write(t_head))
        self.play(Write(eqs))
        self.wait(3)

        # ---------------- Solving ----------------
        solve1 = MathTex(r"\omega_2 = X - 3.8(-X) = 100")
        solve2 = MathTex(r"4.8X = 100 \Rightarrow X = 20.83 \text{ rpm}")
        sol_group = VGroup(solve1, solve2).arrange(DOWN, aligned_edge=LEFT).next_to(eqs, RIGHT, buff=1.0)
        
        self.play(Write(solve1))
        self.play(Write(solve2))
        self.wait(2)

        # ---------------- Final Answer ----------------
        final_ans = MathTex(r"\omega_6 = 20.83 + 0.93(-20.83) = 1.45 \text{ rpm}", color=GREEN)
        final_ans.next_to(sol_group, DOWN, buff=0.5).align_to(sol_group, LEFT)
        
        box = SurroundingRectangle(final_ans, color=GREEN)
        
        self.play(Write(final_ans))
        self.play(Create(box))
        
        note = Text("ทดรอบได้มหาศาล (100 -> 1.45) นี่แหละจุดขายของ Planetary!", font=THAI_FONT, font_size=20, color=YELLOW)
        note.next_to(box, DOWN, buff=0.3)
        self.play(Write(note))
        self.wait(3)
