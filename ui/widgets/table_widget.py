"""
ui/widgets/table_widget.py — O'yin Stoli Widjeti
Hujum/himoya juftliklarini ko'rsatadi.
"""
from typing import List, Tuple, Optional, Callable
from kivy.uix.widget     import Widget
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout  import BoxLayout
from kivy.graphics       import Color, RoundedRectangle, Line, Rectangle
from core.card           import Card
from ui.widgets.card_widget import CardWidget
from core.constants      import COLORS, CARD_W, CARD_H, CARD_RADIUS


SLOT_PAD = 8       # Slot orasidagi bo'shliq
SLOT_W   = CARD_W + SLOT_PAD
SLOT_H   = CARD_H * 2 + SLOT_PAD + 8


class CardSlot(Widget):
    """
    Bitta hujum/himoya juftligi uchun slot.
    Yuqori: himoya kartasi | Past: hujum kartasi
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size      = (CARD_W + 6, CARD_H * 2 + 12)

        self._atk_widget: Optional[CardWidget] = None
        self._dfn_widget: Optional[CardWidget] = None

        self.bind(pos=self._reposition, size=self._reposition)
        self._draw_empty()

    def _draw_empty(self):
        """Bo'sh slot chizish"""
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*COLORS['table'][:3], 0.5)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[CARD_RADIUS])
            Color(*COLORS['gold'][:3], 0.25)
            Line(rounded_rectangle=[self.x, self.y,
                                     self.width, self.height,
                                     CARD_RADIUS], width=1.0)

    def set_attack(self, card: Card):
        """Hujum kartasini qo'yish"""
        if self._atk_widget:
            self.remove_widget(self._atk_widget)

        cw = CardWidget(card=card, face_up=True, draggable=False)
        cw.pos = (self.x + 3, self.y + 3)
        self._atk_widget = cw
        self.add_widget(cw)

    def set_defense(self, card: Card):
        """Himoya kartasini hujum ustiga qo'yish"""
        if self._dfn_widget:
            self.remove_widget(self._dfn_widget)

        cw = CardWidget(card=card, face_up=True, draggable=False)
        cw.pos = (self.x + 3, self.y + CARD_H + 6)
        self._dfn_widget = cw
        self.add_widget(cw)

    def _reposition(self, *args):
        self._draw_empty()
        if self._atk_widget:
            self._atk_widget.pos = (self.x + 3, self.y + 3)
        if self._dfn_widget:
            self._dfn_widget.pos = (self.x + 3, self.y + CARD_H + 6)

    @property
    def is_defended(self) -> bool:
        return self._dfn_widget is not None


class TableWidget(Widget):
    """
    O'yin stoli — hujum/himoya juftliklarini ko'rsatadi.
    Maksimal 6 ta slot.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._slots:  List[CardSlot] = []
        self._table:  List[Tuple[Card, Optional[Card]]] = []

        # Callback — slot bosilganda
        self.on_slot_tap: Optional[Callable[[int], None]] = None

        self.bind(pos=self._reposition, size=self._reposition)

    # ─── Holat yangilash ──────────────────────────────────────────────────────
    def update_table(self, table: List[Tuple[Card, Optional[Card]]]):
        """
        Stol holatini yangilash.
        table = [(atk_card, dfn_card | None), ...]
        """
        self._table = table

        # Barcha eski slotlarni olib tashlash
        for slot in self._slots:
            self.remove_widget(slot)
        self._slots.clear()

        # Yangi slotlarni qurish
        for atk, dfn in table:
            slot = CardSlot()
            slot.set_attack(atk)
            if dfn is not None:
                slot.set_defense(dfn)
            self._slots.append(slot)
            self.add_widget(slot)

        self._reposition()


    def clear_table(self):
        """Barcha slotlarni tozalash"""
        for slot in self._slots:
            self.remove_widget(slot)
        self._slots.clear()
        self._table.clear()

    def clear_selection(self):
        """Slot tanlovini bekor qilish (external call)"""
        pass   # Kelajakda slot glow o'chirish uchun

    # ─── Pozitsiyalash ────────────────────────────────────────────────────────
    def _reposition(self, *args):
        n = len(self._slots)
        if n == 0:
            return

        slot_w  = CARD_W + 6
        spacing = 10
        total   = n * slot_w + (n - 1) * spacing
        start_x = self.x + (self.width - total) / 2
        center_y = self.y + (self.height - CARD_H * 2 - 12) / 2

        for i, slot in enumerate(self._slots):
            slot.pos  = (start_x + i * (slot_w + spacing), center_y)
            slot.size = (slot_w, CARD_H * 2 + 12)

    # ─── Ko'rinish ────────────────────────────────────────────────────────────
    def on_touch_down(self, touch):
        for i, slot in enumerate(self._slots):
            if slot.collide_point(*touch.pos):
                if self.on_slot_tap:
                    self.on_slot_tap(i)
                return True
        return super().on_touch_down(touch)

    @property
    def slot_count(self) -> int:
        return len(self._slots)

    @property
    def all_defended(self) -> bool:
        return all(s.is_defended for s in self._slots)
