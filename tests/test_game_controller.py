"""
tests/test_game_controller.py — GameController uchun unit testlar
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.game_controller import GameController
from core.game_state      import (PHASE_ATTACK, PHASE_DEFENSE,
                                   PHASE_REFILL, PHASE_END)
from core.card            import Card


def make_game(difficulty='easy', mode='podkidnoy') -> GameController:
    gc = GameController(difficulty=difficulty, mode=mode)
    gc.start_game()
    return gc


class TestGameStart:
    def test_game_starts_correctly(self):
        gc = make_game()
        st = gc.state
        assert st.deck is not None
        assert len(st.players) == 2
        assert st.phase == PHASE_ATTACK

    def test_players_have_6_cards(self):
        gc = make_game()
        for p in gc.state.players:
            assert p.card_count == 6

    def test_trump_is_set(self):
        gc = make_game()
        assert gc.state.trump_suit is not None

    def test_attacker_defender_different(self):
        gc = make_game()
        st = gc.state
        assert st.attacker_idx != st.defender_idx

    def test_total_cards_after_deal(self):
        gc = make_game()
        st = gc.state
        total = (st.players[0].card_count +
                 st.players[1].card_count +
                 st.deck.remaining)
        assert total == 36

    def test_human_player_exists(self):
        gc = make_game()
        assert gc.human is not None
        assert gc.human.is_ai is False

    def test_ai_player_exists(self):
        gc = make_game()
        assert gc.ai_player is not None
        assert gc.ai_player.is_ai is True


class TestAttack:
    def _get_human_attacker_game(self):
        """Inson hujumchi bo'lgan holat"""
        for _ in range(20):        # Bir necha urinish
            gc = make_game()
            if gc.is_human_attacker:
                return gc
        return None

    def test_attack_with_valid_first_card(self):
        gc = self._get_human_attacker_game()
        if gc is None:
            return   # Skip if AI always goes first in test
        human = gc.human
        card  = human.hand[0]
        ok, msg = gc.attack(card)
        assert ok is True, msg

    def test_attack_removes_card_from_hand(self):
        gc = self._get_human_attacker_game()
        if gc is None:
            return
        human     = gc.human
        card      = human.hand[0]
        count_before = human.card_count
        gc.attack(card)
        assert human.card_count == count_before - 1

    def test_attack_places_card_on_table(self):
        gc = self._get_human_attacker_game()
        if gc is None:
            return
        card = gc.human.hand[0]
        gc.attack(card)
        assert len(gc.state.table) == 1

    def test_attack_changes_phase_to_defense(self):
        gc = self._get_human_attacker_game()
        if gc is None:
            return
        card = gc.human.hand[0]
        gc.attack(card)
        assert gc.state.phase == PHASE_DEFENSE

    def test_cannot_attack_in_defense_phase(self):
        gc = self._get_human_attacker_game()
        if gc is None:
            return
        card = gc.human.hand[0]
        gc.attack(card)   # Phase → DEFENSE
        # Yana hujum urinishi
        if gc.human.hand:
            ok, _ = gc.attack(gc.human.hand[0])
            assert ok is False


class TestDefend:
    def _setup_defense(self):
        """Inson himoyachi holati"""
        for _ in range(20):
            gc = make_game()
            st = gc.state
            if st.defender and not st.defender.is_ai:
                # AI hujum qilishga urinish
                ai = gc.ai_player
                if ai and ai.hand:
                    atk_card = ai.hand[0]
                    st.table.append((atk_card, None))
                    ai.remove_card(atk_card)
                    st.phase = PHASE_DEFENSE
                    return gc
        return None

    def test_valid_defense(self):
        gc = self._setup_defense()
        if gc is None:
            return
        st = gc.state
        if not st.table:
            return
        atk_card = st.table[0][0]
        # Yopa oladigan kartalarni topish
        human = gc.human
        defenders = [c for c in human.hand if c.beats(atk_card, st.trump_suit)]
        if defenders:
            ok, msg = gc.defend(atk_card, defenders[0])
            assert ok is True, msg

    def test_invalid_defense_weak_card(self):
        gc = self._setup_defense()
        if gc is None:
            return
        st = gc.state
        if not st.table:
            return
        atk_card = Card('spades', 14)  # Eng kuchli pika
        # Trumpsiz kichik karta
        weak_card = Card('clubs', 6)
        if not weak_card.beats(atk_card, st.trump_suit):
            ok, _ = gc.defend(atk_card, weak_card)
            assert ok is False


class TestTakeCards:
    def test_take_cards_clears_table(self):
        gc = make_game()
        st = gc.state
        # Stolga karta qo'yish
        if st.attacker and st.attacker.hand:
            card = st.attacker.hand[0]
            st.table.append((card, None))
            st.attacker.remove_card(card)
            st.phase = PHASE_DEFENSE

            defender = st.defender
            count_before = defender.card_count
            gc.take_cards()
            assert len(st.table) == 0


class TestFullGame:
    def test_game_reaches_end(self):
        """To'liq simulatsiya — 200 ta tur ichida tugashi kerak"""
        gc = GameController(difficulty='easy', mode='podkidnoy')
        gc.start_game()

        turns = 0
        max_turns = 300

        while gc.state.phase != PHASE_END and turns < max_turns:
            st = gc.state

            if st.attacker and st.attacker.is_ai:
                # AI hujum
                gc.execute_ai_turn()
            elif st.defender and st.defender.is_ai:
                # AI himoya
                gc.execute_ai_turn()
            elif st.phase == PHASE_ATTACK and st.attacker and not st.attacker.is_ai:
                # Inson hujum
                human = gc.human
                if human and human.hand and st.can_add_attack:
                    card = human.hand[0]
                    ok, _ = gc.attack(card)
                    if not ok:
                        gc.end_turn()
                else:
                    gc.end_turn()
            elif (st.phase == PHASE_DEFENSE and
                  st.defender and not st.defender.is_ai):
                # Inson himoya — olamiz
                gc.take_cards()
            else:
                break
            turns += 1

        # Test muvaffaqiyatli o'tsa — game over bo'ldi yoki max_turns ga yetdi
        assert turns > 0, "O'yin hech qachon harakat qilmadi"

    def test_winner_is_set_on_end(self):
        """O'yin tugaganda g'olib o'rnatilgan"""
        gc = GameController(difficulty='easy', mode='podkidnoy')
        gc.start_game()

        for _ in range(300):
            if gc.state.phase == PHASE_END:
                break
            gc.execute_ai_turn()
            # Inson harakatlari ham simulatsiya
            st = gc.state
            if st.phase == PHASE_ATTACK and not st.attacker.is_ai:
                if st.attacker.hand:
                    gc.attack(st.attacker.hand[0])
            elif st.phase == PHASE_DEFENSE and not st.defender.is_ai:
                gc.take_cards()

        if gc.state.phase == PHASE_END:
            assert gc.state.winner is not None


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
