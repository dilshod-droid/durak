"""
ui/screens/main_menu_screen.py — Asosiy menyu
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.app import App
from kivy.metrics import dp

from ui.components.luxury_button import LuxuryButton
from ui.components.animated_bg import AnimatedBackground
from core.constants import COLORS, FONT_SIZES

class MainMenuScreen(Screen):
    """
    O'yinning asosiy kirish qismi.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._built = False

    def on_enter(self):
        if not self._built:
            self._build_ui()
            self._built = True
        
        # Animatsiya: tugmalarni paydo qilish
        self._animate_in()
        if self._bg:
            self._bg.start()

    def on_leave(self):
        if self._bg:
            self._bg.stop()

    def _build_ui(self):
        root = FloatLayout()
        self.add_widget(root)

        # ─── Fon (Animated Background) ─────────────────
        self._bg = AnimatedBackground()
        root.add_widget(self._bg)

        # ─── Logo va Sarlavha ───────────────────────────
        header = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.4),
            pos_hint={'center_x': 0.5, 'top': 0.95},
            spacing=dp(10)
        )
        root.add_widget(header)

        # Logo rasmi (placeholder o'rniga vizual element)
        logo_container = FloatLayout(size_hint_y=0.6)
        logo = Image(
            source='assets/cards/card_back.png',  # Karta orqasi logotip kabi
            size_hint=(None, None),
            size=(dp(100), dp(140)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        logo_container.add_widget(logo)
        header.add_widget(logo_container)

        self._title_lbl = Label(
            text='DURAK',
            font_name='Cinzel',
            font_size=dp(48),
            bold=True,
            color=COLORS['gold'],
            size_hint_y=0.4
        )
        header.add_widget(self._title_lbl)

        # ─── Tugmalar Bloki ──────────────────────────────
        self._btn_col = BoxLayout(
            orientation='vertical',
            size_hint=(0.8, 0.45),
            pos_hint={'center_x': 0.5, 'y': 0.08},
            spacing=dp(15)
        )
        root.add_widget(self._btn_col)

        texts = self._get_texts()

        self._btn_play = LuxuryButton(text=texts['play'], style='primary')
        self._btn_play.bind(on_release=lambda *a: self._on_play())

        self._btn_stats = LuxuryButton(text=texts['stats'], style='secondary')
        self._btn_stats.bind(on_release=lambda *a: self._on_stats())

        self._btn_settings = LuxuryButton(text=texts['settings'], style='secondary')
        self._btn_settings.bind(on_release=lambda *a: self._on_settings())

        self._btn_rules = LuxuryButton(text=texts['rules'], style='secondary')
        self._btn_rules.bind(on_release=lambda *a: self._on_rules())

        # Tugmalarni yashirin (opacity=0) holatda qo'shish
        for b in [self._btn_play, self._btn_stats, self._btn_settings, self._btn_rules]:
            b.opacity = 0
            self._btn_col.add_widget(b)

    def _animate_in(self):
        """Tugmalarni ketma-ket paydo qilish"""
        buttons = [self._btn_play, self._btn_stats, self._btn_settings, self._btn_rules]
        for i, b in enumerate(buttons):
            b.opacity = 0
            # Kechikish bilan animatsiya
            def _show(dt, b=b):
                anim = Animation(opacity=1, duration=0.35, t='out_cubic')
                anim.start(b)

            Clock.schedule_once(_show, 0.1 * i + 0.2)

    # ─── Navigatsiya ──────────────────────────────────────────────────────────
    def _on_play(self):
        App.get_running_app().navigate_to('mode_selection')

    def _on_stats(self):
        App.get_running_app().navigate_to('stats')

    def _on_settings(self):
        App.get_running_app().navigate_to('settings')

    def _on_rules(self):
        App.get_running_app().navigate_to('rules')

    # ─── Til matni ────────────────────────────────────────────────────────────
    def _get_texts(self) -> dict:
        app = App.get_running_app()
        lang = getattr(app, 'lang', {})
        return {
            'play':     lang.get('play', 'O\'YNASH'),
            'stats':    lang.get('stats', 'STATISTIKA'),
            'settings': lang.get('settings', 'SOZLAMALAR'),
            'rules':    lang.get('rules', 'QOIDALAR')
        }
