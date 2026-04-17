"""
core/game_controller.py — O'yin boshqaruvchisi
Barcha o'yin qoidalarini amalga oshiradi.
"""
import time
from typing import List, Optional, Callable, Tuple

from core.card       import Card
from core.deck       import Deck
from core.player     import Player
from core.game_state import GameState, PHASE_ATTACK, PHASE_DEFENSE, PHASE_REFILL, PHASE_END
from core.ai_player  import AIPlayer
from core.constants  import HAND_SIZE, AI_THINK_DELAY


class GameController:
    """
    MVC Pattern: Controller qismi.
    O'yin qoidalarini tekshiradi va GameState ni yangilaydi.
    """

    def __init__(self, difficulty: str = 'medium', mode: str = 'podkidnoy'):
        self.state:      GameState = GameState()
        self.difficulty: str       = difficulty   # 'easy' | 'medium' | 'hard'
        self.mode:       str       = mode         # 'podkidnoy' | 'perevodnoy'
        self.ai:         AIPlayer  = AIPlayer(difficulty)

        # ─── Callback-lar (UI ularni o'rnatadi) ──────────────────────────
        self.on_state_changed:    Optional[Callable] = None
        self.on_invalid_move:     Optional[Callable] = None
        self.on_game_over:        Optional[Callable] = None
        self.on_cards_dealt:      Optional[Callable] = None
        self.on_ai_turn_start:    Optional[Callable] = None
        self.on_ai_turn_end:      Optional[Callable] = None

    # =========================================================================
    # O'YIN BOSHLASH
    # =========================================================================
    def start_game(self):
        """Yangi o'yin boshlash"""
        st = self.state

        # Qo'da yaratish va aralashtirish
        st.deck = Deck()
        st.deck.shuffle()
        st.deck.set_trump()

        # O'yinchilar
        human = Player("Siz",    is_ai=False)
        ai    = Player("Raqib",  is_ai=True)
        st.players = [human, ai]

        # Karta berish
        human.add_cards(st.deck.deal(HAND_SIZE))
        ai.add_cards(st.deck.deal(HAND_SIZE))

        # Qo'lni kozirga qarab saralash
        human.sort_hand_trump_last(st.trump_suit)
        ai.sort_hand_trump_last(st.trump_suit)

        # Birinchi hujumchini aniqlash
        self._determine_first_attacker()
        st.phase      = PHASE_ATTACK
        st.turn_count = 0
        st.start_time = time.time()

        self._notify_state_changed()

        # Agar AI birinchi hujum qilsa
        if st.attacker.is_ai:
            self._schedule_ai_turn()

    # =========================================================================
    # HUJUM
    # =========================================================================
    def attack(self, card: Card) -> Tuple[bool, str]:
        """
        Hujumchi karta tashlaydi.
        Qaytaradi: (muvaffaqiyat, xabar)
        """
        st = self.state

        if st.phase != PHASE_ATTACK:
            return False, "Hujum fazasi emas"

        if not self._can_attack(card):
            if st.table:
                return False, "Bu qiymat stol kartasida yo'q"
            return False, "Hujum mumkin emas"

        if not st.can_add_attack:
            return False, "Qo'shimcha hujum kartasi qo'shib bo'lmaydi"

        # Kartani stolga qo'yish
        st.table.append((card, None))
        st.attacker.remove_card(card)
        st.phase = PHASE_DEFENSE

        self._notify_state_changed()

        # Agar himoyachi AI bo'lsa
        if st.defender.is_ai:
            self._schedule_ai_turn()

        return True, "OK"

    def add_attack_card(self, card: Card) -> Tuple[bool, str]:
        """
        Podkidnoy: hujumchi qo'shimcha karta qo'shadi
        (himoyachi muvaffaqiyatli yopgandan keyin)
        """
        st = self.state

        if st.phase not in (PHASE_ATTACK, PHASE_DEFENSE):
            return False, "Qo'shish mumkin emas"

        if not st.can_add_attack:
            return False, "Maksimal stolga yetildi"

        if not self._can_attack(card):
            return False, "Bu qiymat stol kartasida yo'q"

        st.table.append((card, None))
        st.attacker.remove_card(card)

        if st.phase == PHASE_ATTACK:
            st.phase = PHASE_DEFENSE

        self._notify_state_changed()

        if st.defender.is_ai:
            self._schedule_ai_turn()

        return True, "OK"

    # =========================================================================
    # HIMOYA
    # =========================================================================
    def defend(self, attack_card: Card, defense_card: Card) -> Tuple[bool, str]:
        """
        Himoyachi hujum kartasini yopadi.
        """
        st = self.state

        if st.phase != PHASE_DEFENSE:
            return False, "Himoya fazasi emas"

        if not defense_card.beats(attack_card, st.trump_suit):
            return False, f"{defense_card} → {attack_card} ni yopa olmaydi"

        # Stoldagi juftlikni yangilash
        try:
            idx = next(
                i for i, (atk, dfn) in enumerate(st.table)
                if atk == attack_card and dfn is None
            )
        except StopIteration:
            return False, "Bunday hujum kartasi topilmadi"

        st.table[idx] = (attack_card, defense_card)
        st.defender.remove_card(defense_card)

        # Barcha yopildimi?
        if st.all_defended:
            st.phase = PHASE_ATTACK   # Hujumchi qo'shishi mumkin

        self._notify_state_changed()

        if st.phase == PHASE_ATTACK and st.attacker.is_ai:
            self._schedule_ai_turn()

        return True, "OK"

    # =========================================================================
    # KARTALAR OLISH (himoyachi yopib berolmaydi)
    # =========================================================================
    def take_cards(self) -> bool:
        """
        Himoyachi barcha stol kartalarini oladi.
        Navbat o'tmaydi (hujumchi yana hujum qiladi).
        """
        st = self.state

        if st.phase not in (PHASE_ATTACK, PHASE_DEFENSE):
            return False

        all_cards = [c for pair in st.table for c in pair if c is not None]
        st.defender.take_cards(all_cards)
        st.table.clear()
        st.phase = PHASE_REFILL

        # To'ldirish: avval hujumchi
        self._refill_hands()
        st.phase = PHASE_ATTACK
        st.turn_count += 1

        self._check_winner()
        self._notify_state_changed()

        # Agar AI hujumchi bo'lsa
        if not st.is_game_over and st.attacker.is_ai:
            self._schedule_ai_turn()

        return True

    # =========================================================================
    # TURNI YAKUNLASH (himoyachi barcha yopdi)
    # =========================================================================
    def end_turn(self) -> Tuple[bool, str]:
        """
        Himoyachi muvaffaqiyatli yopgandan keyin turn tugaydi.
        Kartalar chetga, navbat o'tadi.
        """
        st = self.state

        if st.phase != PHASE_ATTACK:
            return False, "Tur tugallanmagan"

        if st.undefended_cards:
            return False, "Hali yopilmagan kartalar bor"

        if not st.table:
            return False, "Stol bo'sh"

        # Kartalarni chetga
        for pair in st.table:
            st.discarded.extend([c for c in pair if c is not None])
        st.table.clear()

        # Navbatni o'tkazish
        self._rotate_roles()

        # To'ldirish
        st.phase = PHASE_REFILL
        self._refill_hands()

        st.phase = PHASE_ATTACK
        st.turn_count += 1

        self._check_winner()
        self._notify_state_changed()

        if not st.is_game_over and st.attacker.is_ai:
            self._schedule_ai_turn()

        return True, "OK"

    # =========================================================================
    # PEREVODNOY: hujumni o'tkazish
    # =========================================================================
    def transfer_attack(self, card: Card) -> Tuple[bool, str]:
        """
        Perevodnoy rejimda himoyachi hujumni keyingi o'yinchiga o'tkazadi.
        Faqat bir xil qiymatdagi karta bilan.
        """
        if self.mode != 'perevodnoy':
            return False, "Perevodnoy rejim yoqilmagan"

        st = self.state
        if st.phase != PHASE_DEFENSE:
            return False, "Himoya fazasi emas"

        # Barcha hujum kartalari bir xil qiymatda bo'lishi kerak
        if not st.table:
            return False, "Stol bo'sh"

        first_atk = st.table[0][0]
        if card.value != first_atk.value:
            return False, "Bir xil qiymat kerak"

        # Stoldagi yopilmagan kartalar bor bo'lmasligi kerak (2 o'yinchida)
        # 2 o'yinchida Perevodnoy ishlamaydi
        # Bu versiyada 2 o'yinchi bo'lgani uchun:
        return False, "2 o'yinchida Perevodnoy ishlamaydi"

    # =========================================================================
    # AI NAVBATI
    # =========================================================================
    def _schedule_ai_turn(self):
        """AI navbatini kechiktirish bilan bajarish (UI callback orqali)"""
        if self.on_ai_turn_start:
            self.on_ai_turn_start()

    def execute_ai_turn(self):
        """
        AI harakatini bajarish.
        UI bu metodini AI delay tugagandan keyin chaqiradi.
        """
        st = self.state

        if st.is_game_over:
            return

        if st.attacker.is_ai and st.phase == PHASE_ATTACK:
            self._ai_attack()
        elif st.defender.is_ai and st.phase == PHASE_DEFENSE:
            self._ai_defend()

        if self.on_ai_turn_end:
            self.on_ai_turn_end()

    def _ai_attack(self):
        """AI hujum harakati"""
        st = self.state
        card = self.ai.choose_attack_card(st.attacker.hand, st.table, st.trump_suit)

        if card:
            self.attack(card)
            # AI qo'shimcha karta tashlashini tekshirish
            # (Podkidnoy: AI maksimal 2 ta qo'shadi)
            extra_attempts = 0
            while (st.phase == PHASE_ATTACK and st.all_defended and
                   st.can_add_attack and extra_attempts < 2):
                extra = self.ai.choose_attack_card(st.attacker.hand, st.table, st.trump_suit)
                if extra:
                    self.add_attack_card(extra)
                    extra_attempts += 1
                else:
                    break

            # Agar barcha yopilgan bo'lsa — turn tugatish
            if st.all_defended and not st.undefended_cards:
                self.end_turn()
        else:
            # Karta yo'q yoki tura olmaydi → turni tugat
            if st.all_defended:
                self.end_turn()

    def _ai_defend(self):
        """AI himoya harakati"""
        st = self.state

        if self.ai.should_take_cards(st.table, st.defender.hand, st.trump_suit):
            self.take_cards()
            return

        # Har bir yopilmagan kartani yopishga urinating
        for atk, dfn in list(st.table):
            if dfn is None:
                defense_card = self.ai.choose_defense_card(atk, st.defender.hand, st.trump_suit)
                if defense_card:
                    self.defend(atk, defense_card)
                else:
                    # Yopa olmaydi → olamiz
                    self.take_cards()
                    return

        # Agar barcha yopildi → tur tugaydi → attacker rolida qolib ketadi yoki o'tadi
        # end_turn endi human hujumchisi chaqiradi

    # =========================================================================
    # ICHKI YORDAMCHILAR
    # =========================================================================
    def _can_attack(self, card: Card) -> bool:
        """Hujum kartasi to'g'rimi?"""
        st = self.state
        if not st.table:
            return True   # Birinchi karta — istalgan
        return card.value in st.table_values

    def _determine_first_attacker(self):
        """Eng kichik kozir bor o'yinchi birinchi hujum qiladi"""
        st      = self.state
        trump   = st.trump_suit
        best_idx = -1
        best_val = 15

        for i, player in enumerate(st.players):
            for card in player.hand:
                if card.suit == trump and card.value < best_val:
                    best_val = card.value
                    best_idx = i

        if best_idx == -1:
            # Hech kimda kozir yo'q → eng kichik karta bor o'yinchi
            best_idx = 0
            b_val = 15
            for i, player in enumerate(st.players):
                for card in player.hand:
                    if card.value < b_val:
                        b_val = card.value
                        best_idx = i

        st.attacker_idx = best_idx
        st.defender_idx = 1 - best_idx

    def _rotate_roles(self):
        """Hujumchi ↔ Himoyachi navbatini o'tkazish"""
        st = self.state
        st.attacker_idx = 1 - st.attacker_idx
        st.defender_idx = 1 - st.defender_idx

    def _refill_hands(self):
        """
        Qo'sha olish: avval hujumchi, keyin himoyachi.
        """
        st = self.state
        order = [st.attacker_idx, st.defender_idx]
        for idx in order:
            if not st.deck.is_empty:
                st.players[idx].refill(st.deck)

    def _check_winner(self):
        """
        G'olibni tekshirish:
        Qo'da tugagan + qo'l bo'sh → g'olib
        """
        st = self.state
        if st.deck.is_empty:
            for p in st.players:
                if p.has_won:
                    st.winner = p
                    st.loser  = next(pl for pl in st.players if pl != p)
                    st.phase  = PHASE_END
                    st.elapsed_time = time.time() - st.start_time
                    if self.on_game_over:
                        self.on_game_over(st.winner, st.loser)
                    return

    def _notify_state_changed(self):
        if self.on_state_changed:
            self.on_state_changed(self.state)

    # ─── Tezkor kirish ────────────────────────────────────────────────────────
    @property
    def human(self) -> Optional[Player]:
        return self.state.human_player

    @property
    def ai_player(self) -> Optional[Player]:
        return self.state.ai_player

    @property
    def is_human_attacker(self) -> bool:
        return self.state.attacker and not self.state.attacker.is_ai

    @property
    def is_human_defender(self) -> bool:
        return self.state.defender and not self.state.defender.is_ai
