"""
ui/components/animated_bg.py — Animatsiyali Fon
Dark luxury stol ko'rinishi + aylanuvchi kartalar effekti.
"""
import math
import random

from kivy.uix.widget   import Widget
from kivy.graphics     import (Color, Rectangle, Ellipse,
                                RoundedRectangle, Line, Rotate,
                                PushMatrix, PopMatrix, Translate)
from kivy.clock        import Clock
from kivy.animation    import Animation
from core.constants    import COLORS


class AnimatedBackground(Widget):
    """
    Bosh menu uchun animatsiyali fon.
    - To'q yashil stol gradiyenti
    - Aylaniuvchi semitransparent karta siluetlari
    - Oltin particle effektlari
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._particles  = []
        self._angle      = 0.0
        self._time       = 0.0
        self._cards_data = self._init_cards()

        self.bind(pos=self._redraw, size=self._redraw)
        self._clock_ev = None
        self.start()

    def start(self):
        if not self._clock_ev:
            self._clock_ev = Clock.schedule_interval(self._update, 1 / 30)   # 30 FPS

    def stop(self):
        if self._clock_ev:
            self._clock_ev.cancel()
            self._clock_ev = None

    def _init_cards(self):
        """Orqa fon karta siluetlari uchun boshlang'ich holatlar"""
        cards = []
        for i in range(8):
            cards.append({
                'angle':    random.uniform(0, 360),
                'speed':    random.uniform(0.3, 0.7),
                'scale':    random.uniform(0.6, 1.2),
                'alpha':    random.uniform(0.04, 0.10),
                'x_off':    random.uniform(-0.3, 0.3),
                'y_off':    random.uniform(-0.3, 0.3),
            })
        return cards

    def _update(self, dt):
        self._time += dt
        for card in self._cards_data:
            card['angle'] += card['speed'] * dt * 20
        self._redraw()

    def _redraw(self, *args):
        self.canvas.clear()
        if self.width == 0 or self.height == 0:
            return

        cx = self.x + self.width  / 2
        cy = self.y + self.height / 2

        with self.canvas:
            # ─── Asosiy fon ───────────────────────────────────────────────
            Color(*COLORS['background'])
            Rectangle(pos=self.pos, size=self.size)

            # ─── Radial gradient effekti (konsentrik doiralar) ────────────
            steps = 8
            for i in range(steps, 0, -1):
                t     = i / steps
                alpha = 0.12 * t
                r     = min(self.width, self.height) * 0.7 * t
                Color(0.05, 0.31, 0.16, alpha)
                Ellipse(
                    pos=(cx - r, cy - r),
                    size=(r * 2, r * 2)
                )

            # ─── Aylanuvchan karta siluetlari ─────────────────────────────
            for card in self._cards_data:
                angle_rad = math.radians(card['angle'])
                w_off = self.width  * card['x_off']
                h_off = self.height * card['y_off']

                card_w = 60 * card['scale']
                card_h = 86 * card['scale']

                px = cx + w_off - card_w / 2
                py = cy + h_off - card_h / 2

                PushMatrix()
                Translate(cx + w_off, cy + h_off)
                Rotate(angle=card['angle'], axis=(0, 0, 1), origin=(0, 0))
                Translate(-card_w / 2, -card_h / 2)

                Color(*COLORS['gold'][:3], card['alpha'])
                RoundedRectangle(
                    pos   = (0, 0),
                    size  = (card_w, card_h),
                    radius= [6]
                )
                # Ichki chegara
                Color(*COLORS['gold'][:3], card['alpha'] * 0.5)
                Line(rounded_rectangle=[2, 2, card_w - 4, card_h - 4, 5], width=0.8)

                PopMatrix()

            # ─── Taxtaning stol chizig'i ───────────────────────────────────
            Color(*COLORS['gold'][:3], 0.08)
            Line(
                circle=(cx, cy, min(self.width, self.height) * 0.42),
                width=1.5
            )

    def on_size(self, *args):
        self._redraw()


class TableBackground(Widget):
    """
    O'yin ekrani uchun stol foni.
    Dark green baize + oltin chegara.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *args):
        self.canvas.clear()
        if self.width == 0:
            return

        with self.canvas:
            # Stol foni
            Color(*COLORS['table'])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[16])

            # Oltin chegara
            Color(*COLORS['gold'][:3], 0.6)
            Line(rounded_rectangle=[self.x, self.y,
                                     self.width, self.height, 16],
                 width=1.5)

            # Ichki yoritish effekti
            Color(1, 1, 1, 0.03)
            RoundedRectangle(
                pos=(self.x + 4, self.y + self.height - 20),
                size=(self.width - 8, 18),
                radius=[12, 12, 0, 0]
            )
