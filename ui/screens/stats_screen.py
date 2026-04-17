"""
ui/screens/stats_screen.py — Statistika Ekrani
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout  import FloatLayout
from kivy.uix.boxlayout    import BoxLayout
from kivy.uix.label        import Label
from kivy.uix.widget       import Widget
from kivy.uix.progressbar  import ProgressBar
from kivy.graphics         import Color, Rectangle, RoundedRectangle, Line
from kivy.app              import App
from ui.components.luxury_button import LuxuryButton
from core.constants        import COLORS, FONT_SIZES


class StatsScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._built = False
        self._stat_labels = {}

    def on_enter(self):
        if not self._built:
            self._build_ui()
            self._built = True
        self._refresh_stats()

    def _build_ui(self):
        root = FloatLayout()
        self.add_widget(root)

        with self.canvas.before:
            Color(*COLORS['background'])
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(
            pos=lambda *a: setattr(self._bg, 'pos', self.pos),
            size=lambda *a: setattr(self._bg, 'size', self.size)
        )

        # Sarlavha
        root.add_widget(Label(
            text      = 'STATISTIKA',
            font_size = FONT_SIZES['h1'],
            bold      = True,
            color     = COLORS['gold'],
            size_hint = (1, None),
            height    = 50,
            pos_hint  = {'x': 0, 'top': 1},
            halign    = 'center',
        ))

        col = BoxLayout(
            orientation = 'vertical',
            spacing     = 16,
            padding     = [28, 70, 28, 20],
            size_hint   = (1, 1),
        )
        root.add_widget(col)

        # ─── Asosiy raqamlar ──────────────────────────────────────────────
        top_row = BoxLayout(orientation='horizontal', spacing=12,
                            size_hint_y=None, height=100)
        for key, icon in [('total', ''), ('wins', ''), ('losses', '')]:
            box = _StatBox(icon=icon)
            self._stat_labels[key] = box
            top_row.add_widget(box)
        col.add_widget(top_row)

        # ─── G'alaba foizi ────────────────────────────────────────────────
        col.add_widget(Label(
            text='G\'alaba foizi', font_size=FONT_SIZES['small'],
            color=COLORS['text_secondary'], size_hint_y=None, height=22,
            halign='left'
        ))
        self._win_bar = ProgressBar(max=100, value=0,
                                     size_hint_y=None, height=16)
        col.add_widget(self._win_bar)
        self._win_pct_lbl = Label(
            text='0%', font_size=FONT_SIZES['body'], bold=True,
            color=COLORS['gold'], size_hint_y=None, height=30, halign='center'
        )
        col.add_widget(self._win_pct_lbl)

        # ─── Qo'shimcha ko'rsatkichlar ─────────────────────────────────
        details_grid = BoxLayout(orientation='vertical', spacing=8,
                                  size_hint_y=None, height=100)
        col.add_widget(details_grid)

        for key, label in [('best_time', 'Eng qisqa o\'yin'),
                            ('avg_turns', 'O\'rtacha turlar soni')]:
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=44,
                            spacing=12)
            lbl = Label(text=label, font_size=FONT_SIZES['body'],
                        color=COLORS['text_primary'], halign='left')
            lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))
            val_lbl = Label(text='—', font_size=FONT_SIZES['h3'], bold=True,
                            color=COLORS['gold'], size_hint_x=None, width=80,
                            halign='center')
            row.add_widget(lbl)
            row.add_widget(val_lbl)
            self._stat_labels[key + '_val'] = val_lbl
            details_grid.add_widget(row)

        col.add_widget(Widget())

        # ─── Tozalash tugmasi ─────────────────────────────────────────────
        reset_btn = LuxuryButton(text='Statistikani tozalash', style='danger')
        reset_btn.bind(on_release=lambda *a: self._reset_stats())
        col.add_widget(reset_btn)

        # ─── Orqaga ───────────────────────────────────────────────────────
        back_btn = LuxuryButton(text='Orqaga', style='secondary')
        back_btn.bind(on_release=lambda *a: self._go_back())
        col.add_widget(back_btn)

    def _refresh_stats(self):
        app = App.get_running_app()
        if not (app and hasattr(app, 'stats') and app.stats):
            return

        data = app.stats.get_summary()

        # Asosiy raqamlar
        for key in ['total', 'wins', 'losses']:
            box = self._stat_labels.get(key)
            if box:
                box.set_value(str(data.get(key, 0)))

        # G'alaba foizi
        pct = data.get('win_rate', 0)
        self._win_bar.value = pct
        self._win_pct_lbl.text = f"{pct:.1f}%"

        # Qo'shimcha
        best = data.get('best_time', 0)
        best_lbl = self._stat_labels.get('best_time_val')
        if best_lbl:
            best_lbl.text = app.stats.format_time(best) if best else '—'

        avg = data.get('avg_turns', 0)
        avg_lbl = self._stat_labels.get('avg_turns_val')
        if avg_lbl:
            avg_lbl.text = str(avg) if avg else '—'

    def _reset_stats(self):
        app = App.get_running_app()
        if app and hasattr(app, 'stats') and app.stats:
            app.stats.reset()
            self._refresh_stats()
        if app and hasattr(app, 'audio') and app.audio:
            app.audio.on_button()

    def _go_back(self):
        App.get_running_app().navigate_to('main_menu', direction='right')


class _StatBox(BoxLayout):
    def __init__(self, icon: str, **kwargs):
        super().__init__(orientation='vertical', spacing=4, **kwargs)
        self._icon = icon

        self._icon_lbl = Label(
            text=icon, font_size=28,
            size_hint_y=None, height=36, halign='center'
        )
        self._val_lbl = Label(
            text='0', font_size=FONT_SIZES['h1'], bold=True,
            color=COLORS['gold'], size_hint_y=None, height=42, halign='center'
        )
        self.add_widget(self._icon_lbl)
        self.add_widget(self._val_lbl)
        self.bind(pos=self._draw, size=self._draw)

    def set_value(self, val: str):
        self._val_lbl.text = val

    def _draw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*COLORS['surface'])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
            Color(*COLORS['gold'][:3], 0.3)
            Line(rounded_rectangle=[self.x, self.y,
                                     self.width, self.height, 12], width=1.0)
