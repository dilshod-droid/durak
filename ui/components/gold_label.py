"""
ui/components/gold_label.py — Oltin Matn Komponenti
Cinzel shrift bilan premium ko'rinishdagi label.
"""
from kivy.uix.label       import Label
from kivy.properties      import StringProperty, NumericProperty
from kivy.graphics        import Color, Rectangle
from core.constants       import COLORS, FONT_SIZES


class GoldLabel(Label):
    """
    Oltin rangli sarlavha.
    display_style: 'gold' | 'primary' | 'secondary' | 'muted'
    """
    display_style = StringProperty('gold')

    _STYLE_COLORS = {
        'gold':      COLORS['gold'],
        'primary':   COLORS['text_primary'],
        'secondary': COLORS['text_secondary'],
        'muted':     COLORS['text_muted'],
        'success':   COLORS['success'],
        'danger':    COLORS['danger'],
    }

    def __init__(self, **kwargs):
        kwargs.setdefault('font_size',   FONT_SIZES['h2'])
        kwargs.setdefault('halign',      'center')
        kwargs.setdefault('valign',      'middle')
        kwargs.setdefault('color',       COLORS['gold'])
        super().__init__(**kwargs)
        self.bind(display_style=self._update_color)

    def _update_color(self, *args):
        self.color = self._STYLE_COLORS.get(self.display_style, COLORS['gold'])


class BadgeLabel(Label):
    """
    Oltin badge — raqam yoki qisqa matn uchun.
    O'yinda: karta soni, qo'da soni va h.k.
    """
    def __init__(self, **kwargs):
        kwargs.setdefault('font_size',  FONT_SIZES['small'])
        kwargs.setdefault('size_hint',  (None, None))
        kwargs.setdefault('size',       (36, 24))
        kwargs.setdefault('color',      COLORS['background'])
        super().__init__(**kwargs)
        self.bind(pos=self._redraw, size=self._redraw, text=self._redraw)

    def _redraw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*COLORS['gold'])
            from kivy.graphics import RoundedRectangle
            RoundedRectangle(pos=self.pos, size=self.size, radius=[8])
