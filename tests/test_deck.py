"""
tests/test_deck.py — Deck sinfi uchun unit testlar
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.deck   import Deck
from core.card   import Card
from core.constants import SUITS, VALUES


class TestDeckCreation:
    def test_deck_has_36_cards(self):
        d = Deck()
        assert len(d.cards) == 36

    def test_deck_has_all_suits(self):
        d = Deck()
        for suit in SUITS:
            assert any(c.suit == suit for c in d.cards)

    def test_deck_has_all_values(self):
        d = Deck()
        for value in VALUES:
            assert any(c.value == value for c in d.cards)

    def test_deck_no_duplicates(self):
        d = Deck()
        cards_set = set(d.cards)
        assert len(cards_set) == 36

    def test_deck_remaining(self):
        d = Deck()
        assert d.remaining == 36

    def test_deck_not_empty(self):
        d = Deck()
        assert d.is_empty is False


class TestDeckShuffle:
    def test_shuffle_preserves_count(self):
        d = Deck()
        d.shuffle()
        assert len(d.cards) == 36

    def test_shuffle_preserves_all_cards(self):
        d = Deck()
        before = set(d.cards)
        d.shuffle()
        after  = set(d.cards)
        assert before == after

    def test_shuffle_changes_order(self):
        """Ko'p urinishda kamida bir marta tartib o'zgaradi"""
        d = Deck()
        original = list(d.cards)
        changed  = False
        for _ in range(5):
            d2 = Deck()
            d2.shuffle()
            if [repr(c) for c in d2.cards] != [repr(c) for c in original]:
                changed = True
                break
        assert changed, "Shuffle hech qachon tartibni o'zgartirmadi"


class TestDeckTrump:
    def test_set_trump(self):
        d = Deck()
        d.shuffle()
        d.set_trump()
        assert d.trump_card is not None
        assert d.trump_suit is not None
        assert d.trump_suit in SUITS

    def test_trump_is_last_card(self):
        d = Deck()
        last_card = d.cards[-1]
        d.set_trump()
        assert d.trump_card == last_card

    def test_trump_card_face_up(self):
        d = Deck()
        d.set_trump()
        assert d.trump_card.is_face_up is True


class TestDeckDeal:
    def test_deal_removes_from_deck(self):
        d = Deck()
        dealt = d.deal(6)
        assert len(d.cards) == 30
        assert len(dealt)   == 6

    def test_deal_returns_correct_count(self):
        d = Deck()
        dealt = d.deal(3)
        assert len(dealt) == 3

    def test_deal_more_than_available(self):
        d = Deck()
        d.deal(30)              # 6 ta qoldi
        dealt = d.deal(10)     # 10 so'raydi, 6 oladi
        assert len(dealt) == 6
        assert d.remaining == 0

    def test_deal_from_empty(self):
        d = Deck()
        d.deal(36)
        dealt = d.deal(1)
        assert len(dealt) == 0

    def test_deck_empty_after_full_deal(self):
        d = Deck()
        d.deal(36)
        assert d.is_empty is True
        assert d.remaining == 0

    def test_deal_to_refill(self):
        d = Deck()
        d.deal(20)              # 16 qoldi
        refill = d.deal_to_refill(4)   # 4 ta bor, 2 kerak
        assert len(refill) == 2


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
