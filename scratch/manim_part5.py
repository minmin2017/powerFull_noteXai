from manim import *

THAI_FONT = "Loma"

class Part5_FormulaMethod(Scene):
    def construct(self):
        # ---------------- Title ----------------
        title = Text("Part 5: Planetary Gear - Formula Method", font=THAI_FONT, font_size=40, color=BLUE)
        subtitle = Text("การคำนวณด้วยสูตร (หน้า 62-68)", font=THAI_FONT, font_size=30, color=YELLOW)
        header = VGroup(title, subtitle).arrange(DOWN, buff=0.2).to_edge(UP)
        self.play(Write(header))
        self.wait(1)

        # ---------------- The Formula ----------------
        formula = MathTex(
            r"\frac{\omega_L - \omega_A}{\omega_F - \omega_A} = -\frac{N_F}{N_L}",
            font_size=60
        )
        
        # We need to surround it with Thai explanation
        t_l = Text("L = Last Gear (ตัวตาม)", font=THAI_FONT, font_size=24, color=YELLOW)
        t_f = Text("F = First Gear (ตัวขับ)", font=THAI_FONT, font_size=24, color=BLUE)
        t_a = Text("A = Arm (ก้านพา)", font=THAI_FONT, font_size=24, color=RED)
        
        legend = VGroup(t_l, t_f, t_a).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        
        content = VGroup(formula, legend).arrange(RIGHT, buff=1.5)
        content.shift(DOWN * 0.5)

        self.play(Write(formula))
        self.wait(1)
        self.play(Write(legend))
        self.wait(2)

        # ---------------- Highlight meaning ----------------
        meaning1 = Text("สูตรนี้มาจาก 'ความเร็วสัมพัทธ์' เทียบกับ Arm", font=THAI_FONT, font_size=24)
        meaning2 = Text("สังเกต: ทุกความเร็วจะถูกจับลบด้วย ωA (เสมือนมองว่า Arm หยุดนิ่ง)", font=THAI_FONT, font_size=24, color=GREEN)
        meanings = VGroup(meaning1, meaning2).arrange(DOWN, buff=0.2).next_to(content, DOWN, buff=1.0)
        
        self.play(Write(meaning1))
        self.play(Write(meaning2))
        self.wait(3)
