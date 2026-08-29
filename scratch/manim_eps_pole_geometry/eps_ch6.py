"""EPS บทที่ 6 — ระนาบเป็นกลาง / อาร์เมเจอร์รีแอคชั่น / คอมมิวเตชั่น / interpole

ซีรีส์ EP07–EP10 ต่อจาก EP01–EP06 (บทที่ 1–5)

ออกแบบตาม §14 ของสกิล: ตั้งต้นจาก "ความเข้าใจผิด" ก่อน แล้วค่อยออกแบบให้คลิป
พาไปถึงจังหวะ "อ๋อ" ที่แก้ความเข้าใจผิดนั้น

  EP07  ผิด: ระนาบเป็นกลาง = เส้นตรงกลางระหว่างขั้ว (เป็นเรขาคณิตตายตัว)
        อ๋อ: มันถูกนิยามด้วย "จุดที่ emf = 0" ต่างหาก — พอสนามเอียง จุดนั้นก็ย้าย

  EP08  ผิด: สนามอาร์เมเจอร์ "ต้าน" สนามหลักตรงๆ
        อ๋อ: แกนของมัน ตั้งฉาก 90° กับสนามหลัก — ที่เอียงคือผลบวกเวกเตอร์
             และมันแยกได้ 2 ส่วนที่ให้ผลเสียคนละอย่าง (ต้าน = แรงดันตก / ขวาง = สปาร์ค)

  EP09  ผิด: คอมมิวเตชั่นคือ "สลับขั้ว" เฉยๆ
        อ๋อ: มันคือการส่งไม้ผลัดของกระแส 50→100 / 50→0 ที่ต้องเกิดตอน emf = 0 พอดี
             ถ้าเหนี่ยวนำในตัวเองยังค้าง กระแสไม่ยอมเป็นศูนย์ → อาร์ค

  EP10  ผิด: interpole กับ ขดลวดชดเชย ใช้แทนกันได้
        อ๋อ: คนละตำแหน่ง → แก้คนละปัญหา (จุดเดียว vs รอบวง)

สีประจำปริมาณ (Mayer signaling — ห้ามสลับ):
  FIELD   ฟ้า     สนามแม่เหล็กหลัก
  CURRENT เหลือง  กระแส / สนามที่เกิดจากกระแสอาร์เมเจอร์
  WARN    ส้ม     ตำแหน่งใหม่ของระนาบเป็นกลาง / ปัญหา
  OK      ฟ้าเขียว ข้อสรุป / ตัวแก้
  EMF     แดง     แรงเคลื่อนเหนี่ยวนำ
"""

import numpy as np
from manim import *
from mlib import *

R_ARM = 1.35          # รัศมีอาร์เมเจอร์
POLE_X = 3.55         # ระยะขั้วแม่เหล็กจากศูนย์กลาง
STAGE = np.array([0.0, 0.15, 0.0])


# ------------------------------------------------------------------ ชิ้นส่วนร่วม
def pole(sign, x):
    """แท่งขั้วแม่เหล็ก N หรือ S"""
    body = RoundedRectangle(width=1.5, height=3.0, corner_radius=0.12,
                            fill_color=METAL, fill_opacity=0.55,
                            stroke_color=METAL, stroke_width=2)
    body.move_to(STAGE + np.array([x, 0, 0]))
    lab = Text(sign, font_size=40, color=WHITE).move_to(body.get_center())
    return VGroup(body, lab)


def armature_core():
    """แกนอาร์เมเจอร์ + เพลา"""
    core = Circle(radius=R_ARM, fill_color="#546E7A", fill_opacity=0.75,
                  stroke_color=METAL, stroke_width=2).move_to(STAGE)
    shaft = Dot(STAGE, radius=0.11, color=GRAYTXT)
    return VGroup(core, shaft)


def field_lines(angle=0.0, color=FIELD, n=5, opacity=0.85):
    """เส้นแรงแม่เหล็กหลัก N -> S  (เอียงได้ตามมุมที่ให้)"""
    g = VGroup()
    for k in range(n):
        y = (k - (n - 1) / 2) * 0.62
        a = STAGE + np.array([-POLE_X + 0.8, y, 0])
        b = STAGE + np.array([POLE_X - 0.8, y, 0])
        arr = Arrow(a, b, buff=0, color=color, stroke_width=3.2,
                    tip_length=0.20, max_tip_length_to_length_ratio=0.5)
        arr.set_opacity(opacity)
        g.add(arr)
    if angle:
        g.rotate(angle, about_point=STAGE)
    return g


def plane_line(angle, color, length=2.85, width=5):
    """เส้นระนาบเป็นกลาง (ตั้งฉากกับสนาม)"""
    v = np.array([-np.sin(angle), np.cos(angle), 0.0])
    return Line(STAGE - v * length, STAGE + v * length,
                color=color, stroke_width=width)


# ================================================================== EP07
class EP07(SafeScene):
    """ระนาบเป็นกลางคืออะไร และทำไมมันถึงขยับ"""

    def construct(self):
        t = title("ระนาบเป็นกลาง — ทำไมมันถึงขยับ", size=30)
        self.play(FadeIn(t, shift=DOWN * 0.2))

        # --- ฉาก 1: เครื่อง 2 ขั้ว + สนามแนวนอน
        n_pole, s_pole = pole("N", -POLE_X), pole("S", POLE_X)
        arm = armature_core()
        fld = field_lines(0.0)

        cap1 = caption("เครื่องกำเนิด 2 ขั้ว — เส้นแรงวิ่งจาก N ไป S")
        self.play(FadeIn(n_pole), FadeIn(s_pole), FadeIn(arm),
                  FadeIn(cap1), run_time=1.0)
        self.play(LaggedStart(*[GrowArrow(a) for a in fld], lag_ratio=0.12),
                  run_time=1.4)
        self.wait(0.7)

        # --- ฉาก 2: ขดลวดตัดเส้นแรง -> emf ; ตรงไหน emf = 0
        coil = Dot(STAGE + np.array([0, R_ARM, 0]), radius=0.13, color=CURRENT)
        emf_lbl = Text("emf", font_size=22, color=EMF)
        emf_num = DecimalNumber(0, num_decimal_places=2, font_size=28, color=EMF,
                                mob_class=Text)

        theta = ValueTracker(0.0)

        def coil_pos():
            a = theta.get_value()
            return STAGE + R_ARM * np.array([np.sin(a), np.cos(a), 0.0])

        coil.add_updater(lambda m: m.move_to(coil_pos()))
        # emf ~ sin(มุมจากแนวตั้ง) : สูงสุดตอนขดอยู่ข้างขั้ว, ศูนย์ตอนอยู่บน/ล่าง
        emf_num.add_updater(lambda m: m.set_value(abs(np.sin(theta.get_value()))))

        row = VGroup(emf_lbl, emf_num).arrange(RIGHT, buff=0.22)
        row.move_to([PANEL_X + 0.6, 2.4, 0])

        cap2 = caption("ขดลวดตัดเส้นแรงมาก → emf มาก · ขนานกับเส้นแรง → emf = 0")
        self.play(FadeOut(cap1), run_time=0.3)
        self.play(FadeIn(cap2), FadeIn(coil), FadeIn(row), run_time=0.9)
        self.play(theta.animate.set_value(2 * PI), run_time=4.2,
                  rate_func=linear)
        self.wait(0.4)

        # --- ฉาก 3: ทำเครื่องหมายระนาบเป็นกลาง (แนวตั้ง)
        np_line = plane_line(0.0, OK)
        np_lbl = Text("ระนาบเป็นกลาง", font_size=21, color=OK)
        np_lbl.move_to(STAGE + np.array([0, 3.0, 0]))

        cap3 = caption("เส้นที่ emf = 0 = ระนาบเป็นกลาง  (ตั้งฉากกับเส้นแรง)")
        self.play(FadeOut(cap2), run_time=0.3)
        self.play(FadeIn(cap3), Create(np_line), FadeIn(np_lbl), run_time=1.1)
        self.wait(0.9)

        # --- ฉาก 4: แปรงถ่านต้องอยู่ตรงนี้
        b_top = Rectangle(width=0.42, height=0.34, fill_color=WARN,
                          fill_opacity=0.95, stroke_width=0)
        b_top.move_to(STAGE + np.array([0, R_ARM + 0.20, 0]))
        b_bot = b_top.copy().move_to(STAGE + np.array([0, -R_ARM - 0.20, 0]))

        cap4 = caption("แปรงถ่านต้องลัดวงจรขดลวดตอน emf = 0 เท่านั้น ไม่งั้นขดไหม้")
        self.play(FadeOut(cap3), run_time=0.3)
        self.play(FadeIn(cap4), FadeIn(b_top), FadeIn(b_bot), run_time=1.0)
        self.wait(1.1)

        # --- ฉาก 5: จ่ายโหลด -> สนามเอียง -> ระนาบขยับ  (จังหวะ "อ๋อ")
        coil.clear_updaters()
        emf_num.clear_updaters()
        self.play(FadeOut(coil), FadeOut(row), run_time=0.5)

        tilt = 26 * DEGREES
        fld2 = field_lines(tilt)
        np_line2 = plane_line(tilt, WARN, width=6)
        np_lbl2 = Text("ตำแหน่งใหม่", font_size=21, color=WARN)
        np_lbl2.move_to(STAGE + np.array([2.05, 3.0, 0]))
        rot_arrow = CurvedArrow(STAGE + np.array([-0.8, 2.35, 0]),
                                STAGE + np.array([1.15, 2.15, 0]),
                                color=WARN, stroke_width=3, tip_length=0.18)

        cap5 = caption("พอจ่ายโหลด สนามเอียง → จุดที่ emf = 0 ย้ายตามทิศหมุน")
        self.play(FadeOut(cap4), run_time=0.3)
        self.play(FadeIn(cap5), Transform(fld, fld2),
                  Create(np_line2), FadeIn(np_lbl2), Create(rot_arrow),
                  run_time=1.8)
        self.wait(1.2)

        cap6 = caption("แปรงถ่านยังอยู่ที่เดิม → ลัดวงจรตอนยังมี emf → สปาร์ค",
                       color=WARN)
        spark = VGroup(*[
            Star(n=6, outer_radius=0.20, inner_radius=0.08,
                 color=EMF, fill_opacity=0.95, stroke_width=0)
            .move_to(b.get_center()) for b in (b_top, b_bot)])
        self.play(FadeOut(cap5), run_time=0.3)
        self.play(FadeIn(cap6), FadeIn(spark, scale=1.6), run_time=0.9)
        self.play(Indicate(spark, color=EMF, scale_factor=1.35), run_time=0.8)
        self.wait(1.0)

        # --- สรุป
        self.play(*[FadeOut(m) for m in
                    (n_pole, s_pole, arm, fld, np_line, np_lbl, np_line2,
                     np_lbl2, rot_arrow, b_top, b_bot, spark, cap6, t)],
                  run_time=0.8)
        s1 = Text("ระนาบเป็นกลาง ≠ กึ่งกลางเชิงเรขาคณิต", font_size=30, color=WHITE)
        s2 = Text("แต่คือ “ตำแหน่งที่ emf = 0”  ซึ่งขยับตามโหลด",
                  font_size=26, color=OK)
        card = VGroup(s1, s2).arrange(DOWN, buff=0.45).move_to(ORIGIN)
        self.play(FadeIn(card, shift=UP * 0.25), run_time=1.0)
        self.wait(1.8)


# ================================================================== EP08
class EP08(SafeScene):
    """อาร์เมเจอร์รีแอคชั่น = บวกเวกเตอร์สนาม 2 สนามที่ตั้งฉากกัน"""

    def construct(self):
        t = title("อาร์เมเจอร์รีแอคชั่น — สนามสองสนามบวกกัน", size=29)
        self.play(FadeIn(t, shift=DOWN * 0.2))

        origin = np.array([-3.1, -0.35, 0.0])
        SC = 1.55

        # --- ฉาก 1: สนามหลัก (แนวนอน)
        bf = Arrow(origin, origin + np.array([SC, 0, 0]), buff=0,
                   color=FIELD, stroke_width=7, tip_length=0.26,
                   max_tip_length_to_length_ratio=0.4)
        bf_l = Text("สนามหลัก", font_size=21, color=FIELD)
        bf_l.next_to(bf, DOWN, buff=0.22)

        cap1 = caption("สนามที่ 1 — สนามแม่เหล็กหลัก จากชุดขดลวดสนาม")
        self.play(FadeIn(cap1), GrowArrow(bf), FadeIn(bf_l), run_time=1.1)
        self.wait(0.8)

        # --- ฉาก 2: สนามอาร์เมเจอร์ (ตั้งฉาก!) <- จังหวะ "อ๋อ" ที่ 1
        ba = Arrow(origin, origin + np.array([0, SC, 0]), buff=0,
                   color=CURRENT, stroke_width=7, tip_length=0.26,
                   max_tip_length_to_length_ratio=0.4)
        ba_l = Text("สนามจากอาร์เมเจอร์", font_size=21, color=CURRENT)
        ba_l.next_to(ba, LEFT, buff=0.22)
        rt = RightAngle(bf, ba, length=0.32, color=GRAYTXT, stroke_width=3)

        cap2 = caption("สนามที่ 2 — จากกระแสอาร์เมเจอร์ · แกนของมัน ตั้งฉาก 90°")
        self.play(FadeOut(cap1), run_time=0.3)
        self.play(FadeIn(cap2), GrowArrow(ba), FadeIn(ba_l), Create(rt),
                  run_time=1.3)
        self.wait(1.0)

        # --- ฉาก 3: ผลรวม + โหลดเพิ่ม -> มุมเอียงเพิ่ม
        load = ValueTracker(0.30)

        def res_tip():
            return origin + np.array([SC, SC * load.get_value(), 0])

        res = always_redraw(lambda: Arrow(
            origin, res_tip(), buff=0, color=WARN, stroke_width=8,
            tip_length=0.28, max_tip_length_to_length_ratio=0.4))
        ba_dyn = always_redraw(lambda: DashedLine(
            origin + np.array([SC, 0, 0]), res_tip(),
            color=CURRENT, stroke_width=3, dash_length=0.10))

        res_l = Text("สนามรวม", font_size=21, color=WARN)
        res_l.move_to(origin + np.array([2.35, 1.55, 0]))

        cur_row = live_row("กระแสโหลด", "A",
                           lambda: 40 * load.get_value(),
                           [PANEL_X - 0.25, 2.15, 0], decimals=0,
                           num_color=CURRENT)
        ang_row = live_row("มุมเอียง", "°",
                           lambda: np.degrees(np.arctan(load.get_value())),
                           [PANEL_X - 0.25, 1.15, 0], decimals=1,
                           num_color=WARN)

        cap3 = caption("ผลรวมของสองสนาม = สนามจริงที่ขดลวดตัด → มันเอียง")
        self.play(FadeOut(cap2), run_time=0.3)
        self.play(FadeIn(cap3), FadeIn(res), FadeIn(ba_dyn), FadeIn(res_l),
                  FadeIn(cur_row), FadeIn(ang_row), run_time=1.2)
        self.wait(0.6)

        cap4 = caption("โหลดมากขึ้น → สนามอาร์เมเจอร์แรงขึ้น → เอียงมากขึ้น")
        self.play(FadeOut(cap3), run_time=0.3)
        self.play(FadeIn(cap4), run_time=0.4)
        self.play(load.animate.set_value(1.05), run_time=2.6)
        self.play(load.animate.set_value(0.30), run_time=1.6)
        self.play(load.animate.set_value(0.80), run_time=1.4)
        self.wait(0.6)

        res.clear_updaters()
        ba_dyn.clear_updaters()
        cur_row[1].clear_updaters()
        ang_row[1].clear_updaters()

        self.play(*[FadeOut(m) for m in (bf, bf_l, ba, ba_l, rt, res, ba_dyn,
                                         res_l, cur_row, ang_row, cap4)],
                  run_time=0.8)

        # --- ฉาก 4: แยกผลเสีย 2 ส่วน  <- จังหวะ "อ๋อ" ที่ 2
        cap5 = caption("สนามอาร์เมเจอร์แยกได้ 2 ส่วน — ให้ผลเสียคนละอย่าง")
        self.play(FadeIn(cap5), run_time=0.5)

        # ซ้าย: ส่วนต่อต้าน
        lc = np.array([-3.5, 0.45, 0.0])
        a_main = Arrow(lc + LEFT * 0.9, lc + RIGHT * 0.9, buff=0,
                       color=FIELD, stroke_width=6, tip_length=0.22)
        a_opp = Arrow(lc + RIGHT * 0.9 + DOWN * 0.55,
                      lc + LEFT * 0.9 + DOWN * 0.55, buff=0,
                      color=CURRENT, stroke_width=6, tip_length=0.22)
        l_ttl = Text("ส่วนต่อต้าน (BB)", font_size=23, color=WARN)
        l_ttl.move_to(lc + UP * 1.5)
        l_txt = Text("สนามหลักอ่อนลง →  แรงดันที่ขั้วตก", font_size=20,
                     color=GRAYTXT)
        l_txt.move_to(lc + DOWN * 1.55)
        fit_width(l_txt, 5.6)

        # ขวา: ส่วนขวาง
        rc = np.array([3.5, 0.45, 0.0])
        b_main = Arrow(rc + LEFT * 0.9, rc + RIGHT * 0.9, buff=0,
                       color=FIELD, stroke_width=6, tip_length=0.22)
        b_cross = Arrow(rc + DOWN * 0.75, rc + UP * 0.75, buff=0,
                        color=CURRENT, stroke_width=6, tip_length=0.22)
        r_ttl = Text("ส่วนขวาง (AA)", font_size=23, color=WARN)
        r_ttl.move_to(rc + UP * 1.5)
        r_txt = Text("สนามหลักเบี่ยง →  ระนาบเลื่อน →  สปาร์ค", font_size=20,
                     color=GRAYTXT)
        r_txt.move_to(rc + DOWN * 1.55)
        fit_width(r_txt, 5.6)

        divider = DashedLine([0, -2.1, 0], [0, 2.1, 0], color="#37474F",
                             stroke_width=2, dash_length=0.12)

        self.play(Create(divider), run_time=0.4)
        self.play(FadeIn(l_ttl), GrowArrow(a_main), GrowArrow(a_opp),
                  FadeIn(l_txt), run_time=1.2)
        self.wait(0.9)
        self.play(FadeIn(r_ttl), GrowArrow(b_main), GrowArrow(b_cross),
                  FadeIn(r_txt), run_time=1.2)
        self.wait(1.4)

        self.play(*[FadeOut(m) for m in
                    (divider, l_ttl, a_main, a_opp, l_txt,
                     r_ttl, b_main, b_cross, r_txt, cap5, t)], run_time=0.8)
        s1 = Text("BB ทำให้แรงดันตก   ·   AA ทำให้สปาร์ค", font_size=30,
                  color=WHITE)
        s2 = Text("ระยะเอียงแปรผันตรงกับกระแสโหลด", font_size=26, color=OK)
        card = VGroup(s1, s2).arrange(DOWN, buff=0.45).move_to(ORIGIN)
        self.play(FadeIn(card, shift=UP * 0.25), run_time=1.0)
        self.wait(1.8)


# ================================================================== EP09
class EP09(SafeScene):
    """คอมมิวเตชั่น — การส่งไม้ผลัดของกระแส 50 → 100 A"""

    def construct(self):
        t = title("คอมมิวเตชั่น — ส่งไม้ผลัดกระแส", size=30)
        self.play(FadeIn(t, shift=DOWN * 0.2))

        # --- เวที: ซี่คอมมิวเตเตอร์แนวตรง + แปรงถ่าน
        bar_w, bar_h, gap = 1.30, 0.72, 0.10
        base_y = -0.55
        bars, blabels = VGroup(), VGroup()
        for i, name in enumerate(["", "1", "2", ""]):
            x = (i - 1.5) * (bar_w + gap)
            r = Rectangle(width=bar_w, height=bar_h, fill_color="#455A64",
                          fill_opacity=0.9, stroke_color=METAL, stroke_width=2)
            r.move_to([x, base_y, 0])
            bars.add(r)
            if name:
                blabels.add(Text(name, font_size=24,
                                 color=WHITE).move_to(r.get_center()))

        brush = Rectangle(width=1.55, height=0.55, fill_color=WARN,
                          fill_opacity=0.95, stroke_width=0)
        brush_pos = ValueTracker(-0.70)
        brush.add_updater(lambda m: m.move_to(
            [brush_pos.get_value(), base_y - bar_h / 2 - 0.32, 0]))
        bplus = Text("+", font_size=30, color=BLACK)
        bplus.add_updater(lambda m: m.move_to(brush.get_center()))

        cap1 = caption("แปรงถ่านบวกสัมผัสซี่คอมมิวเตเตอร์ 2 ซี่พร้อมกัน")
        self.play(FadeIn(cap1), FadeIn(bars), FadeIn(blabels),
                  FadeIn(brush), FadeIn(bplus), run_time=1.1)

        # --- ขดลวด A B C ด้านบน
        coil_names = ["A", "B", "C"]
        coils, cl = VGroup(), VGroup()
        for i, nm in enumerate(coil_names):
            x = (i - 1.0) * (bar_w + gap)
            arc = Arc(radius=0.42, start_angle=0, angle=PI,
                      color=CURRENT, stroke_width=5)
            arc.move_to([x, base_y + bar_h / 2 + 0.55, 0])
            coils.add(arc)
            cl.add(Text(nm, font_size=23, color=CURRENT)
                   .move_to([x, base_y + bar_h / 2 + 1.18, 0]))
        self.play(LaggedStart(*[Create(a) for a in coils], lag_ratio=0.2),
                  FadeIn(cl), run_time=1.1)

        # --- ตัวเลขกระแสสองซี่
        prog = ValueTracker(0.0)   # 0 = เริ่ม, 1 = จบการส่งไม้ผลัด

        i1_row = live_row("ซี่ที่ 1", "A", lambda: 50 + 50 * prog.get_value(),
                          [-4.0, 2.35, 0], decimals=0, num_color=CURRENT)
        i2_row = live_row("ซี่ที่ 2", "A", lambda: 50 - 50 * prog.get_value(),
                          [1.5, 2.35, 0], decimals=0, num_color=CURRENT)

        cap2 = caption("โหลด 100 A แบ่ง 2 เส้นทาง → ซี่ละ 50 A")
        self.play(FadeOut(cap1), run_time=0.3)
        self.play(FadeIn(cap2), FadeIn(i1_row), FadeIn(i2_row), run_time=1.0)
        self.wait(1.0)

        # --- ขด B ถูกลัดวงจร emf = 0
        highlight = SurroundingRectangle(coils[1], color=OK, buff=0.14,
                                         stroke_width=4)
        b_note = Text("ขด B ถูกลัดวงจร · emf = 0 · ไม่มีกระแส", font_size=21,
                      color=OK)
        b_note.move_to([0, 1.30, 0])
        cap3 = caption("ขดที่กำลังถูกลัดวงจรต้องมี emf = 0 พอดี")
        self.play(FadeOut(cap2), run_time=0.3)
        self.play(FadeIn(cap3), Create(highlight), FadeIn(b_note),
                  run_time=1.1)
        self.wait(1.2)

        # --- ส่งไม้ผลัด
        cap4 = caption("แปรงถ่านเลื่อน → ซี่ 1 รับเพิ่ม · ซี่ 2 ปล่อยจนหมด")
        self.play(FadeOut(cap3), run_time=0.3)
        self.play(FadeIn(cap4), run_time=0.3)
        self.play(prog.animate.set_value(1.0),
                  brush_pos.animate.set_value(-1.45), run_time=3.0)
        self.wait(0.8)

        done = Text("คอมมิวเตชั่นสมบูรณ์", font_size=24, color=OK)
        done.move_to([0, -2.15, 0])
        self.play(FadeIn(done, scale=1.1), run_time=0.7)
        self.wait(1.0)

        # --- ปัญหา: เหนี่ยวนำในตัวเอง  <- จังหวะ "อ๋อ"
        i1_row[1].clear_updaters()
        i2_row[1].clear_updaters()
        brush.clear_updaters()
        bplus.clear_updaters()
        self.play(*[FadeOut(m) for m in (highlight, b_note, done, cap4)],
                  run_time=0.6)

        cap5 = caption("แต่ตอนกระแสในขด A ลดลง สนามรอบมันยุบ → เกิด emf ต้าน",
                       color=WARN)
        lenz = Arrow([-2.2, 1.55, 0], [-0.7, 1.55, 0], buff=0, color=EMF,
                     stroke_width=6, tip_length=0.22)
        lenz_l = Text("emf เหนี่ยวนำในตัวเอง", font_size=21, color=EMF)
        lenz_l.move_to([0.95, 1.55, 0])
        self.play(FadeIn(cap5), GrowArrow(lenz), FadeIn(lenz_l), run_time=1.1)
        self.wait(1.1)

        cap6 = caption("กระแสจึงไม่ยอมเป็นศูนย์ → อาร์คตอนซี่หลุดจากแปรงถ่าน",
                       color=WARN)
        spark = Star(n=7, outer_radius=0.30, inner_radius=0.13, color=EMF,
                     fill_opacity=1.0, stroke_width=0)
        spark.move_to([-1.45, base_y - bar_h / 2 - 0.32, 0])
        self.play(FadeOut(cap5), run_time=0.3)
        self.play(FadeIn(cap6), FadeIn(spark, scale=1.8), run_time=0.9)
        self.play(Indicate(spark, color=EMF, scale_factor=1.4), run_time=0.8)
        self.wait(1.0)

        self.play(*[FadeOut(m) for m in
                    (bars, blabels, brush, bplus, coils, cl, i1_row, i2_row,
                     lenz, lenz_l, spark, cap6, t)], run_time=0.8)
        s1 = Text("แม้ emf ตัวนี้จะเล็กมาก", font_size=29, color=WHITE)
        s2 = Text("แต่ความต้านทานของแปรงถ่าน/ซี่ ก็เล็กกว่า → กระแสยังไหลได้มาก",
                  font_size=24, color=WARN)
        fit_width(s2, 12.5)
        card = VGroup(s1, s2).arrange(DOWN, buff=0.45).move_to(ORIGIN)
        self.play(FadeIn(card, shift=UP * 0.25), run_time=1.0)
        self.wait(1.8)


# ================================================================== EP10
class EP10(SafeScene):
    """interpole vs ขดลวดชดเชย — คนละตำแหน่ง แก้คนละปัญหา"""

    def construct(self):
        t = title("ตัวแก้ 2 ตัว — คนละตำแหน่ง แก้คนละปัญหา", size=29)
        self.play(FadeIn(t, shift=DOWN * 0.2))

        divider = DashedLine([0, -2.55, 0], [0, 2.75, 0], color="#37474F",
                             stroke_width=2, dash_length=0.12)
        self.play(Create(divider), run_time=0.4)

        # ---------------- ซ้าย: ขั้วแม่เหล็กเสริม
        lc = np.array([-3.55, 0.35, 0.0])
        l_ttl = Text("ขั้วแม่เหล็กเสริม (interpole)", font_size=23, color=OK)
        l_ttl.move_to(lc + UP * 2.25)

        l_arm = Circle(radius=0.78, fill_color="#546E7A", fill_opacity=0.75,
                       stroke_color=METAL, stroke_width=2).move_to(lc)
        l_pn = Rectangle(width=0.52, height=1.05, fill_color=METAL,
                         fill_opacity=0.5, stroke_width=1.5)
        l_pn.move_to(lc + LEFT * 1.45)
        l_ps = l_pn.copy().move_to(lc + RIGHT * 1.45)
        # interpole อยู่บน/ล่าง = ตำแหน่งระนาบเป็นกลาง
        l_ip1 = Rectangle(width=0.60, height=0.36, fill_color=OK,
                          fill_opacity=0.9, stroke_width=0)
        l_ip1.move_to(lc + UP * 1.15)
        l_ip2 = l_ip1.copy().move_to(lc + DOWN * 1.15)
        l_zone = DashedVMobject(Line(lc + UP * 1.55, lc + DOWN * 1.55,
                                     color=OK, stroke_width=4),
                                num_dashes=14)
        l_note = Text("อยู่เฉพาะ “จุด” ระนาบเป็นกลาง", font_size=20, color=GRAYTXT)
        l_note.move_to(lc + DOWN * 2.35)
        fit_width(l_note, 6.0)

        self.play(FadeIn(l_ttl), FadeIn(l_arm), FadeIn(l_pn), FadeIn(l_ps),
                  run_time=0.9)
        self.play(Create(l_zone), FadeIn(l_ip1), FadeIn(l_ip2),
                  FadeIn(l_note), run_time=1.1)
        self.wait(0.9)

        # ---------------- ขวา: ชุดขดลวดชดเชย
        rc = np.array([3.55, 0.35, 0.0])
        r_ttl = Text("ชุดขดลวดชดเชย", font_size=23, color=CURRENT)
        r_ttl.move_to(rc + UP * 2.25)

        r_arm = Circle(radius=0.78, fill_color="#546E7A", fill_opacity=0.75,
                       stroke_color=METAL, stroke_width=2).move_to(rc)
        r_pn = Rectangle(width=0.52, height=1.05, fill_color=METAL,
                         fill_opacity=0.5, stroke_width=1.5)
        r_pn.move_to(rc + LEFT * 1.45)
        r_ps = r_pn.copy().move_to(rc + RIGHT * 1.45)
        # ขดลวดชดเชยฝังในหน้าขั้ว — จุดเรียงตามผิวหน้าขั้วทั้งสองข้าง
        dots = VGroup()
        for side in (-1, 1):
            for k in range(3):
                d = Dot(rc + np.array([side * 1.19, (k - 1) * 0.33, 0]),
                        radius=0.075, color=CURRENT)
                dots.add(d)
        r_ring = DashedVMobject(Circle(radius=1.02, color=CURRENT,
                                       stroke_width=4).move_to(rc),
                                num_dashes=22)
        r_note = Text("ฝังในหน้าขั้ว — ครอบคลุมรอบวง", font_size=20,
                      color=GRAYTXT)
        r_note.move_to(rc + DOWN * 2.35)
        fit_width(r_note, 6.0)

        self.play(FadeIn(r_ttl), FadeIn(r_arm), FadeIn(r_pn), FadeIn(r_ps),
                  run_time=0.9)
        self.play(Create(r_ring), FadeIn(dots), FadeIn(r_note), run_time=1.1)
        self.wait(1.3)

        # ---------------- ตารางเทียบ (จังหวะ "อ๋อ")
        self.play(*[FadeOut(m) for m in
                    (divider, l_ttl, l_arm, l_pn, l_ps, l_ip1, l_ip2, l_zone,
                     l_note, r_ttl, r_arm, r_pn, r_ps, dots, r_ring, r_note)],
                  run_time=0.8)

        rows = [
            ("",                     "interpole",  "ขดลวดชดเชย"),
            ("แก้ การเหนี่ยวนำในตัวเอง", "ได้หมด",     "ไม่หมด"),
            ("แก้ อาร์เมเจอร์รีแอคชั่น", "ได้บางส่วน",  "ได้"),
        ]
        colw = [4.9, 2.9, 2.9]
        xs = [-4.0, 0.95, 4.0]
        tbl = VGroup()
        for r, (a, b, c) in enumerate(rows):
            y = 1.55 - r * 1.05
            for x, txt, w in zip(xs, (a, b, c), colw):
                col = WHITE if r == 0 else GRAYTXT
                sz = 23 if r == 0 else 22
                if r == 0 and txt == "interpole":
                    col = OK
                if r == 0 and txt == "ขดลวดชดเชย":
                    col = CURRENT
                if r > 0 and txt in ("ได้หมด", "ได้"):
                    col = OK
                if r > 0 and txt in ("ไม่หมด", "ได้บางส่วน"):
                    col = WARN
                m = Text(txt, font_size=sz, color=col)
                fit_width(m, w)
                m.move_to([x, y, 0])
                tbl.add(m)
        hline = Line([-6.4, 1.05, 0], [6.0, 1.05, 0], color="#37474F",
                     stroke_width=2)

        self.play(FadeIn(tbl[0:3]), Create(hline), run_time=0.9)
        self.play(FadeIn(tbl[3:6]), run_time=0.8)
        self.wait(0.7)
        self.play(FadeIn(tbl[6:9]), run_time=0.8)
        self.wait(1.6)

        self.play(FadeOut(tbl), FadeOut(hline), FadeOut(t), run_time=0.7)
        s1 = Text("เครื่องใหญ่ / โหลดเปลี่ยนกว้าง", font_size=29, color=WHITE)
        s2 = Text("ใช้ทั้งสองอย่างร่วมกันเสมอ", font_size=30, color=OK)
        card = VGroup(s1, s2).arrange(DOWN, buff=0.45).move_to(ORIGIN)
        self.play(FadeIn(card, shift=UP * 0.25), run_time=1.0)
        self.wait(1.8)
