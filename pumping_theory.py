from manim import *

class PumpingTheory(Scene):
    def construct(self):
        THAI_FONT = "Tahoma"

        # Title
        title = Text("ทฤษฎีการทำงานของปั๊ม", font=THAI_FONT, font_size=48).to_edge(UP)
        self.play(Write(title))

        # Tank and Fluid
        tank = Rectangle(width=6, height=2, color=BLUE).shift(DOWN*2.5)
        fluid_in_tank = Rectangle(width=6, height=1.5, color=BLUE).set_fill(BLUE, opacity=0.5).shift(DOWN*2.75)
        
        # Piston and Cylinder
        cylinder_shell = Rectangle(width=4, height=1.5, color=WHITE).shift(UP*0.5)
        piston = Rectangle(width=0.4, height=1.5, color=GRAY).set_fill(GRAY, opacity=1).shift(UP*0.5 + RIGHT*1.8)
        rod = Line(piston.get_right(), piston.get_right() + RIGHT*2.5, stroke_width=8)

        # Pipe
        pipe_left = Line(tank.get_top() + LEFT*1.1, cylinder_shell.get_bottom() + LEFT*1.1, color=WHITE)
        pipe_right = Line(tank.get_top() + LEFT*0.9, cylinder_shell.get_bottom() + LEFT*0.9, color=WHITE)
        
        self.play(
            Create(tank), 
            FadeIn(fluid_in_tank), 
            Create(cylinder_shell), 
            Create(piston), 
            Create(rod), 
            Create(pipe_left), 
            Create(pipe_right)
        )

        # Atmospheric Pressure arrows
        atm_arrows = VGroup(*[
            Arrow(start=UP*0.5, end=DOWN*0.1, color=RED).scale(0.5).next_to(fluid_in_tank.get_top(), UP, buff=0).shift(RIGHT*(i-1)*2) 
            for i in range(3)
        ])
        atm_text = Text("ความดันบรรยากาศ (Atmospheric Pressure) กดผิวน้ำมัน", font=THAI_FONT, font_size=24, color=RED).next_to(atm_arrows, UP)
        
        # Animation: Piston moves left (retracts)
        self.play(piston.animate.shift(LEFT*3.6), rod.animate.shift(LEFT*3.6), run_time=2)
        
        # Fluid moves up
        fluid_in_pipe = Rectangle(width=0.2, height=2.0, color=BLUE).set_fill(BLUE, opacity=0.5).shift(DOWN*0.5 + LEFT*1)
        fluid_in_cylinder = Rectangle(width=3.6, height=1.5, color=BLUE).set_fill(BLUE, opacity=0.5).shift(UP*0.5 + LEFT*0.2)
        
        self.play(FadeIn(atm_arrows), Write(atm_text))
        self.play(FadeIn(fluid_in_pipe), run_time=1)
        self.play(FadeIn(fluid_in_cylinder), run_time=1)

        desc = Text("เกิดสุญญากาศในกระบอกสูบ น้ำมันจึงถูกดันขึ้นมา", font=THAI_FONT, font_size=32).next_to(title, DOWN)
        self.play(Write(desc))
        self.wait(3)
