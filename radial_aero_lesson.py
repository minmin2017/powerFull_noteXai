# -*- coding: utf-8 -*-
"""
radial_aero_lesson.py — One continuous educational Manim 3D lesson:
Aerodynamics + 7-Cylinder Single-Row Aircraft Radial Piston Engine.

=============================================================================
SHOT LOG / PROOF CRITERIA MAPPING:
  S1: Four forces in cruise; explicit orthogonality: Engine -> Thrust, Wing -> Lift.
  S2: Relative wind (V_inf) and Angle of attack (alpha) with chord line reference.
  S3: Flow turning and downwash wake; Newton/momentum view (L ~ m_dot * Delta_V_y).
  S4: Streamline curvature pressure field; suction peak; debunk equal-transit-time.
  S5: Layered Lift Equation (L = 1/2 rho V^2 S C_L) with V -> 2V yields 4x L demo.
  S6: Four-stroke cylinder cutaway (Intake, Compression, Power, Exhaust) -> torque.
  S7: 7-Cylinder radial layout: Master rod (#1 top) + 6 articulating rods on 1 throw.
  S8: Knuckle-pin elliptical trace (schematic / not-to-scale) vs crank circular orbit.
  S9: 720-degree firing order 1-3-5-7-2-4-6 (FAA rear-view convention, odd per row).
  S10: Integrated throttle-to-lift causal chain closing the loop from spark to flight.
=============================================================================
"""

import sys
import numpy as np
from manim import *

from mlib import (
    SafeThreeDScene, arrow3, line3, title, caption, fit_width, live_row,
    CURRENT, FIELD, FORCE, METAL, GRAYTXT, WARN, OK, WHITE, TITLE_Y, CAP_Y,
    THAI_FONT
)

# Semantic Colors
C_LIFT = FORCE           # #66BB6A Green
C_THRUST = FIELD         # #42A5F5 Blue
C_MASTER = CURRENT       # #FFB300 Gold / Master rod
C_LINK = "#81D4FA"       # Light cyan-blue / Articulating rods
C_FIRE = WARN            # #FF7043 Combustion flash
C_VERIFIED = OK          # #26C6DA Verified conclusion


class AeroRadialLesson(SafeThreeDScene):
    """Continuous teaching film connecting aircraft aerodynamics to radial engine mechanics."""

    def construct(self):
        # Default starting camera: orthogonal 2D view for aerodynamics foundation
        self.set_camera_orientation(phi=0, theta=-90 * DEGREES)

        # S1: Four forces and engine vs wing roles
        self.beat_s1_four_forces()

        # S2: Relative wind and angle of attack
        self.beat_s2_relative_wind_and_aoa()

        # S3: Flow turning and downwash
        self.beat_s3_flow_turning_and_downwash()

        # S4: Pressure map and equal-transit-time debunk
        self.beat_s4_pressure_and_myth_debunk()

        # S5: Layered lift equation dashboard
        self.beat_s5_lift_equation_dashboard()

        # S6: Four-stroke cylinder cutaway
        self.beat_s6_four_stroke_engine_core()

        # S7: Master rod and six articulating rods
        self.beat_s7_radial_master_and_links()

        # S8: Elliptical knuckle-pin path (schematic)
        self.beat_s8_elliptical_knuckle_path()

        # S9: 720-degree firing order (1-3-5-7-2-4-6)
        self.beat_s9_firing_order_720()

        # S10: Throttle-to-lift integration
        self.beat_s10_throttle_to_lift_integration()

    # =========================================================================
    # BEAT IMPLEMENTATIONS
    # =========================================================================

    def beat_s1_four_forces(self):
        """S1: Four forces balance and strict engine=thrust / wing=lift orthogonality."""
        t = self.hud(title("S1: แรงทั้งสี่บนเครื่องบิน — เครื่องยนต์ไม่ได้ยกเครื่องบินโดยตรง"))
        c = self.hud(caption("เครื่องยนต์สร้าง Thrust ขับเคลื่อนไปข้างหน้า | ปีกเปลี่ยนกระแสลมให้เป็น Lift ยกเครื่องบิน"))

        # Schematic airplane fuselage & wing (2.5D planar) shifted down for clear headroom
        body = Polygon(
            [-2.5, -0.2, 0], [-1.0, -0.25, 0], [1.5, -0.2, 0], [2.2, 0.0, 0],
            [2.0, 0.4, 0], [1.3, 0.25, 0], [-2.0, 0.2, 0], [-2.5, 0.6, 0],
            color=METAL, fill_opacity=0.6, stroke_width=2
        )
        wing_stub = Polygon([-0.4, -0.15, 0], [0.6, -0.15, 0], [0.3, 0.25, 0], [-0.3, 0.25, 0],
                            color=WHITE, fill_opacity=0.8, stroke_width=2)
        prop_disk = Ellipse(width=0.3, height=1.6, color=C_THRUST, stroke_width=3).move_to([2.2, 0.1, 0])
        plane = VGroup(body, wing_stub, prop_disk).move_to([-0.5, -0.35, 0])

        # Orthogonal Force Vectors with ample margins
        f_thrust = arrow3([1.7, -0.25, 0], [3.5, -0.25, 0], color=C_THRUST, thickness=0.035)
        f_drag = arrow3([-3.0, -0.25, 0], [-4.6, -0.25, 0], color=GRAYTXT, thickness=0.03)
        f_lift = arrow3([-0.4, -0.1, 0], [-0.4, 1.55, 0], color=C_LIFT, thickness=0.04)
        f_weight = arrow3([-0.4, -0.6, 0], [-0.4, -2.35, 0], color=METAL, thickness=0.035)

        lbl_t = self.hud(Text("Thrust (แรงขับ)", font_size=20, color=C_THRUST).move_to([3.4, 0.15, 0]))
        lbl_d = self.hud(Text("Drag (แรงต้าน)", font_size=19, color=GRAYTXT).move_to([-4.0, 0.15, 0]))
        lbl_l = self.hud(Text("Lift (แรงยก)", font_size=20, color=C_LIFT).move_to([-0.4, 1.85, 0]))
        lbl_w = self.hud(Text("Weight (น้ำหนัก)", font_size=19, color=METAL).move_to([-0.4, -2.6, 0]))

        box_hud = self.hud(VGroup(
            Text("สมดุลการบินระดับ (Cruise):  Thrust ≈ Drag  |  Lift ≈ Weight", font_size=19, color=C_VERIFIED),
            Text("แกนแรงตั้งฉากกันชัดเจน: เครื่องยนต์ไม่ได้ยกตัวตรงๆ", font_size=17, color=WHITE)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12).to_corner(UL).shift(DOWN * 0.75 + RIGHT * 0.2))

        self.play(FadeIn(t), FadeIn(c))
        self.play(Create(plane), FadeIn(box_hud))
        self.play(Create(f_thrust), Create(f_drag), FadeIn(lbl_t), FadeIn(lbl_d))
        self.play(Create(f_lift), Create(f_weight), FadeIn(lbl_l), FadeIn(lbl_w))
        self.wait(2.0)

        # Transition cleanup
        self.play(
            FadeOut(plane), FadeOut(f_thrust), FadeOut(f_drag), FadeOut(f_lift), FadeOut(f_weight),
            FadeOut(lbl_t), FadeOut(lbl_d), FadeOut(lbl_l), FadeOut(lbl_w), FadeOut(box_hud),
            FadeOut(t), FadeOut(c)
        )

    def beat_s2_relative_wind_and_aoa(self):
        """S2: Relative wind (V_inf) and angle of attack (alpha)."""
        t = self.hud(title("S2: ลมสัมพัทธ์ (Relative Wind) และมุมปะทะ (Angle of Attack)"))
        c = self.hud(caption("เครื่องยนต์ผลักให้เกิดความเร็วลมสัมพัทธ์ (V_inf) ไหลสวนปีกที่ทำมุมปะทะ (alpha)"))

        # Airfoil cross section
        foil_pts = [
            [-2.2, 0.0, 0], [-1.5, 0.55, 0], [0.0, 0.65, 0],
            [1.5, 0.35, 0], [2.2, 0.0, 0], [1.2, -0.15, 0],
            [-0.5, -0.20, 0], [-1.8, -0.15, 0]
        ]
        foil = Polygon(*foil_pts, color=WHITE, fill_opacity=0.85, stroke_width=2.5).move_to([-0.5, -0.2, 0])
        chord = DashedLine([-2.7, -0.2, 0], [1.7, -0.2, 0], color=GRAYTXT, stroke_width=2)

        wind_stream = VGroup(*[
            arrow3([-5.0, y, 0], [-2.8, y, 0], color=C_THRUST, thickness=0.025)
            for y in np.linspace(-1.4, 1.0, 5)
        ])
        lbl_v = self.hud(Text("V_inf (ลมสัมพัทธ์จากการเคลื่อนที่ไปข้างหน้า)", font_size=20, color=C_THRUST).move_to([-3.6, 1.5, 0]))

        aoa_arc = Arc(radius=1.2, start_angle=0, angle=12 * DEGREES, arc_center=[-2.7, -0.2, 0], color=WARN)
        lbl_aoa = self.hud(Text("alpha = มุมระหว่าง chord กับ V_inf", font_size=19, color=WARN).next_to(aoa_arc, UP, buff=0.45).shift(RIGHT * 0.3))

        self.play(FadeIn(t), FadeIn(c))
        self.play(Create(foil), Create(chord))
        self.play(Create(wind_stream), FadeIn(lbl_v))
        # Rotate airfoil slightly to show angle of attack
        self.play(foil.animate.rotate(8 * DEGREES, about_point=np.array([-0.5, -0.2, 0])),
                  chord.animate.rotate(8 * DEGREES, about_point=np.array([-0.5, -0.2, 0])),
                  Create(aoa_arc), FadeIn(lbl_aoa))
        self.wait(2.0)

        self.play(FadeOut(wind_stream), FadeOut(lbl_v), FadeOut(aoa_arc), FadeOut(lbl_aoa), FadeOut(chord),
                  FadeOut(foil), FadeOut(t), FadeOut(c))

    def beat_s3_flow_turning_and_downwash(self):
        """S3: Flow turning and downwash wake (Newton's 3rd law view)."""
        t = self.hud(title("S3: การเบนทิศทางลม (Flow Turning) และแรงปฏิกิริยา (Downwash)"))
        c = self.hud(caption("ทั้งผิวด้านบนและด้านล่างร่วมกันเบนกระแสลมลงด้านหลัง (Downwash) ผลักปีกให้ลอยขึ้น"))

        foil = Polygon(
            [-2.2, 0.0, 0], [-1.5, 0.55, 0], [0.0, 0.65, 0],
            [1.5, 0.35, 0], [2.2, 0.0, 0], [1.2, -0.15, 0],
            [-0.5, -0.20, 0], [-1.8, -0.15, 0],
            color=WHITE, fill_opacity=0.85, stroke_width=2.5
        ).move_to([-0.8, -0.2, 0]).rotate(8 * DEGREES)

        # Upper curved streamlines cleanly over upper surface
        upper_pts = [np.array([-4.5, 0.8, 0]), np.array([-1.5, 1.15, 0]), np.array([0.5, 0.9, 0]), np.array([3.0, -0.7, 0])]
        upper_stream = CubicBezier(*upper_pts, color=C_THRUST, stroke_width=3.5)
        upper_tip = arrow3([2.8, -0.6, 0], [3.2, -0.78, 0], color=C_THRUST, thickness=0.03)
        upper_group = VGroup(upper_stream, upper_tip)

        lower_stream = CurvedArrow(np.array([-4.5, -0.7, 0]), np.array([3.0, -1.7, 0]),
                                   angle=-0.25, color=C_THRUST, stroke_width=3.5)

        downwash_vec = arrow3([1.8, -0.7, 0], [2.6, -2.0, 0], color=WARN, thickness=0.035)
        lbl_downwash = self.hud(Text("Downwash (โมเมนตัมอากาศพุ่งลง)", font_size=19, color=WARN).move_to([3.0, -2.25, 0]))

        lift_reaction = arrow3([-0.6, 0.1, 0], [-0.6, 2.0, 0], color=C_LIFT, thickness=0.04)
        lbl_reaction = self.hud(Text("Lift = m_dot * Delta_V_y (Newton's 3rd Law)", font_size=20, color=C_LIFT).move_to([-0.6, 2.3, 0]))

        self.play(FadeIn(t), FadeIn(c))
        self.play(Create(foil))
        self.play(Create(upper_group), Create(lower_stream))
        self.play(Create(downwash_vec), FadeIn(lbl_downwash))
        self.play(Create(lift_reaction), FadeIn(lbl_reaction))
        self.wait(2.0)

        self.play(FadeOut(upper_group), FadeOut(lower_stream), FadeOut(downwash_vec), FadeOut(lbl_downwash),
                  FadeOut(lift_reaction), FadeOut(lbl_reaction), FadeOut(foil), FadeOut(t), FadeOut(c))

    def beat_s4_pressure_and_myth_debunk(self):
        """S4: Streamline curvature pressure map and explicit myth debunk."""
        t = self.hud(title("S4: ความดันบนผิวปีก และ หักล้างมายาคติ Equal Transit Time"))
        c = self.hud(caption("ความโค้งของกระแสลมทำให้เกิดแรงดูด (Suction) ด้านบน — อากาศบนถึงขอบหลังก่อนด้านล่าง"))

        # Physical airfoil shifted to the left half to separate from text box on right
        foil = Polygon(
            [-2.2, 0.0, 0], [-1.5, 0.55, 0], [0.0, 0.65, 0],
            [1.5, 0.35, 0], [2.2, 0.0, 0], [1.2, -0.15, 0],
            [-0.5, -0.20, 0], [-1.8, -0.15, 0],
            color=WHITE, fill_opacity=0.85, stroke_width=2.5
        ).move_to([-2.8, -0.4, 0]).rotate(7 * DEGREES)

        # Suction arrows on top of airfoil in left quadrant
        suction_arrows = VGroup(*[
            arrow3([-2.8 + x, 0.15 + 0.08 * np.cos(x), 0], [-2.8 + x, 1.1 + 0.08 * np.cos(x), 0],
                   color=C_THRUST, thickness=0.03)
            for x in np.linspace(-1.1, 1.1, 5)
        ])
        lbl_suction = self.hud(Text("แรงดูดด้านบน (Suction Peak)\ndp/dn = rho * v^2 / R", font_size=18, color=C_THRUST).move_to([-2.8, 1.65, 0]))

        # Myth Busting HUD Box placed cleanly on the right half
        box_debunk = self.hud(VGroup(
            Text("X มายาคติที่ผิด: อากาศบน-ล่าง\nต้องเดินทางถึงขอบหลังพร้อมกัน (Equal Transit Time)",
                 font_size=17, color=WARN),
            Text("✓ ความจริงตาม NASA: อากาศด้านบนถูกเร่งจนถึงขอบหลังก่อนด้านล่างอย่างมาก",
                 font_size=17, color=C_VERIFIED),
            Text("Bernoulli และ Newton คือสองวิธีมองแรงเดียวกัน ไม่ใช่ทฤษฎีคู่แข่ง",
                 font_size=17, color=WHITE)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([3.1, 0.35, 0]))

        self.play(FadeIn(t), FadeIn(c))
        self.play(Create(foil), Create(suction_arrows), FadeIn(lbl_suction))
        self.play(FadeIn(box_debunk))
        self.wait(2.2)

        self.play(FadeOut(foil), FadeOut(suction_arrows), FadeOut(lbl_suction), FadeOut(box_debunk),
                  FadeOut(t), FadeOut(c))

    def beat_s5_lift_equation_dashboard(self):
        """S5: Layered Lift Equation dashboard and V^2 proof."""
        t = self.hud(title("S5: สมการแรงยก (Lift Equation) และอิทธิพลของ V^2"))
        c = self.hud(caption("ความเร็วลม (V) มีผลกำลังสอง: เมื่อเครื่องยนต์เร่งความเร็ว 2 เท่า แรงยกจะเพิ่มเป็น 4 เท่า"))

        eq_text = self.hud(VGroup(
            Text("สมการสังเคราะห์แรงยกทางวิศวกรรม (NASA):", font_size=21, color=WHITE),
            Text("L = 1/2 * rho * V^2 * S * C_L", font_size=28, color=C_VERIFIED),
            Text("เมื่อ rho, S และ C_L คงที่: V เพิ่ม 2 เท่า -> L เพิ่ม 4 เท่า", font_size=18, color=C_LIFT),
            Text("rho = ความหนาแน่นอากาศ  |  V = ความเร็วลมสัมพัทธ์  |  S = พื้นที่ปีก  |  C_L = สัมประสิทธิ์แรงยก",
                 font_size=18, color=GRAYTXT)
        ).arrange(DOWN, buff=0.18).move_to([0, 1.45, 0]))

        # V^2 Demonstration Dashboard - enlarged width so text stays inside
        dash_box = RoundedRectangle(width=9.8, height=2.6, corner_radius=0.15, color=METAL, stroke_width=2).move_to([0, -1.3, 0])
        bar_base = Rectangle(width=2.2, height=0.35, color=C_THRUST, fill_opacity=0.8).move_to([-1.2, -0.95, 0])
        lbl_v1 = self.hud(Text("ความเร็ว V = 100 km/h  ->  แรงยก L = 1.0x", font_size=18, color=WHITE).next_to(bar_base, UP, buff=0.12))

        bar_double = Rectangle(width=4.4, height=0.35, color=C_THRUST, fill_opacity=0.8).move_to([-0.1, -1.9, 0])
        lbl_v2 = self.hud(Text("ความเร็ว V = 200 km/h (2x) ->  แรงยก L = 4.0x (4 เท่า)", font_size=18, color=C_LIFT).next_to(bar_double, UP, buff=0.12))

        dash_group = VGroup(dash_box, bar_base, bar_double)

        self.play(FadeIn(t), FadeIn(c))
        self.play(FadeIn(eq_text))
        self.play(Create(dash_box), FadeIn(lbl_v1), Create(bar_base))
        self.play(FadeIn(lbl_v2), Create(bar_double))
        self.wait(2.2)

        self.play(FadeOut(eq_text), FadeOut(dash_group), FadeOut(lbl_v1), FadeOut(lbl_v2), FadeOut(t), FadeOut(c))

    def beat_s6_four_stroke_engine_core(self):
        """S6: Four-stroke cycle cutaway showing combustion force converting to crank torque."""
        t = self.hud(title("S6: วัฏจักร 4 จังหวะ (Four-Stroke Engine Cycle) — แรงเผาไหม้สู่ทอร์ก"))
        c = self.hud(caption("จังหวะระเบิด (Power Stroke): ประกายไฟจุดเชื้อเพลิง ผลักลูกสูบลงสู่เพลาข้อเหวี่ยง"))

        # Cylinder cutaway
        cyl_left = line3([-0.8, -0.5, 0], [-0.8, 2.0, 0], color=METAL, thickness=0.04)
        cyl_right = line3([0.8, -0.5, 0], [0.8, 2.0, 0], color=METAL, thickness=0.04)
        cyl_head = line3([-0.8, 2.0, 0], [0.8, 2.0, 0], color=METAL, thickness=0.04)
        cyl = VGroup(cyl_left, cyl_right, cyl_head)

        piston = RoundedRectangle(width=1.5, height=0.7, corner_radius=0.08, color=METAL, fill_opacity=0.9).move_to([0, 1.2, 0])
        crank_center = np.array([0, -1.8, 0])
        crank_pin = np.array([0.5, -1.4, 0])
        crank_arm = line3(crank_center, crank_pin, color=C_MASTER, thickness=0.05)
        con_rod = line3([0, 1.2, 0], crank_pin, color=C_LINK, thickness=0.04)

        fire_flash = Star(n=8, outer_radius=0.6, inner_radius=0.25, color=C_FIRE, fill_opacity=0.9).move_to([0, 1.8, 0])
        force_piston = arrow3([0, 1.5, 0], [0, 0.4, 0], color=C_FIRE, thickness=0.045)
        lbl_force = self.hud(Text("แรงดันก๊าซเผาไหม้\n(Combustion Force)", font_size=18, color=C_FIRE).move_to([2.9, 1.3, 0]))

        torque_arc = CurvedArrow(np.array([0.6, -1.9, 0]), np.array([-0.4, -2.1, 0]),
                                 angle=-1.5, color=C_MASTER, stroke_width=4)
        lbl_torque = self.hud(Text("ทอร์กหมุนเพลา (Torque)", font_size=19, color=C_MASTER).move_to([2.2, -1.8, 0]))

        hud_strokes = self.hud(VGroup(
            Text("1. ดูด (Intake) -> 2. อัด (Compression)", font_size=18, color=GRAYTXT),
            Text("3. ระเบิด (Power) -> ผลักก้านสูบสร้างทอร์ก", font_size=19, color=C_FIRE),
            Text("4. คาย (Exhaust) -> ระบายไอเสีย", font_size=18, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12).to_corner(UL).shift(DOWN * 0.9))

        self.play(FadeIn(t), FadeIn(c))
        self.play(Create(cyl), Create(piston), Create(crank_arm), Create(con_rod), FadeIn(hud_strokes))
        self.play(FadeIn(fire_flash), Create(force_piston), FadeIn(lbl_force))
        self.play(Create(torque_arc), FadeIn(lbl_torque))
        self.wait(2.2)

        self.play(FadeOut(cyl), FadeOut(piston), FadeOut(crank_arm), FadeOut(con_rod), FadeOut(fire_flash),
                  FadeOut(force_piston), FadeOut(lbl_force), FadeOut(torque_arc), FadeOut(lbl_torque),
                  FadeOut(hud_strokes), FadeOut(t), FadeOut(c))

    def beat_s7_radial_master_and_links(self):
        """S7: 7-Cylinder radial layout: Master rod (#1 top) + 6 articulating rods."""
        t = self.hud(title("S7: สถาปัตยกรรม 7 สูบแถวเดียว: Master Rod และ Articulating Rods"))
        c = self.hud(caption("สูบ 1 ใช้ Master Rod จับเพลาข้อเหวี่ยงเดี่ยวโดยตรง | สูบ 2-7 ต่อยึดผ่าน Knuckle Pins"))

        # Shift radial engine group to the right to leave clean space for HUD on left
        rad_center = np.array([1.6, 0.0, 0])
        case = Circle(radius=2.4, color=METAL, stroke_width=2.5).move_to(rad_center)
        hub = Circle(radius=0.65, color=C_MASTER, fill_opacity=0.3, stroke_width=2.5).move_to(rad_center)

        pistons = VGroup()
        rods = VGroup()
        labels = VGroup()

        angles = [90 - i * (360 / 7) for i in range(7)]

        for idx, ang in enumerate(angles):
            rad = ang * DEGREES
            cyl_center = rad_center + np.array([2.1 * np.cos(rad), 2.1 * np.sin(rad), 0])
            p = RoundedRectangle(width=0.42, height=0.28, corner_radius=0.05,
                                 color=WHITE, fill_opacity=0.7).move_to(cyl_center)
            pistons.add(p)

            lbl = self.hud(Text(str(idx + 1), font_size=18, color=C_MASTER if idx == 0 else WHITE).move_to(
                rad_center + np.array([2.55 * np.cos(rad), 2.55 * np.sin(rad), 0])
            ))
            labels.add(lbl)

            if idx == 0:
                r = line3(rad_center, cyl_center, color=C_MASTER, thickness=0.055)
            else:
                pin_pos = rad_center + np.array([0.45 * np.cos(rad), 0.45 * np.sin(rad), 0])
                r = line3(pin_pos, cyl_center, color=C_LINK, thickness=0.035)
            rods.add(r)

        hud_info = self.hud(VGroup(
            Text("1 Master Rod (สีทอง - สูบ 1 ด้านบน)", font_size=18, color=C_MASTER),
            Text("6 Articulating Rods (สีฟ้า - สูบ 2 ถึง 7)", font_size=18, color=C_LINK),
            Text("ขับเคลื่อนเพลาข้อเหวี่ยงชุดเดียว\n(Single Crank Throw)", font_size=17, color=WHITE)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.14).to_corner(UL).shift(DOWN * 0.85 + RIGHT * 0.2))

        self.play(FadeIn(t), FadeIn(c))
        self.play(Create(case), Create(hub), FadeIn(hud_info))
        self.play(Create(pistons), FadeIn(labels))
        self.play(Create(rods))
        self.wait(2.2)

        self.play(FadeOut(case), FadeOut(hub), FadeOut(pistons), FadeOut(labels), FadeOut(rods),
                  FadeOut(hud_info), FadeOut(t), FadeOut(c))

    def beat_s8_elliptical_knuckle_path(self):
        """S8: Elliptical knuckle-pin path (schematic / not-to-scale)."""
        t = self.hud(title("S8: วิถี Knuckle Pin รูปวงรี (Schematic Kinematics — Not to Scale)"))
        c = self.hud(caption("เมื่อ Master Rod แกว่ง จุดยึด Knuckle Pin จะวิ่งเป็นวงรี ไม่ใช่วงกลมสมบูรณ์"))

        phase = ValueTracker(0.0)
        crank_center = np.array([-3.2, 0.05, 0])
        ellipse_center = np.array([3.0, 0.05, 0])
        crank_radius = 1.35
        ellipse_a, ellipse_b = 1.45, 0.95

        crank_circle = DashedVMobject(Circle(radius=crank_radius, color=C_MASTER, stroke_width=2.5)).move_to(crank_center)
        lbl_crank = self.hud(Text("วิถี Crankpin: วงกลมสมบูรณ์ (Circle)", font_size=19, color=C_MASTER).move_to([-3.0, 1.8, 0]))

        knuckle_ellipse = DashedVMobject(Ellipse(width=2 * ellipse_a, height=2 * ellipse_b, color=C_LINK, stroke_width=3)).move_to(ellipse_center)
        lbl_knuckle = self.hud(Text("วิถี Knuckle Pin: รูปวงรี (Ellipse)", font_size=19, color=C_LINK).move_to([3.0, 1.8, 0]))

        crank_dot = always_redraw(lambda: Dot(
            crank_center + crank_radius * np.array([
                np.cos(phase.get_value()), np.sin(phase.get_value()), 0
            ]), color=C_MASTER, radius=0.09
        ))
        knuckle_dot = always_redraw(lambda: Dot(
            ellipse_center + np.array([
                ellipse_a * np.cos(phase.get_value()),
                ellipse_b * np.sin(phase.get_value()), 0
            ]), color=C_LINK, radius=0.09
        ))

        rod_pivot = np.array([0.0, -0.9, 0])
        rod_length = 1.25
        rocking_rod = always_redraw(lambda: Line(
            rod_pivot,
            rod_pivot + rod_length * np.array([
                np.cos(0.28 * np.sin(phase.get_value())),
                np.sin(0.28 * np.sin(phase.get_value())), 0
            ]),
            color=C_MASTER, stroke_width=7
        ))
        rod_pivot_dot = Dot(rod_pivot, color=C_MASTER, radius=0.10)
        rod_label = self.hud(Text("Master Rod rocking (schematic)", font_size=18, color=C_MASTER).move_to([0.0, 0.65, 0]))

        box_schematic = self.hud(VGroup(
            Text("ข้อสังเกตทางกลไก (Kinematic Fact):", font_size=18, color=WARN),
            Text("1. จุดหมุน Knuckle Pins ไม่ได้อยู่ที่ศูนย์กลางเพลา จึงเกิดการแกว่งแบบรี", font_size=17, color=WHITE),
            Text("2. ส่งผลให้ระยะชัก (Stroke) ของแต่ละสูบแตกต่างกันเล็กน้อย", font_size=17, color=WHITE),
            Text("* แผนภาพแสดงเชิงหลักการทั่วไป (Schematic) ไม่เจาะจงสัดส่วนเครื่องยนต์ W670", font_size=16, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.11).to_corner(DL).shift(UP * 0.7 + RIGHT * 0.5))

        self.play(FadeIn(t), FadeIn(c))
        self.play(Create(crank_circle), FadeIn(lbl_crank), Create(knuckle_ellipse), FadeIn(lbl_knuckle))
        self.play(FadeIn(crank_dot, knuckle_dot, rod_pivot_dot), Create(rocking_rod), FadeIn(rod_label))
        self.play(FadeIn(box_schematic))
        self.play(phase.animate.set_value(TAU), run_time=2.4, rate_func=linear)
        self.wait(0.8)

        # Stop live geometry before removing it; this keeps the updater lifecycle clean.
        crank_dot.clear_updaters()
        knuckle_dot.clear_updaters()
        rocking_rod.clear_updaters()
        self.play(FadeOut(crank_dot), FadeOut(knuckle_dot), FadeOut(rocking_rod), FadeOut(rod_pivot_dot),
                  FadeOut(crank_circle), FadeOut(knuckle_ellipse),
                  FadeOut(lbl_crank), FadeOut(lbl_knuckle), FadeOut(box_schematic),
                  FadeOut(rod_label), FadeOut(t), FadeOut(c))

    def beat_s9_firing_order_720(self):
        """S9: 720-degree firing order (1-3-5-7-2-4-6) with rear-view and odd-per-row caveat."""
        t = self.hud(title("S9: ลำดับการจุดระเบิด 720°: 1-3-5-7-2-4-6 (FAA Convention)"))
        c = self.hud(fit_width(caption("เครื่องยนต์ 4 จังหวะหมุน 2 รอบ (720°) ต่อวัฏจักร -> ก้าวทีละ 2 ตำแหน่งในวงแหวน เพื่อช่วงจุดระเบิดที่สม่ำเสมอ"), 13.0))

        # Shift cylinder circle to the right to leave ample space for left HUD
        rad_center = np.array([1.8, 0.0, 0])
        angles = [90 - i * (360 / 7) for i in range(7)]
        cyl_nodes = VGroup()
        cyl_labels = VGroup()
        for i, ang in enumerate(angles):
            rad = ang * DEGREES
            pos = rad_center + np.array([1.9 * np.cos(rad), 1.9 * np.sin(rad), 0])
            cyl_nodes.add(Circle(radius=0.40, color=METAL, fill_opacity=0.4).move_to(pos))
            cyl_labels.add(self.hud(Text(str(i + 1), font_size=19, color=WHITE).move_to(pos)))

        hud_convention = self.hud(VGroup(
            Text("FAA Standard Convention:", font_size=18, color=C_VERIFIED),
            Text("- มองจากด้านหลังเครื่องยนต์ (Rear View)", font_size=16, color=WHITE),
            Text("- สูบ 1 อยู่บนสุด (Top Center)", font_size=16, color=WHITE),
            Text("- นับหมายเลขตามเข็มนาฬิกา (Clockwise)", font_size=16, color=WHITE),
            Text("- ช่วงห่างการจุดระเบิด: Delta_theta = 720° / 7 = 102.86°", font_size=16, color=C_MASTER),
            Text("- ต้องเป็นเลขคี่ต่อแถว (Odd per row) จึงจะก้าว +2 แล้ววนครบทุกสูบ", font_size=16, color=WARN),
            Text("- N=7: +2 วนครบ | N=6: +2 วนซ้ำเพียงครึ่งหนึ่ง", font_size=15, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.1).to_corner(UL).shift(DOWN * 0.85 + RIGHT * 0.2))

        seq_text = self.hud(Text("ลำดับการจุดระเบิด: 1 -> 3 -> 5 -> 7 -> 2 -> 4 -> 6", font_size=21, color=C_FIRE).move_to([1.8, 2.55, 0]))
        crank_angle = ValueTracker(0.0)
        angle_hud = self.hud(live_row(
            "Crank angle:", "° / 720°", crank_angle.get_value,
            [1.8, -2.45, 0], decimals=0,
            num_color=C_MASTER, label_color=WHITE, unit_color=GRAYTXT,
            label_size=18, num_size=21, unit_size=18, buff=0.12
        ))
        angle_value = angle_hud[1]

        crank_indicator = always_redraw(lambda: Line(
            rad_center,
            rad_center + 1.2 * np.array([
                np.cos((crank_angle.get_value() % 360) * DEGREES),
                np.sin((crank_angle.get_value() % 360) * DEGREES), 0
            ]),
            color=C_MASTER, stroke_width=5
        ))
        crank_hub = Dot(rad_center, color=C_MASTER, radius=0.09)

        self.play(FadeIn(t), FadeIn(c))
        self.play(Create(cyl_nodes), FadeIn(cyl_labels), FadeIn(hud_convention), FadeIn(seq_text), FadeIn(angle_hud), FadeIn(crank_hub), Create(crank_indicator))

        # Flash sequence: 1 -> 3 -> 5 -> 7 -> 2 -> 4 -> 6
        fire_order = [0, 2, 4, 6, 1, 3, 5]
        for step, cyl_idx in enumerate(fire_order, start=1):
            flash = Circle(radius=0.50, color=C_FIRE, stroke_width=4).move_to(cyl_nodes[cyl_idx].get_center())
            self.play(
                crank_angle.animate.set_value(step * 720 / 7),
                FadeIn(flash),
                run_time=0.38,
                rate_func=linear,
            )
            self.play(FadeOut(flash, run_time=0.12))

        self.wait(1.5)
        crank_indicator.clear_updaters()
        angle_value.clear_updaters()
        self.play(FadeOut(cyl_nodes), FadeOut(cyl_labels), FadeOut(hud_convention), FadeOut(seq_text), FadeOut(angle_hud), FadeOut(crank_indicator), FadeOut(crank_hub), FadeOut(t), FadeOut(c))

    def beat_s10_throttle_to_lift_integration(self):
        """S10: Throttle-to-lift causal integration closing the loop."""
        t = self.hud(title("S10: ห่วงโซ่เหตุและผลจากคันเร่งสู่แรงยก (Throttle to Lift)"))
        c = self.hud(caption("สรุปบทเรียน: เครื่องยนต์ไม่ได้ยกเครื่องบินโดยตรง แต่สร้างแรงขับและความเร็วลมให้ปีกสร้างแรงยก"))

        # Flow chart chain
        steps = [
            ("1. คันเร่ง (Throttle)", WHITE),
            ("2. เผาไหม้ (Combustion)", C_FIRE),
            ("3. ทอร์กเพลา (Torque)", C_MASTER),
            ("4. แรงขับใบพัด (Thrust)", C_THRUST),
            ("5. ความเร็วลม (V_inf)", C_THRUST),
            ("6. ลมเบนทิศ/แรงดูดปีก", C_LIFT),
            ("7. แรงยก (Lift >= Weight)", C_LIFT)
        ]

        chain_boxes = VGroup()
        for text_str, col in steps:
            box = VGroup(
                RoundedRectangle(width=3.6, height=0.55, corner_radius=0.1, color=col, fill_opacity=0.3, stroke_width=2),
                self.hud(Text(text_str, font_size=18, color=col))
            )
            chain_boxes.add(box)

        chain_boxes.arrange(DOWN, buff=0.18).move_to([-3.0, 0, 0])

        conclusion_card = self.hud(VGroup(
            Text("สรุปหัวใจสำคัญ (North-Star Takeaway):", font_size=22, color=C_VERIFIED),
            Text("• เครื่องยนต์สร้าง Thrust เพื่อเอาชนะ Drag", font_size=19, color=WHITE),
            Text("• ความเร็วลม (V_inf) ไหลผ่านปีกด้วยความโค้งและมุมปะทะ", font_size=19, color=WHITE),
            Text("• ปีกสร้าง Lift ตามกฎอนุรักษ์โมเมนตัมและความดัน", font_size=19, color=WHITE),
            Text("-> เครื่องยนต์สร้างเงื่อนไขให้ปีกสร้างแรงยก", font_size=21, color=C_LIFT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([3.0, 0, 0]))

        self.play(FadeIn(t), FadeIn(c))
        for box in chain_boxes:
            self.play(FadeIn(box, run_time=0.25))

        self.play(FadeIn(conclusion_card))
        self.wait(3.0)

        self.play(FadeOut(chain_boxes), FadeOut(conclusion_card), FadeOut(t), FadeOut(c))
