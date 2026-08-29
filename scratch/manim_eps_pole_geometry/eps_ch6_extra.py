"""EPS บทที่ 6 (เสริม) — ทำไม B อ่อนตรงระนาบเป็นกลาง

Min ท้วงตรงๆ ว่า: "จาก N ไป S มันก็ต้องมีสนามเต็มพื้นที่สิ ทำไม B=0 ได้"
คำตอบที่ EP07 ไม่ได้อธิบาย (แค่บอกเฉยๆ ว่า B=0 ตรงระนาบเป็นกลาง):
  ขั้วแม่เหล็กเป็น "ก้อนเหล็ก" ที่ไม่ได้หุ้มรอบวงกลมทั้งหมด — มันเว้นช่องว่าง
  ระหว่างปลายขั้วสองก้อนไว้ (interpolar gap) เส้นแรงชอบเดินผ่านเหล็ก (reluctance
  ต่ำ) มากกว่าอากาศ (reluctance สูง) จึงแทบไม่มีเส้นแรงเลยตรงช่องว่างนั้น —
  และระนาบเป็นกลางทางกลก็ตั้งอยู่ตรงช่องว่างนี้พอดี

ผิด: "ไม่มีสนามระหว่าง N-S เลยตรงนั้น" (ฟังดูเหมือนสนามหายไปทั้งพื้นที่)
อ๋อ: สนามแรงเต็มที่ใต้หน้าขั้วทั้งสองข้าง แต่ตรง "ช่องว่างระหว่างปลายขั้ว"
     (ไม่มีเหล็กอยู่ใกล้ๆ) มันอ่อนมากเพราะเส้นแรงเลือกวิ่งผ่านเหล็กที่ใกล้กว่า

ใช้สีเดิมจากซีรีส์ EP07-EP10 (ห้ามสลับความหมาย):
  FIELD ฟ้า = สนามหลัก, WARN ส้ม = จุด/ปัญหาที่ต้องสังเกต, OK ฟ้าเขียว = สรุป
"""

import numpy as np
from manim import *
from mlib import *
from eps_ch6 import pole, armature_core, field_lines, plane_line, R_ARM, POLE_X, STAGE

POLE_HALF_H = 1.5   # ครึ่งความสูงจริงของก้อนขั้ว (ตรงกับ pole() ใน eps_ch6.py: height=3.0)
GAP_TOP = 2.4       # กันขอบบนสุดของโซนช่องว่างที่แรเงา (พ้นตัวขั้วขึ้นไปอีกหน่อย)


class EP07B(SafeScene):
    """ทำไม B อ่อนตรงระนาบเป็นกลาง — รูปทรงขั้วแม่เหล็กจริงมีช่องว่าง"""

    def construct(self):
        t = title("ทำไม B อ่อนตรงระนาบเป็นกลาง?", size=30)
        self.play(FadeIn(t, shift=DOWN * 0.2))

        # --- ฉาก 1: ตั้งคำถาม — มันดูเหมือนมีสนามเต็มพื้นที่จริงไหม?
        n_pole, s_pole = pole("N", -POLE_X), pole("S", POLE_X)
        arm = armature_core()
        fld = field_lines(0.0)

        cap1 = caption("จาก N ไป S ต้องมีสนามเต็มพื้นที่ระหว่างขั้วสิ — จริงไหม?")
        self.play(FadeIn(n_pole), FadeIn(s_pole), FadeIn(arm), FadeIn(cap1),
                   run_time=1.0)
        self.play(LaggedStart(*[GrowArrow(a) for a in fld], lag_ratio=0.12),
                   run_time=1.3)
        self.wait(0.8)

        # --- ฉาก 2: เผยว่าขั้วเป็น "ก้อนเหล็ก" ที่มีขอบบน-ล่างจริง ไม่ได้หุ้มรอบวง
        top_edge_n = DashedLine(n_pole.get_top() + LEFT * 0.75,
                                 n_pole.get_top() + RIGHT * 0.75,
                                 color=WARN, stroke_width=3)
        bot_edge_n = top_edge_n.copy().move_to(n_pole.get_bottom())
        top_edge_s = top_edge_n.copy().move_to(s_pole.get_top())
        bot_edge_s = top_edge_n.copy().move_to(s_pole.get_bottom())

        cap2 = caption("ขั้วแม่เหล็กเป็นก้อนเหล็กที่มีขอบจริง — ไม่ได้หุ้มรอบวงกลม",
                       color=WARN)
        self.play(FadeOut(cap1), run_time=0.3)
        self.play(FadeIn(cap2), Create(top_edge_n), Create(bot_edge_n),
                   Create(top_edge_s), Create(bot_edge_s), run_time=1.1)
        self.wait(0.9)

        # --- ฉาก 3: แรเงาช่องว่างบน-ล่าง (interpolar gap) <- จังหวะ "อ๋อ" ที่ 1
        gap_top = Rectangle(width=POLE_X * 2 - 0.4, height=GAP_TOP - POLE_HALF_H,
                             fill_color=WARN, fill_opacity=0.16, stroke_width=0)
        gap_top.move_to(STAGE + np.array([0, (POLE_HALF_H + GAP_TOP) / 2, 0]))
        gap_bot = gap_top.copy().move_to(STAGE + np.array([0, -(POLE_HALF_H + GAP_TOP) / 2, 0]))
        gap_lbl = Text("ช่องว่างระหว่างปลายขั้ว — ไม่มีเหล็กอยู่ตรงนี้",
                       font_size=20, color=WARN)
        fit_width(gap_lbl, 8.2)
        gap_lbl.move_to(STAGE + np.array([0, GAP_TOP + 0.55, 0]))

        cap3 = caption("เหนือ/ใต้ขอบขั้ว = ช่องว่าง ไม่มีก้อนเหล็กอยู่แถวนั้นเลย",
                       color=WARN)
        self.play(FadeOut(cap2), run_time=0.3)
        self.play(FadeIn(cap3), FadeIn(gap_top), FadeIn(gap_bot), FadeIn(gap_lbl),
                   run_time=1.2)
        self.wait(1.1)

        # --- ฉาก 4: reluctance — ทำไมเส้นแรงเลี่ยงช่องว่าง <- จังหวะ "อ๋อ" ที่ 2
        cap4 = caption("เส้นแรงชอบเดินผ่านเหล็ก (reluctance ต่ำ) มากกว่าอากาศ (สูง)")
        self.play(FadeOut(cap3), FadeOut(gap_lbl), run_time=0.3)
        self.play(FadeIn(cap4), run_time=0.4)

        easy = Arrow(STAGE + np.array([-1.1, -2.65, 0]), STAGE + np.array([1.1, -2.65, 0]),
                     buff=0, color=OK, stroke_width=7, tip_length=0.24)
        easy_lbl = Text("ผ่านเหล็ก (หน้าขั้ว) → ง่าย", font_size=19, color=OK)
        easy_lbl.next_to(easy, DOWN, buff=0.15)

        # เส้นแรงที่ "พยายาม" ข้ามช่องว่าง — จางลงเรื่อยๆ จนแทบไม่เหลือ
        attempt = VGroup()
        n_try = 5
        for k in range(n_try):
            frac = k / (n_try - 1)
            y0 = STAGE[1] + R_ARM + 0.15
            x = -0.9 + frac * 1.8
            seg = Line([x, y0, 0], [x, y0 + 0.9, 0], color=EMF, stroke_width=3.5)
            seg.set_opacity(max(0.05, 0.85 * (1 - abs(frac - 0.5) * 1.9)))
            attempt.add(seg)
        attempt_lbl = Text("พยายามข้ามช่องว่าง → จางจนแทบไม่เหลือ (สูง = ยาก)",
                           font_size=19, color=EMF)
        fit_width(attempt_lbl, 7.4)
        attempt_lbl.move_to(STAGE + np.array([0, R_ARM + 1.35, 0]))

        self.play(GrowArrow(easy), FadeIn(easy_lbl),
                   LaggedStart(*[Create(a) for a in attempt], lag_ratio=0.15),
                   FadeIn(attempt_lbl), run_time=1.4)
        self.wait(1.3)

        # --- ฉาก 5: วางเส้นระนาบเป็นกลาง — ตกตรงช่องว่างพอดี
        np_line = plane_line(0.0, OK, length=GAP_TOP + 0.3)
        np_lbl = Text("ระนาบเป็นกลาง", font_size=21, color=OK)
        np_lbl.move_to(STAGE + np.array([-2.1, GAP_TOP + 0.15, 0]))
        hit = Dot(STAGE + np.array([0, R_ARM + 0.35, 0]), radius=0.09, color=OK)
        hit_ring = Circle(radius=0.22, color=OK, stroke_width=3).move_to(hit)

        cap5 = caption("ระนาบเป็นกลางตกอยู่ตรง 'ช่องว่างนี้' พอดี — ไม่ใช่ใต้ขั้วไหนเลย")
        self.play(FadeOut(cap4), FadeOut(attempt_lbl), run_time=0.3)
        self.play(FadeIn(cap5), Create(np_line), FadeIn(np_lbl),
                   FadeIn(hit), Create(hit_ring), run_time=1.2)
        self.wait(1.3)

        # --- ฉาก 6: เชื่อมกลับ EP07 — โหลดทำให้จุดอ่อนสุดขยับในช่องว่างนี้
        self.play(*[FadeOut(m) for m in
                    (top_edge_n, bot_edge_n, top_edge_s, bot_edge_s,
                     easy, easy_lbl, attempt, hit, hit_ring, cap5)],
                   run_time=0.6)

        tilt = 22 * DEGREES
        fld2 = field_lines(tilt)
        np_line2 = plane_line(tilt, WARN, length=GAP_TOP + 0.3, width=6)
        np_lbl2 = Text("ขยับตามทิศหมุน", font_size=20, color=WARN)
        np_lbl2.move_to(STAGE + np.array([0, GAP_TOP + 0.35, 0]))

        cap6 = caption("จ่ายโหลด → สนามรวมเอียง → จุดสนามอ่อนสุดขยับในช่องว่างนี้เอง")
        self.play(FadeIn(cap6), Transform(fld, fld2), Transform(np_line, np_line2),
                   FadeIn(np_lbl2), run_time=1.6)
        self.wait(1.3)

        # --- สรุป
        self.play(*[FadeOut(m) for m in
                    (n_pole, s_pole, arm, fld, np_line, np_lbl, np_lbl2,
                     gap_top, gap_bot, cap6, t)], run_time=0.8)
        s1 = Text("ไม่ใช่ \"ไม่มีสนามระหว่าง N-S\"", font_size=28, color=WHITE)
        s2 = Text("แต่ตรงช่องว่างระหว่างปลายขั้ว ไม่มีหน้าขั้วอยู่ใกล้ๆ ⇒ B อ่อนมาก",
                  font_size=23, color=OK)
        fit_width(s2, 12.0)
        card = VGroup(s1, s2).arrange(DOWN, buff=0.45).move_to(ORIGIN)
        self.play(FadeIn(card, shift=UP * 0.25), run_time=1.0)
        self.wait(2.0)
