"""
scratch/manim_cloud_showcase.py
Rendered directly on GitHub Actions Cloud (Docker + Ubuntu)
"""
from manim import *
import numpy as np

THAI_FONT = "Loma"
CURRENT = "#FFB300"
FIELD   = "#42A5F5"
FORCE   = "#66BB6A"
GEAR_IN = "#4FC3F7"
GEAR_OUT= "#FFB74D"
GRAYTXT = "#B0BEC5"
OK      = "#26C6DA"
WARN    = "#FF7043"

def gear_shape(radius, teeth, color, tooth_depth_frac=0.16, tooth_width_frac=0.55):
    n = max(int(teeth), 4)
    dep = radius * tooth_depth_frac
    r_out, r_in = radius + dep / 2, radius - dep / 2
    pts = []
    for i in range(n):
        a0, a1 = TAU * i / n, TAU * (i + 1) / n
        mid = (a0 + a1) / 2
        half = (a1 - a0) * tooth_width_frac / 2
        for r, a in ((r_in, a0), (r_in, mid - half), (r_out, mid - half),
                     (r_out, mid + half), (r_in, mid + half)):
            pts.append([r * np.cos(a), r * np.sin(a), 0])
    body = Polygon(*pts, color=color, fill_opacity=0.9, stroke_width=2, stroke_color=color)
    hub = Circle(radius=radius * 0.18, color=BLACK, fill_opacity=1, stroke_width=0)
    return VGroup(body, hub)

class CloudShowcase(Scene):
    def construct(self):
        # --- 1. Intro Card ---
        t_head = Text("การส่งกำลังและพลังงานแม่เหล็กไฟฟ้า", font=THAI_FONT, font_size=36, color=WHITE)
        t_sub = Text("Rendered on Cloud (GitHub Actions • Docker • Manim)", font_size=20, color=OK).next_to(t_head, DOWN, buff=0.3)
        self.play(FadeIn(t_head, shift=UP*0.3), FadeIn(t_sub, shift=UP*0.2))
        self.wait(1.2)
        self.play(FadeOut(t_head), FadeOut(t_sub))

        # --- 2. Gear Transmission ---
        t1 = Text("1. กลไกส่งกำลังชุดเฟือง (Gear Velocity Ratio)", font=THAI_FONT, font_size=28, color=WHITE).to_edge(UP, buff=0.6)
        self.play(FadeIn(t1))

        r1, n1 = 1.1, 14
        r2, n2 = 0.55, 7
        c1 = np.array([-3.0, -0.2, 0])
        c2 = c1 + RIGHT * (r1 + r2)

        g1 = gear_shape(r1, n1, GEAR_IN).move_to(c1)
        g2 = gear_shape(r2, n2, GEAR_OUT).move_to(c2)

        lbl1 = Text("เฟืองขับ (Input: 14 ฟัน)", font=THAI_FONT, font_size=18, color=GEAR_IN).next_to(g1, DOWN, buff=0.35)
        lbl2 = Text("เฟืองตาม (Output: 7 ฟัน)", font=THAI_FONT, font_size=18, color=GEAR_OUT).next_to(g2, DOWN, buff=0.35)

        self.play(FadeIn(g1), FadeIn(g2), FadeIn(lbl1), FadeIn(lbl2))

        # Rotate gears
        g1.add_updater(lambda m, dt: m.rotate(1.2 * dt))
        g2.add_updater(lambda m, dt: m.rotate(-2.4 * dt))

        # Right Panel
        f_box = RoundedRectangle(corner_radius=0.15, width=4.6, height=3.0, color=GRAYTXT, fill_opacity=0.15).move_to([3.8, -0.2, 0])
        f_title = Text("อัตราทดความเร็วเชิงมุม", font=THAI_FONT, font_size=20, color=OK).move_to([3.8, 0.9, 0])
        f_eq = MathTex(r"i = \frac{\omega_1}{\omega_2} = -\frac{N_2}{N_1} = -\frac{1}{2}", font_size=28, color=WHITE).move_to([3.8, 0.2, 0])
        f_d1 = Text("• เฟืองตามหมุนเร็วกว่า 2 เท่า", font=THAI_FONT, font_size=16, color=WHITE).move_to([3.8, -0.4, 0])
        f_d2 = Text("• เครื่องหมายลบ = หมุนทิศตรงข้าม", font=THAI_FONT, font_size=16, color=WARN).move_to([3.8, -0.8, 0])

        self.play(Create(f_box), FadeIn(f_title), FadeIn(f_eq), FadeIn(f_d1), FadeIn(f_d2))
        self.wait(2.5)

        g1.clear_updaters()
        g2.clear_updaters()
        self.play(FadeOut(VGroup(t1, g1, g2, lbl1, lbl2, f_box, f_title, f_eq, f_d1, f_d2)))

        # --- 3. Lorentz Force ---
        t2 = Text("2. แรงแม่เหล็กไฟฟ้าลอเรนซ์ (Lorentz Force)", font=THAI_FONT, font_size=28, color=WHITE).to_edge(UP, buff=0.6)
        self.play(FadeIn(t2))

        # B Field
        b_arrows = VGroup(*[
            Arrow([-4.8, y, 0], [-1.0, y, 0], color=FIELD, stroke_width=4, buff=0, max_tip_length_to_length_ratio=0.2).set_opacity(0.65)
            for y in np.linspace(-1.5, 1.2, 5)
        ])
        lbl_b = Text("สนามแม่เหล็ก B", font=THAI_FONT, font_size=18, color=FIELD).move_to([-2.9, 1.6, 0])

        wire = Line([-2.9, -1.8, 0], [-2.9, 1.2, 0], color=CURRENT, stroke_width=8)
        lbl_i = Text("กระแส I", font=THAI_FONT, font_size=18, color=CURRENT).next_to(wire, LEFT, buff=0.2)
        arr_i = Arrow([-2.9, -1.0, 0], [-2.9, 0.4, 0], color=CURRENT, stroke_width=5)

        self.play(Create(b_arrows), FadeIn(lbl_b), Create(wire), FadeIn(lbl_i), GrowArrow(arr_i))

        force_arr = Arrow([-2.9, -0.3, 0], [-1.2, -0.3, 0], color=FORCE, stroke_width=8)
        lbl_f = Text("แรงกล F", font=THAI_FONT, font_size=20, color=FORCE).next_to(force_arr, UP, buff=0.15)

        f_box2 = RoundedRectangle(corner_radius=0.15, width=4.6, height=3.0, color=GRAYTXT, fill_opacity=0.15).move_to([3.8, -0.2, 0])
        f_title2 = Text("สมการแรงแม่เหล็ก", font=THAI_FONT, font_size=20, color=FORCE).move_to([3.8, 0.9, 0])
        f_eq2 = MathTex(r"\vec{F} = I (\vec{L} \times \vec{B})", font_size=32, color=WHITE).move_to([3.8, 0.2, 0])
        f_rhr = Text("กฎมือขวา: ชี้นิ้ว I → งอหา B → โป้งคือ F", font=THAI_FONT, font_size=15, color=OK).move_to([3.8, -0.4, 0])
        f_mot = Text("หลักการขับเคลื่อนมอเตอร์ไฟฟ้า DC", font=THAI_FONT, font_size=15, color=GRAYTXT).move_to([3.8, -0.8, 0])

        self.play(GrowArrow(force_arr), FadeIn(lbl_f), Create(f_box2), FadeIn(f_title2), FadeIn(f_eq2), FadeIn(f_rhr), FadeIn(f_mot))
        self.wait(2.5)

        self.play(FadeOut(VGroup(t2, b_arrows, lbl_b, wire, lbl_i, arr_i, force_arr, lbl_f, f_box2, f_title2, f_eq2, f_rhr, f_mot)))

        # --- 4. Conclusion Card ---
        card = RoundedRectangle(corner_radius=0.2, width=8.5, height=4.0, color=OK, fill_opacity=0.15, stroke_width=3)
        c_title = Text("Render บน Cloud สำเร็จสมบูรณ์ ☁️🎬", font=THAI_FONT, font_size=26, color=WHITE).move_to([0, 1.1, 0])
        c_p1 = Text("✓ ประมวลผลผ่าน GitHub Actions (Docker Manim)", font=THAI_FONT, font_size=19, color=OK).move_to([0, 0.3, 0])
        c_p2 = Text("✓ ฟอนต์ภาษาไทยและสูตรคณิตศาสตร์สวยงาม คมชัด 100%", font=THAI_FONT, font_size=19, color=WHITE).move_to([0, -0.3, 0])
        c_p3 = Text("✓ ไม่กินทรัพยากรเครื่องโลคอล ไวและเสถียร", font=THAI_FONT, font_size=19, color=GEAR_IN).move_to([0, -0.9, 0])

        self.play(Create(card), FadeIn(c_title), FadeIn(c_p1), FadeIn(c_p2), FadeIn(c_p3))
        self.wait(2.5)
