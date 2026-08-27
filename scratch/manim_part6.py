from manim import *

THAI_FONT = "Loma"

class Part6_TabularMethod(Scene):
    def construct(self):
        # ---------------- Title ----------------
        title = Text("Part 6: Tabular Method (Superposition)", font=THAI_FONT, font_size=40, color=BLUE)
        subtitle = Text("ตาราง 3 บรรทัด แก้โจทย์ Planetary ได้ทุกข้อ! (หน้า 70)", font=THAI_FONT, font_size=30, color=YELLOW)
        header = VGroup(title, subtitle).arrange(DOWN, buff=0.2).to_edge(UP)
        self.play(Write(header))
        self.wait(1)

        # ---------------- Table Structure ----------------
        # We will create a simple table using Text and Lines
        
        headers = ["ขั้นตอน (Condition)", "Arm", "Sun", "Planet", "Ring"]
        row1 = ["1. ตรึง Arm, หมุน Sun = Y", "0", "+Y", "-Y(Ns/Np)", "-Y(Ns/Nr)"]
        row2 = ["2. ล็อกทุกชิ้น, หมุน Arm = X", "+X", "+X", "+X", "+X"]
        row3 = ["3. รวมสมการ (Row 1 + 2)", "+X", "X + Y", "X - Y(Ns/Np)", "X - Y(Ns/Nr)"]
        
        # Helper to create a row of texts
        def create_row(texts, colors=None, y_pos=0):
            if colors is None:
                colors = [WHITE] * len(texts)
            vg = VGroup()
            # X positions for columns
            x_pos = [-4, -1, 1, 3.5, 6]
            for i, text in enumerate(texts):
                t = Text(text, font=THAI_FONT, font_size=20, color=colors[i])
                t.move_to(RIGHT * x_pos[i] + UP * y_pos)
                if i == 0:
                    t.align_to(RIGHT * x_pos[0], LEFT) # Left align the first column
                vg.add(t)
            return vg

        header_colors = [WHITE, RED, YELLOW, BLUE, WHITE]
        vg_headers = create_row(headers, colors=header_colors, y_pos=1.5)
        
        hline1 = Line(LEFT*6, RIGHT*7).next_to(vg_headers, DOWN, buff=0.2)
        
        vg_row1 = create_row(row1, colors=[WHITE, RED, YELLOW, BLUE, WHITE], y_pos=0.5)
        vg_row2 = create_row(row2, colors=[WHITE, RED, YELLOW, BLUE, WHITE], y_pos=-0.5)
        
        hline2 = Line(LEFT*6, RIGHT*7).next_to(vg_row2, DOWN, buff=0.2)
        
        vg_row3 = create_row(row3, colors=[GREEN, GREEN, GREEN, GREEN, GREEN], y_pos=-1.5)

        self.play(Write(vg_headers), Create(hline1))
        self.wait(1)
        
        self.play(Write(vg_row1[0]))
        self.play(Write(vg_row1[1:]))
        self.wait(2)
        
        self.play(Write(vg_row2[0]))
        self.play(Write(vg_row2[1:]))
        self.wait(2)
        
        self.play(Create(hline2))
        self.play(Write(vg_row3[0]))
        self.play(Write(vg_row3[1:]))
        self.wait(3)

        # ---------------- Highlight ----------------
        box = SurroundingRectangle(vg_row3, color=GREEN, buff=0.2)
        self.play(Create(box))
        
        note = Text("เอาค่าที่โจทย์ให้มาแทนลงในสมการบรรทัดที่ 3 แล้วแก้หา X, Y!", font=THAI_FONT, font_size=24, color=YELLOW)
        note.next_to(box, DOWN, buff=0.5)
        self.play(Write(note))
        self.wait(3)