"""
mlib — ไลบรารีร่วมสำหรับคลิปสอน (Min's teaching-video standard)

กฎประจำที่ไลบรารีนี้บังคับให้เอง:
  1. ตรวจตำแหน่งตัวอักษรตลอดเส้นเวลา (ต้น/กลาง/ปลาย) ไม่ใช่แค่เฟรมสุดท้าย
     -> SafeScene จะสแกนทุก ~0.25 วิของแอนิเมชัน แล้วพิมพ์ [LAYOUT] เตือนเมื่อ
        ข้อความทับกันเอง หรือหลุดขอบเฟรม
  2. สีเดียว = ปริมาณเดียว ตลอดทุกคลิป (Mayer signaling principle)
  3. โซนตายตัว: หัวเรื่องบน / เวทีกลาง / พาเนลขวา / คำบรรยายล่าง
"""

import sys

from manim import *
import numpy as np

# Cross-platform Thai font: Windows has Leelawadee UI; GitHub Actions'
# Linux container only installs fonts-thai-tlwg (font family name "Loma").
THAI_FONT = "Loma" if sys.platform.startswith("linux") else "Leelawadee UI"
Text.set_default(font=THAI_FONT)

# ---------------------------------------------------------------- palette
# ปริมาณทางฟิสิกส์หนึ่งอย่าง = สีหนึ่งสี ใช้ซ้ำทุกคลิปในซีรีส์
CURRENT = "#FFB300"   # กระแส I
FIELD   = "#42A5F5"   # สนามแม่เหล็ก B
FORCE   = "#66BB6A"   # แรง F
TORQUE  = "#AB47BC"   # ทอร์ก tau
EMF     = "#EF5350"   # แรงเคลื่อนไฟฟ้าย้อนกลับ (back EMF)
METAL   = "#90A4AE"   # ชิ้นส่วนโลหะ / โครงสร้าง
GRAYTXT = "#B0BEC5"   # ข้อความรอง
WARN    = "#FF7043"   # จุดสำคัญ / ปัญหา
OK      = "#26C6DA"   # ผลลัพธ์ / ข้อสรุป

# ---- ชุดสีเฉพาะซีรีส์ Gear Trains (บทที่ 7) — ใช้ตัวเดิมซ้ำทุกคลิปในซีรีส์
GEAR_IN  = "#4FC3F7"  # เฟืองตัวขับ / input / first (F)
GEAR_OUT = "#FFB74D"  # เฟืองตัวตาม / output / last (L)
GEAR_MID = "#81C784"  # เฟืองตัวกลาง (idler / planet)
RING_G   = "#CE93D8"  # ring gear / internal sun
ARM_G    = "#FF8A65"  # arm / carrier

# ---------------------------------------------------------------- zones
FW = config.frame_width      # 14.222
FH = config.frame_height     # 8.0
X_MAX, Y_MAX = FW / 2, FH / 2

TITLE_Y = 3.45               # แถบหัวเรื่อง
CAP_Y = -3.45                # แถบคำบรรยายล่าง
STAGE_C = np.array([-2.2, 0.15, 0])   # จุดกึ่งกลางเวทีเมื่อมีพาเนลขวา
PANEL_X = 4.05                        # แกนกลางพาเนลขวา
PANEL_TOP = 2.55


def title(txt, color=WHITE, size=30):
    """หัวเรื่องบนสุด — ตำแหน่งตายตัว ไม่ชนกับอะไร"""
    return Text(txt, font_size=size, color=color).move_to([0, TITLE_Y, 0])


def caption(txt, color=GRAYTXT, size=23):
    """คำบรรยายล่างสุด — ตำแหน่งตายตัว"""
    return Text(txt, font_size=size, color=color).move_to([0, CAP_Y, 0])


def panel_slot(mob, i, gap=1.25):
    """วางกล่องข้อความในพาเนลขวา ช่องที่ i (0 = บนสุด)"""
    return mob.move_to([PANEL_X, PANEL_TOP - i * gap, 0])


def fit_width(mob, max_w):
    """ย่อให้พอดีความกว้างที่กำหนด (กันข้อความยาวล้นโซน)"""
    if mob.width > max_w:
        mob.scale(max_w / mob.width)
    return mob


# ------------------------------------------------------- layout checking
_TEXTY = (Text, MathTex, Tex, MarkupText, DecimalNumber, Integer)


def _collect(mob, texts, graphics):
    """แยกโหนดข้อความ กับ โหนดกราฟิก (เส้น/รูปทรง) ออกจากกัน"""
    if isinstance(mob, _TEXTY):
        texts.append(mob)
        return
    if isinstance(mob, VMobject) and mob.has_points():
        graphics.append(mob)
    for s in mob.submobjects:
        _collect(s, texts, graphics)


def _dense_points(m, sub=8):
    """สุ่มจุดถี่ๆ ตามเส้นจริงของกราฟิก (ไม่ใช้ bounding box เพราะเส้นทแยงจะหลอก)"""
    pts = m.get_all_points()
    if len(pts) < 2:
        return pts
    a, b = pts[:-1], pts[1:]
    ts = np.linspace(0.0, 1.0, sub, endpoint=False).reshape(-1, 1, 1)
    seg = a[None, :, :] + (b - a)[None, :, :] * ts
    return np.concatenate([seg.reshape(-1, 3), pts[-1:]], axis=0)


def _visible(m):
    try:
        return max(m.get_fill_opacity(), m.get_stroke_opacity()) > 0.5
    except Exception:
        return True


def _bbox(m):
    c = m.get_center()
    return (c[0] - m.width / 2, c[1] - m.height / 2,
            c[0] + m.width / 2, c[1] + m.height / 2)


def _inter_area(a, b):
    dx = min(a[2], b[2]) - max(a[0], b[0])
    dy = min(a[3], b[3]) - max(a[1], b[1])
    return dx * dy if (dx > 0 and dy > 0) else 0.0


def _label(m):
    for attr in ("text", "tex_string"):
        v = getattr(m, attr, None)
        if isinstance(v, str) and v.strip():
            return v.strip().replace("\n", " / ")[:44]
    return type(m).__name__


class LayoutGuard:
    """ตรวจว่าข้อความทับกัน / หลุดขอบ — ใช้ร่วมกับ SafeScene"""

    #: ทับกันเกินสัดส่วนนี้ของกล่องที่เล็กกว่า = เตือน (เกณฑ์หลัก ไม่ขึ้นกับขนาด)
    OVERLAP_FRAC = 0.12
    #: พื้นล่างกันสัญญาณรบกวนเท่านั้น — ที่ 480p ค่า 0.005 ราว 14 พิกเซล
    #: (เคยตั้ง 0.03 แล้วพลาดเคสจริง: เลข "100" ทับ "rad/s" 25% แต่พื้นที่แค่ 0.026)
    OVERLAP_MIN_AREA = 0.005
    #: ระยะขอบที่ยอมให้เข้าใกล้ขอบเฟรมได้
    EDGE_PAD = 0.06

    def _guard_init(self):
        if not hasattr(self, "_seen"):
            self._seen = set()
            self._n_issues = 0

    #: ต้องมีจุดของเส้นตกในกรอบข้อความอย่างน้อยเท่านี้ ถึงนับว่าตัวอักษรทับกราฟิก
    GRAPHIC_HITS = 2
    #: หดกรอบข้อความเข้ามาเล็กน้อย กันเคสแค่ "เฉียด" ขอบ
    GRAPHIC_PAD = 0.035

    def _checkable(self):
        """คืน (ข้อความ, กราฟิก) ที่ตำแหน่งบนจอเชื่อถือได้
        2D = ทุกตัว | 3D = เฉพาะที่ตรึงกับเฟรม (พิกัดโลก 3D เทียบจอตรงๆ ไม่ได้)"""
        texts, graphics = [], []
        for m in self.mobjects:
            _collect(m, texts, graphics)

        fixed = getattr(self.camera, "fixed_in_frame_mobjects", None)
        if fixed:
            # manim ไม่มี pointer ชี้กลับหาแม่ จึงต้องกาง family ลงมาแทนการไล่ขึ้น
            fam = set()
            for f in fixed:
                for d in f.get_family():
                    fam.add(id(d))
            loose = [t for t in texts if id(t) not in fam]
            self._report_unfixed(loose)
            texts = [t for t in texts if id(t) in fam]
            graphics = [g for g in graphics if id(g) in fam]

        texts = [t for t in texts if _visible(t) and t.width > 0.01]
        graphics = [g for g in graphics if _visible(g)]
        return texts, graphics

    def _report_unfixed(self, loose):
        """ในฉาก 3D ข้อความที่ไม่ได้ตรึงกับเฟรมจะเอียง/บิดตามกล้องจนอ่านไม่ออก
        เกือบทุกครั้งคือลืมเรียก hud() — ถ้าตั้งใจให้อยู่ในโลก 3D ให้ประกาศด้วย
        world_text() เพื่อปิดคำเตือนเฉพาะตัวนั้น"""
        ok = getattr(self, "_world_ok", None) or set()
        for t in loose:
            if id(t) in ok or not _visible(t) or t.width <= 0.01:
                continue
            key = ("unfixed", id(t))
            if key in self._seen:
                continue
            self._seen.add(key)
            self._n_issues += 1
            print(f"[LAYOUT] ข้อความไม่ได้ตรึงกับเฟรม (จะเอียงตามกล้อง): "
                  f"'{_label(t)}'  <- ลืมเรียก hud() หรือเปล่า", flush=True)

    def _check_text_vs_graphics(self, texts, graphics, tag):
        """ตัวอักษรพาดทับเส้น/รูปทรงหรือไม่ — เช็คจากจุดบนเส้นจริง
        (ข้อความที่อยู่ 'ใน' กรอบ/วงกลมพอดี เส้นขอบจะไม่ตกในกรอบข้อความ จึงไม่ถูกเตือน)"""
        if not texts or not graphics:
            return
        boxes = []
        for t in texts:
            b = _bbox(t)
            p = self.GRAPHIC_PAD
            boxes.append((b[0] + p, b[1] + p, b[2] - p, b[3] - p))

        for g in graphics:
            try:
                pts = _dense_points(g)
            except Exception:
                continue
            if len(pts) == 0:
                continue
            x, y = pts[:, 0], pts[:, 1]
            for t, bx in zip(texts, boxes):
                if bx[2] <= bx[0] or bx[3] <= bx[1]:
                    continue
                inside = np.count_nonzero(
                    (x > bx[0]) & (x < bx[2]) & (y > bx[1]) & (y < bx[3]))
                if inside < self.GRAPHIC_HITS:
                    continue
                key = ("gfx", id(t), id(g))
                if key in self._seen:
                    continue
                self._seen.add(key)
                self._n_issues += 1
                print(f"[LAYOUT] {tag} ตัวอักษรพาดทับกราฟิก: "
                      f"'{_label(t)}'  ทับ  {type(g).__name__} "
                      f"({inside} จุดบนเส้นตกในกรอบข้อความ)", flush=True)

    def layout_check(self, tag=""):
        self._guard_init()
        items, graphics = self._checkable()
        self._check_text_vs_graphics(items, graphics, tag)

        for m in items:
            b = _bbox(m)
            out = []
            if b[0] < -X_MAX - self.EDGE_PAD:
                out.append("ซ้าย")
            if b[2] > X_MAX + self.EDGE_PAD:
                out.append("ขวา")
            if b[1] < -Y_MAX - self.EDGE_PAD:
                out.append("ล่าง")
            if b[3] > Y_MAX + self.EDGE_PAD:
                out.append("บน")
            if out:
                key = ("edge", id(m), tuple(out))
                if key not in self._seen:
                    self._seen.add(key)
                    self._n_issues += 1
                    print(f"[LAYOUT] {tag} หลุดขอบ{'/'.join(out)}: "
                          f"'{_label(m)}' bbox={tuple(round(v,2) for v in b)}",
                          flush=True)

        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                a, b = items[i], items[j]
                ba, bb = _bbox(a), _bbox(b)
                ov = _inter_area(ba, bb)
                if ov < self.OVERLAP_MIN_AREA:
                    continue
                small = min((ba[2] - ba[0]) * (ba[3] - ba[1]),
                            (bb[2] - bb[0]) * (bb[3] - bb[1]))
                if small <= 0 or ov / small < self.OVERLAP_FRAC:
                    continue
                key = ("ov", min(id(a), id(b)), max(id(a), id(b)))
                if key in self._seen:
                    continue
                self._seen.add(key)
                self._n_issues += 1
                print(f"[LAYOUT] {tag} ข้อความทับกัน {ov/small*100:.0f}%: "
                      f"'{_label(a)}'  <->  '{_label(b)}'", flush=True)

    def _timed_probe(self, every=0.25):
        """mobject จิ๋วที่คอยเรียก layout_check ระหว่างแอนิเมชันกำลังเล่น"""
        probe = Mobject()
        state = {"t": 0.0, "n": 0}

        def upd(_m, dt):
            state["t"] += dt
            if state["t"] >= every:
                state["t"] = 0.0
                state["n"] += 1
                self.layout_check(tag=f"[กลางภาพ #{state['n']}]")

        probe.add_updater(upd)
        return probe


class SafeScene(LayoutGuard, Scene):
    """Scene 2D ที่ตรวจ layout ให้อัตโนมัติทุกช่วงของแอนิเมชัน"""

    def play(self, *args, **kwargs):
        probe = self._timed_probe()
        self.add(probe)
        try:
            super().play(*args, **kwargs)
        finally:
            probe.clear_updaters()
            self.remove(probe)
        self.layout_check(tag="[จบท่า]")

    def wait(self, *args, **kwargs):
        super().wait(*args, **kwargs)
        self.layout_check(tag="[ค้างภาพ]")

    def tear_down(self):
        n = getattr(self, "_n_issues", 0)
        print(f"[LAYOUT] ===== สรุป {type(self).__name__}: "
              f"{'ผ่าน ไม่พบปัญหา' if n == 0 else f'พบ {n} จุดต้องแก้'} =====",
              flush=True)
        super().tear_down()


class SafeThreeDScene(LayoutGuard, ThreeDScene):
    """ThreeDScene ที่ตรวจ layout ของข้อความแบบ fixed-in-frame"""

    def play(self, *args, **kwargs):
        probe = self._timed_probe()
        self.add(probe)
        try:
            super().play(*args, **kwargs)
        finally:
            probe.clear_updaters()
            self.remove(probe)
        self.layout_check(tag="[จบท่า]")

    def wait(self, *args, **kwargs):
        super().wait(*args, **kwargs)
        self.layout_check(tag="[ค้างภาพ]")

    def hud(self, *mobs, show=False):
        """ขึ้นทะเบียนข้อความให้ตรึงกับจอ (ไม่หมุน/ไม่เอียงตามกล้อง)

        ค่าเริ่มต้นจะถอดออกจากฉากก่อน เพื่อให้เอาไป FadeIn เองได้โดยไม่กระพริบ
        — การขึ้นทะเบียนกับกล้องยังอยู่ ถึงจะถอดออกจากฉากชั่วคราวก็ตาม"""
        self.add_fixed_in_frame_mobjects(*mobs)
        if not show:
            self.remove(*mobs)
        return mobs[0] if len(mobs) == 1 else mobs

    def world_text(self, *mobs):
        """ประกาศว่าตั้งใจให้ข้อความนี้อยู่ในปริภูมิ 3D (เอียงตามกล้องได้)
        เช่นป้ายชื่อแกน — ใช้ปิดคำเตือน 'ไม่ได้ตรึงกับเฟรม' เฉพาะตัวที่ตั้งใจ"""
        if not hasattr(self, "_world_ok"):
            self._world_ok = set()
        for m in mobs:
            for d in m.get_family():
                self._world_ok.add(id(d))
        return mobs[0] if len(mobs) == 1 else mobs

    def tear_down(self):
        n = getattr(self, "_n_issues", 0)
        print(f"[LAYOUT] ===== สรุป {type(self).__name__}: "
              f"{'ผ่าน ไม่พบปัญหา' if n == 0 else f'พบ {n} จุดต้องแก้'} =====",
              flush=True)
        super().tear_down()


# ------------------------------------------------------------- utilities
def b_field(x_range, y_range, n=5, color=FIELD, opacity=0.55, z=0.0,
            direction=RIGHT, length=1.0):
    """แถวลูกศรแทนสนามแม่เหล็กสม่ำเสมอ"""
    arrows = VGroup()
    ys = np.linspace(y_range[0], y_range[1], n)
    for y in ys:
        a = Arrow([x_range[0], y, z], [x_range[0] + length, y, z],
                  color=color, buff=0, stroke_width=4,
                  max_tip_length_to_length_ratio=0.22)
        a.put_start_and_end_on(np.array([x_range[0], y, z]),
                               np.array([x_range[1], y, z]))
        a.set_opacity(opacity)
        arrows.add(a)
    return arrows


# ---- ลูกศร/เส้น ในปริภูมิ 3D -----------------------------------------------
# วัดจริงด้วย bench3d.py บนเครื่องนี้ (ลูกศรสนาม 9 ตัว, 1 วินาที, 480p25):
#     Arrow3D (ตาข่าย 3D จริง) = 186 วินาที
#     Arrow    (รูปแบนวางในปริภูมิ 3D) = 3 วินาที      -> เร็วกว่า ~62 เท่า
# ตัวเรนเดอร์ Cairo ฉาย polygon ของตาข่าย 3D ช้ามาก และถ้าอยู่ใน always_redraw
# จะสร้าง+ฉายใหม่ทุกเฟรม ใช้งานจริงไม่ได้เลย
# รูปแบนถูกกล้อง 3D ฉายให้ถูกมุมอยู่แล้ว ผู้เรียนอ่านทิศทางได้เหมือนกันทุกประการ
_SW_PER_THICK = 230.0


def arrow3(start, end, color, thickness=0.028, base_radius=None,
           height=0.30, opacity=1.0):
    """ลูกศรในปริภูมิ 3D (รูปแบน) — พารามิเตอร์เข้ากันได้กับ Arrow3D เดิม"""
    a = Arrow(np.asarray(start, dtype=float), np.asarray(end, dtype=float),
              color=color, buff=0,
              stroke_width=max(2.0, thickness * _SW_PER_THICK),
              tip_length=height, max_tip_length_to_length_ratio=0.5)
    if opacity != 1.0:
        a.set_opacity(opacity)
    return a


def line3(start, end, color, thickness=0.04):
    """เส้นตรงในปริภูมิ 3D (รูปแบน)"""
    return Line(np.asarray(start, dtype=float), np.asarray(end, dtype=float),
                color=color, stroke_width=max(2.0, thickness * _SW_PER_THICK))


def live_row(label_txt, unit_txt, get_value, anchor, decimals=1,
             num_color=WHITE, label_color=GRAYTXT, unit_color=GRAYTXT,
             label_size=21, num_size=30, unit_size=21, buff=0.20):
    """แถวตัวเลขที่เปลี่ยนค่าสด:  ป้าย | ตัวเลข | หน่วย

    เหตุที่ต้องมีตัวช่วยนี้: DecimalNumber กว้างขึ้นเมื่อจำนวนหลักเพิ่ม
    ถ้า arrange() ครั้งเดียวตอนสร้าง พอเลขโตจาก 0 เป็น 100 มันจะขยาย
    ออกไปทับหน่วยที่วางไว้ข้างๆ ตัวช่วยนี้จัดตำแหน่งใหม่ทุกเฟรมหลังตั้งค่า
    โดยตรึงป้ายไว้กับที่แล้วไล่วางตัวเลขและหน่วยต่อไปทางขวา
    """
    lbl = Text(label_txt, font_size=label_size, color=label_color)
    num = DecimalNumber(0, num_decimal_places=decimals,
                        font_size=num_size, color=num_color, mob_class=Text)
    unit = Text(unit_txt, font_size=unit_size, color=unit_color)
    lbl.move_to(np.asarray(anchor, dtype=float))

    def _place(m):
        m.set_value(get_value())
        m.next_to(lbl, RIGHT, buff=buff)
        unit.next_to(m, RIGHT, buff=buff * 0.85)

    _place(num)
    num.add_updater(_place)
    return VGroup(lbl, num, unit)


def rhr_note(size=19):
    """ป้ายเตือนกฎมือขวา (ใช้ซ้ำได้ทุกคลิป)"""
    return Text("กฎมือขวา:  ชี้นิ้ว I  →  งอเข้าหา B  →  นิ้วโป้ง = F",
                font_size=size, color=GRAYTXT)


# ---- เฟือง (gear train series) --------------------------------------------
def gear_shape(radius, teeth, color, tooth_depth_frac=0.16,
               tooth_width_frac=0.55, fill_opacity=1.0, stroke_width=2,
               hub_frac=0.16):
    """เฟืองแบบง่าย (ฟันสี่เหลี่ยมคางหมูรอบวงกลม pitch) — ใช้สอนแนวคิดการขบ/
    อัตราทด ไม่ใช่โปรไฟล์ involute จริง จำนวนฟันที่ส่งเข้ามาคือจำนวนฟันจริงที่วาด
    (นับด้วยตาได้ตรงกับโจทย์) ศูนย์กลางอยู่ที่ origin ก่อนค่อยย้ายด้วย move_to."""
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
    body = Polygon(*pts, color=color, fill_opacity=fill_opacity,
                    stroke_width=stroke_width, stroke_color=color)
    hub = Circle(radius=radius * hub_frac, color=BLACK,
                 fill_opacity=1, stroke_width=0)
    return VGroup(body, hub)


def spin(mob, rate):
    """หมุนต่อเนื่องรอบจุดศูนย์กลางปัจจุบันของตัวเอง — rate เป็น rad/s มีเครื่องหมาย
    (บวก = ทวนเข็มตามหลักคณิตศาสตร์มาตรฐานของ manim, ลบ = ตามเข็ม)"""
    mob.add_updater(lambda m, dt: m.rotate(rate * dt))
    return mob
