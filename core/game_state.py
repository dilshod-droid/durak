"""
core/game_state.py — O'yin holati
"""
from typing import List, Tuple, Optional, TYPE_CHECKING
from core.card import Card

if TYPE_CHECKING:
    from core.deck   import Deck
    from core.player import Player

# ─── Faza konstantalari ───────────────────────────────────────────────────────
PHASE_ATTACK  = 'attack'
PHASE_DEFENSE = 'defense'
PHASE_REFILL  = 'refill'
PHASE_END     = 'end'


class GameState:
    """
    O'yinning to'liq holati.
    Controller bu sinfdan foydalanib holat o'zgarishlarini kuzatadi.
    """

    def __init__(self):
        # ─── Asosiy ob'ektlar ─────────────────────────────────────────────
        self.deck:    Optional['Deck']    = None
        self.players: List['Player']      = []

        # ─── Rollar ───────────────────────────────────────────────────────
        self.attacker_idx: int = 0
        self.defender_idx: int = 1

        # ─── Stol holati ──────────────────────────────────────────────────
        # Har bir element: (hujum_karta, himoya_karta | None)
        self.table: List[Tuple[Card, Optional[Card]]] = []

        # ─── Chetlangan kartalar ──────────────────────────────────────────
        self.discarded: List[Card] = []

        # ─── Faza ─────────────────────────────────────────────────────────
        self.phase: str = PHASE_ATTACK

        # ─── Natija ───────────────────────────────────────────────────────
        self.winner: Optional['Player'] = None
        self.loser:  Optional['Player'] = None

        # ─── Statistika ───────────────────────────────────────────────────
        self.turn_count:    int   = 0
        self.start_time:    float = 0.0
        self.elapsed_time:  float = 0.0

    # ─── Xossa yordam ─────────────────────────────────────────────────────────
    @property
    def trump_suit(self) -> Optional[str]:
        return self.deck.trump_suit if self.deck else None

    @property
    def trump_card(self):
        return self.deck.trump_card if self.deck else None

    @property
    def attacker(self) -> Optional['Player']:
        if self.players:
            return self.players[self.attacker_idx]
        return None

    @property
    def defender(self) -> Optional['Player']:
        if self.players:
            return self.players[self.defender_idx]
        return None

    @property
    def human_player(self) -> Optional['Player']:
        for p in self.players:
            if not p.is_ai:
                return p
        return None

    @property
    def ai_player(self) -> Optional['Player']:
        for p in self.players:
            if p.is_ai:
                return p
        return None

    @property
    def undefended_cards(self) -> List[Card]:
        """Hali yopilmagan hujum kartalari"""
        return [atk for atk, dfn in self.table if dfn is None]

    @property
    def all_defended(self) -> bool:
        """Barcha hujum kartalari yopildimi?"""
        return len(self.table) > 0 and all(dfn is not None for _, dfn in self.table)

    @property
    def table_size(self) -> int:
        return len(self.table)

    @property
    def can_add_attack(self) -> bool:
        """
        Qo'shimcha hujum kartasi tashlash mumkinmi?
        Max 6 ta juft, va himoyachining qo'lidan oshmaydi.
        """
        if len(self.table) >= 6:
            return False
        defender = self.defender
        if defender and len(self.table) >= defender.card_count:
            return False
        return True

    @property
    def table_values(self) -> set:
        """Stoldagi barcha kartalar qiymatlari"""
        vals = set()
        for atk, dfn in self.table:
            vals.add(atk.value)
            if dfn:
                vals.add(dfn.value)
        return vals

    @property
    def is_game_over(self) -> bool:
        return self.phase == PHASE_END

    def __repr__(self):
        atk = self.attacker.name if self.attacker else '?'
        dfn = self.defender.name if self.defender else '?'
        return (f"GameState(phase={self.phase}, turn={self.turn_count}, "
                f"atk={atk}, def={dfn}, table={len(self.table)})")

    def to_dict(self):
        return {
            'trump_card': self.trump_card.to_dict() if self.trump_card else None,
            'players': [p.to_dict() for p in self.players],
            'attacker_idx': self.attacker_idx,
            'defender_idx': self.defender_idx,
            'table': [(atk.to_dict(), dfn.to_dict() if dfn else None) 
                      for atk, dfn in self.table],
            'phase': self.phase,
            'turn_count': self.turn_count,
            'is_deck_empty': self.deck.is_empty if self.deck else True,
            'deck_count': self.deck.card_count if self.deck else 0
        }

    def from_dict(self, d):
        from core.player import Player
        from core.card   import Card
        
        self.players = [Player.from_dict(p) for p in d['players']]
        self.attacker_idx = d['attacker_idx']
        self.defender_idx = d['defender_idx']
        
        # Table parsing: allow second card (defense) to be None
        self.table = []
        for atk_d, dfn_d in d['table']:
            self.table.append((
                Card.from_dict(atk_d),
                Card.from_dict(dfn_d) if dfn_d else None
            ))
            
        self.phase = d['phase']
        self.turn_count = d['turn_count']
        
        # Trump card and Deck count (Client side "Ghost Deck")
        from core.deck import Deck
        if not self.deck: 
            self.deck = Deck()
            self.deck.clear() # Clear initial deck
        
        if d['trump_card']:
            self.deck.trump_card = Card.from_dict(d['trump_card'])
            self.deck.trump_suit = self.deck.trump_card.suit
        
        # Override counts for UI
        self.deck._override_count = d.get('deck_count', 0)
        self.deck._is_empty_flag = d.get('is_deck_empty', True)
