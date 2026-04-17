"""
ui/screens/main_menu_screen.py — Bosh Menyu
Logo + 4 ta tugma (stagger animatsiya).
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout  import FloatLayout
from kivy.uix.boxlayout    import BoxLayout
from kivy.uix.label        import Label
from kivy.uix.widget       import Widget
from kivy.graphics         import (Color, Rectangle, RoundedRectangle,
                                    Line, Ellipse)
from kivy.animation        import Animation
from kivy.clock            import Clock
from kivy.app              import App
from ui.components.luxury_button import LuxuryButton
from ui.components.animated_bg   import AnimatedBackground
from core.constants        import COLORS, FONT_SIZES


class MainMenuScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._built = False
        self._btn_list = []

    def on_enter(self):
        if not self._built:
            self._build_ui()
            self._built = True
        self._animate_entrance()
        
        if hasattr(self, '_bg') and self._bg:
            self._bg.start()

        app = App.get_running_app()
        if app and hasattr(app, 'audio') and app.audio:
            app.audio.on_main_menu()

    def on_leave(self):
        if hasattr(self, '_bg') and self._bg:
            self._bg.stop()

    # ─── UI Yaratish ──────────────────────────────────────────────────────────
    def _build_ui(self):
        root = FloatLayout()
        self.add_widget(root)

        # Fon
        self._bg = AnimatedBackground(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        root.add_widget(self._bg)

        # Markaziy ustun
        col = BoxLayout(
            orientation = 'vertical',
            spacing     = 14,
            padding     = [32, 0],
            size_hint   = (0.85, None),
            pos_hint    = {'center_x': 0.5, 'center_y': 0.5},
        )
        root.add_widget(col)

        # ─── Logo ─────────────────────────────────────────────────────────
        logo_box = BoxLayout(orientation='vertical', size_hint_y=None, height=140)
        col.add_widget(logo_box)

        logo_lbl = Label(
            text      = '',
            font_size = 72,
            size_hint_y = None,
            height    = 80,
            halign    = 'center',
        )
        logo_box.add_widget(logo_lbl)

        title_lbl = Label(
            text      = 'DURAK',
            font_size = FONT_SIZES['display'] + 4,
            bold      = True,
            color     = COLORS['gold'],
            size_hint_y = None,
            height    = 50,
            halign    = 'center',
        )
        logo_box.add_widget(title_lbl)

        # ─── Ajratgich ────────────────────────────────────────────────────
        sep = _GoldDivider(size_hint_y=None, height=2)
        col.add_widget(sep)

        # ─── Tugmalar ─────────────────────────────────────────────────────
        t = self._get_texts()
        btn_data = [
            (t['play'],        'primary',   self._on_play),
            (t['statistics'],  'secondary', self._on_stats),
            (t['settings'],   'secondary', self._on_settings),
            (t['rules'],       'secondary', self._on_rules),
        ]

        self._btn_list = []
        for text, style, callback in btn_data:
            btn = LuxuryButton(text=text, style=style)
            btn.bind(on_release=lambda inst, cb=callback: cb())
            btn.opacity = 0
            col.add_widget(btn)
            self._btn_list.append(btn)

        # Bo'sh ajratgich
        col.add_widget(Widget(size_hint_y=None, height=8))

        # Versiya
        ver = Label(
            text      = 'v 1.0.0',
            font_size = FONT_SIZES['tiny'],
            color     = COLORS['text_muted'],
            size_hint_y = None,
            height    = 24,
            halign    = 'center',
        )
        col.add_widget(ver)

        # Ustunning balandligini hisoblash
        col.height = 140 + 2 + len(btn_data) * 52 + (len(btn_data) - 1) * 14 + 8 + 24

    # ─── Animatsiya ───────────────────────────────────────────────────────────
    def _animate_entrance(self):
        for i, btn in enumerate(self._btn_list):
            btn.opacity = 0

            def _show(dt, b=btn):
                anim = Animation(opacity=1, duration=0.35, t='out_cubic')
                anim.start(b)

            Clock.schedule_once(_show, 0.1 * i + 0.2)

    # ─── Navigatsiya ──────────────────────────────────────────────────────────
    def _on_play(self):
        App.get_running_app().navigate_to('difficulty')

    def _on_stats(self):
        App.get_running_app().navigate_to('stats')

    def _on_settings(self):
        App.get_running_app().navigate_to('settings')

    def _on_rules(self):
        App.get_running_app().navigate_to('rules')

    # ─── Til matni ────────────────────────────────────────────────────────────
    def _get_texts(self) -> dict:
        try:
            app = App.get_running_app()
            if app and hasattr(app, 'lang'):
                return app.lang
        except Exception:
            pass
        return {
            'play': "O'ynash", 'statistics': 'Statistika',
            'settings': 'Sozlamalar', 'rules': 'Qoidalar'
        }


class _GoldDivider(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(*COLORS['gold'][:3], 0.5)
            Rectangle(pos=(self.x + 30, self.y), size=(self.width - 60, 1))
