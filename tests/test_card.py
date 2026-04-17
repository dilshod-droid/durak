"""
tests/test_card.py — Card sinfi uchun unit testlar
Ishlatish: python -m pytest tests/ -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.card import Card


class TestCardCreation:
    def test_valid_card(self):
        c = Card('spades', 10)
        assert c.suit  == 'spades'
        assert c.value == 10

    def test_invalid_suit_raises(self):
        try:
            Card('joker', 10)
            assert False, "ValueError kutilgan edi"
        except ValueError:
            pass

    def test_invalid_value_raises(self):
        try:
            Card('spades', 5)
            assert False, "ValueError kutilgan edi"
        except ValueError:
            pass

    def test_display_value_number(self):
        c = Card('hearts', 9)
        assert c.display_value == '9'

    def test_display_value_face(self):
        assert Card('spades', 11).display_value == 'J'
        assert Card('spades', 12).display_value == 'Q'
        assert Card('spades', 13).display_value == 'K'
        assert Card('spades', 14).display_value == 'A'

    def test_symbol(self):
        assert Card('spades',   6).symbol == '♠'
        assert Card('hearts',   6).symbol == '♥'
        assert Card('diamonds', 6).symbol == '♦'
        assert Card('clubs',    6).symbol == '♣'

    def test_is_red(self):
        assert Card('hearts',   6).is_red is True
        assert Card('diamonds', 6).is_red is True
        assert Card('spades',   6).is_red is False
        assert Card('clubs',    6).is_red is False

    def test_repr(self):
        c = Card('hearts', 14)
        assert 'A' in repr(c) and '♥' in repr(c)

    def test_equality(self):
        c1 = Card('spades', 10)
        c2 = Card('spades', 10)
        c3 = Card('hearts', 10)
        assert c1 == c2
        assert c1 != c3

    def test_hash(self):
        c1 = Card('spades', 10)
        c2 = Card('spades', 10)
        assert hash(c1) == hash(c2)

    def test_to_from_dict(self):
        c = Card('diamonds', 12)
        d = c.to_dict()
        c2 = Card.from_dict(d)
        assert c == c2


class TestCardBeats:
    def test_same_suit_higher_beats(self):
        """Bir xil mast, katta qiymat yengadi"""
        atk = Card('spades', 8)
        dfn = Card('spades', 10)
        assert dfn.beats(atk, 'hearts') is True

    def test_same_suit_lower_loses(self):
        """Bir xil mast, kichik qiymat yutqizadi"""
        atk = Card('spades', 10)
        dfn = Card('spades', 8)
        assert dfn.beats(atk, 'hearts') is False

    def test_same_suit_equal_value(self):
        """Bir xil mast, teng qiymat — yopib bo'lmaydi"""
        atk = Card('spades', 9)
        dfn = Card('spades', 9)
        assert dfn.beats(atk, 'hearts') is False

    def test_trump_beats_any_non_trump(self):
        """Kozir eng kuchli oddiy kartani yengadi"""
        atk = Card('spades', 14)   # Tuz pika
        dfn = Card('hearts', 6)    # Eng kichik kozir
        assert dfn.beats(atk, 'hearts') is True

    def test_non_trump_cannot_beat_trump(self):
        """Oddiy karta kozirni yenga olmaydi"""
        atk = Card('hearts', 6)    # Kozir
        dfn = Card('spades', 14)   # Eng kuchli pika
        assert dfn.beats(atk, 'hearts') is False

    def test_higher_trump_beats_lower_trump(self):
        """Katta kozir kichik kozirni yengadi"""
        atk = Card('hearts', 8)
        dfn = Card('hearts', 10)
        assert dfn.beats(atk, 'hearts') is True

    def test_lower_trump_cannot_beat_higher_trump(self):
        atk = Card('hearts', 10)
        dfn = Card('hearts', 8)
        assert dfn.beats(atk, 'hearts') is False

    def test_different_suit_no_trump(self):
        """Turli mast, trumpsiz — yopib bo'lmaydi"""
        atk = Card('spades', 6)
        dfn = Card('clubs',  14)
        assert dfn.beats(atk, 'hearts') is False

    def test_different_suit_both_not_trump(self):
        """Ikkalasi ham trump emas, turli mast"""
        atk = Card('spades',   7)
        dfn = Card('diamonds', 14)
        assert dfn.beats(atk, 'clubs') is False


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
