"""
ui/widgets/table_widget.py — O'yin Stoli Widjeti
Hujum/himoya juftliklarini aniq ko'rsatadi + hint slot ko'rsatgich.
"""
from typing import List, Tuple, Optional, Callable
from kivy.uix.widget     import Widget
from kivy.graphics       import Color, RoundedRectangle, Line, Rectangle
from kivy.animation      import Animation
from kivy.clock          import Clock
from core.card           import Card
from ui.widgets.card_widget import CardWidget
from core.constants      import COLORS, CARD_W, CARD_H, CARD_RADIUS


SLOT_PAD  = 10    # Slotlar orasidagi bo'sh joy
OFFSET_Y  = 32   # Himoya kartasi hujum ustidagi offset (overlap)


class CardSlot(Widget):
    """
    Bitta hujum/himoya juftligi uchun slot.
    - Hujum karta pastda
    - Himoya karta diagonal offset bilan tepada (overlap)
    - selected=True → oltin chegara (hint tanlangan slot)
    """

    SLOT_W = CARD_W + 10
    SLOT_H = CARD_H + OFFSET_Y + 6

    def __init__(self, slot_idx: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.slot_idx = slot_idx
        self.size_hint = (None, None)
        self.size = (self.SLOT_W, self.SLOT_H)

        self._atk_widget: Optional[CardWidget] = None
        self._dfn_widget: Optional[CardWidget] = None
        self._is_selected = False

        self.bind(pos=self._reposition, size=self._reposition)
        self._draw_bg()

    def _draw_bg(self):
        self.canvas.before.clear()
        with self.canvas.before:
            # Slot background
            Color(*COLORS['table'][:3], 0.35)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[CARD_RADIUS])

            # Slot chegarasi
            if self._is_selected:
                # Oltin hint: "bu slotga yopish"
                Color(*COLORS['gold'][:3], 0.9)
                Line(rounded_rectangle=[self.x, self.y, self.width, self.height,
                                         CARD_RADIUS], width=2.2)
                # Yashil glow
                Color(0.2, 0.85, 0.3, 0.5)
                Line(rounded_rectangle=[self.x-2, self.y-2, self.width+4, self.height+4,
                                         CARD_RADIUS+2], width=1.5)
            else:
                Color(*COLORS['gold'][:3], 0.18)
                Line(rounded_rectangle=[self.x, self.y, self.width, self.height,
                                         CARD_RADIUS], width=0.9)

    def set_attack(self, card: Card):
        if self._atk_widget:
            self.remove_widget(self._atk_widget)
        cw = CardWidget(card=card, face_up=True, draggable=False)
        cw.size = (CARD_W, CARD_H)
        cw.pos = (self.x + 5, self.y + 3)
        self._atk_widget = cw
        self.add_widget(cw)

    def set_defense(self, card: Card):
        if self._dfn_widget:
            self.remove_widget(self._dfn_widget)
        cw = CardWidget(card=card, face_up=True, draggable=False)
        cw.size = (CARD_W, CARD_H)
        # Himoya diagonal offset — ustiga yopilgan ko'rinish
        cw.pos = (self.x + 5 + 6, self.y + OFFSET_Y)
        self._dfn_widget = cw
        # Himoya kartasini yuqorida ko'rsatish
        self.add_widget(cw)

    def set_selected(self, val: bool):
        self._is_selected = val
        self._draw_bg()
        self._reposition()

    def _reposition(self, *args):
        self._draw_bg()
        if self._atk_widget:
            self._atk_widget.pos = (self.x + 5, self.y + 3)
            self._atk_widget.size = (CARD_W, CARD_H)
        if self._dfn_widget:
            self._dfn_widget.pos = (self.x + 5 + 6, self.y + OFFSET_Y)
            self._dfn_widget.size = (CARD_W, CARD_H)

    @property
    def is_defended(self) -> bool:
        return self._dfn_widget is not None

    @property
    def attack_card_widget(self) -> Optional[CardWidget]:
        return self._atk_widget


class TableWidget(Widget):
    """
    O'yin stoli — hujum/himoya juftliklarini ko'rsatadi.
    Maksimal 6 ta slot. Slotlar markazda joylashadi.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._slots:  List[CardSlot] = []
        self._table:  List[Tuple[Card, Optional[Card]]] = []
        self._selected_slot_idx: Optional[int] = None

        # Callback — slot bosilganda
        self.on_slot_tap: Optional[Callable[[int], None]] = None

        self.bind(pos=self._reposition, size=self._reposition)

    # ─── Holat yangilash ──────────────────────────────────────────────────────
    def update_table(self, table: List[Tuple[Card, Optional[Card]]]):
        """Stol holatini to'liq yangilash"""
        self._table = list(table)
        self._selected_slot_idx = None

        # Eski slotlarni olib tashlash
        for slot in self._slots:
            self.remove_widget(slot)
        self._slots.clear()

        # Yangi slotlarni qurish
        for i, (atk, dfn) in enumerate(table):
            slot = CardSlot(slot_idx=i)
            slot.set_attack(atk)
            if dfn is not None:
                slot.set_defense(dfn)
            self._slots.append(slot)
            self.add_widget(slot)

        self._reposition()

    def clear_table(self):
        for slot in self._slots:
            self.remove_widget(slot)
        self._slots.clear()
        self._table.clear()
        self._selected_slot_idx = None

    def clear_selection(self):
        if self._selected_slot_idx is not None:
            if self._selected_slot_idx < len(self._slots):
                self._slots[self._selected_slot_idx].set_selected(False)
        self._selected_slot_idx = None

    def set_slot_selected(self, idx: Optional[int]):
        """Slotni tanlash (hint uchun)"""
        # Avvingi tanlovni o'chirish
        if self._selected_slot_idx is not None:
            if self._selected_slot_idx < len(self._slots):
                self._slots[self._selected_slot_idx].set_selected(False)

        self._selected_slot_idx = idx
        if idx is not None and idx < len(self._slots):
            self._slots[idx].set_selected(True)

    def highlight_undefended(self, active: bool):
        """Himoya kutilayotgan slotlarni yashil ko'rsatish"""
        for i, slot in enumerate(self._slots):
            if i < len(self._table):
                _, dfn = self._table[i]
                slot.set_selected(active and dfn is None)

    # ─── Pozitsiyalash ────────────────────────────────────────────────────────
    def _reposition(self, *args):
        n = len(self._slots)
        if n == 0:
            return

        slot_w   = CardSlot.SLOT_W
        slot_h   = CardSlot.SLOT_H
        spacing  = SLOT_PAD

        # 2 qatorli grid agar 3 dan ortiq slot
        if n <= 3:
            cols, rows = n, 1
        else:
            cols = min(n, 3)
            rows = (n + cols - 1) // cols

        total_w = cols * slot_w + (cols - 1) * spacing
        total_h = rows * slot_h + (rows - 1) * spacing

        # Stol markazida joylashtirish
        start_x = self.x + (self.width  - total_w) / 2
        start_y = self.y + (self.height - total_h) / 2

        for i, slot in enumerate(self._slots):
            col = i % cols
            row = i // cols
            slot.pos  = (start_x + col * (slot_w + spacing),
                          start_y + (rows - 1 - row) * (slot_h + spacing))
            slot.size = (slot_w, slot_h)

    # ─── Touch ────────────────────────────────────────────────────────────────
    def on_touch_down(self, touch):
        for i, slot in enumerate(self._slots):
            if slot.collide_point(*touch.pos):
                if self.on_slot_tap:
                    self.on_slot_tap(i)
                return True
        return super().on_touch_down(touch)

    # ─── Xossalar ─────────────────────────────────────────────────────────────
    @property
    def slot_count(self) -> int:
        return len(self._slots)

    @property
    def all_defended(self) -> bool:
        return all(s.is_defended for s in self._slots)

    def get_slot_at(self, pos) -> int:
        """Berilgan touch pozitsiyasida qaysi slot borligini qaytaradi"""
        for i, slot in enumerate(self._slots):
            if slot.collide_point(*pos):
                return i
        return -1
