"""
core/ai_player.py — Sun'iy intellekt o'yinchi
3 ta qiyinlik darajasi: easy | medium | hard
"""
import random
from typing import List, Optional, Tuple
from core.card import Card


class AIPlayer:
    """
    Durak o'yinida AI harakatlarini belgilaydi.
    
    Easy:  Tasodifiy karta tanlov
    Medium: Eng tejamkor karta (kozirlarni asrash)
    Hard:  Strategik o'yin (raqibni qiynash, kozirlarni optimal sarflash)
    """

    def __init__(self, difficulty: str = 'medium'):
        self.difficulty = difficulty

    # =========================================================================
    # HUJUM KARTASI TANLASH
    # =========================================================================
    def choose_attack_card(
        self,
        hand:   List[Card],
        table:  List[Tuple[Card, Optional[Card]]],
        trump:  str
    ) -> Optional[Card]:
        """
        Hujum uchun eng yaxshi kartani tanlash.
        Birinchi hujum yoki qo'shimcha hujum bo'lishi mumkin.
        """
        valid = self._get_valid_attacks(hand, table)
        if not valid:
            return None

        if self.difficulty == 'easy':
            return self._attack_easy(valid, trump)
        elif self.difficulty == 'medium':
            return self._attack_medium(valid, trump)
        else:
            return self._attack_hard(valid, trump, hand, table)

    def _attack_easy(self, valid: List[Card], trump: str) -> Optional[Card]:
        """Tasodifiy karta"""
        return random.choice(valid)

    def _attack_medium(self, valid: List[Card], trump: str) -> Optional[Card]:
        """
        Kozir bo'lmagan eng kichik karta bilan hujum.
        Agar faqat kozir bo'lsa — eng kichik kozir.
        """
        non_trump = [c for c in valid if c.suit != trump]
        pool = non_trump if non_trump else valid
        return min(pool, key=lambda c: c.value)

    def _attack_hard(
        self,
        valid:  List[Card],
        trump:  str,
        hand:   List[Card],
        table:  List[Tuple[Card, Optional[Card]]]
    ) -> Optional[Card]:
        """
        Strategik hujum:
        1. Raqib qo'lida ko'p bo'lgan qiymatlarni tashlash
        2. Kozirlarni oxirgacha saqlash
        3. Eng kichik qiymatli o'lim kartasini sinab ko'rish
        """
        non_trump = [c for c in valid if c.suit != trump]
        trumps    = [c for c in valid if c.suit == trump]

        if non_trump:
            # Eng kichik ikki karta
            non_trump.sort(key=lambda c: c.value)
            return non_trump[0]
        elif trumps:
            trumps.sort(key=lambda c: c.value)
            return trumps[0]
        return None

    # =========================================================================
    # HIMOYA KARTASI TANLASH
    # =========================================================================
    def choose_defense_card(
        self,
        attack_card: Card,
        hand:        List[Card],
        trump:       str
    ) -> Optional[Card]:
        """
        Hujum kartasini yopish uchun eng tejamkor kartani tanlash.
        """
        possible = [c for c in hand if c.beats(attack_card, trump)]

        if not possible:
            return None

        if self.difficulty == 'easy':
            return self._defend_easy(possible, attack_card, trump)
        elif self.difficulty == 'medium':
            return self._defend_medium(possible, attack_card, trump)
        else:
            return self._defend_hard(possible, attack_card, trump)

    def _defend_easy(self, possible: List[Card], atk: Card, trump: str) -> Optional[Card]:
        """Tasodifiy yopish"""
        return random.choice(possible)

    def _defend_medium(self, possible: List[Card], atk: Card, trump: str) -> Optional[Card]:
        """
        Eng tejamkor yopish:
        1. Bir xil mastdan eng kichik
        2. Kozir bilan yopish majburlansa — eng kichik kozir
        """
        same_suit = [c for c in possible if c.suit == atk.suit]
        if same_suit:
            return min(same_suit, key=lambda c: c.value)
        return min(possible, key=lambda c: c.value)

    def _defend_hard(self, possible: List[Card], atk: Card, trump: str) -> Optional[Card]:
        """
        Optimal yopish:
        1. Bir xil mastdan minimal margin bilan yopish
        2. Kozirni faqat zarur hollarda ishlatish
        """
        same_suit = [c for c in possible if c.suit == atk.suit]
        if same_suit:
            # Eng kichik margin bilan yopish
            return min(same_suit, key=lambda c: c.value - atk.value)

        trump_cards = [c for c in possible if c.suit == trump]
        if trump_cards:
            return min(trump_cards, key=lambda c: c.value)

        return min(possible, key=lambda c: c.value)

    # =========================================================================
    # KARTALARNI OLISH QARORI
    # =========================================================================
    def should_take_cards(
        self,
        table:  List[Tuple[Card, Optional[Card]]],
        hand:   List[Card],
        trump:  str
    ) -> bool:
        """
        Kartalarni olish kerakmi yoki barcha yopishga urinishmi?
        """
        undefended = [atk for atk, dfn in table if dfn is None]

        if not undefended:
            return False

        if self.difficulty == 'easy':
            # 30% ehtimol bilan oladi (hamma vaqt ham yopa olmas)
            can_defend_all = all(
                any(c.beats(atk, trump) for c in hand)
                for atk in undefended
            )
            if not can_defend_all:
                return True
            return random.random() < 0.15

        # Medium va Hard: faqat yopib bo'lmasa oladi
        return not all(
            any(c.beats(atk, trump) for c in hand)
            for atk in undefended
        )

    # =========================================================================
    # YORDAMCHILAR
    # =========================================================================
    def _get_valid_attacks(
        self,
        hand:  List[Card],
        table: List[Tuple[Card, Optional[Card]]]
    ) -> List[Card]:
        """
        Qo'ldagi hujum uchun yaroqli kartalar.
        Birinchi hujumda — hammasi.
        Podkidnoyda — stoldagi qiymatga to'g'ri keladigan.
        """
        if not table:
            return list(hand)

        table_values = set()
        for atk, dfn in table:
            table_values.add(atk.value)
            if dfn:
                table_values.add(dfn.value)

        return [c for c in hand if c.value in table_values]

    def get_best_opening_card(self, hand: List[Card], trump: str) -> Optional[Card]:
        """O'yin boshida birinchi hujum kartasi"""
        return self._attack_medium(list(hand), trump)
