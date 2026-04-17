"""
ui/screens/difficulty_screen.py — Qiyinlik va Rejim Tanlash
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout  import FloatLayout
from kivy.uix.boxlayout    import BoxLayout
from kivy.uix.gridlayout   import GridLayout
from kivy.uix.label        import Label
from kivy.uix.widget       import Widget
from kivy.uix.behaviors    import ButtonBehavior
from kivy.graphics         import Color, RoundedRectangle, Line, Rectangle
from kivy.animation        import Animation
from kivy.clock            import Clock
from kivy.app              import App
from ui.components.luxury_button import LuxuryButton
from core.constants        import COLORS, FONT_SIZES


class DifficultyScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._selected_diff = 'medium'
        self._selected_mode = 'podkidnoy'
        self._diff_btns = {}
        self._mode_btns = {}
        self._built = False

    def on_enter(self):
        if not self._built:
            self._build_ui()
            self._built = True
        self._highlight_selection()

    def _build_ui(self):
        root = FloatLayout()
        self.add_widget(root)

        # Fon
        with self.canvas.before:
            Color(*COLORS['background'])
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *a: setattr(self._bg_rect, 'pos', self.pos),
                  size=lambda *a: setattr(self._bg_rect, 'size', self.size))

        # Asosiy ustun
        col = BoxLayout(
            orientation = 'vertical',
            spacing     = 16,
            padding     = [28, 60, 28, 40],
            size_hint   = (1, 1),
        )
        root.add_widget(col)

        # ─── Sarlavha ─────────────────────────────────────────────────────
        col.add_widget(Label(
            text      = 'QIYINLIK TANLANG',
            font_size = FONT_SIZES['h1'],
            bold      = True,
            color     = COLORS['gold'],
            size_hint_y = None,
            height    = 50,
            halign    = 'center',
        ))

        col.add_widget(Widget(size_hint_y=None, height=4))

        # ─── Qiyinlik tugmalari ───────────────────────────────────────────
        difficulties = [
            ('easy',   'OSON',   'Yangi boshlovchi'),
            ('medium', 'O\'RTA',  'Tajribali'),
            ('hard',   'QIYIN',   'Ekspert'),
        ]

        for diff_key, label, desc in difficulties:
            btn = _DifficultyCard(
                diff_key = diff_key,
                label    = label,
                desc     = desc,
            )
            btn.bind(on_release=lambda inst, dk=diff_key: self._select_diff(dk))
            self._diff_btns[diff_key] = btn
            col.add_widget(btn)

        col.add_widget(Widget(size_hint_y=None, height=12))

        # Rejim olib tashlandi. Dastur doim 'podkidnoy' rejimida ishlaydi.

        col.add_widget(Widget())   # bo'sh joy

        # ─── Boshlash tugmasi ─────────────────────────────────────────────
        start_btn = LuxuryButton(text='O\'YINNI BOSHLASH', style='primary')
        start_btn.height = 56
        start_btn.bind(on_release=lambda *a: self._start_game())
        col.add_widget(start_btn)

        # ─── Orqaga ───────────────────────────────────────────────────────
        back_btn = LuxuryButton(text='Orqaga', style='secondary')
        back_btn.height = 44
        back_btn.bind(on_release=lambda *a: self._go_back())
        col.add_widget(back_btn)

    def _highlight_selection(self):
        for key, btn in self._diff_btns.items():
            btn.set_selected(key == self._selected_diff)
        for key, btn in self._mode_btns.items():
            btn.set_selected(key == self._selected_mode)

    def _select_diff(self, key: str):
        self._selected_diff = key
        self._highlight_selection()
        app = App.get_running_app()
        if app and hasattr(app, 'audio') and app.audio:
            app.audio.on_button()

    def _select_mode(self, key: str):
        self._selected_mode = key
        self._highlight_selection()

    def _start_game(self):
        app = App.get_running_app()
        if app:
            app.game_difficulty = self._selected_diff
            app.game_mode       = self._selected_mode
            app.navigate_to('game')

    def _go_back(self):
        App.get_running_app().navigate_to('main_menu', direction='right')


class _DifficultyCard(ButtonBehavior, BoxLayout):
    def __init__(self, diff_key, label, desc, **kwargs):
        super().__init__(**kwargs)
        self.diff_key    = diff_key
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height      = 68
        self.padding     = [16, 8]
        self._selected   = False

        self._title = Label(
            text      = label,
            font_size = FONT_SIZES['body'],
            bold      = True,
            color     = COLORS['text_primary'],
            halign    = 'left',
            size_hint_y = None,
            height    = 28,
        )
        self._desc = Label(
            text      = desc,
            font_size = FONT_SIZES['small'],
            color     = COLORS['text_muted'],
            halign    = 'left',
            size_hint_y = None,
            height    = 22,
        )
        self.add_widget(self._title)
        self.add_widget(self._desc)
        self.bind(pos=self._draw, size=self._draw)

    def set_selected(self, val: bool):
        self._selected = val
        self._draw()

    def _draw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if self._selected:
                Color(*COLORS['gold'][:3], 0.2)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
                Color(*COLORS['gold'])
                Line(rounded_rectangle=[self.x, self.y,
                                         self.width, self.height, 10], width=1.8)
                self._title.color = COLORS['gold']
            else:
                Color(*COLORS['surface'])
                RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
                Color(*COLORS['divider'])
                Line(rounded_rectangle=[self.x, self.y,
                                         self.width, self.height, 10], width=1.0)
                self._title.color = COLORS['text_primary']

    def on_press(self):
        Animation(opacity=0.8, duration=0.05).start(self)

    def on_release(self):
        Animation(opacity=1.0, duration=0.08).start(self)
