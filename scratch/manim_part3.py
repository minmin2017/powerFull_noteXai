from manim import *

THAI_FONT = "Tahoma"

class Part3_CompoundGears(Scene):
    def construct(self):
        title = Text("Part 3: Compound Gear Train (หน้า 49-52)", font=THAI_FONT, font_size=40, color=BLUE)
        title.to_edge(UP, buff=0.5)
        self.play(Write(title))
        
        # ---------------------------------------------------------
        # Page 49: What is a Compound Gear?
        # ---------------------------------------------------------
        def_title = Text("หน้า 49: Compound Gear คืออะไร?", font=THAI_FONT, font_size=32, color=YELLOW)
        def_title.next_to(title, DOWN, buff=0.3)
        self.play(Write(def_title))
        
        box = Rectangle(width=10, height=2, color=WHITE, fill_opacity=0.1)
        def_text = Text("คือระบบที่มี เฟือง 2 ตัว (หรือมากกว่า) ยึดติดบน 'เพลาเดียวกัน'\nทำให้เฟืองทั้งสองหมุนไปด้วย ความเร็วเชิงมุม (ω) เท่ากันเป๊ะ!", 
                        font=THAI_FONT, font_size=24, color=WHITE).move_to(box.get_center())
        
        def_group = VGroup(box, def_text).move_to(ORIGIN)
        self.play(Create(box), Write(def_text))
        self.wait(3)
        
        self.play(FadeOut(def_group, def_title))
        
        # ---------------------------------------------------------
        # Page 50-51: Visualizing Compound Gear & Formula
        # ---------------------------------------------------------
        form_title = Text("หน้า 50-51: การคำนวณอัตราทด (Train Value)", font=THAI_FONT, font_size=32, color=YELLOW)
        form_title.next_to(title, DOWN, buff=0.3)
        self.play(Write(form_title))
        
        # Draw gears
        # Shaft 1: Gear 2 (Input)
        shaft1 = Line(UP*0.5, DOWN*0.5, color=GREY, stroke_width=8).shift(LEFT*4)
        g2 = Circle(radius=1, color=GREEN).move_to(shaft1.get_center())
        l2 = Text("N2 (Input)", font=THAI_FONT, font_size=18).move_to(g2)
        
        # Shaft 2: Gear 3 (Driven by 2) and Gear 4 (Compound with 3)
        shaft2 = Line(UP*0.5, DOWN*0.5, color=GREY, stroke_width=8).shift(LEFT*1.5)
        g3 = Circle(radius=1.5, color=RED).move_to(shaft2.get_center())
        g4 = Circle(radius=0.7, color=ORANGE).move_to(shaft2.get_center()) # Compounded
        l3 = Text("N3", font=THAI_FONT, font_size=18).next_to(g3, UP)
        l4 = Text("N4", font=THAI_FONT, font_size=18).next_to(g4, DOWN)
        
        # Shaft 3: Gear 5 (Driven by 4)
        shaft3 = Line(UP*0.5, DOWN*0.5, color=GREY, stroke_width=8).shift(RIGHT*0.7)
        g5 = Circle(radius=1.5, color=BLUE).move_to(shaft3.get_center())
        l5 = Text("N5 (Output)", font=THAI_FONT, font_size=18).move_to(g5)
        
        gears = VGroup(shaft1, g2, l2, shaft2, g3, g4, l3, l4, shaft3, g5, l5).shift(DOWN*0.5)
        self.play(Create(gears))
        
        # Formula (Mixed Thai Text and Math)
        formula_left = MathTex(r"e = \frac{\omega_{out}}{\omega_{in}} = ", font_size=32)
        
        formula_frac_up = Text("ผลคูณ N ของเฟืองขับ", font=THAI_FONT, font_size=20)
        formula_frac_down = Text("ผลคูณ N ของเฟืองตาม", font=THAI_FONT, font_size=20)
        
        line = Line(LEFT*1.5, RIGHT*1.5, color=WHITE)
        formula_right = VGroup(formula_frac_up, line, formula_frac_down).arrange(DOWN, buff=0.1)
        
        formula = VGroup(formula_left, formula_right).arrange(RIGHT, buff=0.2)
        
        formula2 = MathTex(r"e = +\frac{N_2 \times N_4}{N_3 \times N_5}", font_size=36, color=YELLOW)
        
        f_group = VGroup(formula, formula2).arrange(DOWN, buff=0.5).next_to(gears, RIGHT, buff=1)
        
        self.play(Write(formula))
        self.wait(1)
        self.play(Write(formula2))
        self.wait(3)
        
        note = Text("*เครื่องหมาย + เพราะมี 2 คู่ขบนอก (ลบ x ลบ = บวก)", font=THAI_FONT, font_size=20, color=GREEN_B)
        note.next_to(f_group, DOWN, buff=0.5)
        self.play(FadeIn(note))
        self.wait(4)
        
        self.play(FadeOut(gears, f_group, note, form_title, title))

# Trigger GitHub Action
