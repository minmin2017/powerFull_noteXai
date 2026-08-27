from manim import *

THAI_FONT = "Loma"

class Part4_PlanetaryBasics(Scene):
    def construct(self):
        # ---------------- Title ----------------
        title = Text("Part 4: Planetary Gear Train (หน้า 53-55)", font=THAI_FONT, font_size=40, color=BLUE)
        subtitle = Text("ทำไมถึงพิเศษ? เพราะมี 2 DOF (องศาอิสระ)!", font=THAI_FONT, font_size=30, color=YELLOW)
        header = VGroup(title, subtitle).arrange(DOWN, buff=0.2).to_edge(UP)
        self.play(Write(header))
        self.wait(1)

        # ---------------- Schematic Drawing ----------------
        # 1. Ring Gear (Internal Sun)
        ring_gear = Circle(radius=2.5, color=WHITE, stroke_width=4)
        ring_label = Text("Ring Gear", font=THAI_FONT, font_size=20, color=WHITE).next_to(ring_gear, UP)
        
        # 2. Sun Gear (External Sun)
        sun_gear = Circle(radius=1.0, color=YELLOW, stroke_width=6)
        sun_gear.set_fill(YELLOW, opacity=0.3)
        sun_dot = Dot(color=YELLOW)
        
        # 3. Planet Gear
        planet_gear = Circle(radius=0.75, color=BLUE, stroke_width=6)
        planet_gear.set_fill(BLUE, opacity=0.3)
        planet_gear.shift(RIGHT * 1.75) # 1.0 (sun) + 0.75 (planet)
        planet_dot = Dot(planet_gear.get_center(), color=BLUE)
        
        # 4. Arm (Carrier)
        arm = Line(sun_dot.get_center(), planet_dot.get_center(), color=RED, stroke_width=8)
        
        system = VGroup(ring_gear, sun_gear, sun_dot, planet_gear, planet_dot, arm, ring_label)
        system.shift(LEFT * 2 + DOWN * 1.0)

        self.play(Create(ring_gear), Write(ring_label))
        self.play(Create(sun_gear), Create(sun_dot))
        self.play(Create(planet_gear), Create(planet_dot))
        self.play(Create(arm))
        self.wait(1)

        # ---------------- Labels & Explanations (Right side) ----------------
        exp1 = Text("1. Sun Gear (เฟืองกลาง)", font=THAI_FONT, font_size=24, color=YELLOW)
        exp1_sub = Text("มักถูกตรึงแกนให้อยู่กับที่", font=THAI_FONT, font_size=18, color=GREY)
        g1 = VGroup(exp1, exp1_sub).arrange(DOWN, aligned_edge=LEFT, buff=0.1)

        exp2 = Text("2. Planet Gear (เฟืองบริวาร)", font=THAI_FONT, font_size=24, color=BLUE)
        exp2_sub = Text("หมุนรอบตัวเอง และโคจรรอบ Sun\n(แกนเคลื่อนที่ได้!)", font=THAI_FONT, font_size=18, color=GREY)
        g2 = VGroup(exp2, exp2_sub).arrange(DOWN, aligned_edge=LEFT, buff=0.1)

        exp3 = Text("3. Arm / Carrier (ก้านพา)", font=THAI_FONT, font_size=24, color=RED)
        exp3_sub = Text("ก้านที่พา Planet เดินรอบ Sun", font=THAI_FONT, font_size=18, color=GREY)
        g3 = VGroup(exp3, exp3_sub).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        
        exp_group = VGroup(g1, g2, g3).arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        exp_group.next_to(system, RIGHT, buff=1.0)
        
        self.play(Write(g1))
        self.play(Write(g2))
        self.play(Write(g3))
        self.wait(2)

        # ---------------- Animation of DOF ----------------
        self.play(
            Rotate(arm, angle=PI, about_point=sun_gear.get_center(), rate_func=linear),
            Rotate(planet_gear, angle=PI*3, rate_func=linear), 
            UpdateFromFunc(planet_gear, lambda m: m.move_to(arm.get_end())),
            UpdateFromFunc(planet_dot, lambda m: m.move_to(arm.get_end())),
            run_time=4
        )
        self.wait(2)

        # Conclusion Text
        conc = Text("เพราะ Arm ขยับได้อิสระ จึงมี 2 DOF (ต้องรู้ 2 แกนเพื่อหาแกนที่ 3)", font=THAI_FONT, font_size=24, color=GREEN)
        conc.next_to(system, DOWN, buff=0.5).shift(RIGHT * 1.5)
        self.play(Write(conc))
        self.wait(3)