"""
ui/screens/settings_screen.py — Sozlamalar Ekrani
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout   import FloatLayout
from kivy.uix.boxlayout     import BoxLayout
from kivy.uix.gridlayout    import GridLayout
from kivy.uix.scrollview    import ScrollView
from kivy.uix.label         import Label
from kivy.uix.slider        import Slider
from kivy.uix.switch        import Switch
from kivy.uix.widget        import Widget
from kivy.graphics          import Color, Rectangle, RoundedRectangle, Line
from kivy.app               import App
from ui.components.luxury_button import LuxuryButton
from core.constants         import COLORS, FONT_SIZES


class SettingsScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._built = False
        self._widgets = {}

    def on_enter(self):
        if not self._built:
            self._build_ui()
            self._built = True
        self._load_current_settings()

    def _build_ui(self):
        root = FloatLayout()
        self.add_widget(root)

        # Fon
        with self.canvas.before:
            Color(*COLORS['background'])
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(
            pos=lambda *a: setattr(self._bg, 'pos', self.pos),
            size=lambda *a: setattr(self._bg, 'size', self.size)
        )

        # Sarlavha
        root.add_widget(Label(
            text      = 'SOZLAMALAR',
            font_size = FONT_SIZES['h1'],
            bold      = True,
            color     = COLORS['gold'],
            size_hint = (1, None),
            height    = 50,
            pos_hint  = {'x': 0, 'top': 1},
            halign    = 'center',
            padding   = [0, 8],
        ))

        # Scroll area
        scroll = ScrollView(
            size_hint    = (1, 1),
            pos_hint     = {'x': 0, 'y': 0},
            bar_width    = 4,
            bar_color    = COLORS['gold'][:3] + (0.5,),
        )
        root.add_widget(scroll)

        col = BoxLayout(
            orientation  = 'vertical',
            spacing      = 10,
            padding      = [24, 70, 24, 20],
            size_hint_y  = None,
        )
        col.bind(minimum_height=col.setter('height'))
        scroll.add_widget(col)

        # ─── Ovoz ─────────────────────────────────────────────────────────
        col.add_widget(self._section('OVOZ'))
        col.add_widget(self._switch_row('Ovoz effektlari', 'sound'))
        col.add_widget(self._slider_row('Ovoz darajasi', 'sound_vol', 0, 1))
        col.add_widget(self._switch_row('Musiqa', 'music'))
        col.add_widget(self._slider_row('Musiqa darajasi', 'music_vol', 0, 1))

        # ─── Boshqalar ────────────────────────────────────────────────────
        col.add_widget(self._section('BOSHQA'))
        col.add_widget(self._switch_row('Titroq (vibration)', 'vibration'))
        col.add_widget(self._slider_row('Animatsiya tezligi', 'anim_speed',
                                        0.5, 2.0, reverse_label=True))

        # ─── Standartga qaytish ───────────────────────────────────────────
        col.add_widget(Widget(size_hint_y=None, height=12))
        reset_btn = LuxuryButton(text='Standart sozlamalar', style='secondary')
        reset_btn.bind(on_release=lambda *a: self._reset_settings())
        col.add_widget(reset_btn)

        # ─── Orqaga ───────────────────────────────────────────────────────
        col.add_widget(Widget(size_hint_y=None, height=8))
        back_btn = LuxuryButton(text='Orqaga', style='secondary')
        back_btn.bind(on_release=lambda *a: self._go_back())
        col.add_widget(back_btn)

    def _section(self, title: str) -> Label:
        lbl = Label(
            text        = title,
            font_size   = FONT_SIZES['small'],
            bold        = True,
            color       = COLORS['gold'][:3] + (0.7,),
            size_hint_y = None,
            height      = 28,
            halign      = 'left',
        )
        lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))
        return lbl

    def _switch_row(self, label: str, key: str) -> BoxLayout:
        row = BoxLayout(orientation='horizontal', size_hint_y=None, height=44,
                        spacing=10)
        lbl = Label(text=label, font_size=FONT_SIZES['body'],
                    color=COLORS['text_primary'], halign='left')
        lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))
        sw = Switch(size_hint=(None, None), size=(60, 30))
        row.add_widget(lbl)
        row.add_widget(sw)
        self._widgets[key] = sw
        sw.bind(active=lambda inst, val: self._save(key, val))
        return row

    def _slider_row(self, label: str, key: str,
                    min_v: float, max_v: float,
                    reverse_label: bool = False) -> BoxLayout:
        col = BoxLayout(orientation='vertical', size_hint_y=None, height=56)
        lbl = Label(text=label, font_size=FONT_SIZES['small'],
                    color=COLORS['text_secondary'], size_hint_y=None, height=20,
                    halign='left')
        lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))

        sl = Slider(min=min_v, max=max_v, value=(min_v + max_v) / 2,
                    size_hint_y=None, height=36,
                    cursor_size=(20, 20))
        sl.bind(value=lambda inst, val: self._save(key, round(val, 2)))
        col.add_widget(lbl)
        col.add_widget(sl)
        self._widgets[key] = sl
        return col

    def _load_current_settings(self):
        app = App.get_running_app()
        if not (app and hasattr(app, 'settings') and app.settings):
            return
        s = app.settings
        for key in ['sound', 'music', 'vibration']:
            if key in self._widgets:
                self._widgets[key].active = s.get(key, True)
        for key in ['sound_vol', 'music_vol', 'anim_speed']:
            if key in self._widgets:
                self._widgets[key].value = s.get(key, 0.7)

    def _save(self, key: str, val):
        app = App.get_running_app()
        if app and hasattr(app, 'settings') and app.settings:
            app.settings.set(key, val)
        if app and hasattr(app, 'audio') and app.audio:
            app.audio.apply_settings(app.settings)

    def _reset_settings(self):
        app = App.get_running_app()
        if app and hasattr(app, 'settings') and app.settings:
            app.settings.reset()
            self._load_current_settings()

    def _go_back(self):
        App.get_running_app().navigate_to('main_menu', direction='right')
