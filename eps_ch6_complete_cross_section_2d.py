# -*- coding: utf-8 -*-
"""
eps_ch6_complete_cross_section_2d.py — Complete 2D Cross-Section Assembly of DC Machine
(1080p Full HD @ 25fps)
Scene: CompleteDCCrossSectionAssembly
Shows:
1. Stator Magnetic Poles (N left, S right)
2. Armature Slotted Core with Conductor Coils (Dot / Cross)
3. Commutator Hub with Segments in the center + Tap Connections
4. Carbon Brushes (+) and (-) touching the Commutator
5. External Load Circuit
"""

import math
from manim import *
import numpy as np
from mlib import *

class CompleteDCCrossSectionAssembly(SafeScene):
    def construct(self):
        t_title = title("แผนผัง 2D ครบชุด: ตำแหน่งประกอบจริงของขดลวด, คอมมิวเตเตอร์ & แปรงถ่าน")
        fit_width(t_title, 12.2)
        self.play(FadeIn(t_title))

        # Right Summary HUD
        panel = RoundedRectangle(corner_radius=0.18, width=4.6, height=5.6, color="#1E293B", fill_opacity=0.92).move_to([4.7, 0, 0])
        p_head = Text("ตำแหน่ง 4 ส่วนประกอบ", font_size=18, color=WHITE).move_to([4.7, 2.3, 0])

        c1 = VGroup(
            Text("1. ขั้วแม่เหล็ก N-S (Stator):", font_size=13, color=FIELD),
            Text("ประกบอยู่วงนอกสุด ซ้าย-ขวา", font_size=11, color=GRAYTXT)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.04).move_to([4.7, 1.4, 0])

        c2 = VGroup(
            Text("2. ขดลวดอาร์เมเจอร์ (Coils):", font_size=13, color=YELLOW),
            Text("ฝังอยู่ในร่องสล็อตรอบผิวโรเตอร์", font_size=11, color=GRAYTXT),
            Text("ซีกซ้ายพุ่งออก ⊙ / ซีกขวาพุ่งเข้า ⊗", font_size=11, color=YELLOW)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.04).move_to([4.7, 0.4, 0])

        c3 = VGroup(
            Text("3. วงแหวนคอมมิวเตเตอร์:", font_size=13, color=WARN),
            Text("เป็นซี่ทองแดงอยู่รอบเพลาแกนกลาง", font_size=11, color=GRAYTXT),
            Text("มีสายต่อ (Tap) เชื่อมจากขดลวดเข้ามา", font_size=11, color=WARN)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.04).move_to([4.7, -0.6, 0])

        c4 = VGroup(
            Text("4. แปรงถ่าน (+) และ (-):", font_size=13, color=WHITE),
            Text("อยู่นิ่ง แตะบน-ล่างที่ซี่คอมมิวเตเตอร์", font_size=11, color=GRAYTXT),
            Text("ส่งกระแสตรง 100A ออกสู่วงจรโหลด", font_size=11, color=EMF)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.04).move_to([4.7, -1.6, 0])

        hud_grp = VGroup(panel, p_head, c1, c2, c3, c4)
        self.play(FadeIn(hud_grp))

        cx = -2.2
        # 1. Stator Poles (N Left Red, S Right Blue)
        pole_n = ArcPolygon(
            [cx - 2.8, -1.6, 0], [cx - 2.8, 1.6, 0],
            [cx - 2.1, 1.3, 0], [cx - 2.1, -1.3, 0],
            color=RED, fill_color="#991B1B", fill_opacity=0.7
        )
        lbl_n = Text("N", font_size=24, color=WHITE).move_to([cx - 2.5, 0, 0])

        pole_s = ArcPolygon(
            [cx + 2.8, 1.6, 0], [cx + 2.8, -1.6, 0],
            [cx + 2.1, -1.3, 0], [cx + 2.1, 1.3, 0],
            color=BLUE, fill_color="#1E3A8A", fill_opacity=0.7
        )
        lbl_s = Text("S", font_size=24, color=WHITE).move_to([cx + 2.5, 0, 0])

        cap1 = caption("1. ขั้วแม่เหล็กสเตเตอร์ N (ซ้าย) และ S (ขวา) ประกบอยู่ด้านนอกสุด")
        self.play(Create(pole_n), FadeIn(lbl_n), Create(pole_s), FadeIn(lbl_s), FadeIn(cap1))
        self.wait(1.5)

        # 2. Rotor Slotted Core (Outer Grey Ring)
        rotor_outer = Annulus(inner_radius=1.2, outer_radius=1.85, color=METAL, fill_color="#0F172A", fill_opacity=0.9).move_to([cx, 0, 0])
        cap2 = caption("2. แกนเหล็กโรเตอร์อาร์เมเจอร์ (วงแหวนสีเทา) วางอยู่ตรงกลางระหว่างขั้ว")
        self.play(FadeOut(cap1), Create(rotor_outer), FadeIn(cap2))
        self.wait(1.5)

        # 3. Commutator Hub & Segments (Inner Bronze Ring)
        comm_ring = Annulus(inner_radius=0.45, outer_radius=0.85, color="#F59E0B", fill_color="#B45309", fill_opacity=0.9).move_to([cx, 0, 0])
        shaft_dot = Dot([cx, 0, 0], radius=0.25, color=GRAY)
        lbl_shaft = Text("เพลา", font_size=10, color=WHITE).move_to([cx, 0, 0])

        # Commutator segment divider lines
        comm_lines = VGroup()
        for deg in [0, 45, 90, 135, 180, 225, 270, 315]:
            rad = math.radians(deg)
            p1 = np.array([cx + 0.45 * math.cos(rad), 0.45 * math.sin(rad), 0])
            p2 = np.array([cx + 0.85 * math.cos(rad), 0.85 * math.sin(rad), 0])
            comm_lines.add(Line(p1, p2, color=BLACK, stroke_width=2))

        lbl_comm = Text("คอมมิวเตเตอร์", font_size=11, color=YELLOW).move_to([cx, 0, 0]).shift(UP * 0.0)

        cap3 = caption("3. ซี่คอมมิวเตเตอร์ (วงแหวนทองแดงด้านใน) แบ่งเป็นซี่ๆ อยู่รอบแกนเพลา")
        self.play(FadeOut(cap2), Create(comm_ring), Create(comm_lines), FadeIn(shaft_dot), FadeIn(lbl_shaft), FadeIn(cap3))
        self.wait(1.5)

        # 4. Armature Conductor Coils in Slots + Tap Wires to Commutator
        num_slots = 8
        coils_grp = VGroup()
        taps_grp = VGroup()

        for i in range(num_slots):
            deg = i * (360.0 / num_slots)
            rad = math.radians(deg)
            r_slot = 1.55
            p_slot = np.array([cx + r_slot * math.cos(rad), r_slot * math.sin(rad), 0])
            p_comm = np.array([cx + 0.85 * math.cos(rad), 0.85 * math.sin(rad), 0])

            # Left side: Dot (out), Right side: Cross (in)
            is_left = (90 < deg < 270)
            c_color = YELLOW if is_left else WARN
            dot_slot = Circle(radius=0.14, color=c_color, fill_color="#0F172A", fill_opacity=1.0).move_to(p_slot)
            
            if is_left:
                sym = Dot(p_slot, radius=0.04, color=WHITE)
            else:
                sym = VGroup(
                    Line(p_slot + [-0.05, -0.05, 0], p_slot + [0.05, 0.05, 0], color=WHITE, stroke_width=1.5),
                    Line(p_slot + [-0.05, 0.05, 0], p_slot + [0.05, -0.05, 0], color=WHITE, stroke_width=1.5)
                )

            tap_line = Line(p_slot, p_comm, color=YELLOW, stroke_width=2.2)
            coils_grp.add(dot_slot, sym)
            taps_grp.add(tap_line)

        cap4 = caption("4. ขดลวดอาร์เมเจอร์ (⊙ ซ้าย, ⊗ ขวา) ฝังในร่องสล็อต และมีสาย Tap สีทองเชื่อมเข้าซี่คอมมิวเตเตอร์")
        self.play(FadeOut(cap3), Create(coils_grp), Create(taps_grp), FadeIn(cap4))
        self.wait(2.0)

        # 5. Carbon Brushes (+) Top, (-) Bottom & External Circuit
        brush_top = Rectangle(width=0.45, height=0.35, color=WHITE, fill_color="#334155", fill_opacity=0.95).move_to([cx, 1.05, 0])
        lbl_bt = Text("(+)", font_size=11, color=WHITE).move_to(brush_top.get_center())

        brush_bot = Rectangle(width=0.45, height=0.35, color=WHITE, fill_color="#334155", fill_opacity=0.95).move_to([cx, -1.05, 0])
        lbl_bb = Text("(-)", font_size=11, color=WHITE).move_to(brush_bot.get_center())

        # External Load Circuit
        wire_out_t = Line([cx, 1.22, 0], [cx, 2.5, 0], color=EMF, stroke_width=3)
        wire_out_b = Line([cx, -1.22, 0], [cx, -2.5, 0], color=EMF, stroke_width=3)
        wire_to_load_t = Line([cx, 2.5, 0], [cx + 3.2, 2.5, 0], color=EMF, stroke_width=3)
        wire_to_load_b = Line([cx, -2.5, 0], [cx + 3.2, -2.5, 0], color=EMF, stroke_width=3)
        wire_load_box = Rectangle(width=0.8, height=1.4, color=EMF, fill_color="#581C87", fill_opacity=0.8).move_to([cx + 3.2, 0, 0])
        lbl_load = Text("LOAD\n100A", font_size=12, color=WHITE).move_to(wire_load_box.get_center())
        wire_load_t = Line([cx + 3.2, 2.5, 0], [cx + 3.2, 0.7, 0], color=EMF, stroke_width=3)
        wire_load_b = Line([cx + 3.2, -2.5, 0], [cx + 3.2, -0.7, 0], color=EMF, stroke_width=3)

        circuit_grp = VGroup(
            brush_top, lbl_bt, brush_bot, lbl_bb,
            wire_out_t, wire_out_b, wire_to_load_t, wire_to_load_b,
            wire_load_box, lbl_load, wire_load_t, wire_load_b
        )

        cap5 = caption("5. แปรงถ่าน (+) และ (-) แตะบนซี่คอมมิวเตเตอร์ตรงระนาบเป็นกลาง เพื่อส่งกระแสตรง 100A ออกสู่โหลดภายนอก!")
        self.play(FadeOut(cap4), FadeIn(circuit_grp), FadeIn(cap5))
        self.wait(4.0)
