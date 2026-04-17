"""
core/deck.py — Qo'da sinfi (36 ta karta)
"""
import random
from typing import List, Optional
from core.card import Card
from core.constants import SUITS, VALUES


class Deck:
    """36 ta kartali Durak qo'dasi."""

    def __init__(self):
        self.cards: List[Card]      = []
        self.trump_card: Optional[Card] = None
        self.trump_suit: Optional[str]  = None
        self._build()

    # ─── Yaratish ─────────────────────────────────────────────────────────────
    def _build(self):
        """36 ta karta yaratish"""
        for suit in SUITS:
            for value in VALUES:
                self.cards.append(Card(suit, value))

    def shuffle(self):
        """Fisher-Yates algoritmi bilan aralashtirish"""
        cards = self.cards
        for i in range(len(cards) - 1, 0, -1):
            j = random.randint(0, i)
            cards[i], cards[j] = cards[j], cards[i]

    # ─── Kozir ───────────────────────────────────────────────────────────────
    def set_trump(self):
        """
        Oxirgi karta kozir sifatida ochiq qo'yiladi.
        Karta qo'daning tagida qoladi.
        """
        self.trump_card = self.cards[-1]
        self.trump_suit = self.trump_card.suit
        self.trump_card.is_face_up = True

    # ─── Karta berish ─────────────────────────────────────────────────────────
    def deal(self, count: int) -> List[Card]:
        """
        Qo'daning tepasidan 'count' ta karta berish.
        Agar qo'da yetarlicha karta bo'lmasa — qolganlarini beradi.
        """
        actual = min(count, len(self.cards))
        dealt  = self.cards[:actual]
        self.cards = self.cards[actual:]
        return dealt

    def deal_to_refill(self, current_count: int) -> List[Card]:
        """
        O'yinchining qo'li 6 talikka to'ldiriladi.
        """
        need = max(0, 6 - current_count)
        if need == 0 or not self.cards:
            return []
        return self.deal(min(need, len(self.cards)))

    # ─── Xossalar ─────────────────────────────────────────────────────────────
    @property
    def remaining(self) -> int:
        """Qo'dada qolgan kartalar soni"""
        return len(self.cards)

    @property
    def is_empty(self) -> bool:
        return len(self.cards) == 0

    def __len__(self):
        return len(self.cards)

    def __repr__(self):
        trump = f" | Kozir: {self.trump_card}" if self.trump_card else ""
        return f"Deck({self.remaining} karta{trump})"
