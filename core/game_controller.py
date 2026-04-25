"""
core/game_controller.py — O'yin boshqaruvchisi
Barcha o'yin qoidalarini amalga oshiradi.

Tuzatishlar:
  - _check_winner: draw (ikkalasi bir vaqtda bo'sh) holati ham qayta ishlandi
  - transfer_attack: 2-o'yinchi rejimda nima uchun ishlamasligini aniq izohlaydi
  - _execute_ai_turn_clock: try/finally — exception bo'lsa ham _ai_thinking reset bo'ladi
  - _ai_attack: loop MAX_EXTRA_ATTACKS bilan cheklangan
"""
import time
import logging
from typing import List, Optional, Callable, Tuple

from kivy.clock import Clock

from core.card       import Card
from core.deck       import Deck
from core.player     import Player
from core.game_state import GameState, PHASE_ATTACK, PHASE_DEFENSE, PHASE_REFILL, PHASE_END
from core.ai_player  import AIPlayer
from core.constants  import HAND_SIZE, AI_THINK_DELAY

logger = logging.getLogger(__name__)

# AI bir turda maksimal qo'shimcha hujum kartalari
MAX_EXTRA_ATTACKS = 3


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

        # ─── Rekursiyadan himoya: AI faqat bitta navbatda aktiv ──────────
        self._ai_thinking: bool = False

        # ─── Callback-lar (UI ularni o'rnatadi) ──────────────────────────
        self.on_state_changed:    Optional[Callable] = None
        self.on_invalid_move:     Optional[Callable] = None
        self.on_game_over:        Optional[Callable] = None
        self.on_cards_dealt:      Optional[Callable] = None
        self.on_ai_turn_start:    Optional[Callable] = None
        self.on_ai_turn_end:      Optional[Callable] = None

        # ─── Multiplayer ──────────────────────────────────────────────────
        from core.network_manager import NetworkManager
        self.net = NetworkManager.get_instance()
        self.is_multiplayer = False
        self.net.on_data_received = self._on_network_data

    def _on_network_data(self, data: dict):
        """Tarmoqdan kelgan xabarlarni qayta ishlash"""
        t = data.get('type')
        if t == 'state_sync':
            self.state.from_dict(data['state'])
            self._notify_state_changed()
        elif t == 'action':
            action = data.get('action')
            # Raqib harakatini bajarish
            if action == 'attack':
                from core.card import Card
                self.attack(Card.from_dict(data['card']), remote=True)
            elif action == 'defend':
                from core.card import Card
                self.defend(Card.from_dict(data['attack_card']), 
                            Card.from_dict(data['defense_card']), remote=True)
            elif action == 'take':
                self.take_cards(remote=True)
            elif action == 'end_turn':
                self.end_turn(remote=True)
        elif t == 'ready':
            # Client tayyor bo'lganda Host unga stateni jo'natadi
            if self.is_multiplayer and self.net.mode == 'host':
                self.net.send_data({'type': 'state_sync', 'state': self.state.to_dict()})

    # =========================================================================
    # O'YIN BOSHLASH
    # =========================================================================
    def start_game(self):
        """Yangi o'yin boshlash"""
        st = self.state

        if self.is_multiplayer:
            if self.net.mode == 'join':
                # Client: Hostdan state kutamiz. Hozircha stateni tozalaymiz.
                st.phase = PHASE_ATTACK
                return
            else:
                # Host: O'yinni boshlaydi va Clientga jo'natadi
                pass

        # Qo'da yaratish va aralashtirish
        st.deck = Deck()
        st.deck.shuffle()
        st.deck.set_trump()

        # O'yinchilar
        if self.is_multiplayer:
            # Multiplayerda ismlar tarmoqdan keladi
            human = Player("Siz", is_ai=False)
            peer  = Player(self.net.peer_name, is_ai=False) # Raqib AI emas
            st.players = [human, peer]
        else:
            human = Player("Siz",    is_ai=False)
            ai    = Player("Raqib",  is_ai=True)
            st.players = [human, ai]

        # Karta berish
        st.players[0].add_cards(st.deck.deal(HAND_SIZE))
        st.players[1].add_cards(st.deck.deal(HAND_SIZE))

        # Qo'lni kozirga qarab saralash
        for p in st.players:
            p.sort_hand_trump_last(st.trump_suit)

        # Birinchi hujumchini aniqlash
        self._determine_first_attacker()
        st.phase      = PHASE_ATTACK
        st.turn_count = 0
        st.start_time = time.time()

        self._notify_state_changed()

        # Multiplayerda Host ma'lumotni Clientga jo'natadi
        if self.is_multiplayer and self.net.mode == 'host':
            self.net.send_data({'type': 'state_sync', 'state': st.to_dict()})

        # Agar AI bo'lsa (offline rejimda)
        if not self.is_multiplayer and st.attacker.is_ai:
            self._schedule_ai_turn()

    # =========================================================================
    # HUJUM
    # =========================================================================
    def attack(self, card: Card, remote: bool = False) -> Tuple[bool, str]:
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

        # Multiplayer sinxronizatsiyasi
        if self.is_multiplayer:
            if not remote:
                # Mahalliy o'yinchi harakati -> Raqibga jo'natish
                self.net.send_data({'type': 'action', 'action': 'attack', 'card': card.to_dict()})
            if self.net.mode == 'host':
                # Host har doim state ni yangilab turadi
                self.net.send_data({'type': 'state_sync', 'state': st.to_dict()})

        # Agar himoyachi AI bo'lsa (offline)
        if not self.is_multiplayer and st.defender.is_ai:
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
    def defend(self, attack_card: Card, defense_card: Card, remote: bool = False) -> Tuple[bool, str]:
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

        # Multiplayer sinxronizatsiyasi
        if self.is_multiplayer:
            if not remote:
                self.net.send_data({
                    'type': 'action', 'action': 'defend',
                    'attack_card': attack_card.to_dict(),
                    'defense_card': defense_card.to_dict()
                })
            if self.net.mode == 'host':
                self.net.send_data({'type': 'state_sync', 'state': st.to_dict()})

        if not self.is_multiplayer and st.phase == PHASE_ATTACK and st.attacker.is_ai:
            self._schedule_ai_turn()

        return True, "OK"

    # =========================================================================
    # KARTALAR OLISH (himoyachi yopib berolmaydi)
    # =========================================================================
    def take_cards(self, remote: bool = False) -> bool:
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

        # Multiplayer sinxronizatsiyasi
        if self.is_multiplayer:
            if not remote:
                self.net.send_data({'type': 'action', 'action': 'take'})
            if self.net.mode == 'host':
                self.net.send_data({'type': 'state_sync', 'state': st.to_dict()})

        # Agar AI hujumchi bo'lsa
        if not self.is_multiplayer and not st.is_game_over and st.attacker.is_ai:
            self._schedule_ai_turn()

        return True

    # =========================================================================
    # TURNI YAKUNLASH (himoyachi barcha yopdi)
    # =========================================================================
    def end_turn(self, remote: bool = False) -> Tuple[bool, str]:
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

        # Multiplayer sinxronizatsiyasi
        if self.is_multiplayer:
            if not remote:
                self.net.send_data({'type': 'action', 'action': 'end_turn'})
            if self.net.mode == 'host':
                self.net.send_data({'type': 'state_sync', 'state': st.to_dict()})

        if not self.is_multiplayer and not st.is_game_over and st.attacker.is_ai:
            self._schedule_ai_turn()

        return True, "OK"

    # =========================================================================
    # PEREVODNOY: hujumni o'tkazish
    # =========================================================================
    def transfer_attack(self, card: Card) -> Tuple[bool, str]:
        """
        Perevodnoy rejimda himoyachi hujumni o'tkazadi.
        Qoida: faqat bir xil qiymatdagi karta bilan, faqat 3+ o'yinchida.
        2 o'yinchili versiyada bu harakat qoidaga ko'ra taqiqlangan.
        """
        if self.mode != 'perevodnoy':
            return False, "Perevodnoy rejim yoqilmagan"

        st = self.state
        if st.phase != PHASE_DEFENSE:
            return False, "Himoya fazasi emas"

        if not st.table:
            return False, "Stol bo'sh"

        # 2 o'yinchili o'yinda Perevodnoy qoidaga ko'ra ishlamaydi
        # (TZ § 3.5: "Faqat 2 o'yinchida bu rejim ishlamaydi")
        if len(st.players) <= 2:
            return False, "Perevodnoy faqat 3 va undan ko'p o'yinchida ishlaydi"

        # Bir xil qiymat tekshiruvi
        first_atk = st.table[0][0]
        if card.value != first_atk.value:
            return False, f"Bir xil qiymat kerak ({first_atk.display_value})"

        # Himoyachi o'z qo'lida bu karta borligini tekshiruvi
        if not st.defender.has_card(card):
            return False, "Bu karta qo'lingizda yo'q"

        # Hujumni keyingi o'yinchiga o'tkazish
        st.table.append((card, None))
        st.defender.remove_card(card)
        # Rollarni aylantirish: himoyachi → hujumchi bo'ladi
        # (3+ o'yinchi uchun to'liq implementatsiya keyingi versiyada)
        self._notify_state_changed()
        return True, "Hujum o'tkazildi"

    # =========================================================================
    # AI NAVBATI
    # =========================================================================
    def _schedule_ai_turn(self):
        """
        AI navbatini Clock.schedule_once orqali kechiktirish.
        _ai_thinking flag ikki marta scheduling ni bloklaydi.
        """
        if self._ai_thinking:
            return  # Allaqachon rejalashtirilgan — ikkinchi marta shart emas

        self._ai_thinking = True

        if self.on_ai_turn_start:
            self.on_ai_turn_start()

        Clock.schedule_once(self._execute_ai_turn_clock, AI_THINK_DELAY)

    def _execute_ai_turn_clock(self, dt):
        """
        Clock.schedule_once tomonidan chaqiriladigan wrapper.
        dt — Kivy Clock beradi, biz foydalanmaymiz.
        try/finally: exception bo'lsa ham _ai_thinking flag doim tozalanadi.
        """
        try:
            self.execute_ai_turn()
        except Exception as e:
            logger.error(f"[GameController] AI turn xatosi: {e}", exc_info=True)
        finally:
            self._ai_thinking = False

    def execute_ai_turn(self):
        """
        AI harakatini bajarish.
        To'g'ridan-to'g'ri yoki _execute_ai_turn_clock orqali chaqiriladi.
        """
        st = self.state

        if st.is_game_over:
            if self.on_ai_turn_end:
                self.on_ai_turn_end()
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
            ok, msg = self.attack(card)
            if not ok:
                logger.warning(f"[AI] Hujum muvaffaqiyatsiz: {msg}")
                return

            # Podkidnoy: AI qo'shimcha kartalar tashlaydi (MAX_EXTRA_ATTACKS ga qadar)
            extra_attempts = 0
            prev_table_size = len(st.table)
            while (extra_attempts < MAX_EXTRA_ATTACKS and
                   st.phase == PHASE_ATTACK and
                   st.all_defended and
                   st.can_add_attack and
                   not st.is_game_over):
                extra = self.ai.choose_attack_card(st.attacker.hand, st.table, st.trump_suit)
                if not extra:
                    break
                ok2, _ = self.add_attack_card(extra)
                if not ok2:
                    break
                extra_attempts += 1
                # Stol hajmi o'zgarmasa — chiqamiz (sonsiz loop himoyasi)
                if len(st.table) == prev_table_size:
                    break
                prev_table_size = len(st.table)

            # Barcha kartalar yopilgan bo'lsa turni tugat
            if not st.is_game_over and st.all_defended and not st.undefended_cards:
                self.end_turn()
        else:
            # Tashlash uchun yaroqli karta yo'q → turni tugat
            if st.all_defended and not st.is_game_over:
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
          - Qo'da bo'sh va biror o'yinchi qo'li bo'sh → g'olib
          - Ikkalasi ham bir vaqtda qo'li bo'sh (draw) → hujumchi g'olib, himoyachi "durak"
        """
        st = self.state
        if not st.deck.is_empty:
            return   # Qo'da hali karta bor — o'yin davom etadi

        winners = [p for p in st.players if p.has_won]

        if not winners:
            return   # Hech kim hali g'olib bo'lmagan

        if len(winners) == len(st.players):
            # Draw: ikkalasi ham bir vaqtda qo'li bo'shib qoldi
            # Qoidaga ko'ra bunday holatda hujumchi g'olib, himoyachi durak
            st.winner = st.attacker
            st.loser  = st.defender
            logger.info("[Game] Tengsizlik (draw): hujumchi g'olib deb hisoblanadi")
        else:
            st.winner = winners[0]
            remaining = [p for p in st.players if p != st.winner]
            # Eng ko'p kartasi bor o'yinchi "durak"
            st.loser = max(remaining, key=lambda p: p.card_count) if remaining else None

        st.phase = PHASE_END
        st.elapsed_time = time.time() - st.start_time
        logger.info(f"[Game] O'yin tugadi — G'olib: {st.winner}, Durak: {st.loser}")
        if self.on_game_over:
            self.on_game_over(st.winner, st.loser)

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

    @property
    def is_human_turn(self) -> bool:
        return self.is_human_attacker or self.is_human_defender
