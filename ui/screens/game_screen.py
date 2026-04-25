"""
ui/screens/game_screen.py — Asosiy O'yin Ekrani
Luxury dizayn: AI kartalari tepada, stol markazda, o'yinchi pastda.
45 soniyalik navbat taymer + avto-olish, hint ko'rsatgich.

Tuzatishlar:
  - PauseOverlay, TimerRing, DeckBadge → game_overlays.py dan import qilinadi
  - _start_new_game: network disconnect callback ulandi
  - _show_status: ikki xil implement birlashtirilib, rangi to'g'ri reset bo'ladi
"""
import math
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout   import FloatLayout
from kivy.uix.boxlayout     import BoxLayout
from kivy.uix.widget        import Widget
from kivy.uix.label         import Label
from kivy.graphics          import (Color, Rectangle, RoundedRectangle,
                                     Line, Ellipse)
from kivy.animation         import Animation
from kivy.clock             import Clock
from kivy.app               import App
from kivy.core.text         import Label as CoreLabel

from core.constants         import COLORS, FONT_SIZES, AI_THINK_DELAY, SUIT_SYMBOLS
from core.game_controller   import GameController
from core.game_state        import PHASE_ATTACK, PHASE_DEFENSE, PHASE_END
from core.card              import Card

from ui.widgets.hand_widget   import HandWidget
from ui.widgets.table_widget  import TableWidget
from ui.components.luxury_button  import LuxuryButton
from ui.components.animated_bg    import TableBackground
from ui.components.game_overlays  import PauseOverlay, TimerRing, DeckBadge

# ─────────────────────────────────────────────────────────────────────────────
# PauseOverlay, TimerRing, DeckBadge → ui/components/game_overlays.py da
# ─────────────────────────────────────────────────────────────────────────────
TURN_TIMEOUT = 45   # soniya


# ─────────────────────────────────────────────────────────────────────────────
# Asosiy ekran
# ─────────────────────────────────────────────────────────────────────────────
class GameScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._built              = False
        self._controller         = None
        self._game_timer         = None     # Umumiy o'yin vaqti (daqiqa:soniya)
        self._elapsed            = 0
        self._turn_timer         = None     # 45 soniyalik navbat taymeri
        self._turn_remaining     = TURN_TIMEOUT
        self._selected_hand_card = None
        self._selected_atk_card  = None     # Himoya uchun tanlangan hujum kartasi

    # ─── Hayot tsikli ─────────────────────────────────────────────────────────
    def on_enter(self):
        if not self._built:
            self._build_ui()
            self._built = True
        self._start_new_game()

    def on_leave(self):
        self._cancel_all_timers()

    # ─── UI Yaratish ──────────────────────────────────────────────────────────
    def _build_ui(self):
        root = FloatLayout()
        self.add_widget(root)

        # Fon
        with self.canvas.before:
            Color(*COLORS['background'])
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(
            pos  = lambda *a: setattr(self._bg_rect, 'pos',  self.pos),
            size = lambda *a: setattr(self._bg_rect, 'size', self.size),
        )

        # ── Asosiy layout ─────────────────────────────────────────────────
        main = BoxLayout(
            orientation = 'vertical',
            size_hint   = (1, 1),
            padding     = [8, 6, 8, 6],
            spacing     = 4,
        )
        root.add_widget(main)

        # 1. AI info paneli
        main.add_widget(self._build_ai_panel())

        # 2. AI kartalari (tepada, yopiq)
        self._ai_hand = HandWidget(
            face_up      = False,
            selectable   = False,
            is_opponent  = True,
            size_hint_y  = None,
            height       = 90,
        )
        main.add_widget(self._ai_hand)

        # 3. Stol maydoni
        table_area = self._build_table_area()
        main.add_widget(table_area)

        # 4. O'yinchi kartalari (pastda, ochiq)
        self._player_hand = HandWidget(
            face_up     = True,
            selectable  = True,
            size_hint_y = None,
            height      = 110,
        )
        self._player_hand.on_card_selected   = self._on_player_card_selected
        self._player_hand.on_card_deselected = self._on_player_card_deselected
        self._player_hand.on_card_dropped    = self._on_player_card_dropped
        main.add_widget(self._player_hand)

        # 5. Amallar qatori
        main.add_widget(self._build_action_row())

        # (Status label removed)

        # Float: hint banner (stol ustida - yozuv kattalashtirildi)
        self._hint_banner = Label(
            text      = '',
            font_size = 18,
            color     = (0.3, 1.0, 0.5, 1),
            size_hint = (0.9, None),
            height    = 32,
            halign    = 'center', # Corrected indentation
            pos_hint  = {'center_x': 0.5, 'center_y': 0.38},
            opacity   = 0,
        )
        self._hint_banner.bind(
            size=lambda inst, v: setattr(inst, 'text_size', v)
        )
        root.add_widget(self._hint_banner)

        # Loading overlay for multiplayer
        self._loading_overlay = FloatLayout(opacity=0)
        with self._loading_overlay.canvas.before:
            Color(0, 0, 0, 0.8)
            self._loading_bg = Rectangle(pos=self.pos, size=self.size)
        self._loading_lbl = Label(text="RAQIB KUTILMOQDA...", font_size=20, color=COLORS['gold'])
        self._loading_overlay.add_widget(self._loading_lbl)
        self._loading_overlay.bind(size=self._upd_loading_bg, pos=self._upd_loading_bg)
        root.add_widget(self._loading_overlay)

    # ── AI paneli ─────────────────────────────────────────────────────────────
    def _build_ai_panel(self) -> BoxLayout:
        panel = BoxLayout(
            orientation = 'horizontal',
            size_hint_y = None,
            height      = 40,
            padding     = [10, 4],
            spacing     = 10,
        )
        # Pauza tugmasi (Canvas orqali 3ta chiziq chizish)
        from kivy.uix.button import Button
        self._btn_menu = Button(
            size_hint_x=None, width=32,
            background_normal='', background_color=(0,0,0,0),
        )
        with self._btn_menu.canvas.after:
            Color(*COLORS['gold'])
            # 3ta chiziqcha
            for i in range(3):
                y_pos = self._btn_menu.y + 12 + i*8
                Line(points=[self._btn_menu.x + 6, y_pos, self._btn_menu.x + 26, y_pos], width=1.3)
        
        # Pozitsiya o'zgarganda chiziqlarni yangilash
        def _refresh_lines(*a):
            self._btn_menu.canvas.after.clear()
            with self._btn_menu.canvas.after:
                Color(*COLORS['gold'])
                for i in range(3):
                    y_pos = self._btn_menu.y + 12 + i*8
                    Line(points=[self._btn_menu.x + 6, y_pos, self._btn_menu.x + 26, y_pos], width=1.3)
        self._btn_menu.bind(pos=_refresh_lines, size=_refresh_lines)

        self._btn_menu.bind(on_release=lambda *a: self._toggle_pause())
        panel.add_widget(self._btn_menu)

        with panel.canvas.before:
            Color(*COLORS['surface'])
            self._ai_panel_bg = RoundedRectangle(pos=panel.pos, size=panel.size, radius=[12])
            Color(*COLORS['gold'][:3], 0.3)
            self._ai_panel_line = Line(
                rounded_rectangle=[panel.x, panel.y, panel.width, panel.height, 12],
                width=0.8
            )
        def _upd(*a):
            self._ai_panel_bg.pos  = panel.pos
            self._ai_panel_bg.size = panel.size
            self._ai_panel_line.rounded_rectangle = [panel.x, panel.y, panel.width, panel.height, 12]
        panel.bind(pos=_upd, size=_upd)

        self._ai_name_lbl = Label(
            text='Raqib', font_size=FONT_SIZES['small'], bold=True,
            color=COLORS['text_primary'], halign='left',
        )
        self._ai_name_lbl.bind(size=lambda i, v: setattr(i, 'text_size', (v[0], None)))

        self._ai_role_lbl = Label(
            text='', font_size=FONT_SIZES['tiny'],
            color=COLORS['gold'], size_hint_x=None, width=75, halign='center',
        )

        self._ai_card_lbl = Label(
            text='6 karta', font_size=FONT_SIZES['tiny'],
            color=COLORS['text_secondary'], size_hint_x=None, width=60, halign='right',
        )

        # Umumiy o'yin vaqti
        self._game_time_lbl = Label(
            text='0:00', font_size=FONT_SIZES['tiny'],
            color=COLORS['text_muted'], size_hint_x=None, width=42, halign='center',
        )

        panel.add_widget(self._ai_name_lbl)
        panel.add_widget(self._ai_role_lbl)
        panel.add_widget(self._ai_card_lbl)
        panel.add_widget(self._game_time_lbl)
        return panel

    # ── Stol maydoni ──────────────────────────────────────────────────────────
    def _build_table_area(self) -> Widget:
        """Stol + deck badge (pastki-o'ng) + taymer doirasi (pastki-chap)"""
        area = FloatLayout(size_hint=(1, 1))

        # Stol foni (yashil baxmal)
        self._table_bg = TableBackground(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        area.add_widget(self._table_bg)

        # Stol widget (kartalar ko'rinadigan joy)
        self._table_widget = TableWidget(
            size_hint = (0.92, 0.88),
            pos_hint  = {'center_x': 0.5, 'center_y': 0.5},
        )
        self._table_widget.on_slot_tap = self._on_table_slot_tap
        area.add_widget(self._table_widget)

        # Deck badge — pastki-o'ng burchak
        self._deck_badge = DeckBadge(
            pos_hint = {'right': 0.99, 'y': 0.01},
        )
        area.add_widget(self._deck_badge)

        # Taymer doirasi — pastki-chap burchak
        self._turn_ring = TimerRing(
            total    = TURN_TIMEOUT,
            pos_hint = {'x': 0.01, 'y': 0.01},
        )
        area.add_widget(self._turn_ring)

        return area

    # ── Amallar qatori ────────────────────────────────────────────────────────
    def _build_action_row(self) -> BoxLayout:
        row = BoxLayout(
            orientation = 'horizontal',
            size_hint_y = None,
            height      = 50,
            spacing     = 8,
            padding     = [4, 0],
        )

        # O'yinchi info
        info = BoxLayout(orientation='vertical', size_hint_x=None, width=90, spacing=0)
        self._player_role_lbl = Label(
            text='', font_size=FONT_SIZES['tiny'],
            color=COLORS['gold'], halign='center',
        )
        self._player_card_lbl = Label(
            text='6 karta', font_size=FONT_SIZES['tiny'],
            color=COLORS['text_secondary'], halign='center',
        )
        info.add_widget(self._player_role_lbl)
        info.add_widget(self._player_card_lbl)
        row.add_widget(info)

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
        app  = App.get_running_app()
        diff = getattr(app, 'game_difficulty', 'medium')
        mode = getattr(app, 'game_mode',       'podkidnoy')

        self._controller = GameController(difficulty=diff, mode=mode)
        self._controller.is_multiplayer = getattr(app, 'is_multiplayer', False)

        self._controller.on_state_changed = self._on_state_changed
        self._controller.on_game_over     = self._on_game_over
        self._controller.on_ai_turn_start = self._on_ai_turn_start

        # ✅ Network disconnect callback ulash
        if hasattr(self._controller, 'net') and self._controller.net:
            self._controller.net.on_disconnected = self._on_network_disconnected

        self._elapsed        = 0
        self._turn_remaining = TURN_TIMEOUT
        self._selected_hand_card = None
        self._selected_atk_card  = None

        self._controller.start_game()

        # Umumiy o'yin vaqti
        self._game_timer = Clock.schedule_interval(self._tick_game_timer, 1.0)

        if app and hasattr(app, 'audio') and app.audio:
            app.audio.on_game_start()

    # ─── Taymerlar ────────────────────────────────────────────────────────────
    def _tick_game_timer(self, dt):
        self._elapsed += 1
        m, s = divmod(self._elapsed, 60)
        self._game_time_lbl.text = f"{m}:{s:02d}"

    def _start_turn_timer(self):
        """45 soniyalik navbat taymeri"""
        self._cancel_turn_timer()
        self._turn_remaining = TURN_TIMEOUT
        self._turn_ring.update(self._turn_remaining)
        self._turn_timer = Clock.schedule_interval(self._tick_turn_timer, 1.0)

    def _tick_turn_timer(self, dt):
        self._turn_remaining -= 1
        self._turn_ring.update(self._turn_remaining)

        if self._turn_remaining <= 10:
            # Qizil ogoh — "X soniya qoldi"
            self._show_status(
                f"⚠ {self._turn_remaining} soniya qoldi!", duration=1.0,
                color=COLORS['danger']
            )

        if self._turn_remaining <= 0:
            self._cancel_turn_timer()
            self._auto_action()

    def _auto_action(self):
        """
        Vaqt tugadi: o'yinchi himoyachi bo'lsa → olish,
        hujumchi bo'lsa → tur tugaydi.
        """
        c = self._controller
        if not c:
            return
        state = c.state
        if state.phase == PHASE_END:
            return

        self._show_status("Vaqt tugadi! Kartalar avtomatik olindi.", duration=2.0,
                           color=COLORS['danger'])

        if c.is_human_defender:
            c.take_cards()
        elif c.is_human_attacker and state.all_defended and len(state.table) > 0:
            c.end_turn()

    def _cancel_turn_timer(self):
        if self._turn_timer:
            self._turn_timer.cancel()
            self._turn_timer = None

    def _cancel_all_timers(self):
        self._cancel_turn_timer()
        if self._game_timer:
            self._game_timer.cancel()
            self._game_timer = None

    # ─── State yangilash (Controller → UI) ───────────────────────────────────
    def _on_state_changed(self, state):
        # AI qo'li
        ai = state.ai_player
        if ai:
            self._ai_hand.set_cards(ai.hand)
            self._ai_card_lbl.text = f"{ai.card_count} karta"

        # O'yinchi qo'li
        human = state.human_player
        if human:
            self._player_hand.set_cards(human.hand)
            self._player_card_lbl.text = f"{human.card_count} karta"

        # Stol
        self._table_widget.update_table(state.table)
        if self._loading_overlay.opacity > 0:
            self._loading_overlay.opacity = 0

        # Deck badge
        if state.deck:
            trump_sym = SUIT_SYMBOLS.get(state.trump_suit, '') if state.trump_suit else ''
            is_red    = state.trump_suit in ('hearts', 'diamonds') if state.trump_suit else False
            self._deck_badge.update(state.deck.remaining, trump_sym, is_red)

        # Rollar
        self._update_roles(state)

        # Tugmalar
        self._update_buttons(state)

        # Hint ko'rsatgich
        self._update_hints(state)

        # Navbat taymer — faqat o'yinchi navbatida
        if not state.is_game_over:
            c = self._controller
            if c and (c.is_human_attacker or c.is_human_defender):
                self._start_turn_timer()
            else:
                self._cancel_turn_timer()
                self._turn_ring.update(TURN_TIMEOUT)

        # Audio
        app = App.get_running_app()
        if app and hasattr(app, 'audio') and app.audio:
            app.audio.on_card_place()

    def _update_roles(self, state):
        ai_atk = state.attacker and state.attacker.is_ai
        self._ai_role_lbl.text     = 'HUJUM' if ai_atk    else 'HIMOYA'
        self._player_role_lbl.text = 'HIMOYA' if ai_atk   else 'HUJUM'
        # Rang: hujumchi — issiq, himoyachi — sovuq
        atk_c  = (*COLORS['warning'][:3], 1)
        def_c  = (*COLORS['info'][:3], 1)
        self._ai_role_lbl.color     = atk_c if ai_atk  else def_c
        self._player_role_lbl.color = def_c if ai_atk  else atk_c

    def _update_buttons(self, state):
        c = self._controller
        if not c:
            return
        is_def = c.is_human_defender
        is_atk = c.is_human_attacker

        can_take = (is_def and
                    state.phase == PHASE_DEFENSE and
                    len(state.table) > 0)
        self._take_btn.enabled = can_take
        self._take_btn.opacity = 1.0 if can_take else 0.35

        can_end = (is_atk and
                   state.phase == PHASE_ATTACK and
                   state.all_defended and
                   len(state.table) > 0)
        self._end_btn.enabled = can_end
        self._end_btn.opacity = 1.0 if can_end else 0.35

    def _update_hints(self, state):
        """
        Hint ko'rsatgich:
        - Hujum: o'yinchi qo'lida tashlash mumkin bo'lgan kartalar yashil
        - Himoya: tanlangan hujum kartasiga yopadigan kartalar yashil,
                  stoldagi yopilmagan slotlar oltin glow
        """
        c = self._controller
        if not c or state.is_game_over:
            self._player_hand.clear_hints()
            self._table_widget.clear_selection()
            self._hide_hint_banner()
            return

        human = state.human_player
        if not human:
            return

        if c.is_human_attacker and state.phase == PHASE_ATTACK:
            # Hujum: stoldagi qiymatlarga to'g'ri keladigan kartalar
            if state.table:
                valid = [cd for cd in human.hand if cd.value in state.table_values]
                if not valid:
                    valid = list(human.hand)  # birinchi karta — hammasi to'g'ri
            else:
                valid = list(human.hand)
            self._player_hand.show_hints(valid)
            self._table_widget.clear_selection()

            if state.all_defended and len(state.table) > 0:
                self._show_hint_banner("Qo'shimcha karta tashlang yoki TUGALLASH tugmasini bosing")
            else:
                self._show_hint_banner("Kartangizni tanlang va stolga tashlang")

        elif c.is_human_defender and state.phase == PHASE_DEFENSE:
            # Himoya: stoldagi yopilmagan slotlar glow
            self._table_widget.highlight_undefended(True)

            if self._selected_atk_card:
                # Tanlangan hujum kartasiga yopadigan qo'l kartalari
                valid = [cd for cd in human.hand
                         if cd.beats(self._selected_atk_card, state.trump_suit)]
                self._player_hand.show_hints(valid)
                self._show_hint_banner(
                    f"  {self._selected_atk_card}  kartasini yoping — qo'lingizdan mos karta tanlang"
                )
            else:
                self._player_hand.clear_hints()
                self._show_hint_banner("Avval stoldagi hujum kartasiga teging, so'ng qo'lingizdan yoping")
        else:
            self._player_hand.clear_hints()
            self._table_widget.clear_selection()
            self._hide_hint_banner()

    # ─── Hint banner ──────────────────────────────────────────────────────────
    def _show_hint_banner(self, text: str):
        self._hint_banner.text    = text
        self._hint_banner.opacity = 1.0

    def _hide_hint_banner(self):
        self._hint_banner.opacity = 0

    def _show_status(self, text: str, duration: float = 2.0,
                     color=None):
        if color is None:
            color = (0.3, 1.0, 0.5, 1)
        
        # Sariq yozuv o'rniga yashil bannerni ishlatamiz
        self._hint_banner.color = color
        self._hint_banner.text = text
        self._hint_banner.opacity = 1.0
        
        # Animatsiya bilan yo'qolishi (agar vaqtli bo'lsa)
        if duration > 0:
            Clock.schedule_once(
                lambda dt: Animation(opacity=0, duration=0.8).start(self._hint_banner),
                duration
            )

    # ─── O'yinchi harakatlari ─────────────────────────────────────────────────
    def _on_player_card_selected(self, card: Card, idx: int):
        self._selected_hand_card = card
        c = self._controller
        if not c:
            return
        state = c.state

        if state.phase == PHASE_END:
            return

        # ── Hujum fazasi ──────────────────────────────────────────────────────
        if c.is_human_attacker and state.phase == PHASE_ATTACK:
            ok, msg = c.attack(card)
            if not ok and state.all_defended and len(state.table) > 0:
                ok, msg = c.add_attack_card(card)

            if ok:
                self._player_hand.deselect_all()
                self._selected_hand_card = None
                app = App.get_running_app()
                if app and hasattr(app, 'audio') and app.audio:
                    app.audio.on_card_place()
            else:
                w = self._player_hand.selected_widget
                if w:
                    w.animate_invalid()
                self._show_status(msg)

        # ── Himoya fazasi ──────────────────────────────────────────────────────
        elif c.is_human_defender and state.phase == PHASE_DEFENSE:
            if self._selected_atk_card:
                ok, msg = c.defend(self._selected_atk_card, card)
                if ok:
                    self._player_hand.deselect_all()
                    self._selected_hand_card = None
                    self._selected_atk_card  = None
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
                # Avtomatik: birinchi yopilmagan kartaga qarshi
                undefended = state.undefended_cards
                if len(undefended) == 1:
                    self._selected_atk_card = undefended[0]
                    ok, msg = c.defend(self._selected_atk_card, card)
                    if ok:
                        self._player_hand.deselect_all()
                        self._selected_hand_card = None
                        self._selected_atk_card  = None
                    else:
                        w = self._player_hand.selected_widget
                        if w:
                            w.animate_invalid()
                        self._show_status(msg)
                        self._selected_atk_card = None
                else:
                    self._show_status(
                        "Avval stoldagi hujum kartasiga teging", duration=1.5
                    )

    def _on_player_card_deselected(self):
        self._selected_hand_card = None

    def _on_player_card_dropped(self, card: Card, pos) -> bool:
        c = self._controller
        if not c:
            return False
        state = c.state
        if state.phase == PHASE_END:
            return False

        # ── Hujum ─────────────────────────────────────────────────────────────
        if c.is_human_attacker and state.phase == PHASE_ATTACK:
            if not self._table_widget.collide_point(*pos):
                return False
            ok, msg = c.attack(card)
            if not ok and state.all_defended and len(state.table) > 0:
                ok, msg = c.add_attack_card(card)
            if ok:
                self._player_hand.deselect_all()
                self._selected_hand_card = None
                app = App.get_running_app()
                if app and hasattr(app, 'audio') and app.audio:
                    app.audio.on_card_place()
                return True
            else:
                w = self._player_hand.selected_widget
                if w:
                    w.animate_invalid()
                self._show_status(msg)
                return False

        # ── Himoya ────────────────────────────────────────────────────────────
        elif c.is_human_defender and state.phase == PHASE_DEFENSE:
            if not self._table_widget.collide_point(*pos):
                return False

            slot_idx = self._table_widget.get_slot_at(pos)

            if slot_idx >= 0 and slot_idx < len(state.table):
                atk, dfn = state.table[slot_idx]
                if dfn is None:
                    ok, msg = c.defend(atk, card)
                    if ok:
                        self._player_hand.deselect_all()
                        self._selected_hand_card = None
                        self._selected_atk_card  = None
                        self._table_widget.clear_selection()
                        app = App.get_running_app()
                        if app and hasattr(app, 'audio') and app.audio:
                            app.audio.on_card_place()
                        return True
                    else:
                        w = self._player_hand.selected_widget
                        if w:
                            w.animate_invalid()
                        self._show_status(msg)
                        app = App.get_running_app()
                        if app and hasattr(app, 'audio') and app.audio:
                            app.audio.on_invalid()
                        return False
                else:
                    self._show_status("Bu slot allaqachon yopilgan")
                    return False
            else:
                # Umumiy drop: faqat bitta yopilmagan bo'lsa — avtomat
                undefended = state.undefended_cards
                if len(undefended) == 1:
                    ok, msg = c.defend(undefended[0], card)
                    if ok:
                        self._player_hand.deselect_all()
                        self._selected_hand_card = None
                        self._selected_atk_card  = None
                        app = App.get_running_app()
                        if app and hasattr(app, 'audio') and app.audio:
                            app.audio.on_card_place()
                        return True
                    else:
                        w = self._player_hand.selected_widget
                        if w:
                            w.animate_invalid()
                        self._show_status(msg)
                        return False
                else:
                    self._show_status("Hujum kartasi ustiga tashlang!", duration=1.2)
                    return False

        return False

    def _on_table_slot_tap(self, slot_idx: int):
        """Stoldagi slot bosildi — himoya uchun maqsad karta tanlash"""
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
            self._show_status("Bu karta allaqachon yopilgan", duration=1.0)
            return

        self._selected_atk_card = atk
        self._table_widget.set_slot_selected(slot_idx)
        self._show_status(
            f"{atk} kartasini yopish uchun qo'lingizdan karta tanlang",
            duration=2.5
        )
        # Yopadigan kartalarni yashil qilish
        human = state.human_player
        if human:
            valid = [cd for cd in human.hand if cd.beats(atk, state.trump_suit)]
            self._player_hand.show_hints(valid)
            if not valid:
                self._show_status(
                    f"{atk} kartasini yopa oladigan karta yo'q — OLISH tugmasini bosing",
                    duration=3.0, color=COLORS['danger']
                )

    # ─── OLISH ────────────────────────────────────────────────────────────────
    def _on_take(self):
        c = self._controller
        if not c or not c.is_human_defender:
            return
        self._cancel_turn_timer()
        ok = c.take_cards()
        if ok:
            self._selected_atk_card = None
            self._player_hand.clear_hints()
            app = App.get_running_app()
            if app and hasattr(app, 'audio') and app.audio:
                app.audio.on_card_take()

    # ─── TUGALLASH ────────────────────────────────────────────────────────────
    def _on_end_turn(self):
        c = self._controller
        if not c:
            return
        self._cancel_turn_timer()
        ok, msg = c.end_turn()
        if not ok:
            self._show_status(msg)

    # ─── AI navbati ───────────────────────────────────────────────────────────
    def _on_ai_turn_start(self):
        """AI o'ylayapti — navbat taymerini to'xtatish"""
        self._cancel_turn_timer()
        self._turn_ring.update(TURN_TIMEOUT)
        self._show_status('Raqib o\'ylayapti...', duration=AI_THINK_DELAY + 0.6)

    # ─── O'yin tugadi ─────────────────────────────────────────────────────────
    def _on_game_over(self, winner, loser):
        self._cancel_all_timers()
        self._player_hand.clear_hints()
        self._hide_hint_banner()

        app   = App.get_running_app()
        state = self._controller.state
        human = state.human_player
        is_win = (winner == human)

        if app and hasattr(app, 'stats') and app.stats:
            app.stats.record_game(
                result       = 'win' if is_win else 'loss',
                difficulty   = getattr(app, 'game_difficulty', 'medium'),
                mode         = getattr(app, 'game_mode', 'podkidnoy'),
                turns        = state.turn_count,
                cards_taken  = getattr(human, 'cards_taken', 0) if human else 0,
                duration_sec = self._elapsed,
            )

        if app and hasattr(app, 'audio') and app.audio:
            if is_win:
                app.audio.on_victory()
            else:
                app.audio.on_lose()

        if app:
            app.game_result = {
                'is_win':      is_win,
                'turns':       state.turn_count,
                'cards_taken': getattr(human, 'cards_taken', 0) if human else 0,
                'time_sec':    self._elapsed,
            }

        Clock.schedule_once(
            lambda dt: App.get_running_app().navigate_to('result'), 0.6
        )

    # ─── Pauza va Menyu ───────────────────────────────────────────────────────
    def _toggle_pause(self):
        """Pauza rejimini yoqish/o'chirish"""
        if not hasattr(self, '_pause_overlay'):
            self._pause_overlay = PauseOverlay(
                on_resume = self._toggle_pause,
                on_menu   = self._on_menu_click
            )
        
        if self._pause_overlay.parent:
            self.remove_widget(self._pause_overlay)
            if getattr(self, '_turn_remaining', 0) > 0 and self._controller and self._controller.is_human_turn:
                self._start_turn_timer()
        else:
            self.add_widget(self._pause_overlay)
            self._cancel_turn_timer()

    def _on_menu_click(self):
        """Asosiy menyuga qaytish"""
        self._cancel_all_timers()
        if hasattr(self._controller, 'net'):
            self._controller.net.stop_all()
        App.get_running_app().navigate_to('main_menu', direction='right')

    def _on_network_disconnected(self):
        """Ulanish uzilganda xabar berish"""
        self._show_status("RAQIB TARMOG'DAN UZILDI!", duration=5.0, color=COLORS['danger'])
        Clock.schedule_once(lambda dt: self._on_menu_click(), 3.0)

    def _upd_loading_bg(self, *a):
        self._loading_bg.pos = self._loading_overlay.pos
        self._loading_bg.size = self._loading_overlay.size

    # ─── Yagona _show_status implementatsiyasi ────────────────────────────────
    def _show_status(self, text: str, duration: float = 2.5,
                     color=None):
        """
        Hint bannerda vaqtli xabar ko'rsatish.
        duration <= 0 bo'lsa — xabar qulay ravishda ko'rsatiladi (avtomatik yo'qolmaydi).
        """
        if color is None:
            color = COLORS['text_primary']

        self._hint_banner.color   = color
        self._hint_banner.text    = text
        self._hint_banner.opacity = 1.0

        # Oldingi rejalashtirilgan yashirishni bekor qilish
        Clock.unschedule(self._hide_hint_banner)

        if duration > 0:
            Clock.schedule_once(self._hide_hint_banner, duration)

    def _hide_hint_banner(self, *args):
        """Hint bannerni silliq animatsiya bilan yashirish"""
        anim = Animation(opacity=0, duration=0.4)
        anim.start(self._hint_banner)
