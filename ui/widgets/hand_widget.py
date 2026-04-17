"""
ui/widgets/hand_widget.py — O'yinchi Qo'li Widjeti
Kartalarni gorizontal yoyiq ko'rinishda ko'rsatadi.
"""
from kivy.uix.widget  import Widget
from kivy.clock       import Clock
from typing import List, Optional, Callable
from core.card        import Card
from ui.widgets.card_widget import CardWidget
from core.constants   import CARD_W, CARD_H


class HandWidget(Widget):
    """
    O'yinchi qo'lidagi kartalarni ko'rsatadi.
    - Gorizontal yoyiq (overlapping fan)
    - Tanlash: bir karta — deselect boshqalar
    - face_up=False → AI kartalari (yopiq)
    """

    def __init__(self, face_up: bool = True, selectable: bool = True, **kwargs):
        # Atributlar super() DAN OLDIN yaratiladi — Kivy size eventi erta kelmasligi uchun
        self._cards:        List[Card]       = []
        self._widgets:      List[CardWidget] = []
        self._selected_idx: Optional[int]    = None
        self.on_card_selected:   Optional[Callable[[Card, int], None]] = None
        self.on_card_deselected: Optional[Callable] = None

        super().__init__(**kwargs)
        self.face_up    = face_up
        self.selectable = selectable
        self.on_card_selected   = None
        self.on_card_deselected = None
        self.on_card_dropped    = None

        self.size_hint_y = None
        self.height      = CARD_H + 20
        self.bind(pos=self._on_bind_update, size=self._on_bind_update)

    def _on_bind_update(self, *args):
        self._repositions()

    # ─── Kartalarni o'rnatish ─────────────────────────────────────────────────
    def set_cards(self, cards: List[Card], animate: bool = False):
        """Qo'ldagi kartalarni yangilash"""
        self._cards = list(cards)
        self._selected_idx = None
        self._rebuild(animate=animate)

    def update_cards(self, cards: List[Card]):
        """Animatsiyasiz yangilash"""
        self.set_cards(cards, animate=False)

    def _rebuild(self, animate: bool = False):
        """Barcha karta widjetlarini qayta qurish"""
        # Eski widjetlarni olib tashlash
        for w in self._widgets:
            self.remove_widget(w)
        self._widgets.clear()

        if not self._cards:
            return

        for card in self._cards:
            cw = CardWidget(
                card=card,
                face_up=self.face_up,
                draggable=self.selectable and self.face_up,
            )
            cw.bind(on_touch_up=self._on_card_touch)
            self._widgets.append(cw)
            self.add_widget(cw)
            if animate:
                # Oddiy boshlang'ich nuqta o'rnatib qo'yamiz
                cw.pos = (self.center_x, self.y - 50)
                
        self._repositions(animate=animate)

    def _repositions(self, animate: bool = False):
        """Kartalarni faqat o'zgargan pos/size ga ko'ra qayta joylashtirish"""
        if not self._widgets:
            return
            
        n = len(self._widgets)
        available_w = self.width or 350
        max_overlap = max(CARD_W * 0.55, available_w / max(1, n + 1))
        step        = min(CARD_W * 0.45, max_overlap)
        total_w     = (n - 1) * step + CARD_W
        start_x     = self.center_x - total_w / 2

        base_y  = self.y + 6   # Past qismida joy

        for i, cw in enumerate(self._widgets):
            x = start_x + i * step
            if animate:
                cw.animate_deal(from_pos=cw.pos, delay=i*0.07)
                # target pos is handled inside animate_deal logically?
                # animate_deal only animates FROM a pos.
                # Actually, animate_deal in CardWidget animates to cw.pos! so we set it first:
                cw.pos = (x, base_y)
            else:
                cw.pos = (x, base_y)

    def _on_card_touch(self, widget, touch):
        """Karta bosilganda"""
        if not self.selectable or not self.face_up:
            return
        if not widget.collide_point(*touch.pos):
            return

        idx = self._widgets.index(widget) if widget in self._widgets else -1
        if idx < 0:
            return

        if self._selected_idx == idx:
            # Deselect
            widget.deselect()
            self._selected_idx = None
            if self.on_card_deselected:
                self.on_card_deselected()
        else:
            # Boshqa kartani deselect
            if self._selected_idx is not None:
                self._widgets[self._selected_idx].deselect()
            widget.select()
            self._selected_idx = idx
            if self.on_card_selected:
                self.on_card_selected(self._cards[idx], idx)

    def on_card_tap(self, widget):
        """CardWidget dan tap eventi"""
        pass

    def on_card_drop(self, widget, pos):
        """CardWidget dan drop eventi"""
        if self.on_card_dropped:
            return self.on_card_dropped(widget.card, pos)
        return False

    # ─── Tezkor kirish ────────────────────────────────────────────────────────
    @property
    def selected_card(self) -> Optional[Card]:
        if self._selected_idx is not None:
            return self._cards[self._selected_idx]
        return None

    @property
    def selected_widget(self) -> Optional[CardWidget]:
        if self._selected_idx is not None:
            return self._widgets[self._selected_idx]
        return None

    def deselect_all(self):
        for w in self._widgets:
            w.deselect()
        self._selected_idx = None

    def remove_selected(self) -> Optional[Card]:
        """Tanlangan kartani qo'ldan olib tashlash"""
        if self._selected_idx is None:
            return None
        idx  = self._selected_idx
        card = self._cards.pop(idx)
        self._selected_idx = None
        self._rebuild()
        return card

    def on_size(self, *args):
        self._repositions()

    def on_pos(self, *args):
        self._repositions()
