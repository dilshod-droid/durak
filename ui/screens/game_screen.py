"""
ui/screens/game_screen.py — Asosiy O'yin Ekrani ⭐
To'liq o'yin interfeysi: AI kartalari, stol, o'yinchi qo'li, amallar.
"""
import time
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout  import FloatLayout
from kivy.uix.boxlayout    import BoxLayout
from kivy.uix.label        import Label
from kivy.uix.widget       import Widget
from kivy.graphics         import Color, Rectangle, RoundedRectangle, Line
from kivy.animation        import Animation
from kivy.clock            import Clock
from kivy.app              import App

from core.constants        import COLORS, FONT_SIZES, AI_THINK_DELAY
from core.game_controller  import GameController
from core.game_state       import PHASE_ATTACK, PHASE_DEFENSE, PHASE_END
from core.card             import Card

from ui.widgets.hand_widget  import HandWidget
from ui.widgets.table_widget import TableWidget
from ui.widgets.deck_widget  import DeckWidget, TrumpWidget
from ui.components.luxury_button import LuxuryButton
from ui.components.animated_bg   import TableBackground


class GameScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._built              = False
        self._controller         = None
        self._ai_timer           = None
        self._game_timer         = None
        self._elapsed            = 0
        self._selected_hand_card    = None
        self._selected_attack_card  = None

    # ─── Hayot tsikli ─────────────────────────────────────────────────────────
    def on_enter(self):
        if not self._built:
            self._build_ui()
            self._built = True
        self._start_new_game()

    def on_leave(self):
        self._cancel_timers()

    # ─── UI Yaratish ──────────────────────────────────────────────────────────
    def _build_ui(self):
        root = FloatLayout()
        self.add_widget(root)

        with self.canvas.before:
            Color(*COLORS['background'])
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(
            pos=lambda *a: setattr(self._bg_rect, 'pos', self.pos),
            size=lambda *a: setattr(self._bg_rect, 'size', self.size),
        )

        # Asosiy vertikal layout
        main = BoxLayout(
            orientation = 'vertical',
            size_hint   = (1, 1),
            padding     = [10, 8, 10, 8],
            spacing     = 6,
        )
        root.add_widget(main)

        # ─── 1. AI info paneli ────────────────────────────────────────────
        ai_panel = self._build_ai_panel()
        main.add_widget(ai_panel)

        # ─── 2. AI kartalari (yopiq) ──────────────────────────────────────
        self._ai_hand = HandWidget(
            face_up    = False,
            selectable = False,
            size_hint_y = None,
            height     = 100,
        )
        main.add_widget(self._ai_hand)

        # ─── 3. Stol ──────────────────────────────────────────────────────
        table_area = self._build_table_area()
        main.add_widget(table_area)

        # ─── 4. Info paneli olib tashlandi ────────────────────────────────

        # ─── 5. O'yinchi kartalari ────────────────────────────────────────
        self._player_hand = HandWidget(
            face_up    = True,
            selectable = True,
            size_hint_y = None,
            height     = 100,
        )
        self._player_hand.on_card_selected   = self._on_player_card_selected
        self._player_hand.on_card_deselected = self._on_player_card_deselected
        self._player_hand.on_card_dropped    = self._on_player_card_dropped
        main.add_widget(self._player_hand)

        # ─── 6. Harakatlar ────────────────────────────────────────────────
        action_row = self._build_action_row()
        main.add_widget(action_row)

        # ─── Holat matni (markazda, float) ────────────────────────────────
        self._status_lbl = Label(
            text      = '',
            font_size = FONT_SIZES['small'],
            color     = COLORS['gold'],
            size_hint = (1, None),
            height    = 24,
            halign    = 'center',
            pos_hint  = {'x': 0, 'center_y': 0.5},
            opacity   = 0,
        )
        root.add_widget(self._status_lbl)

    def _build_ai_panel(self) -> BoxLayout:
        panel = BoxLayout(
            orientation = 'horizontal',
            size_hint_y = None,
            height      = 36,
            padding     = [8, 4],
            spacing     = 8,
        )
        with panel.canvas.before:
            Color(*COLORS['surface'])
            self._ai_panel_bg = RoundedRectangle(
                pos=panel.pos, size=panel.size, radius=[10]
            )
        panel.bind(
            pos=lambda *a: setattr(self._ai_panel_bg, 'pos', panel.pos),
            size=lambda *a: setattr(self._ai_panel_bg, 'size', panel.size),
        )

        self._ai_name_lbl = Label(
            text='Raqib', font_size=FONT_SIZES['small'], bold=True,
            color=COLORS['text_primary'], halign='left',
        )
        self._ai_name_lbl.bind(
            size=lambda inst, v: setattr(inst, 'text_size', (v[0], None))
        )

        self._timer_lbl = Label(
            text      = '0:00',
            font_size = FONT_SIZES['small'],
            color     = COLORS['text_muted'],
            size_hint_x = None,
            width     = 50,
            halign    = 'center',
        )

        self._ai_card_count = Label(
            text='6 karta', font_size=FONT_SIZES['small'],
            color=COLORS['text_secondary'], size_hint_x=None, width=70,
            halign='right',
        )

        self._ai_role_lbl = Label(
            text='', font_size=FONT_SIZES['tiny'],
            color=COLORS['gold'],
            size_hint_x=None, width=80, halign='center',
        )

        panel.add_widget(self._ai_name_lbl)
        panel.add_widget(self._ai_role_lbl)
        panel.add_widget(self._timer_lbl)
        panel.add_widget(self._ai_card_count)
        return panel

    def _build_table_area(self) -> BoxLayout:
        area = BoxLayout(orientation='vertical', spacing=0)

        # Stol foni
        self._table_bg = TableBackground(size_hint=(1, 1))
        area.add_widget(self._table_bg)

        # Stol widget (float layoutda)
        self._table_widget = TableWidget(
            size_hint = (0.95, 0.9),
            pos_hint  = {'center_x': 0.5, 'center_y': 0.5},
        )
        self._table_widget.on_slot_tap = self._on_table_slot_tap
        self._table_bg.add_widget(self._table_widget)

        # ixcham ma'lumot (karta soni va kozir)
        self._mini_deck_info = BoxLayout(
            orientation='horizontal', spacing=4, size_hint=(None, None), size=(100, 36),
            pos_hint={'right': 0.98, 'top': 0.98}
        )
        with self._mini_deck_info.canvas.before:
            Color(*COLORS['surface'][:3], 0.8)
            self._mdi_bg = RoundedRectangle(size=self._mini_deck_info.size, pos=self._mini_deck_info.pos, radius=[8])
            Color(*COLORS['gold'][:3], 0.4)
            self._mdi_line = Line(rounded_rectangle=[self._mini_deck_info.x, self._mini_deck_info.y, 100, 36, 8], width=1)
            
        def _update_mdi_bg(*a):
            self._mdi_bg.pos = self._mini_deck_info.pos
            self._mdi_bg.size = self._mini_deck_info.size
            self._mdi_line.rounded_rectangle = [self._mini_deck_info.x, self._mini_deck_info.y, self._mini_deck_info.width, self._mini_deck_info.height, 8]
            
        self._mini_deck_info.bind(pos=_update_mdi_bg, size=_update_mdi_bg)

        self._mini_deck_lbl = Label(text='36', font_size=FONT_SIZES['body'], color=COLORS['text_primary'], bold=True)
        self._mini_trump_lbl = Label(text='', font_name='DejaVu', font_size=FONT_SIZES['h3'], color=COLORS['red_suit'])
        self._mini_deck_info.add_widget(self._mini_deck_lbl)
        self._mini_deck_info.add_widget(self._mini_trump_lbl)
        self._table_bg.add_widget(self._mini_deck_info)

        return area



    def _build_action_row(self) -> BoxLayout:
        row = BoxLayout(
            orientation = 'horizontal',
            size_hint_y = None,
            height      = 52,
            spacing     = 12,
            padding     = [4, 0],
        )

        # O'yinchi panel
        player_info = BoxLayout(orientation='horizontal', spacing=8, size_hint_x=None, width=110)
        self._player_role_lbl = Label(
            text='', font_size=FONT_SIZES['tiny'],
            color=COLORS['gold'], halign='center',
        )
        self._player_card_count = Label(
            text='6 karta', font_size=FONT_SIZES['small'],
            color=COLORS['text_secondary'], halign='center',
        )
        player_info.add_widget(self._player_role_lbl)
        player_info.add_widget(self._player_card_count)
        row.add_widget(player_info)

        # OLISH tugmasi
        self._take_btn = LuxuryButton(text='OLISH', style='danger')
        self._take_btn.bind(on_release=lambda *a: self._on_take())
        row.add_widget(self._take_btn)

        # TUGALLASH tugmasi
        self._end_btn = LuxuryButton(text='TUGALLASH', style='primary')
        self._end_btn.bind(on_release=lambda *a: self._on_end_turn())
        row.add_widget(self._end_btn)

        return row

    # ─── O'yin boshqaruvi ─────────────────────────────────────────────────────
    def _start_new_game(self):
        app = App.get_running_app()

        diff = getattr(app, 'game_difficulty', 'medium')
        mode = getattr(app, 'game_mode',       'podkidnoy')

        self._controller = GameController(difficulty=diff, mode=mode)

        # Callback-larni ulash
        self._controller.on_state_changed = self._on_state_changed
        self._controller.on_game_over     = self._on_game_over
        self._controller.on_ai_turn_start = self._on_ai_turn_start

        # O'yinni boshlash
        self._controller.start_game()

        # Timer
        self._elapsed    = 0
        self._game_timer = Clock.schedule_interval(self._tick_timer, 1.0)

        # Audio
        if app and hasattr(app, 'audio') and app.audio:
            app.audio.on_game_start()

    def _tick_timer(self, dt):
        self._elapsed += 1
        m, s = divmod(self._elapsed, 60)
        self._timer_lbl.text = f"{m}:{s:02d}"

    def _cancel_timers(self):
        if self._ai_timer:
            self._ai_timer.cancel()
            self._ai_timer = None
        if self._game_timer:
            self._game_timer.cancel()
            self._game_timer = None

    # ─── State yangilash (Controller → UI) ───────────────────────────────────
    def _on_state_changed(self, state):
        """GameController state o'zgarganda UI ni yangilash"""
        # AI hand
        ai = state.ai_player
        if ai:
            self._ai_hand.set_cards(ai.hand)
            self._ai_card_count.text = f"{ai.card_count} karta"

        # Player hand
        human = state.human_player
        if human:
            self._player_hand.set_cards(human.hand)
            self._player_card_count.text = f"{human.card_count} karta"

        # Stol
        self._table_widget.update_table(state.table)

        # Qo'da va kozir
        self._mini_deck_lbl.text = f"{state.deck.remaining} ta"
        if state.trump_suit:
            from core.constants import SUIT_SYMBOLS, COLORS
            self._mini_trump_lbl.text = SUIT_SYMBOLS.get(state.trump_suit, '')
            self._mini_trump_lbl.color = COLORS['red_suit'] if state.trump_suit in ('hearts', 'diamonds') else COLORS['black_suit']

        # Rollar
        self._update_roles(state)

        # Tugmalar holati
        self._update_buttons(state)

        # Audio
        app = App.get_running_app()
        if app and hasattr(app, 'audio') and app.audio:
            app.audio.on_card_place()

    def _update_roles(self, state):
        """Hujumchi/himoyachi belgilarini yangilash"""
        ai_is_attacker = state.attacker and state.attacker.is_ai

        if ai_is_attacker:
            self._ai_role_lbl.text       = 'HUJUM'
            self._player_role_lbl.text   = 'HIMOYA'
        else:
            self._ai_role_lbl.text       = 'HIMOYA'
            self._player_role_lbl.text   = 'HUJUM'

    def _update_buttons(self, state):
        """Tugmalar holati"""
        c = self._controller
        is_human_def = c.is_human_defender
        is_human_atk = c.is_human_attacker

        # OLISH — faqat himoyachi ocha oladi
        can_take = (is_human_def and
                    state.phase == PHASE_DEFENSE and
                    len(state.table) > 0)
        self._take_btn.enabled = can_take
        self._take_btn.opacity = 1.0 if can_take else 0.4

        # TUGALLASH — hujumchi (barcha yopilgandan keyin) chaqiradi
        can_end = (is_human_atk and
                   state.phase == PHASE_ATTACK and
                   state.all_defended and
                   len(state.table) > 0)
        self._end_btn.enabled = can_end
        self._end_btn.opacity = 1.0 if can_end else 0.4

    def _show_status(self, text: str, duration: float = 1.5):
        self._status_lbl.text    = text
        self._status_lbl.opacity = 1
        Clock.schedule_once(
            lambda dt: Animation(opacity=0, duration=0.4).start(self._status_lbl),
            duration
        )

    # ─── O'yinchi harakatlari ─────────────────────────────────────────────────
    def _on_player_card_selected(self, card: Card, idx: int):
        """O'yinchi karta tanladi"""
        self._selected_hand_card = card
        c = self._controller
        state = c.state

        if state.phase == PHASE_END:
            return

        if c.is_human_attacker and state.phase == PHASE_ATTACK:
            # Hujum — to'g'ridan-to'g'ri karta tashlash
            ok, msg = c.attack(card)
            if ok:
                self._player_hand.deselect_all()
                self._selected_hand_card = None
                app = App.get_running_app()
                if app and hasattr(app, 'audio') and app.audio:
                    app.audio.on_card_place()
            else:
                # Podkidnoy: barcha yopilgan bo'lsa, qo'shimcha karta tashlash
                if state.all_defended and len(state.table) > 0:
                    ok2, msg2 = c.add_attack_card(card)
                    if ok2:
                        self._player_hand.deselect_all()
                        self._selected_hand_card = None
                    else:
                        w = self._player_hand.selected_widget
                        if w:
                            w.animate_invalid()
                        self._show_status(msg2)
                else:
                    w = self._player_hand.selected_widget
                    if w:
                        w.animate_invalid()
                    self._show_status(msg)

        elif c.is_human_defender and state.phase == PHASE_DEFENSE:
            # Himoya: tanlangan hujum kartasiga yopish
            if self._selected_attack_card:
                ok, msg = c.defend(self._selected_attack_card, card)
                if ok:
                    self._player_hand.deselect_all()
                    self._selected_hand_card = None
                    self._selected_attack_card = None
                    self._table_widget.clear_selection()
                    app = App.get_running_app()
                    if app and hasattr(app, 'audio') and app.audio:
                        app.audio.on_card_place()
                else:
                    w = self._player_hand.selected_widget
                    if w:
                        w.animate_invalid()
                    self._show_status(msg)
                    app = App.get_running_app()
                    if app and hasattr(app, 'audio') and app.audio:
                        app.audio.on_invalid()
            else:
                # Stoldagi yopilmagan birinchi kartani avtomatik tanlash
                undefended = state.undefended_cards
                if undefended:
                    self._selected_attack_card = undefended[0]
                    ok, msg = c.defend(self._selected_attack_card, card)
                    if ok:
                        self._player_hand.deselect_all()
                        self._selected_hand_card = None
                        self._selected_attack_card = None
                    else:
                        w = self._player_hand.selected_widget
                        if w:
                            w.animate_invalid()
                        self._show_status(msg)
                        self._selected_attack_card = None
                        app = App.get_running_app()
                        if app and hasattr(app, 'audio') and app.audio:
                            app.audio.on_invalid()


    def _on_player_card_deselected(self):
        self._selected_hand_card = None

    def _on_player_card_dropped(self, card, pos) -> bool:
        c = self._controller
        if not c: return False
        
        # O'yin stoli hududiga tushganligini tekshirish
        if not self._table_widget.collide_point(*pos):
            return False
            
        state = c.state
        if state.phase == PHASE_END:
            return False
            
        if c.is_human_attacker and state.phase == PHASE_ATTACK:
            ok, msg = c.attack(card)
            if not ok and state.all_defended and len(state.table) > 0:
                ok, msg = c.add_attack_card(card)
            
            if ok:
                self._player_hand.deselect_all()
                self._selected_hand_card = None
                app = App.get_running_app()
                if app and hasattr(app, 'audio') and app.audio: app.audio.on_card_place()
            else:
                w = self._player_hand.selected_widget
                if w: w.animate_invalid()
                self._show_status(msg)
                app = App.get_running_app()
                if app and hasattr(app, 'audio') and app.audio: app.audio.on_invalid()
                
        elif c.is_human_defender and state.phase == PHASE_DEFENSE:
            # Drop slotini aniqlash
            dropped_slot = -1
            for i, slot in enumerate(self._table_widget._slots):
                if slot.collide_point(*pos):
                    dropped_slot = i
                    break
            
            if dropped_slot >= 0:
                atk, dfn = state.table[dropped_slot]
                if dfn is None:
                    ok, msg = c.defend(atk, card)
                    if ok:
                        self._player_hand.deselect_all()
                        self._selected_hand_card = None
                        app = App.get_running_app()
                        if app and hasattr(app, 'audio') and app.audio: app.audio.on_card_place()
                    else:
                        w = self._player_hand.selected_widget
                        if w: w.animate_invalid()
                        self._show_status(msg)
                        app = App.get_running_app()
                        if app and hasattr(app, 'audio') and app.audio: app.audio.on_invalid()
                else:
                    w = self._player_hand.selected_widget
                    if w: w.animate_invalid()
                    self._show_status("Bu karta allaqachon yopilgan")
            else:
                # Agar to'g'ri slotga tushmasa, lekin faqat bitta yopilmagan karta bo'lsa, avtomat yopadi:
                undefended = state.undefended_cards
                if len(undefended) == 1:
                    ok, msg = c.defend(undefended[0], card)
                    if ok:
                        self._player_hand.deselect_all()
                        self._selected_hand_card = None
                        app = App.get_running_app()
                        if app and hasattr(app, 'audio') and app.audio: app.audio.on_card_place()
                    else:
                        w = self._player_hand.selected_widget
                        if w: w.animate_invalid()
                        self._show_status(msg)
                        app = App.get_running_app()
                        if app and hasattr(app, 'audio') and app.audio: app.audio.on_invalid()
                else:
                    w = self._player_hand.selected_widget
                    if w: w.animate_invalid()
                    self._show_status("Karta yopish uchun hujum kartasi ustiga tashlang!")
                    app = App.get_running_app()
                    if app and hasattr(app, 'audio') and app.audio: app.audio.on_invalid()
        
        return False

    def _on_table_slot_tap(self, slot_idx: int):
        """O'yinchi stoldagi kartani bosdi — himoya uchun moslashtirish"""
        c = self._controller
        if not c or not c.is_human_defender:
            return
        state = c.state
        if state.phase != PHASE_DEFENSE:
            return
        if slot_idx >= len(state.table):
            return
        atk, dfn = state.table[slot_idx]
        if dfn is not None:
            return  # Bu karta allaqachon yopilgan
        self._selected_attack_card = atk
        self._show_status('Yopish uchun qo\'lingizdan karta tanlang', duration=2.0)

    def _on_take(self):
        c = self._controller
        if not c or not c.is_human_defender:
            return
        ok = c.take_cards()
        if ok:
            app = App.get_running_app()
            if app and hasattr(app, 'audio') and app.audio:
                app.audio.on_card_take()

    def _on_end_turn(self):
        c = self._controller
        if not c:
            return
        ok, msg = c.end_turn()
        if not ok:
            self._show_status(msg)

    # ─── AI navbati ───────────────────────────────────────────────────────────
    def _on_ai_turn_start(self):
        """AI o'ylayapti — indikator ko'rsatish"""
        self._show_status('Raqib o\'ylayapti...', duration=AI_THINK_DELAY + 0.5)
        delay = AI_THINK_DELAY

        # Qiyinlikka qarab tezlik
        app = App.get_running_app()
        if app:
            diff = getattr(app, 'game_difficulty', 'medium')
            delay = {
                'easy': 0.8, 'medium': 1.2, 'hard': 1.6
            }.get(diff, 1.2)

        if self._ai_timer:
            self._ai_timer.cancel()
        self._ai_timer = Clock.schedule_once(self._execute_ai, delay)

    def _execute_ai(self, dt):
        if self._controller:
            self._controller.execute_ai_turn()
        self._ai_timer = None

    # ─── O'yin tugadi ─────────────────────────────────────────────────────────
    def _on_game_over(self, winner, loser):
        """O'yin tugadi — natija ekraniga o'tish"""
        self._cancel_timers()

        app = App.get_running_app()

        # Statistika yozish
        state = self._controller.state
        human = state.human_player
        is_win = (winner == human)

        if app and hasattr(app, 'stats') and app.stats:
            app.stats.record_game(
                result       = 'win' if is_win else 'loss',
                difficulty   = getattr(app, 'game_difficulty', 'medium'),
                mode         = getattr(app, 'game_mode', 'podkidnoy'),
                turns        = state.turn_count,
                cards_taken  = human.cards_taken if human else 0,
                duration_sec = self._elapsed,
            )

        # Audio
        if app and hasattr(app, 'audio') and app.audio:
            if is_win:
                app.audio.on_victory()
            else:
                app.audio.on_lose()

        # Natija ekraniga ma'lumot uzatish
        if app:
            app.game_result = {
                'is_win':      is_win,
                'turns':       state.turn_count,
                'cards_taken': human.cards_taken if human else 0,
                'time_sec':    self._elapsed,
            }

        Clock.schedule_once(
            lambda dt: App.get_running_app().navigate_to('result'),
            0.5
        )
