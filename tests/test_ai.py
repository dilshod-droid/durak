"""
tests/test_ai.py — AIPlayer sinfi uchun unit testlar
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ai_player import AIPlayer
from core.card      import Card


def make_hand(*card_specs) -> list:
    """(suit, value) juftlaridan karta ro'yxat yaratish"""
    return [Card(suit, value) for suit, value in card_specs]


class TestAIEasy:
    def test_choose_attack_returns_valid_card(self):
        ai   = AIPlayer('easy')
        hand = make_hand(('spades', 6), ('hearts', 9), ('clubs', 11))
        card = ai.choose_attack_card(hand, [], 'hearts')
        assert card in hand

    def test_no_valid_attack_returns_none(self):
        ai   = AIPlayer('easy')
        hand = make_hand(('spades', 6), ('clubs',  8))
        # Stoldagi qiymat 9 — qo'lda yo'q
        table = [(Card('hearts', 9), Card('hearts', 11))]
        card  = ai.choose_attack_card(hand, table, 'hearts')
        assert card is None

    def test_choose_defense_returns_beating_card(self):
        ai       = AIPlayer('easy')
        atk_card = Card('spades', 8)
        hand     = make_hand(('spades', 10), ('hearts', 6))
        dfn      = ai.choose_defense_card(atk_card, hand, 'hearts')
        assert dfn is not None
        assert dfn.beats(atk_card, 'hearts')

    def test_cannot_defend_returns_none(self):
        ai       = AIPlayer('easy')
        atk_card = Card('spades', 14)   # Tuz pika
        # Faqat kichik pika (yenga olmaydi) + trump yo'q
        hand = make_hand(('clubs', 6))
        dfn  = ai.choose_defense_card(atk_card, hand, 'diamonds')
        assert dfn is None


class TestAIMedium:
    def test_prefers_non_trump_attack(self):
        ai   = AIPlayer('medium')
        hand = make_hand(
            ('hearts', 6),    # Trump (hearts)
            ('spades', 8),    # Non-trump
            ('clubs',  10),   # Non-trump
        )
        card = ai.choose_attack_card(hand, [], 'hearts')
        # Kozir emas karta tanlashi kerak
        assert card is not None
        assert card.suit != 'hearts'

    def test_chooses_minimal_defense(self):
        ai       = AIPlayer('medium')
        atk_card = Card('spades', 8)
        hand     = make_hand(
            ('spades', 9),    # Minimal margin
            ('spades', 14),   # Katta margin
        )
        dfn = ai.choose_defense_card(atk_card, hand, 'hearts')
        assert dfn.value == 9   # Minimal kartani tanlaydi

    def test_prefers_same_suit_defense(self):
        ai       = AIPlayer('medium')
        atk_card = Card('spades', 8)
        hand     = make_hand(
            ('hearts', 6),    # Trump
            ('spades', 10),   # Same suit, bigger
        )
        dfn = ai.choose_defense_card(atk_card, hand, 'hearts')
        assert dfn.suit == 'spades'   # Trumpsiz yopish

    def test_uses_trump_when_necessary(self):
        ai       = AIPlayer('medium')
        atk_card = Card('spades', 14)   # Tuz pika
        hand = make_hand(
            ('hearts', 6),    # Trump (hearts)
        )
        dfn = ai.choose_defense_card(atk_card, hand, 'hearts')
        assert dfn is not None
        assert dfn.suit == 'hearts'

    def test_attack_smallest_non_trump(self):
        ai   = AIPlayer('medium')
        hand = make_hand(
            ('spades', 9),
            ('spades', 12),
            ('clubs',  7),
        )
        card = ai.choose_attack_card(hand, [], 'hearts')
        assert card.value == 7   # Eng kichik non-trump


class TestAIHard:
    def test_hard_avoids_trump_first(self):
        ai   = AIPlayer('hard')
        hand = make_hand(
            ('diamonds', 6),   # Trump
            ('spades',   8),   # Non-trump
        )
        card = ai.choose_attack_card(hand, [], 'diamonds')
        assert card.suit != 'diamonds'   # Trumpni saqlaydi

    def test_hard_uses_trump_if_only_option(self):
        ai   = AIPlayer('hard')
        hand = make_hand(('diamonds', 6))   # Faqat trump
        card = ai.choose_attack_card(hand, [], 'diamonds')
        assert card is not None


class TestAIShouldTake:
    def test_should_take_when_cannot_defend(self):
        ai       = AIPlayer('medium')
        atk_card = Card('spades', 14)   # Yenga bo'lmaydi
        table    = [(atk_card, None)]
        hand     = make_hand(('clubs', 6))   # Yenga olmaydi
        result   = ai.should_take_cards(table, hand, 'hearts')
        assert result is True

    def test_should_not_take_when_can_defend(self):
        ai       = AIPlayer('medium')
        atk_card = Card('spades', 8)
        table    = [(atk_card, None)]
        hand     = make_hand(('spades', 10))   # Yenga oladi
        result   = ai.should_take_cards(table, hand, 'hearts')
        assert result is False

    def test_empty_table_no_take(self):
        ai     = AIPlayer('medium')
        result = ai.should_take_cards([], [], 'hearts')
        assert result is False


class TestValidAttacks:
    def test_first_attack_all_cards_valid(self):
        ai   = AIPlayer('medium')
        hand = make_hand(('spades', 6), ('hearts', 9), ('clubs', 11))
        valid = ai._get_valid_attacks(hand, [])
        assert set(valid) == set(hand)

    def test_podkidnoy_only_matching_values(self):
        ai   = AIPlayer('medium')
        hand = make_hand(('spades', 9), ('clubs', 11), ('hearts', 7))
        # Stoldagi qiymat = 9
        table = [(Card('hearts', 9), Card('spades', 11))]
        valid = ai._get_valid_attacks(hand, table)
        # Faqat 9 qiymati va 11 qiymati valid (stol: 9, 11)
        valid_values = {c.value for c in valid}
        assert valid_values.issubset({9, 11})

    def test_no_matching_values_empty(self):
        ai   = AIPlayer('medium')
        hand = make_hand(('clubs', 6), ('diamonds', 7))
        table = [(Card('spades', 14), None)]
        valid = ai._get_valid_attacks(hand, table)
        assert len(valid) == 0


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
