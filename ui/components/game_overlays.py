"""
ui/components/game_overlays.py — O'yin ekrani uchun alohida komponentlar
PauseOverlay, TimerRing, DeckBadge — game_screen.py dan ajratib chiqarildi.
"""
import math
from kivy.uix.floatlayout  import FloatLayout
from kivy.uix.boxlayout    import BoxLayout
from kivy.uix.widget       import Widget
from kivy.uix.label        import Label
from kivy.graphics          import (Color, Rectangle, RoundedRectangle,
                                    Line, Ellipse)
from kivy.core.text         import Label as CoreLabel

from core.constants         import COLORS, FONT_SIZES, SUIT_SYMBOLS


# ─────────────────────────────────────────────────────────────────────────────
# PauseOverlay
# ─────────────────────────────────────────────────────────────────────────────
class PauseOverlay(FloatLayout):
    """
    O'yinni pauza qiladigan qoʻshimcha qatlam.
    O'yin ekraniga FloatLayout sifatida qoʻshiladi.
    """
    def __init__(self, on_resume, on_menu, **kwargs):
        super().__init__(**kwargs)

        # Qorong'i shaffof fon
        with self.canvas.before:
            Color(0, 0, 0, 0.72)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        # Markaziy panel
        box = BoxLayout(
            orientation='vertical',
            size_hint=(None, None),
            size=(250, 210),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            spacing=16,
            padding=[20, 20],
        )

        # Oltin chegara
        with box.canvas.before:
            Color(*COLORS['surface'])
            self._box_bg = RoundedRectangle(pos=box.pos, size=box.size, radius=[16])
            Color(*COLORS['gold'][:3], 0.5)
            self._box_line = Line(
                rounded_rectangle=[box.x, box.y, box.width, box.height, 16],
                width=1.2
            )
        def _upd_box(*a):
            self._box_bg.pos   = box.pos
            self._box_bg.size  = box.size
            self._box_line.rounded_rectangle = [box.x, box.y, box.width, box.height, 16]
        box.bind(pos=_upd_box, size=_upd_box)

        # PAUZA yozuvi
        lbl = Label(
            text='⏸  PAUZA',
            font_size=FONT_SIZES['h2'],
            bold=True,
            color=COLORS['gold'],
            size_hint_y=None,
            height=44,
        )
        box.add_widget(lbl)

        # Tugmalar — ichki import (circular import oldini olish)
        from ui.components.luxury_button import LuxuryButton

        btn_resume = LuxuryButton(text='▶  DAVOM ETISH', style='primary')
        btn_resume.bind(on_release=lambda *a: on_resume())

        btn_menu = LuxuryButton(text='✕  MENYUGA CHIQISH', style='danger')
        btn_menu.bind(on_release=lambda *a: on_menu())

        box.add_widget(btn_resume)
        box.add_widget(btn_menu)
        self.add_widget(box)

    def _update_bg(self, *args):
        self._bg_rect.pos  = self.pos
        self._bg_rect.size = self.size


# ─────────────────────────────────────────────────────────────────────────────
# TimerRing
# ─────────────────────────────────────────────────────────────────────────────
class TimerRing(Widget):
    """
    Aylana taymer (arc-based).
    total soniya vaqt uchun progressni ko'rsatadi.
    Rang: yashil → sariq → qizil (vaqt tugashiga qarab).
    """

    def __init__(self, total: int = 45, **kwargs):
        super().__init__(**kwargs)
        self.total     = total
        self.remaining = total
        self.size_hint = (None, None)
        self.size      = (44, 44)
        self.bind(pos=self._draw, size=self._draw)
        self._draw()

    def update(self, remaining: int):
        """Qolgan vaqtni yangilash va qayta chizish"""
        self.remaining = max(0, remaining)
        self._draw()

    def _draw(self, *args):
        self.canvas.clear()

        cx = self.x + self.width  / 2
        cy = self.y + self.height / 2
        r  = min(self.width, self.height) / 2 - 4

        ratio = self.remaining / max(self.total, 1)

        # Rang interpolatsiyasi: 1.0→yashil, 0.5→sariq, 0.0→qizil
        if ratio > 0.5:
            t  = (ratio - 0.5) * 2
            rc = (1 - t) * 0.95
            gc = 0.55 + t * 0.4
            bc = 0.05
        else:
            t  = ratio * 2
            rc = 0.95
            gc = t * 0.55
            bc = 0.05

        with self.canvas:
            # Fon doira (xira)
            Color(0.08, 0.08, 0.08, 0.65)
            Ellipse(pos=(cx - r - 3, cy - r - 3), size=(r * 2 + 6, r * 2 + 6))

            # Kulrang aylana trek
            Color(0.3, 0.3, 0.3, 0.5)
            Line(circle=[cx, cy, r], width=3)

            # Progress arc
            if ratio > 0:
                Color(rc, gc, bc, 1.0)
                angle_start = 90
                sweep       = ratio * 360
                steps       = max(int(sweep / 4), 3)
                points      = []
                for i in range(steps + 1):
                    a = math.radians(angle_start - sweep * i / steps)
                    points += [cx + r * math.cos(a), cy + r * math.sin(a)]
                if len(points) >= 4:
                    Line(points=points, width=3.5, cap='round')

            # Markaziy son
            Color(1, 1, 1, 0.95)
            tex = self._make_num_tex(str(self.remaining))
            if tex:
                Rectangle(
                    texture=tex,
                    pos=(cx - tex.width / 2, cy - tex.height / 2),
                    size=tex.size,
                )

    def _make_num_tex(self, text: str):
        try:
            lbl = CoreLabel(text=text, font_size=16, bold=True, color=(1, 1, 1, 1))
            lbl.refresh()
            return lbl.texture
        except Exception:
            return None


# ─────────────────────────────────────────────────────────────────────────────
# DeckBadge
# ─────────────────────────────────────────────────────────────────────────────
class DeckBadge(Widget):
    """
    Qo'da qolgan kartalar soni + kozir belgisi.
    O'yin stolining burchagida joylashadi.
    Luxury xira shisha effekti.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._count       = 36
        self._trump_sym   = ''
        self._trump_color = (1, 1, 1, 1)
        self.size_hint    = (None, None)
        self.size         = (64, 60)
        self.bind(pos=self._draw, size=self._draw)
        self._draw()

    def update(self, count: int, trump_sym: str, is_red: bool):
        """Ma'lumotlarni yangilash va qayta chizish"""
        self._count = count
        self._trump_sym = trump_sym
        if is_red:
            self._trump_color = (*COLORS['red_suit'][:3], 1.0)
        else:
            self._trump_color = (0.12, 0.12, 0.22, 1.0)
        self._draw()

    def _draw(self, *args):
        self.canvas.clear()
        x, y, w, h = self.x, self.y, self.width, self.height

        with self.canvas:
            # Soya
            Color(0, 0, 0, 0.22)
            Ellipse(pos=(x + 1, y - 1), size=(w, h))

            # Asosiy fon
            Color(0.08, 0.14, 0.10, 0.78)
            Ellipse(pos=(x, y), size=(w, h))

            # Oltin chegara
            Color(*COLORS['gold'][:3], 0.45)
            Line(ellipse=[x + 1, y + 1, w - 2, h - 2], width=1.0)

            # Karta soni (yuqorida)
            Color(1, 1, 1, 0.95)
            cnt_tex = self._make_tex(
                str(self._count), font_size=16, bold=True, color=(1, 1, 1, 1)
            )
            if cnt_tex:
                Rectangle(
                    texture=cnt_tex,
                    pos=(x + w / 2 - cnt_tex.width / 2, y + h / 2 + 2),
                    size=cnt_tex.size,
                )

            # Kozir belgisi (pastda, kattaroq)
            if self._trump_sym:
                Color(*self._trump_color)
                trump_tex = self._make_tex(
                    self._trump_sym, font_size=24, bold=True,
                    color=self._trump_color, font='DejaVu'
                )
                if trump_tex:
                    Rectangle(
                        texture=trump_tex,
                        pos=(x + w / 2 - trump_tex.width / 2, y + 3),
                        size=trump_tex.size,
                    )

    def _make_tex(self, text: str, font_size: int = 14, bold: bool = False,
                  color=(1, 1, 1, 1), font: str = 'Roboto'):
        try:
            lbl = CoreLabel(
                text=text, font_name=font, font_size=font_size,
                bold=bold, color=color,
            )
            lbl.refresh()
            return lbl.texture
        except Exception:
            try:
                lbl = CoreLabel(text=text, font_size=font_size, bold=bold, color=color)
                lbl.refresh()
                return lbl.texture
            except Exception:
                return None
