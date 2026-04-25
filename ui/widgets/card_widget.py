"""
ui/widgets/card_widget.py — Karta Widjeti
Luxury dizayn: chiroyli orqa tomon, aniq yuz, drag & drop, glow effekti.
"""
import os
from kivy.uix.widget      import Widget
from kivy.graphics        import (Color, RoundedRectangle, Line,
                                   Rectangle, Ellipse, SmoothLine)
from kivy.animation       import Animation
from kivy.properties      import ObjectProperty, BooleanProperty
from kivy.clock           import Clock
from core.constants       import (COLORS, CARD_W, CARD_H, CARD_RADIUS,
                                   CARDS_DIR, VALUE_NAMES, SUIT_SYMBOLS)


BACK_IMG  = os.path.join(CARDS_DIR, 'card_back.png')


def _core_label(text, font_size, bold=False, color=(1,1,1,1), font_name='DejaVu'):
    from kivy.core.text import Label as CL
    lbl = CL(text=text, font_name=font_name, font_size=font_size,
              bold=bold, color=color, halign='center')
    lbl.refresh()
    return lbl.texture


class CardWidget(Widget):
    """
    Bitta kartani ko'rsatuvchi widget.
    - face_up=True  → karta rasmi (yuzi)
    - face_up=False → luxury orqa tomon
    - selected       → yuqoriga ko'tariladi + oltin glow
    - draggable      → drag & drop
    - hint_glow      → yashil glow (tashlash mumkin bo'lgan joy)
    """
    card      = ObjectProperty(None, allownone=True)
    selected  = BooleanProperty(False)
    face_up   = BooleanProperty(True)
    draggable = BooleanProperty(True)
    glow      = BooleanProperty(False)
    hint_glow = BooleanProperty(False)   # Yashil "bu yerga tashlang" ko'rsatgich
    is_manually_moved = BooleanProperty(False)

    def __init__(self, card=None, face_up=True, draggable=True, **kwargs):
        super().__init__(**kwargs)
        self.card      = card
        self.face_up   = face_up
        self.draggable = draggable

        self.size_hint = (None, None)
        self.size      = (CARD_W, CARD_H)

        self._selected    = False
        self._drag_touch  = None
        self._orig_pos    = None
        self._base_y      = None    # Home Y (selection animatsiyasi uchun)

        self.bind(
            pos       = self._redraw,
            size      = self._redraw,
            card      = self._redraw,
            face_up   = self._redraw,
            selected  = self._on_select_change,
            glow      = self._redraw,
            hint_glow = self._redraw,
        )
        self._redraw()

    # ─── Chizish ──────────────────────────────────────────────────────────────
    def _redraw(self, *args):
        self.canvas.clear()
        with self.canvas:
            if not self.face_up or self.card is None:
                self._draw_back()
            else:
                self._draw_face()

    def _draw_back(self):
        """Luxury orqa tomon — qoʻyuq yashil + oltin naqsh"""
        x, y, w, h = self.x, self.y, self.width, self.height
        r = CARD_RADIUS

        # Soya
        Color(0, 0, 0, 0.35)
        RoundedRectangle(pos=(x + 3, y - 3), size=(w, h), radius=[r])

        # Asosiy fon (koʻyuq zaytun)
        Color(0.07, 0.20, 0.12, 1)
        RoundedRectangle(pos=(x, y), size=(w, h), radius=[r])

        # Ichki ramka
        Color(*COLORS['gold'][:3], 0.9)
        Line(rounded_rectangle=[x+2, y+2, w-4, h-4, r-1], width=1.1)

        # Tashqi ramka
        Color(*COLORS['gold'][:3], 0.5)
        Line(rounded_rectangle=[x, y, w, h, r], width=0.8)

        # Diagonal naqsh chiziqlari
        Color(*COLORS['gold'][:3], 0.08)
        step = 14
        for i in range(-h, w + h, step):
            x1 = x + max(0, i)
            y1 = y if i >= 0 else y + min(-i, h)
            x2 = x + min(w, i + h)
            y2 = y2 = y + h if i + h <= w else y + h - (i + h - w)
            Line(points=[x1, y1, x2, y2], width=0.8)

        # Markaziy oltin doira
        cx, cy = x + w / 2, y + h / 2
        Color(*COLORS['gold'][:3], 0.25)
        Ellipse(pos=(cx - 22, cy - 22), size=(44, 44))
        Color(*COLORS['gold'][:3], 0.7)
        Line(circle=(cx, cy, 22), width=1.2)

        # "D" harfi
        Color(*COLORS['gold'][:3], 1.0)
        tex = _core_label('D', font_size=22, bold=True, color=(*COLORS['gold'][:3], 1))
        if tex:
            Rectangle(texture=tex,
                      pos=(cx - tex.width/2, cy - tex.height/2),
                      size=tex.size)

    def _draw_face(self):
        """Karta yuzi — aniq qiymat va mast belgisi"""
        card = self.card
        x, y, w, h = self.x, self.y, self.width, self.height
        r = CARD_RADIUS
        is_red = card.suit in ('hearts', 'diamonds')
        tc = COLORS['red_suit'] if is_red else (0.10, 0.10, 0.18, 1)

        # Soya
        Color(0, 0, 0, 0.3)
        RoundedRectangle(pos=(x + 3, y - 3), size=(w, h), radius=[r])

        # Oq fon
        Color(0.98, 0.96, 0.93, 1)
        RoundedRectangle(pos=(x, y), size=(w, h), radius=[r])

        # Glow/Hint ko'rsatgich
        if self.hint_glow:
            Color(0.2, 0.9, 0.3, 0.8)
            Line(rounded_rectangle=[x-1, y-1, w+2, h+2, r+1], width=2.2)
        elif self.glow or self.selected:
            Color(*COLORS['gold_light'][:3], 0.95)
            Line(rounded_rectangle=[x-1, y-1, w+2, h+2, r+1], width=2.0)
        else:
            Color(*COLORS['card_border'][:3], 0.6)
            Line(rounded_rectangle=[x, y, w, h, r], width=0.9)

        val_str = VALUE_NAMES.get(card.value, str(card.value))
        sym_str = SUIT_SYMBOLS.get(card.suit, '')

        # Yuqori chap burchak
        Color(*tc[:3], 1)
        tex_val = _core_label(val_str, font_size=14, bold=True,
                               color=(*tc[:3], 1), font_name='DejaVu')
        if tex_val:
            Rectangle(texture=tex_val,
                      pos=(x + 5, y + h - tex_val.height - 4),
                      size=tex_val.size)

        tex_sym_sm = _core_label(sym_str, font_size=13, color=(*tc[:3], 1),
                                  font_name='DejaVu')
        if tex_sym_sm:
            Rectangle(texture=tex_sym_sm,
                      pos=(x + 5, y + h - tex_val.height - tex_sym_sm.height - 6),
                      size=tex_sym_sm.size)

        # Pastki oʻng burchak (teskari)
        if tex_val:
            Rectangle(texture=tex_val,
                      pos=(x + w - tex_val.width - 5,
                           y + 4 + (tex_sym_sm.height if tex_sym_sm else 0)),
                      size=tex_val.size)
        if tex_sym_sm:
            Rectangle(texture=tex_sym_sm,
                      pos=(x + w - tex_sym_sm.width - 5, y + 4),
                      size=tex_sym_sm.size)

        # Markaziy katta mast belgisi
        tex_big = _core_label(sym_str, font_size=46, color=(*tc[:3], 0.88),
                               font_name='DejaVu')
        if tex_big:
            Rectangle(texture=tex_big,
                      pos=(x + w/2 - tex_big.width/2,
                           y + h/2 - tex_big.height/2),
                      size=tex_big.size)

    # ─── Tanlash ──────────────────────────────────────────────────────────────
    def _on_select_change(self, *args):
        if self._base_y is None:
            self._base_y = self.y
        target_y = self._base_y + (16 if self.selected else 0)
        Animation(y=target_y, duration=0.18, t='out_sine').start(self)
        self.glow = self.selected
        self._redraw()

    def select(self):
        if self._base_y is None:
            self._base_y = self.y
        self.selected = True

    def deselect(self):
        self.selected = False

    def set_base_y(self, y):
        """HandWidget pozitsiyalanishidan keyin base_y ni yangilash"""
        self._base_y = y
        if not self.selected:
            self.y = y

    # ─── Hint ─────────────────────────────────────────────────────────────────
    def set_hint(self, active: bool):
        self.hint_glow = active
        self._redraw()

    # ─── Touch (tap va drag) ──────────────────────────────────────────────────
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        touch.grab(self)
        self._drag_touch  = touch
        self._orig_pos    = tuple(self.pos)
        if self._base_y is None:
            self._base_y = self.y
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self or not self.draggable:
            return False
        self.center = touch.pos
        # Z-tartib: drag vaqtida boshqalar ustida bo'lishini ta'minlash
        p = self.parent
        if p and p.children[0] is not self:
            p.remove_widget(self)
            p.add_widget(self)
        self.is_manually_moved = True
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return False
        touch.ungrab(self)

        if self.draggable and self._orig_pos:
            dx = abs(touch.pos[0] - touch.opos[0])
            dy = abs(touch.pos[1] - touch.opos[1])

            if dx < 10 and dy < 10:
                # Tap — tanlash/bekor
                if self.parent and hasattr(self.parent, '_on_card_touch'):
                    self.parent._on_card_touch(self, touch)
        elif not self.draggable:
            # Non-draggable tap
            if self.parent and hasattr(self.parent, '_on_card_touch'):
                self.parent._on_card_touch(self, touch)
        
        # O'zboshimcha harakatlantirish imkoniyati (xohlagan joyga qo'yish)
        # return_home chaqirilmaydi (foydalanuvchi xohishi)
        
        self._drag_touch = None
        return True

    def _return_home(self):
        if self._orig_pos:
            Animation(
                x=self._orig_pos[0], y=self._orig_pos[1],
                duration=0.22, t='out_cubic'
            ).start(self)

    # ─── Animatsiyalar ────────────────────────────────────────────────────────
    def animate_deal(self, from_pos, delay=0.0):
        orig_pos = tuple(self.pos)
        self.pos = from_pos
        self.opacity = 0

        def _start(dt):
            anim = (
                Animation(opacity=1, duration=0.12) &
                Animation(x=orig_pos[0], y=orig_pos[1],
                          duration=0.28, t='out_cubic')
            )
            anim.start(self)

        Clock.schedule_once(_start, delay)

    def animate_invalid(self):
        ox = self.x
        anim = (
            Animation(x=ox - 9, duration=0.04) +
            Animation(x=ox + 9, duration=0.04) +
            Animation(x=ox - 5, duration=0.04) +
            Animation(x=ox + 5, duration=0.04) +
            Animation(x=ox,     duration=0.04)
        )
        anim.start(self)

    def __repr__(self):
        return f"CardWidget({self.card}, face_up={self.face_up})"
