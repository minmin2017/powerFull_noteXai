"""agile_wheelleg_robot_anim.py — teaching video for:
Yun, Park, Seo, Kim, "Development of an Agile Omnidirectional Mobile Robot
With GRF Compensated Wheel-leg Mechanisms for Human Environments,"
IEEE Robotics and Automation Letters, Vol.6, No.4, Oct 2021.
DOI: 10.1109/LRA.2021.3098954

Cross-platform: Windows (local draft) + GitHub Actions Docker (cloud final).
"""
import os
import sys

from mlib import *  # SafeScene, SafeThreeDScene, palette, title/caption/panel_slot,
                     # arrow3/line3, live_row, fit_width, TITLE_Y, CAP_Y, STAGE_C

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = lambda name: os.path.join(HERE, "assets", "agile_robot", name)

# ---------------------------------------------------------------- palette
# one color per recurring quantity, reused across every scene (Mayer signaling)
LEGC = FIELD       # "#42A5F5" leg / joint / actuator
WHEELC = METAL     # "#90A4AE" mecanum wheel / body structure
GRFC = WARN        # "#FF7043" ground reaction force / lifting torque
SPRINGC = TORQUE   # "#AB47BC" compensation spring / compensation torque
POLYC = OK         # "#26C6DA" support polygon
COPC = "#FFEE58"   # COP marker (new, distinct from caption gray)
ACTC = EMF         # "#EF5350" actuator torque (net, after compensation)


def fit_height(mob, max_h):
    if mob.height > max_h:
        mob.scale(max_h / mob.height)
    return mob


def bullets(items, color=WHITE, size=26, buff=0.28):
    g = VGroup(*[Text(f"•  {t}", font_size=size, color=color) for t in items])
    g.arrange(DOWN, aligned_edge=LEFT, buff=buff)
    return g


def image_stage(path, max_w=7.6, max_h=4.6, center=None):
    img = ImageMobject(path)
    if img.width > max_w:
        img.scale(max_w / img.width)
    if img.height > max_h:
        img.scale(max_h / img.height)
    img.move_to(center if center is not None else [0, 0.15, 0])
    return img


# ============================================================== R01_Intro
class R01_Intro(SafeScene):
    def construct(self):
        t1 = Text("Development of an Agile Omnidirectional Mobile Robot",
                   font_size=32, color=WHITE)
        t2 = Text("With GRF Compensated Wheel-leg Mechanisms for Human Environments",
                   font_size=26, color=GRAYTXT)
        VGroup(t1, t2).arrange(DOWN, buff=0.25).move_to([0, 2.7, 0])
        self.play(Write(t1), run_time=1.6)
        self.play(FadeIn(t2))

        meta = Text("Yun, Park, Seo, Kim — KOREATECH  |  IEEE RA-L Vol.6 No.4, Oct 2021",
                     font_size=20, color=GRAYTXT).move_to([0, 2.0, 0])
        self.play(FadeIn(meta))
        self.wait(1)

        img = image_stage(IMG("fig1_hero.png"), max_w=4.6, max_h=4.2, center=[0, -0.3, 0])
        self.play(FadeIn(img, shift=UP * 0.3))
        self.wait(1.5)

        hook = Text("ทำไมหุ่นยนต์เคลื่อนที่ทั่วไป อยู่ร่วมพื้นที่กับมนุษย์ไม่ได้?",
                     font_size=24, color=WARN).move_to([0, CAP_Y, 0])
        self.play(FadeIn(hook))
        self.wait(1)
        sub = Text("ลิฟต์แคบ / ทางเดินคับ / ธรณีประตู / ทางลาด",
                    font_size=20, color=GRAYTXT).next_to(hook, UP, buff=0.15)
        self.play(FadeIn(sub))
        self.wait(1.5)

        self.play(FadeOut(Group(t1, t2, meta, img, hook, sub)))

        title2 = title("3 จุดเด่นของงานวิจัยนี้", color=WHITE)
        self.play(Write(title2))
        items = bullets([
            "ขา mecanum wheel-leg ที่เปลี่ยน support polygon ได้อิสระในปริภูมิ 3 มิติ",
            "เกียร์ compound planetary แบบ backdrivable ทดรอบสูง 65:1",
            "กลไกชดเชยแรงปฏิกิริยาพื้น (GRF compensation) ลดภาระ actuator",
        ], size=27).move_to([0, 0, 0])
        for it in items:
            self.play(FadeIn(it, shift=RIGHT * 0.2), run_time=0.8)
            self.wait(0.4)
        self.wait(1.5)
        self.play(FadeOut(VGroup(title2, items)))


# =========================================================== R02_Motivation
class R02_Motivation(SafeScene):
    def construct(self):
        self.play(Write(title("โจทย์: หุ่นยนต์เคลื่อนที่แบบไหนดีที่สุด?")))

        col_x = [-4.4, 0, 4.4]
        heads = ["ล้อ (Differential-drive)", "ขา (Legged, เช่น BigDog, MIT Cheetah)",
                 "ล้อ+ขา แบบผสม (เช่น CENTAURO, ANYmal, Rollin' Justin)"]
        good = [["เรียบง่าย มีประสิทธิภาพ"], ["คล่องตัวบนพื้นขรุขระ"],
                ["ได้ทั้งสองข้อดี"]]
        bad = [["Non-holonomic หลบสิ่งกีดขวางกะทันหันไม่ได้"],
               ["ใช้พลังงานเยอะ ทรงตัวยากกว่า"],
               ["กลไกซับซ้อน / DOF สูง / ควบคุมยาก"]]

        cols = VGroup()
        for i, x in enumerate(col_x):
            h = Text(heads[i], font_size=19, color=WHITE).move_to([x, 2.3, 0])
            fit_width(h, 4.2)
            g_txt = Text("✓ " + good[i][0], font_size=17, color=OK).next_to(h, DOWN, buff=0.35)
            b_txt = Text("✗ " + bad[i][0], font_size=17, color=WARN).next_to(g_txt, DOWN, buff=0.25)
            fit_width(g_txt, 4.2)
            fit_width(b_txt, 4.2)
            cols.add(VGroup(h, g_txt, b_txt))

        for c in cols:
            self.play(FadeIn(c, shift=UP * 0.2), run_time=0.9)
            self.wait(0.3)
        self.wait(0.5)

        line1 = Line([-6.2, 0.5, 0], [6.2, 0.5, 0], color=GRAYTXT, stroke_width=1)
        self.play(Create(line1))

        novelty = Text(
            "จุดใหม่ของเปเปอร์นี้: ระบบล้อ-ขา mecanum ตัวแรกที่เปลี่ยน\n"
            "support polygon ได้อิสระในปริภูมิ 3 มิติ",
            font_size=23, color=POLYC, line_spacing=1.2
        ).move_to([0, -1.6, 0])
        fit_width(novelty, 11.5)
        self.play(FadeIn(novelty, shift=UP * 0.2))
        self.wait(2)

        self.play(FadeOut(VGroup(cols, line1, novelty)))


# ======================================================== R03_DesignConcept
class R03_DesignConcept(SafeScene):
    def construct(self):
        ttl1 = title("แนวคิดการออกแบบ: มนุษย์เปลี่ยน support polygon ตามท่าทาง")
        self.play(Write(ttl1))

        img = image_stage(IMG("fig2_support_polygon.png"), max_w=9.6, max_h=4.7,
                           center=[0, 0.1, 0])
        self.play(FadeIn(img))
        self.wait(0.5)

        # 6 sub-panel boxes approximated on a 3-col x 2-row grid within the image
        iw, ih = img.width, img.height
        ic = img.get_center()
        col_xs = [ic[0] - iw / 3, ic[0], ic[0] + iw / 3]
        row_ys = [ic[1] + ih / 4, ic[1] - ih / 4]
        caps = [
            "(a) ยืนตรง — polygon เล็กสุดพอทรงตัว",
            "(b) เดิน — polygon ยาวรีตามแนวเดิน",
            "(c) เคลื่อนไหวเร็ว (ชก) — polygon กว้างทุกทิศ",
            "(d) ก้มหยิบของ — ปรับความสูงตัว",
            "(e) ขึ้นทางลาด",
            "(f) ขึ้นบันไดขั้นเดียว",
        ]
        idx = 0
        cap = None
        for ry in row_ys:
            for cx in col_xs:
                box = SurroundingRectangle(Dot([cx, ry, 0]), color=POLYC,
                                            buff=0.55, stroke_width=3)
                box.width = iw / 3 * 0.92
                box.height = ih / 2 * 0.92
                box.move_to([cx, ry, 0])
                newcap = Text(caps[idx], font_size=20, color=POLYC).move_to([0, CAP_Y, 0])
                fit_width(newcap, 10.5)
                if cap is None:
                    self.play(Create(box), FadeIn(newcap))
                else:
                    self.play(ReplacementTransform(prevbox, box), FadeOut(cap))
                    self.play(FadeIn(newcap))
                cap = newcap
                prevbox = box
                self.wait(0.7)
                idx += 1
        self.play(FadeOut(Group(img, prevbox, cap, ttl1)))

        title2 = Text("เป้าหมายการออกแบบ 4 ข้อ", font_size=28, color=WHITE).move_to([0, TITLE_Y, 0])
        self.play(Write(title2))
        items = bullets([
            "รูปทรงเพรียวบาง ใกล้เคียงขนาดมนุษย์",
            "Support polygon ปรับได้ ด้วย DOF น้อยที่สุด",
            "เคลื่อนที่แบบ holonomic คล่องตัวปลอดภัย",
            "คล่องตัวในพื้นที่มนุษย์: ทางเดิน ธรณีประตู ทางลาด ลิฟต์",
        ], size=25).move_to([0, 0, 0])
        for it in items:
            self.play(FadeIn(it, shift=RIGHT * 0.2), run_time=0.7)
        self.wait(2)
        self.play(FadeOut(VGroup(title2, items)))


# ======================================================= R04_MecanumProblem
class R04_MecanumProblem(SafeScene):
    def construct(self):
        self.play(Write(title("ปัญหา: ล้อ mecanum ต้องคงมุมโรลเลอร์ ±45°")))

        # simple mecanum wheel schematic: circle + rollers at 45deg
        wheel = Circle(radius=1.3, color=WHEELC, stroke_width=5).move_to([-3.2, 0.3, 0])
        rollers = VGroup()
        for k in range(8):
            ang = k * TAU / 8
            c = wheel.get_center() + 1.3 * np.array([np.cos(ang), np.sin(ang), 0])
            r = Line(ORIGIN, [0.42, 0, 0], color=WHEELC, stroke_width=6)
            r.rotate(ang + PI / 4)
            r.move_to(c)
            rollers.add(r)
        fwd = Arrow(wheel.get_center() + LEFT * 3.6, wheel.get_center() + LEFT * 1.7,
                    color=OK, buff=0, stroke_width=5)
        fwd_lbl = Text("ทิศเดินหน้าตัวหุ่น", font_size=18, color=OK).next_to(fwd, DOWN, buff=0.15)

        self.play(Create(wheel), Create(rollers))
        self.play(GrowArrow(fwd), FadeIn(fwd_lbl))
        self.wait(1)

        rule = Text("แกนโรลเลอร์ต้องทำมุมคงที่ ±45° กับทิศเดินหน้าตัวหุ่นเสมอ",
                     font_size=22, color=WHEELC).move_to([2.6, 1.6, 0])
        fit_width(rule, 5.6)
        self.play(FadeIn(rule))
        self.wait(1)

        problem = Text("ถ้าขาขยับ (yaw/pitch) แล้วล้อหมุนตามไปด้วย\nมุมโรลเลอร์จะเพี้ยน — สูญเสียคุณสมบัติ holonomic",
                        font_size=20, color=WARN, line_spacing=1.3).move_to([2.6, -0.3, 0])
        fit_width(problem, 5.6)
        self.play(FadeIn(problem))
        self.wait(1.5)

        solve = Text("ทางแก้: กลไก parallel-link พิเศษ ตรึงทิศทางล้อไว้\nแม้ขาจะขยับ 2-DOF อิสระ (ดูฉากถัดไป)",
                      font_size=20, color=POLYC, line_spacing=1.3).move_to([2.6, -2.0, 0])
        fit_width(solve, 5.6)
        self.play(FadeIn(solve))
        self.wait(2)

        self.play(FadeOut(VGroup(wheel, rollers, fwd, fwd_lbl, rule, problem, solve)))


# =============================================================== R05_Overview
class R05_Overview(SafeScene):
    def construct(self):
        self.play(Write(title("โครงสร้างรวมและสเปกของหุ่นยนต์")))

        img = image_stage(IMG("fig4_overview.png"), max_w=5.6, max_h=5.0,
                           center=[-3.4, 0.0, 0])
        self.play(FadeIn(img))

        specs = [
            ("ขนาด (ยืน)", "430×475×900 mm"),
            ("ขนาด (หมอบ)", "920×880×350 mm"),
            ("น้ำหนัก", "54 kg"),
            ("ความเร็ว", "0 – 7.36 m/s"),
            ("DOF", "12 (ขาละ 2 + ล้อละ 1)"),
            ("ขา yaw ROM", "-45° ถึง 45°"),
            ("ขา pitch ROM", "10° – 120°"),
            ("ทอร์กสูงสุด/ต่อเนื่อง", "132.1 / 48.8 N·m"),
            ("อัตราทดเกียร์", "65 : 1"),
            ("ชดเชยแรงโน้มถ่วง", "8 – 30 kgf/ขา"),
            ("Payload", "80 kgf"),
        ]
        labels = VGroup(*[Text(k, font_size=18, color=GRAYTXT) for k, _ in specs])
        values = VGroup(*[Text(v, font_size=18, color=WHITE) for _, v in specs])
        labels.arrange(DOWN, aligned_edge=LEFT, buff=0.17)
        values.arrange(DOWN, aligned_edge=LEFT, buff=0.17)
        labels.move_to([1.5, 0.0, 0], aligned_edge=LEFT)
        for lb, vl in zip(labels, values):
            vl.next_to(lb, RIGHT, buff=0.35).align_to(lb, UP)
        rows = VGroup(*[VGroup(lb, vl) for lb, vl in zip(labels, values)])

        for r in rows:
            self.play(FadeIn(r, shift=RIGHT * 0.15), run_time=0.35)
        self.wait(2)
        self.play(FadeOut(Group(img, rows)))


# ============================================================ R06_LegMechanism
class R06_LegMechanism(SafeThreeDScene):
    def construct(self):
        self.set_camera_orientation(phi=62 * DEGREES, theta=-55 * DEGREES, distance=9)

        ttl = self.hud(Text("กลไกขา: Parallel-link 2-DOF ตรึงทิศทางล้อ mecanum",
                             font_size=26, color=WHITE).move_to([0, TITLE_Y, 0]), show=True)

        body = np.array([0, 0, 1.6])
        yaw_act = np.array([-0.4, 0.0, 1.6])
        pitch_act = np.array([-0.9, 0.0, 1.3])
        wheel_c = np.array([-2.6, 0.0, -0.4])

        body_dot = Dot3D(body, color=LEGC, radius=0.09)
        main_link = line3(pitch_act, wheel_c, LEGC, thickness=0.05)
        sup1 = line3(pitch_act + np.array([0, 0.28, 0]), wheel_c + np.array([0, 0.28, -0.15]),
                     GRAYTXT, thickness=0.03)
        sup2 = line3(pitch_act + np.array([0, -0.28, 0]), wheel_c + np.array([0, -0.28, -0.15]),
                     GRAYTXT, thickness=0.03)
        yaw_dot = Dot3D(yaw_act, color=WARN, radius=0.1)
        pitch_dot = Dot3D(pitch_act, color=WARN, radius=0.1)
        wheel = Cylinder(radius=0.55, height=0.35, direction=[0, 1, 0],
                          fill_color=WHEELC, fill_opacity=1, stroke_width=1).move_to(wheel_c)

        self.play(FadeIn(body_dot))
        self.play(Create(main_link), Create(sup1), Create(sup2))
        self.play(FadeIn(yaw_dot), FadeIn(pitch_dot))
        self.play(FadeIn(wheel))
        self.wait(0.5)

        lbl1 = self.hud(Text("Yaw actuator (น้ำเงิน) + Pitch actuator: ข้อต่อขับเคลื่อน",
                              font_size=20, color=WARN).move_to([0, CAP_Y, 0]), show=True)
        self.wait(1)
        self.play(FadeOut(lbl1))
        lbl2 = self.hud(Text("Main link + Support link คู่ขนาน = Parallel-link (สามเหลี่ยมเสมือน)",
                              font_size=20, color=GRAYTXT).move_to([0, CAP_Y, 0]), show=True)
        self.wait(1)

        # sweep pitch: rotate the leg group about pitch_act while keeping wheel orientation fixed
        leg_group = VGroup(main_link, sup1, sup2, wheel)
        self.play(Rotate(leg_group, angle=25 * DEGREES, axis=[0, 1, 0],
                          about_point=pitch_act), run_time=1.6)
        self.play(Rotate(leg_group, angle=-40 * DEGREES, axis=[0, 1, 0],
                          about_point=pitch_act), run_time=2.0)
        self.play(Rotate(leg_group, angle=15 * DEGREES, axis=[0, 1, 0],
                          about_point=pitch_act), run_time=1.0)
        self.wait(0.5)
        self.play(FadeOut(lbl2))
        lbl3 = self.hud(Text("ROM: yaw -45°~45°, pitch 10°~120° — ล้อยังชี้ทิศเดิมเสมอ",
                              font_size=20, color=POLYC).move_to([0, CAP_Y, 0]), show=True)
        self.wait(1.5)

        self.play(FadeOut(VGroup(body_dot, main_link, sup1, sup2, yaw_dot, pitch_dot, wheel, lbl3, ttl)))


# ========================================================== R07_PlanetaryGear
class R07_PlanetaryGear(SafeScene):
    def construct(self):
        self.play(Write(title("เกียร์ Compound Planetary แบบ Backdrivable")))

        img = image_stage(IMG("fig6b_gear_section.png"), max_w=3.2, max_h=4.6,
                           center=[-4.6, 0.1, 0])
        self.play(FadeIn(img))
        img_lbl = Text("หน้าตัดจริง (Fig.6b)", font_size=16, color=GRAYTXT).next_to(img, DOWN, buff=0.15)
        self.play(FadeIn(img_lbl))

        # schematic: sun S center, ring R1/R2 outer, planets P1/P2/P3
        c = np.array([0.9, -0.5, 0])
        ring2 = Circle(radius=1.55, color=RING_G, stroke_width=4).move_to(c)
        ring1 = Circle(radius=1.3, color=GEAR_OUT, stroke_width=3).move_to(c)
        sun = Circle(radius=0.3, color=GEAR_IN, fill_color=GEAR_IN, fill_opacity=1).move_to(c)
        s_lbl = Text("S", font_size=18, color=BLACK).move_to(c)

        r2_lbl = Text("R2 (fixed ring)", font_size=16, color=RING_G).next_to(ring2, UP, buff=0.3)
        r1_lbl = Text("R1 (output ring)", font_size=16, color=GEAR_OUT).next_to(ring1, DOWN, buff=0.3)

        planets = VGroup()
        p_labels = VGroup()
        for k, (name, col, rad, rr) in enumerate([
            ("P1", GEAR_MID, 0.62, 0.17), ("P2", ARM_G, 0.92, 0.17), ("P3", "#FFD54F", 1.18, 0.17)
        ]):
            ang = -30 * DEGREES
            p = Circle(radius=rr, color=col, fill_color=col, fill_opacity=1).move_to(
                c + rad * np.array([np.cos(ang), np.sin(ang), 0]))
            lab = Text(name, font_size=14, color=BLACK).move_to(p.get_center())
            planets.add(p)
            p_labels.add(lab)

        self.play(Create(ring2), Create(ring1))
        self.play(FadeIn(r2_lbl), FadeIn(r1_lbl))
        self.play(FadeIn(sun), FadeIn(s_lbl))
        self.play(FadeIn(planets), FadeIn(p_labels))
        self.wait(1)

        eq_title = Text("อัตราทดรวม:", font_size=20, color=WHITE).move_to([4.6, 2.6, 0])
        eq1 = MathTex(
            r"N=\dfrac{\dfrac{n_{p1}}{n_s}+\dfrac{n_{p3}}{n_{r2}}}"
            r"{\dfrac{n_{p3}}{n_{r2}}-\dfrac{n_{p2}}{n_{r1}}}",
            font_size=30, color=WHITE
        ).move_to([4.6, 1.4, 0])
        fit_width(eq1, 5.0)
        self.play(FadeIn(eq_title))
        self.play(Write(eq1))
        self.wait(1.5)

        sub = MathTex(
            r"n_s{=}18,\ n_{r1}{=}90,\ n_{r2}{=}96,",
            font_size=22, color=GRAYTXT
        ).move_to([4.6, 0.2, 0])
        sub2 = MathTex(
            r"n_{p1}{=}48,\ n_{p2}{=}24,\ n_{p3}{=}30",
            font_size=22, color=GRAYTXT
        ).next_to(sub, DOWN, buff=0.2)
        fit_width(sub, 5.2)
        fit_width(sub2, 5.2)
        self.play(FadeIn(sub), FadeIn(sub2))
        self.wait(1)

        result = MathTex(r"N \approx 65:1", font_size=34, color=OK).move_to([4.6, -1.2, 0])
        self.play(FadeIn(result, scale=1.2))
        self.wait(1)

        note = Text("แรงเสียดทาน Coulomb เพียง 0.10 N·m (Harmonic Drive ทั่วไป ~4.8 N·m)\nจึง backdrivable สูง ดูดซับแรงกระแทกจากพื้นได้",
                     font_size=19, color=GRAYTXT, line_spacing=1.3).move_to([0, CAP_Y, 0])
        fit_width(note, 11.5)
        self.play(FadeIn(note))
        self.wait(2)

        self.play(FadeOut(Group(img, img_lbl, ring2, ring1, sun, s_lbl, r2_lbl, r1_lbl,
                                  planets, p_labels, eq_title, eq1, sub, sub2, result, note)))


# ====================================================== R08_PassiveWheelsGRF
class R08_PassiveWheelsGRF(SafeScene):
    def construct(self):
        self.play(Write(title("ล้อพาสซีฟช่วยไต่ขั้นบันได + กลไกชดเชย GRF")))

        img1 = image_stage(IMG("fig7_passive_wheels.png"), max_w=10.5, max_h=4.8, center=[0, 0.05, 0])
        self.play(FadeIn(img1))
        caps1 = [
            "(a) ล้อยึด 2 + ล้อ caster 2 ที่ใต้ลำตัว",
            "(b) ยกขาหน้า 2 ข้าง ใช้ล้อพาสซีฟรับน้ำหนัก",
            "(c) ไต่ขั้นบันไดทีละขา คง COM ไว้กับที่",
            "(d) ไต่บันไดแบบเร็ว ด้วยการขยับ COM ลำตัว",
        ]
        cap = Text(caps1[0], font_size=20, color=WHEELC).move_to([0, CAP_Y, 0])
        self.play(FadeIn(cap))
        self.wait(0.8)
        for c in caps1[1:]:
            newcap = Text(c, font_size=20, color=WHEELC).move_to([0, CAP_Y, 0])
            fit_width(newcap, 11.0)
            self.play(FadeOut(cap))
            self.play(FadeIn(newcap))
            cap = newcap
            self.wait(0.8)
        note = Text("เมื่อยกล้อ mecanum 2 ล้อ หุ่นยนต์กลายเป็นโมเดล differential-drive ชั่วคราว",
                     font_size=19, color=GRAYTXT).move_to([0, -3.0, 0])
        fit_width(note, 11)
        self.play(FadeIn(note))
        self.wait(1.5)
        self.play(FadeOut(Group(img1, cap, note)))

        img2 = image_stage(IMG("fig8_grf_compensation.png"), max_w=5.4, max_h=5.0,
                            center=[-3.9, 0.0, 0])
        self.play(FadeIn(img2))

        e1 = MathTex(r"l_s = d_3 + d_1\cos\theta - d_4\sin\theta - \sqrt{d_2^2-(d_4\cos\theta+d_1\sin\theta)^2}",
                      font_size=20, color=WHITE)
        e2 = MathTex(r"F_s = k\,(l_0 - l_s)", font_size=22, color=WHITE)
        e3 = MathTex(r"\alpha = \cos^{-1}\!\left(\dfrac{d_1^2-d_2^2+d_4^2-(d_3-l_s)^2}{-2d_2(d_3-l_s)}\right)",
                      font_size=20, color=WHITE)
        e4 = MathTex(r"\tau_C = F_s\cos\alpha\,(d_3-l_s)\sin\alpha", font_size=24, color=SPRINGC)
        eqs = VGroup(e1, e2, e3, e4).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        for e in eqs:
            fit_width(e, 5.6)
        eqs.move_to([3.9, 1.4, 0])

        for e in eqs:
            self.play(Write(e), run_time=1.1)
            self.wait(0.3)
        self.wait(1)

        graph_note = Text(
            "กราฟ torque-vs-angle: ช่วง 10–60° (ขับปกติ) actuator torque < joint torque มาก\n"
            "ใกล้ 90° (ยกขา) offset d4 ทำให้ compensation torque → 0 ไม่ต้านการยก",
            font_size=18, color=GRAYTXT, line_spacing=1.3
        ).move_to([3.9, -2.0, 0])
        fit_width(graph_note, 5.7)
        self.play(FadeIn(graph_note))
        self.wait(2.5)

        self.play(FadeOut(Group(img2, eqs, graph_note)))


# =========================================================== R09_Kinematics
class R09_Kinematics(SafeScene):
    def construct(self):
        ttl1 = title("Kinematics: จากความเร็วขา สู่ความเร็วล้อ")
        self.play(Write(ttl1))

        # top-view 4-wheel frame diagram
        R = Dot(ORIGIN, color=WHITE)
        Rlbl = Text("Σ_R", font_size=18, color=WHITE).next_to(R, DOWN, buff=0.12)
        wheel_pos = {
            "Σw1": [-1.9, 1.3, 0], "Σw2": [1.9, 1.3, 0],
            "Σw3": [-1.9, -1.3, 0], "Σw4": [1.9, -1.3, 0],
        }
        frame = VGroup(R, Rlbl)
        body_box = Rectangle(width=3.6, height=2.4, color=GRAYTXT, stroke_width=2).move_to(ORIGIN)
        frame.add(body_box)
        wheels = VGroup()
        for name, pos in wheel_pos.items():
            w = Rectangle(width=0.7, height=0.35, color=WHEELC, fill_color=WHEELC,
                          fill_opacity=1).move_to(pos)
            lab = Text(name, font_size=16, color=WHEELC).next_to(w, UP if pos[1] > 0 else DOWN, buff=0.1)
            wheels.add(VGroup(w, lab))
        vx = Arrow(ORIGIN, [1.0, 0, 0], color=OK, buff=0, stroke_width=5)
        vx_lbl = Text("v_x", font_size=16, color=OK).next_to(vx, UP, buff=0.08)
        vy = Arrow(ORIGIN, [0, 0.9, 0], color=COPC, buff=0, stroke_width=5)
        vy_lbl = Text("v_y", font_size=16, color=COPC).next_to(vy, RIGHT, buff=0.08)
        wz = Arc(radius=0.5, angle=250 * DEGREES, color=GRFC, stroke_width=4).move_to(ORIGIN)
        wz_lbl = Text("ω_z", font_size=16, color=GRFC).next_to(wz, LEFT, buff=0.08)

        diagram = VGroup(frame, wheels, vx, vx_lbl, vy, vy_lbl, wz, wz_lbl).move_to([-3.6, 0.7, 0])
        self.play(Create(body_box), FadeIn(R), FadeIn(Rlbl))
        self.play(FadeIn(wheels))
        self.play(GrowArrow(vx), FadeIn(vx_lbl), GrowArrow(vy), FadeIn(vy_lbl))
        self.play(Create(wz), FadeIn(wz_lbl))
        self.wait(1)

        eq_roller = MathTex(r"v_{iw} = v_{ix} - n_i\,v_{iy}", font_size=26, color=WHITE).move_to([3.4, 2.4, 0])
        self.play(Write(eq_roller))
        note1 = Text("ความเร็วแนวหมุนของล้อ = ผลรวมความเร็วตัวหุ่น + การขยับปลายขา",
                      font_size=17, color=GRAYTXT).next_to(eq_roller, DOWN, buff=0.25)
        fit_width(note1, 5.6)
        self.play(FadeIn(note1))
        self.wait(1)

        eq_jac = MathTex(r"V_w = J\,V_o", font_size=32, color=OK).move_to([3.4, 0.4, 0])
        self.play(Write(eq_jac))
        note2 = Text("J คือ Jacobian 4×11 เชื่อมความเร็ว 4 ล้อกับ\n(v_x, v_y, ω_z) และมุมข้อต่อขาทั้ง 8 ค่า",
                      font_size=17, color=GRAYTXT, line_spacing=1.3).next_to(eq_jac, DOWN, buff=0.3)
        fit_width(note2, 5.6)
        self.play(FadeIn(note2))
        self.wait(1.5)

        note3 = Text("เมื่อยกขาหน้า/หลัง 2 ข้าง → ใช้ Jacobian ย่อยแบบ\ndifferential-drive (v_y = 0)",
                      font_size=17, color=WARN, line_spacing=1.3).move_to([3.4, -2.2, 0])
        fit_width(note3, 5.6)
        self.play(FadeIn(note3))
        self.wait(1.5)

        self.play(FadeOut(VGroup(diagram, eq_roller, note1, eq_jac, note2, note3, ttl1)))

        ttl2 = Text("สถาปัตยกรรมควบคุม", font_size=28, color=WHITE).move_to([0, TITLE_Y, 0])
        self.play(Write(ttl2))

        boxes_txt = ["Motion Planning\n(วางแผน support polygon\n+ ท่าทางลำตัว)",
                     "Motion Tracking\n(200 Hz)\nคำนวณตำแหน่งขา\n+ ความเร็วล้อ",
                     "Actuator Control\n(10 kHz)\nควบคุมข้อต่อ/ล้อ\nระดับต่ำ"]
        boxes = VGroup()
        for i, t in enumerate(boxes_txt):
            b = RoundedRectangle(width=3.6, height=2.4, corner_radius=0.15,
                                  color=LEGC, stroke_width=3).move_to([(i - 1) * 4.3, 0, 0])
            txt = Text(t, font_size=17, color=WHITE, line_spacing=1.2).move_to(b.get_center())
            fit_width(txt, 3.3)
            boxes.add(VGroup(b, txt))
        arrows = VGroup(*[
            Arrow(boxes[i][0].get_right(), boxes[i + 1][0].get_left(), color=GRAYTXT,
                  buff=0.1, stroke_width=4) for i in range(2)
        ])
        for b in boxes:
            self.play(FadeIn(b), run_time=0.6)
        for a in arrows:
            self.play(GrowArrow(a), run_time=0.5)
        self.wait(2)
        self.play(FadeOut(VGroup(ttl2, boxes, arrows)))


# =========================================================== R10_Experiments
class R10_Experiments(SafeScene):
    def construct(self):
        ttl1 = title("ผลการทดลอง: Agile Motion Test")
        self.play(Write(ttl1))

        img = image_stage(IMG("fig11a_path_test.png"), max_w=10.8, max_h=3.6, center=[0, 1.4, 0])
        self.play(FadeIn(img))
        stat = Text("เส้นทางรูปตัว C: ระยะ 3m×3m รวม 11s | ความเร็วสูงสุด 1.5 m/s | ความเร่ง 1.5 m/s²",
                     font_size=19, color=GRAYTXT).move_to([0, -0.6, 0])
        fit_width(stat, 11.5)
        self.play(FadeIn(stat))
        self.wait(1.5)

        finding = Text(
            "ผลลัพธ์: COP อยู่ใน support polygon แบบปรับได้เสมอ\n"
            "แต่ถ้าใช้ polygon เล็กคงที่ COP จะทะลุขอบหลายครั้ง — หุ่นยนต์จะล้ม!",
            font_size=21, color=WARN, line_spacing=1.3
        ).move_to([0, -2.0, 0])
        fit_width(finding, 11.5)
        self.play(FadeIn(finding))
        self.wait(2)
        self.play(FadeOut(Group(img, stat, finding, ttl1)))

        self.play(Write(title("ผลการทดลองในสภาพแวดล้อมมนุษย์")))
        img2 = image_stage(IMG("fig12_human_env_tests.png"), max_w=6.0, max_h=5.2, center=[0, -0.1, 0])
        self.play(FadeIn(img2))
        caps = [
            "(a) ไต่ขั้นบันได สูง 170 mm ใช้เวลา 9.4 s",
            "(b) ขึ้นลิฟต์ขนาด 1380×1340 mm พร้อมคน 3 คน",
            "(c) ผ่านช่องแคบ 1000 mm ระหว่างคน 2 คน ด้วยความเร็ว 0.9 m/s\n(กว้าง 430 mm เดินหน้า / 483 mm ด้านข้าง)",
        ]
        cap = Text(caps[0], font_size=19, color=WHEELC).move_to([0, CAP_Y, 0])
        fit_width(cap, 11)
        self.play(FadeIn(cap))
        self.wait(1.2)
        for c in caps[1:]:
            newcap = Text(c, font_size=19, color=WHEELC, line_spacing=1.2).move_to([0, CAP_Y, 0])
            fit_width(newcap, 11)
            self.play(FadeOut(cap))
            self.play(FadeIn(newcap))
            cap = newcap
            self.wait(1.4)
        self.wait(1)
        self.play(FadeOut(Group(img2, cap)))


# ============================================================ R11_Conclusion
class R11_Conclusion(SafeScene):
    def construct(self):
        self.play(Write(title("สรุปและก้าวต่อไป")))

        items = bullets([
            "ขา mecanum wheel-leg เปลี่ยน support polygon ได้อิสระใน 3 มิติ",
            "เกียร์ compound planetary 65:1 แบบ backdrivable",
            "กลไกชดเชย GRF ลดภาระ actuator ทั้งช่วงขับและช่วงยกขา",
        ], size=25).move_to([0, 1.6, 0])
        for it in items:
            self.play(FadeIn(it, shift=RIGHT * 0.2), run_time=0.6)
        self.wait(1)

        future_title = Text("งานต่อไป:", font_size=22, color=GRAYTXT).move_to([0, -0.6, 0])
        self.play(FadeIn(future_title))
        future = bullets([
            "แบตเตอรี่ความจุสูงสำหรับระบบไร้สาย",
            "แขนกลน้ำหนักเบา ปลอดภัยต่อมนุษย์",
            "เอวหลาย DOF + ควบคุมสมดุลด้วย IMU/GRF",
            "นำทางอัตโนมัติด้วยข้อมูลเซนเซอร์ 3 มิติ",
        ], size=19, color=GRAYTXT, buff=0.18).move_to([0, -2.0, 0])
        self.play(FadeIn(future))
        self.wait(2)
        self.play(FadeOut(VGroup(items, future_title, future)))

        cite = Text(
            "S.-H. Yun, J. Park, J. Seo, Y.-J. Kim,\n"
            "\"Development of an Agile Omnidirectional Mobile Robot With GRF\n"
            "Compensated Wheel-leg Mechanisms for Human Environments,\"\n"
            "IEEE Robotics and Automation Letters, vol.6, no.4, pp.8301-8308, 2021.\n"
            "DOI: 10.1109/LRA.2021.3098954",
            font_size=18, color=GRAYTXT, line_spacing=1.3
        ).move_to([0, 0.6, 0])
        fit_width(cite, 11)
        self.play(FadeIn(cite))
        self.wait(2)

        end = Text("จบ", font_size=48, color=WHITE).move_to([0, -2.6, 0])
        self.play(Write(end))
        self.wait(1.5)
        self.play(FadeOut(VGroup(cite, end)))
