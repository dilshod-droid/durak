"""
core/card.py — Karta sinfi
"""
from core.constants import SUITS, VALUES, VALUE_NAMES, SUIT_SYMBOLS, CARDS_DIR
import os


class Card:
    """Bitta o'yin kartasini ifodalaydi."""

    SUITS  = SUITS
    VALUES = VALUES

    def __init__(self, suit: str, value: int):
        if suit not in self.SUITS:
            raise ValueError(f"Noto'g'ri mast: {suit}")
        if value not in self.VALUES:
            raise ValueError(f"Noto'g'ri qiymat: {value}")

        self.suit   = suit
        self.value  = value
        self.is_face_up = True

    # ─── Ko'rinish ────────────────────────────────────────────────────────────
    @property
    def display_value(self) -> str:
        """6–10 → '6'–'10', 11→'J', 12→'Q', 13→'K', 14→'A'"""
        return VALUE_NAMES.get(self.value, str(self.value))

    @property
    def symbol(self) -> str:
        """Mast belgisi: ♠ ♥ ♦ ♣"""
        return SUIT_SYMBOLS[self.suit]

    @property
    def image_path(self) -> str:
        """Karta rasmi yo'li"""
        return os.path.join(CARDS_DIR, f"{self.suit}_{self.value}.png")

    @property
    def is_red(self) -> bool:
        return self.suit in ('hearts', 'diamonds')

    # ─── O'yin Mexanikasi ─────────────────────────────────────────────────────
    def beats(self, other: 'Card', trump_suit: str) -> bool:
        """
        Bu karta 'other' kartani yenga oladimi?
        Qoidalar:
          1. Bir xil mast → kattaroq qiymat yengadi
          2. Kozir mast + boshqa mast → kozir yengadi
          3. Boshqa holatlarda → yopib bo'lmaydi
        """
        if self.suit == other.suit:
            return self.value > other.value
        if self.suit == trump_suit and other.suit != trump_suit:
            return True
        return False

    def same_value(self, other: 'Card') -> bool:
        """Qiymatlari teng?"""
        return self.value == other.value

    # ─── Yordamchi ────────────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return f"{self.display_value}{self.symbol}"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.value == other.value

    def __hash__(self):
        return hash((self.suit, self.value))

    def to_dict(self) -> dict:
        return {'suit': self.suit, 'value': self.value}

    @classmethod
    def from_dict(cls, d: dict) -> 'Card':
        return cls(d['suit'], d['value'])
