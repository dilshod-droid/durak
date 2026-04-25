"""
ui/widgets/hand_widget.py — O'yinchi Qo'li Widjeti
Fan layout: AI kartalari tepada yopiq, o'yinchi kartalari pastda.
"""
from kivy.uix.widget  import Widget
from kivy.clock       import Clock
from kivy.graphics    import Color, RoundedRectangle, Line
from typing import List, Optional, Callable
from core.card        import Card
from ui.widgets.card_widget import CardWidget
from core.constants   import CARD_W, CARD_H, COLORS


class HandWidget(Widget):
    """
    O'yinchi yoki AI qo'lidagi kartalarni ko'rsatadi.
    - face_up=False → raqib kartalari (yopiq, overlap fan)
    - face_up=True  → o'yinchi kartalari (ochiq, tanlash/drag)
    - is_opponent=True → yuqoridan pastga (sahifaning yuqori qismi)
    """

    def __init__(self, face_up: bool = True, selectable: bool = True,
                 is_opponent: bool = False, **kwargs):
        self._cards:        List[Card]       = []
        self._widgets:      List[CardWidget] = []
        self._selected_idx: Optional[int]    = None
        self.face_up    = face_up
        self.selectable = selectable
        self.is_opponent = is_opponent

        # Callbacklar
        self.on_card_selected:   Optional[Callable[[Card, int], None]] = None
        self.on_card_deselected: Optional[Callable]                    = None
        self.on_card_dropped:    Optional[Callable]                    = None

        super().__init__(**kwargs)

        self.size_hint  = (1, None)
        self.height     = CARD_H + 24

        self.bind(pos=self._layout, size=self._layout)

    # ─── Kartalarni o'rnatish ─────────────────────────────────────────────────
    def set_cards(self, cards: List[Card], animate: bool = False):
        self._cards = list(cards)
        self._selected_idx = None
        self._rebuild(animate=animate)

    def _rebuild(self, animate: bool = False):
        for w in self._widgets:
            self.remove_widget(w)
        self._widgets.clear()

        if not self._cards:
            return

        for i, card in enumerate(self._cards):
            cw = CardWidget(
                card=card,
                face_up=self.face_up,
                draggable=self.selectable and self.face_up,
            )
            self._widgets.append(cw)
            self.add_widget(cw)

        self._layout(animate=animate)

    def _layout(self, *args, animate=False):
        """Fan tartibida kartalarni joylashtirish"""
        if not self._widgets:
            return

        n = len(self._widgets)
        available_w = max(self.width, 300)

        # Overlap hisobi: kartalar soni ko'paysa, overlap kuchayadi
        max_step = CARD_W * 0.72
        min_step = CARD_W * 0.28
        step = max(min_step, min(max_step, (available_w - CARD_W) / max(n - 1, 1)))

        total_w = (n - 1) * step + CARD_W
        start_x = self.x + (self.width - total_w) / 2

        # Y pozitsiya: AI uchun yuqori, o'yinchi uchun pastdan 8px
        base_y = self.y + 8

        for i, cw in enumerate(self._widgets):
            if cw.is_manually_moved:
                continue
                
            x = start_x + i * step
            y = base_y
            
            if animate:
                cw.opacity = 0
                cw.pos = (x, y)
                Clock.schedule_once(
                    lambda dt, w=cw, px=x, py=y: self._animate_in(w, px, py),
                    i * 0.06
                )
            else:
                cw.pos = (x, y)
                cw.set_base_y(y)

    def _animate_in(self, widget, x, y):
        from kivy.animation import Animation
        widget.pos = (x, y - 40)
        anim = (
            Animation(opacity=1, duration=0.12) &
            Animation(y=y, duration=0.25, t='out_cubic')
        )
        anim.start(widget)
        widget.set_base_y(y)

    # ─── Touch ────────────────────────────────────────────────────────────────
    def _on_card_touch(self, widget, touch):
        """CardWidget dan tap eventi"""
        if not self.selectable or not self.face_up:
            return
        if widget not in self._widgets:
            return

        idx = self._widgets.index(widget)

        if self._selected_idx == idx:
            widget.deselect()
            self._selected_idx = None
            if self.on_card_deselected:
                self.on_card_deselected()
        else:
            if self._selected_idx is not None:
                old = self._widgets[self._selected_idx]
                old.deselect()
            widget.select()
            self._selected_idx = idx
            if self.on_card_selected:
                self.on_card_selected(self._cards[idx], idx)

    def on_card_drop(self, widget, pos):
        """CardWidget drag drop eventi"""
        if self.on_card_dropped:
            return self.on_card_dropped(widget.card, pos)
        return False

    # ─── Hint ko'rsatgichlari ─────────────────────────────────────────────────
    def show_hints(self, valid_cards: List[Card]):
        """Hujum mumkin bo'lgan kartalarni yashil glow bilan belgilash"""
        for i, cw in enumerate(self._widgets):
            if i < len(self._cards):
                cw.set_hint(self._cards[i] in valid_cards)

    def clear_hints(self):
        for cw in self._widgets:
            cw.set_hint(False)

    # ─── Tezkor kirish ────────────────────────────────────────────────────────
    @property
    def selected_card(self) -> Optional[Card]:
        if self._selected_idx is not None and self._selected_idx < len(self._cards):
            return self._cards[self._selected_idx]
        return None

    @property
    def selected_widget(self) -> Optional[CardWidget]:
        if self._selected_idx is not None and self._selected_idx < len(self._widgets):
            return self._widgets[self._selected_idx]
        return None

    def deselect_all(self):
        for w in self._widgets:
            w.deselect()
        self._selected_idx = None

    def on_size(self, *args):
        self._layout()

    def on_pos(self, *args):
        self._layout()
