"""
ui/widgets/deck_widget.py — Qo'da Widjeti
Qo'da va kozir kartasini ko'rsatadi.
"""
import os
from kivy.uix.widget  import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label   import Label
from kivy.graphics    import Color, RoundedRectangle, Line, Rectangle
from kivy.properties  import NumericProperty, StringProperty
from core.constants   import COLORS, CARDS_DIR, CARD_W, CARD_H, CARD_RADIUS
from core.constants   import SUIT_SYMBOLS, FONT_SIZES
from kivy.core.text   import Label as CoreLabel


class DeckWidget(Widget):
    """
    Qo'da widgeti:
    - Qo'da rasmi (yopiq kartalar uyumi)
    - Qolgan kartalar soni
    - Kozir kartasi ochiq ko'rsatiladi
    """
    remaining = NumericProperty(0)
    trump_suit = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size      = (CARD_W * 2 + 20, CARD_H + 20)
        self.bind(pos=self._redraw, size=self._redraw,
                  remaining=self._redraw, trump_suit=self._redraw)

    def set_state(self, remaining: int, trump_suit: str):
        self.remaining  = remaining
        self.trump_suit = trump_suit

    def _redraw(self, *args):
        self.canvas.clear()
        if self.width == 0:
            return

        with self.canvas:
            # ─── Qo'da ────────────────────────────────────────────────────
            # Bir necha qavatli ko'rinish (uyum effekti)
            for offset in range(3, 0, -1):
                alpha = 0.3 + offset * 0.15
                Color(*COLORS['surface'][:3], alpha)
                RoundedRectangle(
                    pos=(self.x + offset, self.y + offset),
                    size=(CARD_W, CARD_H),
                    radius=[CARD_RADIUS]
                )

            # Asosiy karta
            Color(*COLORS['surface'])
            RoundedRectangle(pos=self.pos, size=(CARD_W, CARD_H),
                             radius=[CARD_RADIUS])

            # Oltin chegara
            Color(*COLORS['gold'][:3], 0.9)
            Line(rounded_rectangle=[self.x, self.y, CARD_W, CARD_H,
                                     CARD_RADIUS], width=1.2)

            # Ko'nda qolgan soni
            lbl_rem = CoreLabel(text=str(self.remaining), font_size=32, bold=True, color=(*COLORS['gold'][:3], 1.0))
            lbl_rem.refresh()
            if lbl_rem.texture:
                Rectangle(texture=lbl_rem.texture,
                          pos=(self.x + (CARD_W - lbl_rem.texture.width)/2, 
                               self.y + (CARD_H - lbl_rem.texture.height)/2),
                          size=lbl_rem.texture.size)

            # ─── Kozir kartasi ────────────────────────────────────────────
            if self.trump_suit:
                trump_x = self.x + CARD_W + 8
                is_red  = self.trump_suit in ('hearts', 'diamonds')

                # Karta foni
                Color(*COLORS['card_face'])
                RoundedRectangle(pos=(trump_x, self.y),
                                 size=(CARD_W, CARD_H),
                                 radius=[CARD_RADIUS])
                # Oltin chegara
                Color(*COLORS['gold'])
                Line(rounded_rectangle=[trump_x, self.y, CARD_W, CARD_H,
                                         CARD_RADIUS], width=1.5)

                # Suit symbol marker
                suit_color = COLORS['red_suit'] if is_red else COLORS['black_suit']
                sym_str = SUIT_SYMBOLS.get(self.trump_suit, '')
                lbl_suit = CoreLabel(text=sym_str, font_name='DejaVu', font_size=42, color=(*suit_color[:3], 1.0))
                lbl_suit.refresh()
                if lbl_suit.texture:
                    Rectangle(texture=lbl_suit.texture,
                              pos=(trump_x + (CARD_W - lbl_suit.texture.width)/2,
                                   self.y + (CARD_H - lbl_suit.texture.height)/2),
                              size=lbl_suit.texture.size)


class TrumpWidget(Widget):
    """
    Kozir belgisi — o'yin davomida o'ng pastda ko'rsatiladi.
    Kozir mast belgisi + rangi.
    """
    trump_suit = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size      = (56, 56)
        self.bind(pos=self._redraw, size=self._redraw,
                  trump_suit=self._redraw)

        self._symbol_label = Label(
            text      = '',
            font_name = 'DejaVu',
            font_size = 28,
            halign    = 'center',
            valign    = 'middle',
        )
        self.add_widget(self._symbol_label)

    def set_trump(self, suit: str):
        self.trump_suit = suit
        self._symbol_label.text  = SUIT_SYMBOLS.get(suit, '')
        is_red = suit in ('hearts', 'diamonds')
        self._symbol_label.color = (
            *COLORS['red_suit'][:3], 1.0
        ) if is_red else (*COLORS['black_suit'][:3], 1.0)

    def _redraw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*COLORS['gold'][:3], 0.25)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
            Color(*COLORS['gold'])
            Line(rounded_rectangle=[self.x, self.y,
                                     self.width, self.height, 12], width=1.2)

        self._symbol_label.pos  = self.pos
        self._symbol_label.size = self.size
        self._symbol_label.text_size = self.size
