"""
ui/widgets/card_widget.py — Karta Widjeti
Karta tasvirini ko'rsatadi, tanlash va drag & drop imkoniyati.
"""
import os
from kivy.uix.widget      import Widget
from kivy.uix.image       import Image as KivyImage
from kivy.graphics        import (Color, RoundedRectangle, Line,
                                   Rectangle, Ellipse)
from kivy.animation       import Animation
from kivy.properties      import ObjectProperty, BooleanProperty, NumericProperty
from core.constants       import (COLORS, CARD_W, CARD_H, CARD_RADIUS,
                                   CARDS_DIR)


BACK_IMG  = os.path.join(CARDS_DIR, 'card_back.png')
EMPTY_IMG = os.path.join(CARDS_DIR, 'empty_slot.png')


class CardWidget(Widget):
    """
    Bitta kartani ko'rsatuvchi widget.
    - face_up=True  → karta rasmi
    - face_up=False → yopiq orqa tomon
    - selected       → yuqoriga ko'tariladi + glow
    - draggable      → drag & drop imkoniyati
    """
    card      = ObjectProperty(None, allownone=True)
    selected  = BooleanProperty(False)
    face_up   = BooleanProperty(True)
    draggable = BooleanProperty(True)
    glow      = BooleanProperty(False)

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
        self._orig_parent = None
        self._img_widget  = None

        self._setup_image()

        self.bind(
            pos      = self._update_image_pos,
            card     = self._on_card_change,
            face_up  = self._on_card_change,
            selected = self._on_select,
        )

    # ─── Rasm ─────────────────────────────────────────────────────────────────
    def _setup_image(self):
        self._draw_canvas_card()
        if self._img_widget:
            try:
                self.remove_widget(self._img_widget)
            except Exception:
                pass

        img_path = self._get_image_path()

        if img_path and os.path.exists(img_path):
            self._img_widget = KivyImage(
                source   = img_path,
                pos      = self.pos,
                size     = self.size,
                fit_mode = 'contain',
            )
            self.add_widget(self._img_widget)
        else:
            # Rasm yo'q — canvas orqali chizamiz
            self._draw_canvas_card()

    def _get_image_path(self) -> str:
        return ''

    def _on_card_change(self, *args):
        self._setup_image()

    def _update_image_pos(self, *args):
        if self._img_widget:
            self._img_widget.pos  = self.pos
            self._img_widget.size = self.size

    def _draw_canvas_card(self, *args):
        """Card ni faqat canvasda yuqori sifatda chizish"""
        self.canvas.clear()
        with self.canvas:
            if not self.face_up or self.card is None:
                self._draw_back()
            else:
                self._draw_face()

    def _draw_back(self):
        """Yopiq karta orqa tomoni"""
        Color(*COLORS['surface'])
        RoundedRectangle(pos=self.pos, size=self.size, radius=[CARD_RADIUS])
        Color(*COLORS['gold'][:3], 0.8)
        Line(rounded_rectangle=[self.x, self.y, self.width, self.height,
                                 CARD_RADIUS], width=1.2)
        # Ko'ndalang naqsh (Oltin chiziqlar)
        Color(*COLORS['gold'][:3], 0.25)
        step = 16
        for i in range(0, int(self.width), step):
            Line(points=[self.x + i, self.y,
                         self.x + i, self.y + self.height], width=1.0)
            Line(points=[self.x, self.y + i,
                         self.x + self.width, self.y + i], width=1.0)
        
        # O'rta logo
        Color(*COLORS['surface_alt'][:3], 0.9)
        Ellipse(pos=(self.center_x - 18, self.center_y - 18), size=(36, 36))
        Color(*COLORS['gold'][:3], 1.0)
        Line(circle=(self.center_x, self.center_y, 18), width=1.2)
        
        from kivy.core.text import Label as CoreLabel
        lbl = CoreLabel(text='D', font_size=20, bold=True, color=COLORS['gold'])
        lbl.refresh()
        tex = lbl.texture
        if tex:
            Rectangle(texture=tex,
                      pos=(self.center_x - tex.width/2, self.center_y - tex.height/2),
                      size=tex.size)

    def _draw_face(self):
        """Karta yuzi (rasm bo'lmasa)"""
        card = self.card
        is_red = card.suit in ('hearts', 'diamonds')

        # Fon
        Color(*COLORS['card_face'])
        RoundedRectangle(pos=self.pos, size=self.size, radius=[CARD_RADIUS])

        # Chegara
        glow_c = COLORS['gold_light'] if self.glow else COLORS['card_border']
        Color(*glow_c[:3], 1.0)
        Line(rounded_rectangle=[self.x, self.y, self.width, self.height,
                                 CARD_RADIUS], width=1.2)

        # Suit colour
        tc = COLORS['red_suit'] if is_red else COLORS['black_suit']
        Color(*tc[:3], 1.0)

        # Qiymat + mast belgisi
        from kivy.core.text import Label as CoreLabel
        from core.constants import VALUE_NAMES, SUIT_SYMBOLS

        val_str = VALUE_NAMES.get(card.value, str(card.value))
        sym_str = SUIT_SYMBOLS.get(card.suit, '')

        # Yuqori burchak
        txt = f"{val_str}\n{sym_str}"
        lbl = CoreLabel(text=txt, font_name='DejaVu', font_size=20, bold=True, color=tc, halign='center', line_height=0.9)
        lbl.refresh()
        tex = lbl.texture
        if tex:
            Rectangle(texture=tex, pos=(self.x + 8, self.y + self.height - tex.height - 8), size=tex.size)
            
        # O'rtada katta suit belgisi
        lbl_center = CoreLabel(text=sym_str, font_name='DejaVu', font_size=56, color=tc)
        lbl_center.refresh()
        tex_center = lbl_center.texture
        if tex_center:
            Rectangle(texture=tex_center,
                      pos=(self.center_x - tex_center.width/2, self.center_y - tex_center.height/2),
                      size=tex_center.size)

    # ─── Tanlash ──────────────────────────────────────────────────────────────
    def _on_select(self, *args):
        anim = Animation(
            y = self.y + (14 if self.selected else -14),
            duration = 0.15, t='out_sine'
        )
        anim.start(self)
        self.glow = self.selected

    def select(self):
        self.selected = True

    def deselect(self):
        self.selected = False

    def toggle_select(self):
        self.selected = not self.selected

    # ─── Touch (tap va drag) ──────────────────────────────────────────────────
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        if not self.draggable:
            touch.grab(self)
            return True

        touch.grab(self)
        self._drag_touch = touch
        self._orig_pos   = tuple(self.pos)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self or not self.draggable:
            return False
        self.center = touch.pos
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return False
        touch.ungrab(self)

        if self.draggable and self._orig_pos:
            dx = abs(self.center_x - touch.opos[0])
            dy = abs(self.center_y - touch.opos[1])

            if dx < 10 and dy < 10:
                # Tap — tanlash
                self.toggle_select()
                if self.parent and hasattr(self.parent, 'on_card_tap'):
                    self.parent.on_card_tap(self)
            else:
                # Drop — qayt yoki joylash
                if self.parent and hasattr(self.parent, 'on_card_drop'):
                    dropped = self.parent.on_card_drop(self, touch.pos)
                    if not dropped:
                        self._return_home()
                else:
                    self._return_home()

        self._drag_touch = None
        return True

    def _return_home(self):
        """Drag bekor bo'lganda orig pozitsiyaga qaytish"""
        if self._orig_pos:
            Animation(
                x=self._orig_pos[0], y=self._orig_pos[1],
                duration=0.25, t='out_cubic'
            ).start(self)

    # ─── Animatsiyalar ────────────────────────────────────────────────────────
    def animate_deal(self, from_pos, delay=0.0):
        """Karta berish animatsiyasi"""
        orig_pos = tuple(self.pos)
        self.pos = from_pos
        self.opacity = 0

        def _start(dt):
            anim = (
                Animation(opacity=1, duration=0.1) &
                Animation(x=orig_pos[0], y=orig_pos[1],
                          duration=0.3, t='out_cubic')
            )
            anim.start(self)

        from kivy.clock import Clock
        Clock.schedule_once(_start, delay)

    def animate_invalid(self):
        """Noto'g'ri harakat effekti"""
        ox = self.x
        anim = (
            Animation(x=ox - 8, duration=0.04) +
            Animation(x=ox + 8, duration=0.04) +
            Animation(x=ox - 5, duration=0.04) +
            Animation(x=ox + 5, duration=0.04) +
            Animation(x=ox,     duration=0.04)
        )
        anim.start(self)

    def __repr__(self):
        return f"CardWidget({self.card}, face_up={self.face_up})"
