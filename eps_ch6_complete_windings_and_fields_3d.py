# -*- coding: utf-8 -*-
"""
eps_ch6_complete_windings_and_fields_3d.py
Scene: EP03_ArmatureReaction_3D_Windings_And_Dual_Magnetic_Fields
Combines:
1. 3D Stator Poles (N-S)
2. 3D Rotor Cylinder + 12 Copper Winding Loops + Commutator + Brushes
3. 3D Main Magnetic Field (Bf)
4. 3D Armature Magnetic Field (Ba circulating around the 3D windings)
5. 3D Combined Distorted Field (Btotal S-curve) + 3D Tilted Neutral Plane
"""

import math
from manim import *
import numpy as np
from mlib import *

class CompleteWindingsAndDualFields3D(SafeThreeDScene):
    def construct(self):
        self.set_camera_orientation(phi=65 * DEGREES, theta=-55 * DEGREES)

        # Title with fit_width to prevent any edge clipping
        t_title = title("3D แท้: ขดลวดอาร์เมเจอร์ของจริง & สนามแม่เหล็ก 2 สนามรวมกัน (หน้า 3-8)")
        fit_width(t_title, 12.0)
        self.hud(t_title)
        self.play(FadeIn(t_title))

        # HUD Panel on Right
        hud_p = RoundedRectangle(corner_radius=0.18, width=4.6, height=5.6, color="#1E293B", fill_opacity=0.92).move_to([4.7, 0, 0])
        hud_h = Text("กลไกสนาม 3 มิติครบชุด", font_size=18, color=WHITE).move_to([4.7, 2.3, 0])

        c1 = VGroup(
            Text("1. ขดลวด 3D + คอมมิวเตเตอร์:", font_size=13, color=YELLOW),
            Text("สายทองแดงร้อยรอบแกนเหล็กโรเตอร์", font_size=11, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.04).move_to([4.7, 1.4, 0])

        c2 = VGroup(
            Text("2. สนามหลัก Bf (สีฟ้า):", font_size=13, color=FIELD),
            Text("พุ่งแนวนอนจาก N ซ้ายไป S ขวา", font_size=11, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.04).move_to([4.7, 0.5, 0])

        c3 = VGroup(
            Text("3. สนามอาร์เมเจอร์ Ba (สีส้ม):", font_size=13, color=WARN),
            Text("วนรอบสายไฟขดลวดในแนวตั้งฉาก", font_size=11, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.04).move_to([4.7, -0.4, 0])

        c4 = VGroup(
            Text("4. สนามรวมบิดเบี้ยว Btotal (สีม่วง):", font_size=13, color=EMF),
            Text("เส้นแรงรวมกัน ➔ ระนาบ MNP เอียงตาม", font_size=11, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.04).move_to([4.7, -1.4, 0])

        hud_grp = VGroup(hud_p, hud_h, c1, c2, c3, c4)
        self.hud(hud_grp)
        self.play(FadeIn(hud_grp))

        cx, cy, cz = -1.8, 0.0, 0.0

        # Stator Poles
        pole_n = Prism(dimensions=[1.0, 3.2, 2.6]).move_to([cx - 3.2, cy, cz]).set_color(RED).set_opacity(0.85)
        pole_s = Prism(dimensions=[1.0, 3.2, 2.6]).move_to([cx + 3.2, cy, cz]).set_color(BLUE).set_opacity(0.85)
        lbl_n = Text("N", font_size=20, color=WHITE).move_to([cx - 3.2, cy, cz + 1.6])
        lbl_s = Text("S", font_size=20, color=WHITE).move_to([cx + 3.2, cy, cz + 1.6])
        self.world_text(lbl_n, lbl_s)
        self.play(FadeIn(pole_n), FadeIn(pole_s), FadeIn(lbl_n), FadeIn(lbl_s))

        # Rotor Core + Commutator + Shaft
        rotor = Cylinder(radius=1.5, height=2.2, direction=[0, 0, 1], color=METAL).move_to([cx, cy, cz]).set_opacity(0.45)
        shaft = Cylinder(radius=0.15, height=4.2, direction=[0, 0, 1], color=GRAY).move_to([cx, cy, cz])
        comm_z = cz + 1.4
        comm_hub = Cylinder(radius=0.55, height=0.6, direction=[0, 0, 1], color="#B45309").move_to([cx, cy, comm_z])
        self.play(FadeIn(rotor), FadeIn(shaft), FadeIn(comm_hub))

        # 3D Winding Coils (12 loops) & Tap Wires
        num_coils = 12
        windings = VGroup()
        tap_wires = VGroup()
        for i in range(num_coils):
            ang = i * (2 * PI / num_coils)
            r_out = 1.54
            p_back = np.array([cx + r_out * math.cos(ang), cy + r_out * math.sin(ang), cz - 1.1])
            p_front = np.array([cx + r_out * math.cos(ang), cy + r_out * math.sin(ang), cz + 1.1])
            rod = Line(p_back, p_front, color=YELLOW, stroke_width=4)

            ang_next = (i + num_coils // 2) * (2 * PI / num_coils)
            p_back_next = np.array([cx + r_out * math.cos(ang_next), cy + r_out * math.sin(ang_next), cz - 1.1])
            arch = Line(p_back, p_back_next, color=WARN, stroke_width=3)

            p_comm = np.array([cx + 0.55 * math.cos(ang), cy + 0.55 * math.sin(ang), comm_z])
            tap = Line(p_front, p_comm, color=YELLOW, stroke_width=2.5)

            windings.add(rod, arch)
            tap_wires.add(tap)

        # Brushes
        brush_top = Prism(dimensions=[0.3, 0.4, 0.4]).move_to([cx, cy + 0.7, comm_z]).set_color(WHITE).set_opacity(0.95)
        brush_bot = Prism(dimensions=[0.3, 0.4, 0.4]).move_to([cx, cy - 0.7, comm_z]).set_color(WHITE).set_opacity(0.95)

        cap1 = caption("1. ขดลวดอาร์เมเจอร์ 3D (เส้นสีทอง) พันรอบแกนเหล็กและเชื่อมเข้าซี่คอมมิวเตเตอร์")
        self.hud(cap1)
        self.play(Create(windings), Create(tap_wires), FadeIn(brush_top), FadeIn(brush_bot), FadeIn(cap1))
        self.wait(2.0)

        # Step 2: Main Magnetic Field (Bf) in 3D (Straight Cyan Flux Lines)
        main_flux = VGroup()
        for y_val in np.linspace(-1.0, 1.0, 5):
            for z_val in np.linspace(-0.6, 0.6, 3):
                l = Line([cx - 2.4, cy + y_val, cz + z_val], [cx + 2.4, cy + y_val, cz + z_val], color=FIELD, stroke_width=2.5).set_opacity(0.7)
                main_flux.add(l)

        cap2 = caption("2. สนามหลัก Bf (เส้นสีฟ้า): วิ่งตรงจากขั้ว N ไปยังขั้ว S ในแนวนอน")
        self.hud(cap2)
        self.play(FadeOut(cap1), Create(main_flux), FadeIn(cap2))
        self.wait(2.0)

        # Step 3: Armature Field (Ba) in 3D (Circular Loops circulating around the 3D Windings)
        arm_loops = VGroup()
        for rad in [0.7, 1.1]:
            c_left = Circle(radius=rad, color=WARN, stroke_width=3.5).rotate(PI/2, axis=RIGHT).move_to([cx - 0.8, cy, cz])
            c_right = Circle(radius=rad, color=WARN, stroke_width=3.5).rotate(PI/2, axis=RIGHT).move_to([cx + 0.8, cy, cz])
            arm_loops.add(c_left, c_right)

        cap3 = caption("3. สนามอาร์เมเจอร์ Ba (วงกลมสีส้ม): กระแสในขดลวดสร้างสนามแม่เหล็กวนรอบตัวนำในแนวตั้งฉาก")
        self.hud(cap3)
        self.play(FadeOut(cap2), Create(arm_loops), FadeIn(cap3))
        self.wait(2.5)

        # Step 4: Combined Distorted 3D Flux (Btotal S-curve) + Shifted Neutral Plane (MNP)
        distorted_flux = VGroup()
        for y_val in np.linspace(-1.0, 1.0, 5):
            for z_val in np.linspace(-0.6, 0.6, 3):
                p_start = np.array([cx - 2.4, cy + y_val + 0.5, cz + z_val])
                p_end = np.array([cx + 2.4, cy + y_val - 0.5, cz + z_val])
                curve = CubicBezier(p_start, p_start + [0.9, -0.35, 0], p_end + [-0.9, 0.35, 0], p_end, color=EMF, stroke_width=3.2)
                distorted_flux.add(curve)

        tilt = 24 * DEGREES
        mnp_plane = Polygon(
            [cx - 1.6 * math.sin(tilt), cy - 1.6 * math.cos(tilt), cz - 1.2],
            [cx + 1.6 * math.sin(tilt), cy + 1.6 * math.cos(tilt), cz - 1.2],
            [cx + 1.6 * math.sin(tilt), cy + 1.6 * math.cos(tilt), cz + 1.2],
            [cx - 1.6 * math.sin(tilt), cy - 1.6 * math.cos(tilt), cz + 1.2],
            color="#EC4899", fill_color="#EC4899", fill_opacity=0.35, stroke_width=2.5
        )
        lbl_mnp = Text("ระนาบเป็นกลางใหม่ (MNP)", font_size=14, color="#EC4899").move_to([cx + 0.8, cy + 1.9, cz])
        self.world_text(lbl_mnp)

        cap4 = caption("4. สนามรวมบิดเบี้ยว Btotal (เส้นสีม่วง): เส้นแรง 2 สนามรวมกัน ➔ บิดเบี้ยว & ระนาบเป็นกลางเอียงตาม!")
        self.hud(cap4)
        self.play(
            FadeOut(cap3),
            FadeOut(main_flux),
            FadeOut(arm_loops),
            Create(distorted_flux),
            FadeIn(mnp_plane), FadeIn(lbl_mnp),
            FadeIn(cap4)
        )

        # 3D Camera Rotation to show complete spatial view from multiple angles
        self.move_camera(phi=75 * DEGREES, theta=-15 * DEGREES, run_time=3.5)
        self.wait(1.5)
        self.move_camera(phi=60 * DEGREES, theta=-85 * DEGREES, run_time=3.5)
        self.wait(2.5)
