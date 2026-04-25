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
        1. Juftliklar (pair) bor bo'lsa — ularni ishlatish (raqibni qiynash)
        2. Kozir bo'lmagan eng kichik karta bilan boshlash
        3. Kozirlarni oxirigacha asrash
        """
        non_trump = [c for c in valid if c.suit != trump]
        trumps    = [c for c in valid if c.suit == trump]

        # Bir xil qiymatdagi juftliklar bormi? (stolga podkidnoy qilish uchun)
        if table:
            value_counts: dict = {}
            for c in non_trump:
                value_counts[c.value] = value_counts.get(c.value, 0) + 1
            # Juftliklari bor qiymatlar — raqibni ko'proq karta olishga majburlash
            paired = [c for c in non_trump if value_counts.get(c.value, 0) >= 2]
            if paired:
                return min(paired, key=lambda c: c.value)

        # Oddiy holat: kozir bo'lmagan eng kichik
        if non_trump:
            non_trump.sort(key=lambda c: c.value)
            return non_trump[0]

        # Faqat kozirlar qolgan
        if trumps:
            return min(trumps, key=lambda c: c.value)

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
        1. Bir xil mastdan MINIMAL margin bilan yopish (tejamkor)
        2. Kozirni faqat zarur holda va eng kichigini ishlatish
        3. Agar kozirlarni saqlash mumkin bo'lsa — saqla
        """
        same_suit = [c for c in possible if c.suit == atk.suit]
        if same_suit:
            # Eng kichik margin: raqibdan faqat bir qadam yuqori
            return min(same_suit, key=lambda c: c.value - atk.value)

        trump_cards = [c for c in possible if c.suit == trump]
        if trump_cards:
            # Kozirlar orasidan eng kuchsizini ishlat
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
            # 15% ehtimol bilan tasodifiy oladi (hamma vaqt ham yopa olmas)
            can_defend_all = all(
                any(c.beats(atk, trump) for c in hand)
                for atk in undefended
            )
            if not can_defend_all:
                return True
            return random.random() < 0.15

        if self.difficulty == 'medium':
            # Faqat yopib bo'lmasa oladi
            return not all(
                any(c.beats(atk, trump) for c in hand)
                for atk in undefended
            )

        # Hard: Karta iqtisodini hisoblash
        # Stoldagi kartalar soni qo'ldagi kartalar sonidan ko'p bo'lsa — olmaslik
        # Aks holda, yopib bo'lmasa yoki juda qimmat bo'lsa olish
        can_defend_all = all(
            any(c.beats(atk, trump) for c in hand)
            for atk in undefended
        )
        if not can_defend_all:
            return True

        # Qo'lda kozirlar bor, ularni sarflamaslik uchun kartalarni olish
        trump_needed = sum(
            1 for atk in undefended
            if not any(c.beats(atk, trump) for c in hand if c.suit != trump)
            and any(c.beats(atk, trump) for c in hand if c.suit == trump)
        )
        # Agar 2 dan ko'p kozir sarflash kerak bo'lsa — olgan ma'qul
        return trump_needed >= 2

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
