"""
ui/widgets/trump_widget.py — Kozir belgisi widget
O'yin ekranining burchagida kozir mast va kozir kartasini ko'rsatadi.
"""
from kivy.uix.widget    import Widget
from kivy.graphics      import Color, RoundedRectangle, Line, Ellipse
from kivy.core.text     import Label as CoreLabel
from core.constants     import COLORS, SUIT_SYMBOLS, CARD_RADIUS


class TrumpWidget(Widget):
    """
    Kozir belgisini ko'rsatuvchi kichik widget.
    - Yuqori qismda kozir mast belgisi (♠/♥/♦/♣)
    - Pastida 'KOZIR' yozuvi
    Luxury qoraygan shisha effekti (glassmorphism).
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._trump_suit:   str = ''
        self._trump_symbol: str = ''
        self._is_red:       bool = False
        self.size_hint = (None, None)
        self.size      = (56, 72)
        self.bind(pos=self._draw, size=self._draw)
        self._draw()

    # ─── Yangilash ────────────────────────────────────────────────────────────
    def set_trump(self, suit: str):
        """Kozir mastini o'rnatish va qayta chizish"""
        self._trump_suit   = suit
        self._trump_symbol = SUIT_SYMBOLS.get(suit, '')
        self._is_red       = suit in ('hearts', 'diamonds')
        self._draw()

    def clear(self):
        """Kozirni tozalash"""
        self._trump_suit   = ''
        self._trump_symbol = ''
        self._is_red       = False
        self._draw()

    # ─── Chizish ──────────────────────────────────────────────────────────────
    def _draw(self, *args):
        self.canvas.clear()
        if not self._trump_symbol:
            return

        x, y, w, h = self.x, self.y, self.width, self.height

        # Suit rang
        if self._is_red:
            suit_color = (*COLORS['red_suit'][:3], 1.0)
        else:
            suit_color = (0.92, 0.92, 0.95, 1.0)

        with self.canvas:
            # Soya
            Color(0, 0, 0, 0.35)
            RoundedRectangle(pos=(x + 2, y - 2), size=(w, h), radius=[CARD_RADIUS])

            # Fon — shaffof qoraygan yashil
            Color(0.06, 0.12, 0.08, 0.82)
            RoundedRectangle(pos=(x, y), size=(w, h), radius=[CARD_RADIUS])

            # Oltin chegara
            Color(*COLORS['gold'][:3], 0.7)
            Line(rounded_rectangle=[x + 1, y + 1, w - 2, h - 2, CARD_RADIUS], width=1.0)

            # Kozir mast belgisi (markazda, katta)
            Color(*suit_color)
            sym_tex = self._make_tex(self._trump_symbol, font_size=30, bold=True,
                                     color=suit_color)
            if sym_tex:
                sx = x + w / 2 - sym_tex.width / 2
                sy = y + h / 2 - sym_tex.height / 2 + 6
                from kivy.graphics import Rectangle
                Rectangle(texture=sym_tex, pos=(sx, sy), size=sym_tex.size)

            # 'KOZIR' yozuvi (pastda)
            label_color = (*COLORS['gold'][:3], 0.9)
            lbl_tex = self._make_tex('KOZIR', font_size=8, bold=True, color=label_color)
            if lbl_tex:
                lx = x + w / 2 - lbl_tex.width / 2
                ly = y + 4
                from kivy.graphics import Rectangle
                Color(*label_color)
                Rectangle(texture=lbl_tex, pos=(lx, ly), size=lbl_tex.size)

    def _make_tex(self, text: str, font_size: int = 14, bold: bool = False,
                  color=(1, 1, 1, 1), font_name: str = 'DejaVu'):
        """Matn teksturasini yaratish"""
        try:
            lbl = CoreLabel(
                text=text,
                font_name=font_name,
                font_size=font_size,
                bold=bold,
                color=color,
            )
            lbl.refresh()
            return lbl.texture
        except Exception:
            # Fallback: DejaVu topilmasa standart shrift
            try:
                lbl = CoreLabel(text=text, font_size=font_size, bold=bold, color=color)
                lbl.refresh()
                return lbl.texture
            except Exception:
                return None
