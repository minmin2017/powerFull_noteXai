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
            Text("กระบอกสูบหยุดนิ่ง (Locked)", font=THAI_FONT, font_size=18, color=GRAYTXT),
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


# ================================================================ HV03_CenterTypes
class HV03_CenterTypes(Scene):
    """Week 6: Open Center vs Tandem Center (4/3 DCV)"""

    def construct(self):
        title = Text("Week 6 — ตำแหน่งกลางของวาล์ว: Open vs Tandem Center", font=THAI_FONT, font_size=30, color=BLUE).to_edge(UP)
        self.play(Write(title))

        def make_valve(cx, cy):
            body = Rectangle(width=4.4, height=1.6, color=METAL, stroke_width=4).move_to([cx, cy, 0])
            ports = VGroup(
                Text("P", font_size=18, color=FIELD).move_to([cx - 0.7, cy - 1.2, 0]),
                Text("T", font_size=18, color=METAL).move_to([cx + 0.7, cy - 1.2, 0]),
                Text("A", font_size=18, color=OK).move_to([cx - 0.7, cy + 1.2, 0]),
                Text("B", font_size=18, color=OK).move_to([cx + 0.7, cy + 1.2, 0]),
            )
            return body, ports

        cxL, cxR, cy = -3.4, 3.0, -0.6
        bodyL, portsL = make_valve(cxL, cy)
        bodyR, portsR = make_valve(cxR, cy)
        labelL = Text("Open Center", font=THAI_FONT, font_size=22, color=OK).next_to(bodyL, UP, buff=0.55)
        labelR = Text("Tandem Center", font=THAI_FONT, font_size=22, color=OK).next_to(bodyR, UP, buff=0.55)

        self.play(Create(bodyL), Write(portsL), Create(bodyR), Write(portsR),
                  FadeIn(labelL), FadeIn(labelR), run_time=1.0)

        # Open center: ทุกพอร์ตต่อถึงกันหมด (เส้นเดียวลอดผ่านทุกพอร์ต)
        openflow = VGroup(
            Line([cxL - 0.7, cy - 1.2, 0], [cxL - 0.7, cy + 1.2, 0], color=CURRENT, stroke_width=6),
            Line([cxL - 0.7, cy + 1.2, 0], [cxL + 0.7, cy + 1.2, 0], color=CURRENT, stroke_width=6),
            Line([cxL + 0.7, cy + 1.2, 0], [cxL + 0.7, cy - 1.2, 0], color=CURRENT, stroke_width=6),
        )
        noteL = VGroup(
            Text("ทุกพอร์ตต่อถึงกันหมด", font=THAI_FONT, font_size=17, color=GRAYTXT),
            Text("กระบอกสูบ 'ลอยตัว' ได้อิสระ", font=THAI_FONT, font_size=17, color=GRAYTXT),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.1).next_to(bodyL, DOWN, buff=0.4)

        # Tandem center: เฉพาะ P-T ต่อกัน (A,B ปิด)
        tandemflow = Line([cxR - 0.7, cy - 1.2, 0], [cxR + 0.7, cy - 1.2, 0], color=CURRENT, stroke_width=6)
        blockA = Line([cxR - 0.7, cy + 0.5, 0], [cxR - 0.7, cy + 1.2, 0], color=WARN, stroke_width=6)
        blockB = Line([cxR + 0.7, cy + 0.5, 0], [cxR + 0.7, cy + 1.2, 0], color=WARN, stroke_width=6)
        noteR = VGroup(
            Text("P-T ต่อกัน (ปั๊มไหลฟรี)", font=THAI_FONT, font_size=17, color=GRAYTXT),
            Text("A,B ปิด — กระบอกสูบล็อกนิ่ง", font=THAI_FONT, font_size=17, color=GRAYTXT),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.1).next_to(bodyR, DOWN, buff=0.4)

        self.play(Create(openflow), FadeIn(noteL), Create(tandemflow), Create(blockA), Create(blockB), FadeIn(noteR),
                  run_time=1.3)
        self.wait(1.8)


# ================================================================ HV04_ReliefValve
class HV04_ReliefValve(Scene):
    """Week 6: Pressure Relief Valve — cracking / relieving"""

    def construct(self):
        title = Text("Week 6 — วาล์วนิรภัย (Pressure Relief Valve)", font=THAI_FONT, font_size=32, color=BLUE).to_edge(UP)
        self.play(Write(title))

        cx = -2.5
        body = Rectangle(width=2.2, height=3.2, color=METAL, stroke_width=4).move_to([cx, -0.3, 0])
        inlet = Rectangle(width=0.8, height=0.6, color=METAL, stroke_width=3).next_to(body, DOWN, buff=0).shift(LEFT * 0.4)
        outlet = Rectangle(width=0.8, height=0.6, color=METAL, stroke_width=3).move_to([cx + 1.5, 0.8, 0])

        poppet = Rectangle(width=1.0, height=0.4, color=WARN, fill_opacity=0.9).move_to([cx, -0.7, 0])
        spring = VGroup(*[
            Line([cx - 0.3 + i * 0.15, 0.3 + (0.2 if i % 2 == 0 else -0.2), 0],
                 [cx - 0.3 + (i + 1) * 0.15, 0.3 + (-0.2 if i % 2 == 0 else 0.2), 0],
                 color=METAL, stroke_width=3)
            for i in range(5)
        ])
        adj = Text("ปรับตั้งค่าได้", font=THAI_FONT, font_size=16, color=GRAYTXT).next_to(body, UP, buff=0.15)

        self.play(Create(body), Create(inlet), Create(outlet), FadeIn(poppet), Create(spring), FadeIn(adj), run_time=1.0)

        p1 = VGroup(
            Text("ปกติ: ปิดสนิท", font=THAI_FONT, font_size=22, color=OK),
            Text("สปริงกดลูกสูบปิดไว้", font=THAI_FONT, font_size=18, color=GRAYTXT),
            Text("ความดัน inlet < ค่าที่ตั้ง", font=THAI_FONT, font_size=18, color=GRAYTXT),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([3.2, 1.3, 0])
        self.play(FadeIn(p1))
        self.wait(1.0)

        p2 = VGroup(
            Text("เกิน setting: เปิดระบาย", font=THAI_FONT, font_size=22, color=WARN),
            Text("ความดัน inlet ชนะแรงสปริง", font=THAI_FONT, font_size=18, color=GRAYTXT),
            Text("ดันลูกสูบเปิด ระบายกลับถัง", font=THAI_FONT, font_size=18, color=GRAYTXT),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([3.2, -1.2, 0])

        relief_arrow = Arrow([cx, -0.3, 0], [cx + 1.3, 0.8, 0], color=CURRENT, stroke_width=6)
        self.play(
            FadeOut(p1),
            poppet.animate.shift(UP * 0.5),
            spring.animate.stretch_to_fit_height(spring.height * 0.6, about_edge=UP),
            FadeIn(p2),
            GrowArrow(relief_arrow),
            run_time=1.3
        )
        self.wait(1.8)


# ================================================================ HC02_SeriesVsParallel
class HC02_SeriesVsParallel(Scene):
    """Week 7: Cylinders in Parallel (no sync) vs Series (sync)"""

    def construct(self):
        title = Text("Week 7 — กระบอกสูบต่อขนาน vs อนุกรม (Synchronization)", font=THAI_FONT, font_size=28, color=BLUE).to_edge(UP)
        self.play(Write(title))

        def make_cyl(cx, cy):
            body = Rectangle(width=2.6, height=0.9, color=METAL, stroke_width=3).move_to([cx, cy, 0])
            piston = Rectangle(width=0.25, height=0.8, color=WARN, fill_opacity=0.9).move_to([cx - 1.0, cy, 0])
            return VGroup(body, piston), piston

        labelP = Text("Parallel — ไม่ sync", font=THAI_FONT, font_size=22, color=WARN).move_to([-3.3, 2.3, 0])
        cyl1, pist1 = make_cyl(-3.3, 1.3)
        cyl2, pist2 = make_cyl(-3.3, 0.1)
        pumpP = Text("ปั๊ม", font=THAI_FONT, font_size=16, color=FIELD).move_to([-5.6, 0.7, 0])
        feedP = VGroup(
            Line([-5.2, 0.7, 0], [-4.6, 0.7, 0], color=CURRENT, stroke_width=4),
            Line([-4.6, 0.7, 0], [-4.6, 1.3, 0], color=CURRENT, stroke_width=4),
            Line([-4.6, 0.7, 0], [-4.6, 0.1, 0], color=CURRENT, stroke_width=4),
            Line([-4.6, 1.3, 0], [-4.4, 1.3, 0], color=CURRENT, stroke_width=4),
            Line([-4.6, 0.1, 0], [-4.4, 0.1, 0], color=CURRENT, stroke_width=4),
        )
        noteP = Text("โหลดไม่เท่ากัน -> เร็วไม่เท่ากัน", font=THAI_FONT, font_size=15, color=GRAYTXT).move_to([-3.3, -0.9, 0])

        labelS = Text("Series — sync เสมอ", font=THAI_FONT, font_size=22, color=OK).move_to([3.3, 2.3, 0])
        cyl3, pist3 = make_cyl(2.0, 1.3)
        cyl4, pist4 = make_cyl(4.6, 0.1)
        connect = Line([3.3, 0.85, 0], [3.3, 0.55, 0], color=CURRENT, stroke_width=4)
        noteS = Text("out(1) = in(2) บังคับ v เท่ากัน", font=THAI_FONT, font_size=15, color=GRAYTXT).move_to([3.3, -0.9, 0])

        self.play(
            FadeIn(labelP), Create(cyl1), Create(cyl2), FadeIn(pumpP), Create(feedP), FadeIn(noteP),
            FadeIn(labelS), Create(cyl3), Create(cyl4), Create(connect), FadeIn(noteS),
            run_time=1.2,
        )
        self.wait(0.4)

        # Parallel: unequal speeds (ต่างกันชัดเจน)
        self.play(pist1.animate.shift(RIGHT * 1.6), pist2.animate.shift(RIGHT * 0.6),
                   pist3.animate.shift(RIGHT * 1.1), pist4.animate.shift(RIGHT * 1.1),
                   run_time=2.0, rate_func=linear)
        self.wait(1.8)


# ================================================================ HC03_MeterInOut
class HC03_MeterInOut(Scene):
    """Week 7: Meter-in vs Meter-out speed control"""

    def construct(self):
        title = Text("Week 7 — Meter-in vs Meter-out Speed Control", font=THAI_FONT, font_size=30, color=BLUE).to_edge(UP)
        self.play(Write(title))

        def make_cyl(cx, cy):
            body = Rectangle(width=3.2, height=0.9, color=METAL, stroke_width=3).move_to([cx, cy, 0])
            piston = Rectangle(width=0.25, height=0.8, color=WARN, fill_opacity=0.9).move_to([cx - 1.2, cy, 0])
            return VGroup(body, piston), piston

        cyA, cyB = 1.2, -1.2
        cylA, pistA = make_cyl(-1.0, cyA)
        cylB, pistB = make_cyl(-1.0, cyB)

        fcvA = Rectangle(width=0.5, height=0.5, color=FIELD, fill_opacity=0.9).move_to([-3.0, cyA, 0])
        labelA = VGroup(
            Text("Meter-in", font=THAI_FONT, font_size=22, color=FIELD),
            Text("FCV ก่อนกระบอกสูบ (ทางเข้า)", font=THAI_FONT, font_size=16, color=GRAYTXT),
            Text("เหมาะกับโหลดต้านทาน", font=THAI_FONT, font_size=16, color=GRAYTXT),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to([3.2, cyA, 0])

        fcvB = Rectangle(width=0.5, height=0.5, color=FIELD, fill_opacity=0.9).move_to([1.8, cyB, 0])
        labelB = VGroup(
            Text("Meter-out", font=THAI_FONT, font_size=22, color=OK),
            Text("FCV หลังกระบอกสูบ (ทางออก)", font=THAI_FONT, font_size=16, color=GRAYTXT),
            Text("เหมาะกับโหลดดึงตัวเอง (overrunning)", font=THAI_FONT, font_size=16, color=GRAYTXT),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to([3.2, cyB - 0.9, 0])

        self.play(Create(cylA), Create(cylB), FadeIn(fcvA), FadeIn(fcvB), FadeIn(labelA), FadeIn(labelB), run_time=1.0)
        self.wait(0.4)
        self.play(pistA.animate.shift(RIGHT * 1.6), pistB.animate.shift(RIGHT * 1.6), run_time=1.8, rate_func=linear)
        self.wait(1.5)
