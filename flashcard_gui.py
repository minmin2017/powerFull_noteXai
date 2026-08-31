# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import math
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "flashcard-app", "data")
os.makedirs(DATA_DIR, exist_ok=True)

class FlashcardNativeApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PowerNote Flashcard Studio 🎴 (Native Windows)")
        self.geometry("960x720")
        self.minsize(800, 600)
        self.configure(fg_color="#0b0f19")

        # Bring window to front
        self.lift()
        self.attributes("-topmost", True)
        self.after(500, lambda: self.attributes("-topmost", False))
        self.focus_force()

        # State
        self.decks = {}
        self.current_deck_id = None
        self.cards = []
        self.card_index = 0
        self.is_flipped = False
        self.animating = False

        self.load_all_decks()
        self.setup_ui()
        self.bind_shortcuts()

        if self.decks:
            first_id = list(self.decks.keys())[0]
            self.select_deck(first_id)

    def load_all_decks(self):
        self.decks = {}
        if not os.path.exists(DATA_DIR):
            return
        for fname in os.listdir(DATA_DIR):
            if fname.endswith(".json"):
                p = os.path.join(DATA_DIR, fname)
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        deck_id = data.get("id", fname.replace(".json", ""))
                        self.decks[deck_id] = data
                except Exception as e:
                    print(f"Error loading {fname}: {e}")

    def save_current_deck(self):
        if not self.current_deck_id or self.current_deck_id not in self.decks:
            return
        p = os.path.join(DATA_DIR, f"{self.current_deck_id}.json")
        try:
            with open(p, "w", encoding="utf-8") as f:
                json.dump(self.decks[self.current_deck_id], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving deck: {e}")

    def setup_ui(self):
        # Header Frame
        self.header_frame = ctk.CTkFrame(self, fg_color="#121826", corner_radius=14, border_width=1, border_color="#1f293d")
        self.header_frame.pack(fill="x", padx=24, pady=(20, 12))

        # Title / Brand
        self.brand_label = ctk.CTkLabel(
            self.header_frame,
            text="🎴 Flashcard Studio",
            font=ctk.CTkFont(family="IBM Plex Sans Thai", size=20, weight="bold"),
            text_color="#38bdf8"
        )
        self.brand_label.pack(side="left", padx=16, pady=12)

        # Deck Option Menu
        deck_titles = [d.get("title", k) for k, d in self.decks.items()] or ["ไม่มีชุดการ์ด"]
        self.deck_menu = ctk.CTkOptionMenu(
            self.header_frame,
            values=deck_titles,
            command=self.on_deck_menu_select,
            font=ctk.CTkFont(family="IBM Plex Sans Thai", size=13),
            fg_color="#1e293b",
            button_color="#0284c7",
            button_hover_color="#0369a1",
            width=320
        )
        self.deck_menu.pack(side="left", padx=10, pady=12)

        # Progress / Due Badge
        self.badge_frame = ctk.CTkFrame(self.header_frame, fg_color="#1e293b", corner_radius=10)
        self.badge_frame.pack(side="right", padx=16, pady=12)

        self.due_label = ctk.CTkLabel(
            self.badge_frame,
            text="⏳ 0 ใบ",
            font=ctk.CTkFont(family="IBM Plex Sans Thai", size=13, weight="bold"),
            text_color="#fb923c"
        )
        self.due_label.pack(padx=12, pady=4)

        # Main Arena
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=24, pady=8)

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self.main_frame, fg_color="#1e293b", progress_color="#38bdf8", height=8, corner_radius=4)
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 6))
        self.progress_bar.set(0)

        self.progress_text = ctk.CTkLabel(
            self.main_frame,
            text="การ์ด 0 / 0",
            font=ctk.CTkFont(family="IBM Plex Sans Thai", size=12),
            text_color="#9ca3af"
        )
        self.progress_text.pack(anchor="e", padx=12, pady=(0, 10))

        # 3D Flip Card Canvas Container
        self.card_canvas = tk.Canvas(
            self.main_frame,
            bg="#0b0f19",
            highlightthickness=0,
            cursor="hand2"
        )
        self.card_canvas.pack(fill="both", expand=True, padx=10, pady=10)
        self.card_canvas.bind("<Configure>", lambda e: self.draw_card())
        self.card_canvas.bind("<Button-1>", lambda e: self.flip_card_animated())

        # Control Bar
        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.pack(fill="x", padx=24, pady=(6, 20))

        # Flip Action Button
        self.btn_flip = ctk.CTkButton(
            self.control_frame,
            text="พลิกดูเฉลย (กด Spacebar หรือคลิกที่การ์ด) 🔄",
            font=ctk.CTkFont(family="IBM Plex Sans Thai", size=15, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            height=46,
            corner_radius=12,
            command=self.flip_card_animated
        )
        self.btn_flip.pack(fill="x", pady=(0, 10))

        # SRS Rating Bar (Again, Hard, Good, Easy)
        self.srs_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        
        self.btn_again = ctk.CTkButton(
            self.srs_frame, text="Again [1]\nจําไม่ได้ (<1 วัน)", fg_color="#7f1d1d", hover_color="#991b1b",
            font=ctk.CTkFont(family="IBM Plex Sans Thai", size=12, weight="bold"), corner_radius=10, height=48,
            command=lambda: self.rate_card(1)
        )
        self.btn_again.pack(side="left", fill="x", expand=True, padx=4)

        self.btn_hard = ctk.CTkButton(
            self.srs_frame, text="Hard [2]\nยาก (1 วัน)", fg_color="#7c2d12", hover_color="#9a3412",
            font=ctk.CTkFont(family="IBM Plex Sans Thai", size=12, weight="bold"), corner_radius=10, height=48,
            command=lambda: self.rate_card(2)
        )
        self.btn_hard.pack(side="left", fill="x", expand=True, padx=4)

        self.btn_good = ctk.CTkButton(
            self.srs_frame, text="Good [3]\nพอได้ (3 วัน)", fg_color="#064e3b", hover_color="#065f46",
            font=ctk.CTkFont(family="IBM Plex Sans Thai", size=12, weight="bold"), corner_radius=10, height=48,
            command=lambda: self.rate_card(3)
        )
        self.btn_good.pack(side="left", fill="x", expand=True, padx=4)

        self.btn_easy = ctk.CTkButton(
            self.srs_frame, text="Easy [4]\nแม่นยํา (7 วัน)", fg_color="#1e3a8a", hover_color="#1e40af",
            font=ctk.CTkFont(family="IBM Plex Sans Thai", size=12, weight="bold"), corner_radius=10, height=48,
            command=lambda: self.rate_card(4)
        )
        self.btn_easy.pack(side="left", fill="x", expand=True, padx=4)

    def bind_shortcuts(self):
        self.bind("<space>", lambda e: self.flip_card_animated())
        self.bind("1", lambda e: self.rate_card(1) if self.is_flipped else None)
        self.bind("2", lambda e: self.rate_card(2) if self.is_flipped else None)
        self.bind("3", lambda e: self.rate_card(3) if self.is_flipped else None)
        self.bind("4", lambda e: self.rate_card(4) if self.is_flipped else None)

    def on_deck_menu_select(self, choice):
        for k, d in self.decks.items():
            if d.get("title") == choice:
                self.select_deck(k)
                break

    def select_deck(self, deck_id):
        self.current_deck_id = deck_id
        deck = self.decks.get(deck_id, {})
        self.cards = list(deck.get("cards", []))
        self.card_index = 0
        self.is_flipped = False
        self.srs_frame.pack_forget()
        self.btn_flip.pack(fill="x", pady=(0, 10))
        self.draw_card()

    def draw_card(self, scale_x=1.0):
        self.card_canvas.delete("all")
        w = self.card_canvas.winfo_width()
        h = self.card_canvas.winfo_height()
        if w < 50 or h < 50:
            return

        cx, cy = w / 2, h / 2
        card_w = min(w - 40, 740) * scale_x
        card_h = min(h - 30, 420)

        x1 = cx - card_w / 2
        x2 = cx + card_w / 2
        y1 = cy - card_h / 2
        y2 = cy + card_h / 2

        if not self.cards or self.card_index >= len(self.cards):
            self.draw_all_done(w, h)
            return

        card = self.cards[self.card_index]

        if not self.is_flipped:
            bg_color = "#121826"
            border_color = "#38bdf8"
            tag_text = "💡 โจทย์ / คำถาม (Question)"
            tag_color = "#38bdf8"
            body_text = card.get("front", "")
        else:
            bg_color = "#0f2027"
            border_color = "#34d399"
            tag_text = "✅ เฉลย & คำอธิบาย (Answer)"
            tag_color = "#34d399"
            body_text = card.get("back", "")

        r = 16 * scale_x
        pts = [
            x1 + r, y1, x2 - r, y1, x2, y1 + r, x2, y2 - r,
            x2 - r, y2, x1 + r, y2, x1, y2 - r, x1, y1 + r
        ]
        self.card_canvas.create_polygon(pts, fill=bg_color, outline=border_color, width=2, smooth=True)

        if scale_x > 0.3:
            self.card_canvas.create_text(
                cx, y1 + 32,
                text=tag_text,
                fill=tag_color,
                font=("IBM Plex Sans Thai", 13, "bold")
            )

            display_text = body_text.replace("$$", "\n").replace("$", "").replace("**", "")
            self.card_canvas.create_text(
                cx, cy,
                text=display_text,
                fill="#f3f4f6",
                font=("IBM Plex Sans Thai", 15),
                width=int(card_w - 60),
                justify="center"
            )

        total = len(self.cards)
        curr = self.card_index + 1
        pct = (self.card_index) / max(total, 1)
        self.progress_bar.set(pct)
        self.progress_text.configure(text=f"การ์ด {curr} / {total}")
        self.due_label.configure(text=f"⏳ {total - self.card_index} ใบ")

    def draw_all_done(self, w, h):
        self.progress_bar.set(1.0)
        self.progress_text.configure(text="ทบทวนครบทุกใบแล้ว! 🎉")
        self.due_label.configure(text="⏳ 0 ใบ")
        cx, cy = w / 2, h / 2
        self.card_canvas.create_text(cx, cy - 30, text="🏆", font=("Segoe UI Emoji", 48))
        self.card_canvas.create_text(cx, cy + 30, text="ยอดเยี่ยมมาก! ทบทวนครบทุกใบแล้ว", fill="#38bdf8", font=("IBM Plex Sans Thai", 18, "bold"))
        self.card_canvas.create_text(cx, cy + 65, text="สมองของคุณบันทึกความจำระยะยาวเรียบร้อยแล้ว", fill="#9ca3af", font=("IBM Plex Sans Thai", 13))

    def flip_card_animated(self):
        if self.animating or not self.cards or self.card_index >= len(self.cards):
            return
        self.animating = True

        steps = 10
        def step_contract(i):
            if i <= steps:
                progress = i / steps
                scale = math.cos(progress * math.pi / 2)
                self.draw_card(scale_x=max(scale, 0.05))
                self.after(16, lambda: step_contract(i + 1))
            else:
                self.is_flipped = not self.is_flipped
                if self.is_flipped:
                    self.btn_flip.pack_forget()
                    self.srs_frame.pack(fill="x", pady=(0, 10))
                else:
                    self.srs_frame.pack_forget()
                    self.btn_flip.pack(fill="x", pady=(0, 10))
                step_expand(0)

        def step_expand(j):
            if j <= steps:
                progress = j / steps
                scale = math.sin(progress * math.pi / 2)
                self.draw_card(scale_x=max(scale, 0.05))
                self.after(16, lambda: step_expand(j + 1))
            else:
                self.animating = False
                self.draw_card(scale_x=1.0)

        step_contract(0)

    def rate_card(self, rating):
        if self.card_index >= len(self.cards):
            return
        card = self.cards[self.card_index]

        interval = card.get("interval", 1)
        repetition = card.get("repetition", 0)
        efactor = card.get("efactor", 2.5)

        score = rating
        sm2_score = 1 if score == 1 else (3 if score == 2 else (4 if score == 3 else 5))

        if sm2_score >= 3:
            if repetition == 0:
                interval = 1
            elif repetition == 1:
                interval = 6
            else:
                interval = int(round(interval * efactor))
            repetition += 1
        else:
            repetition = 0
            interval = 1

        efactor = efactor + (0.1 - (5 - sm2_score) * (0.08 + (5 - sm2_score) * 0.02))
        if efactor < 1.3:
            efactor = 1.3

        card["interval"] = interval
        card["repetition"] = repetition
        card["efactor"] = round(efactor, 2)
        card["lastReviewed"] = int(time.time() * 1000)

        self.save_current_deck()

        self.card_index += 1
        self.is_flipped = False
        self.srs_frame.pack_forget()
        self.btn_flip.pack(fill="x", pady=(0, 10))
        self.draw_card()

if __name__ == "__main__":
    app = FlashcardNativeApp()
    app.mainloop()
