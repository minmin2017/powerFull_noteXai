"""valves_circuits_anim.py — Manim animation for Hydraulic Valves & Circuits (Week 4 & 5)
Supports both Windows (Tahoma) and Linux Docker / GitHub Actions (Loma).
"""
import sys
import os
from manim import *

# Cross-platform Thai font
THAI_FONT = "Loma" if sys.platform.startswith("linux") else "Tahoma"

# Palette
CURRENT = "#FFB300"
FIELD   = "#42A5F5"
FORCE   = "#66BB6A"
METAL   = "#B0BEC5"
GRAYTXT = "#B0BEC5"
WARN    = "#FF7043"
OK      = "#26C6DA"
RESULT  = OK


# ================================================================ HV01_CheckValve
class HV01_CheckValve(Scene):
    """Week 4: Check Valve Operation"""

    def construct(self):
        title = Text("Week 4 — การทำงานของ Check Valve & Pilot Check", font=THAI_FONT, font_size=32, color=BLUE).to_edge(UP)
        self.play(Write(title))

        cx = -2.5
        body = Rectangle(width=4.0, height=2.2, color=METAL, stroke_width=4).move_to([cx, 0, 0])
        port_in = Rectangle(width=1.0, height=0.6, color=METAL, stroke_width=3).next_to(body, LEFT, buff=0)
        port_out = Rectangle(width=1.0, height=0.6, color=METAL, stroke_width=3).next_to(body, RIGHT, buff=0)

        seat_upper = Line([cx - 0.2, 1.1, 0], [cx - 0.2, 0.4, 0], color=METAL, stroke_width=5)
        seat_lower = Line([cx - 0.2, -1.1, 0], [cx - 0.2, -0.4, 0], color=METAL, stroke_width=5)
        poppet = Polygon([cx - 0.1, 0.5, 0], [cx + 0.6, 0.8, 0], [cx + 0.6, -0.8, 0], [cx - 0.1, -0.5, 0],
                         color=WARN, fill_opacity=0.8, stroke_width=2)
        spring = VGroup(*[
            Line([cx + 0.6 + i * 0.2, 0.4 * (1 if i % 2 == 0 else -1), 0],
                 [cx + 0.6 + (i + 1) * 0.2, 0.4 * (-1 if i % 2 == 0 else 1), 0],
                 color=METAL, stroke_width=3)
            for i in range(5)
        ])

        self.play(Create(body), Create(port_in), Create(port_out), Create(seat_upper), Create(seat_lower),
                  FadeIn(poppet), Create(spring), run_time=1.0)

        p1 = VGroup(
            Text("1. Free Flow (ไหลอิสระ)", font=THAI_FONT, font_size=22, color=OK),
            Text("ความดันทางเข้าเอาชนะสปริง", font=THAI_FONT, font_size=18, color=GRAYTXT),
            Text("ดัน Poppet เปิด น้ำมันไหลผ่านได้", font=THAI_FONT, font_size=18, color=GRAYTXT),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([3.5, 1.5, 0])
        self.play(FadeIn(p1))

        flow_arrow = Arrow([cx - 2.5, 0, 0], [cx - 0.5, 0, 0], color=CURRENT, stroke_width=6)
        self.play(
            poppet.animate.shift(RIGHT * 0.6),
            spring.animate.scale([0.6, 1, 1], about_point=[cx + 1.6, 0, 0]),
            GrowArrow(flow_arrow),
            run_time=1.2
        )
        self.wait(1.0)

        p2 = VGroup(
            Text("2. Blocked Flow (บล็อกย้อนกลับ)", font=THAI_FONT, font_size=22, color=WARN),
            Text("แรงดันย้อนกลับ + แรงสปริง", font=THAI_FONT, font_size=18, color=GRAYTXT),
            Text("กด Poppet แนบบ่าวาล์ว ปิดสนิท!", font=THAI_FONT, font_size=18, color=GRAYTXT),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([3.5, -1.0, 0])

        self.play(
            FadeOut(flow_arrow),
            poppet.animate.shift(LEFT * 0.6),
            spring.animate.scale([1 / 0.6, 1, 1], about_point=[cx + 1.6, 0, 0]),
            FadeIn(p2),
            run_time=1.0
        )
        rev_arrow = Arrow([cx + 2.5, 0, 0], [cx + 0.8, 0, 0], color=FIELD, stroke_width=6)
        self.play(GrowArrow(rev_arrow), run_time=0.8)
        self.wait(1.5)


# ================================================================ HV02_SpoolValve
class HV02_SpoolValve(Scene):
    """Week 4: 4/3 DCV Spool Valve Operation"""

    def construct(self):
        title = Text("Week 4 — วาล์วเลื่อนควบคุมทิศทาง (4/3 DCV)", font=THAI_FONT, font_size=32, color=BLUE).to_edge(UP)
        self.play(Write(title))

        cx = -2.2
        valve_body = Rectangle(width=5.0, height=1.8, color=METAL, stroke_width=4).move_to([cx, 0, 0])
        ports = VGroup(
            Text("P", font_size=20, color=FIELD).move_to([cx - 0.8, -1.3, 0]),
            Text("T", font_size=20, color=METAL).move_to([cx + 0.8, -1.3, 0]),
            Text("A", font_size=20, color=OK).move_to([cx - 0.8, 1.3, 0]),
            Text("B", font_size=20, color=OK).move_to([cx + 0.8, 1.3, 0]),
        )

        spool_rod = Line([cx - 2.8, 0, 0], [cx + 2.8, 0, 0], color=GRAYTXT, stroke_width=6)
        land1 = Rectangle(width=0.7, height=1.6, color=WARN, fill_opacity=0.9).move_to([cx - 1.4, 0, 0])
        land2 = Rectangle(width=0.7, height=1.6, color=WARN, fill_opacity=0.9).move_to([cx, 0, 0])
        land3 = Rectangle(width=0.7, height=1.6, color=WARN, fill_opacity=0.9).move_to([cx + 1.4, 0, 0])
        spool = VGroup(spool_rod, land1, land2, land3)

        self.play(Create(valve_body), Write(ports), FadeIn(spool), run_time=1.0)

        p1 = VGroup(
            Text("ตำแหน่งกลาง (Center)", font=THAI_FONT, font_size=22, color=OK),
            Text("สปูลปิดกั้นพอร์ตทั้งหมด", font=THAI_FONT, font_size=18, color=GRAYTXT),
            Text("กระบอกสูบหยุดนิ่ง (Locked)", font_THAI_FONT, font_size=18, color=GRAYTXT),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([3.5, 1.5, 0])
        self.play(FadeIn(p1))
        self.wait(1.0)

        p2 = VGroup(
            Text("เลื่อนขวา (Shift Right)", font=THAI_FONT, font_size=22, color=FIELD),
            Text("เปิดทาง P -> A (ลูกสูบยืด)", font=THAI_FONT, font_size=18, color=GRAYTXT),
            Text("และ B -> T (น้ำมันกลับถัง)", font=THAI_FONT, font_size=18, color=GRAYTXT),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([3.5, -1.0, 0])

        arrow_pa = CurvedArrow([cx - 0.8, -0.8, 0], [cx - 0.8, 0.8, 0], color=FIELD)
        arrow_bt = CurvedArrow([cx + 0.8, 0.8, 0], [cx + 0.8, -0.8, 0], color=METAL)
        self.play(
            spool.animate.shift(RIGHT * 0.7),
            FadeIn(p2),
            Create(arrow_pa),
            Create(arrow_bt),
            run_time=1.2
        )
        self.wait(1.5)


# ================================================================ HC01_Regenerative
class HC01_Regenerative(Scene):
    """Week 5: Regenerative Circuit"""

    def construct(self):
        title = Text("Week 5 — วงจรรีเจนเนอเรทีฟ (Regenerative Speed)", font=THAI_FONT, font_size=32, color=BLUE).to_edge(UP)
        self.play(Write(title))

        cx = -2.2
        cyl_body = Rectangle(width=4.5, height=1.8, color=METAL, stroke_width=4).move_to([cx, 0.5, 0])
        piston = Rectangle(width=0.5, height=1.6, color=WARN, fill_opacity=0.9).move_to([cx - 1.5, 0.5, 0])
        rod = Rectangle(width=3.2, height=0.6, color=METAL, fill_opacity=0.8).next_to(piston, RIGHT, buff=0)
        cylinder = VGroup(cyl_body, piston, rod)

        self.play(Create(cylinder), run_time=1.0)

        p1 = VGroup(
            Text("สูตรความเร็วพุ่งสูงขึ้น", font=THAI_FONT, font_size=22, color=FIELD),
            MathTex(r"v_{ext} = \frac{Q_P}{A_{rod}}", font_size=28, color=OK),
            Text("เอาน้ำมันก้านสูบสมทบเข้าหัวสูบ", font=THAI_FONT, font_size=18, color=GRAYTXT),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([3.5, 0, 0])
        self.play(FadeIn(p1))

        arr_in = Arrow([cx - 3.2, 0.5, 0], [cx - 1.8, 0.5, 0], color=FIELD, stroke_width=7)
        self.play(GrowArrow(arr_in), piston.animate.shift(RIGHT * 2.2), rod.animate.shift(RIGHT * 2.2), run_time=2.0)
        self.wait(1.5)
