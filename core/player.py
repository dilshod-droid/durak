"""
core/player.py — O'yinchi sinfi
"""
from typing import List, Optional, TYPE_CHECKING
from core.card import Card

if TYPE_CHECKING:
    from core.deck import Deck


class Player:
    """Inson yoki AI o'yinchisini ifodalaydi."""

    def __init__(self, name: str, is_ai: bool = False):
        self.name:   str       = name
        self.is_ai:  bool      = is_ai
        self.hand:   List[Card] = []
        self.wins:   int       = 0
        self.losses: int       = 0
        self.cards_taken: int  = 0   # O'yin davomida olingan kartalar

    # ─── Qo'l boshqaruvi ──────────────────────────────────────────────────────
    def add_cards(self, cards: List[Card]):
        """Yangi kartalar qo'shish"""
        self.hand.extend(cards)
        self._sort_hand()

    def remove_card(self, card: Card) -> bool:
        """Qo'ldan karta olib tashlash. Topilmasa False qaytaradi."""
        try:
            self.hand.remove(card)
            return True
        except ValueError:
            return False

    def take_cards(self, cards: List[Card]):
        """Himoyachi barcha stoldan kartalarni oladi"""
        self.hand.extend(cards)
        self.cards_taken += len(cards)
        self._sort_hand()

    def refill(self, deck: 'Deck') -> List[Card]:
        """
        Turdan keyin qo'lni 6 tagacha to'ldirish.
        Berilgan kartalar ro'yxatini qaytaradi.
        """
        new_cards = deck.deal_to_refill(len(self.hand))
        if new_cards:
            self.add_cards(new_cards)
        return new_cards

    def has_card(self, card: Card) -> bool:
        return card in self.hand

    def can_beat(self, attack_card: Card, trump_suit: str) -> bool:
        """Qo'ldagi biron karta hujum kartasini yopa oladimi?"""
        return any(c.beats(attack_card, trump_suit) for c in self.hand)

    # ─── Saralash ─────────────────────────────────────────────────────────────
    def _sort_hand(self):
        """
        Qo'lni tartibga solish: mast bo'yicha, so'ngra qiymat bo'yicha.
        Kozir kartalar oxirida.
        """
        suit_order = {'spades': 0, 'clubs': 1, 'hearts': 2, 'diamonds': 3}
        self.hand.sort(key=lambda c: (suit_order.get(c.suit, 0), c.value))

    def sort_hand_trump_last(self, trump_suit: str):
        """Kozirlarni qo'lning oxiriga qo'yish"""
        non_trump = [c for c in self.hand if c.suit != trump_suit]
        trumps    = [c for c in self.hand if c.suit == trump_suit]
        non_trump.sort(key=lambda c: c.value)
        trumps.sort(key=lambda c: c.value)
        self.hand = non_trump + trumps

    # ─── Xossalar ─────────────────────────────────────────────────────────────
    @property
    def card_count(self) -> int:
        return len(self.hand)

    @property
    def has_won(self) -> bool:
        """Qo'l bo'sh → g'olib"""
        return len(self.hand) == 0

    def trump_cards(self, trump_suit: str) -> List[Card]:
        """Qo'ldagi kozir kartalar"""
        return [c for c in self.hand if c.suit == trump_suit]

    def smallest_trump(self, trump_suit: str) -> Optional[Card]:
        """Qo'ldagi eng kichik kozir"""
        trumps = self.trump_cards(trump_suit)
        return min(trumps, key=lambda c: c.value) if trumps else None

    # ─── Statistika ───────────────────────────────────────────────────────────
    def record_win(self):
        self.wins += 1

    def record_loss(self):
        self.losses += 1

    def reset_game_stats(self):
        """Bitta o'yin statistikasini tiklash"""
        self.cards_taken = 0

    def __repr__(self):
        ai_tag = " [AI]" if self.is_ai else ""
        return f"Player({self.name}{ai_tag}, {self.card_count} karta)"

    def to_dict(self):
        return {
            'name': self.name,
            'is_ai': self.is_ai,
            'hand': [c.to_dict() for c in self.hand],
            'wins': self.wins,
            'losses': self.losses
        }

    @staticmethod
    def from_dict(d):
        p = Player(name=d['name'], is_ai=d['is_ai'])
        p.hand = [Card.from_dict(c) for c in d['hand']]
        p.wins = d['wins']
        p.losses = d['losses']
        return p
