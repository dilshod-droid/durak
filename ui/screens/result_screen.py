"""
ui/screens/result_screen.py — Natija Ekrani
G'alaba yoki yutqizuv — confetti yoki sad animatsiya.
"""
import random
import math
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout  import FloatLayout
from kivy.uix.boxlayout    import BoxLayout
from kivy.uix.label        import Label
from kivy.uix.widget       import Widget
from kivy.graphics         import Color, Ellipse, Rectangle, RoundedRectangle
from kivy.animation        import Animation
from kivy.clock            import Clock
from kivy.app              import App
from ui.components.luxury_button import LuxuryButton
from core.constants        import COLORS, FONT_SIZES


class ResultScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._built      = False
        self._particles  = []
        self._anim_event = None

    def on_enter(self):
        result = getattr(App.get_running_app(), 'game_result', {})
        self._build_ui(result)
        self._start_effects(result.get('is_win', False))

    def on_leave(self):
        if self._anim_event:
            self._anim_event.cancel()
            self._anim_event = None
        for child in list(self.children):
            self.remove_widget(child)
        self._built = False
        self._particles.clear()

    def _build_ui(self, result: dict):
        root = FloatLayout()
        self.add_widget(root)

        is_win = result.get('is_win', False)

        # ─── Fon ──────────────────────────────────────────────────────────
        bg_color = COLORS['table'] if is_win else COLORS['surface']
        with self.canvas.before:
            Color(*bg_color)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(
            pos=lambda *a: setattr(self._bg_rect, 'pos', self.pos),
            size=lambda *a: setattr(self._bg_rect, 'size', self.size),
        )

        # ─── Particle fon ─────────────────────────────────────────────────
        self._particle_layer = _ParticleLayer(
            is_win=is_win, size_hint=(1, 1), pos_hint={'x': 0, 'y': 0}
        )
        root.add_widget(self._particle_layer)

        # ─── Markaziy kontent ─────────────────────────────────────────────
        col = BoxLayout(
            orientation = 'vertical',
            spacing     = 18,
            padding     = [32, 0],
            size_hint   = (0.9, None),
            pos_hint    = {'center_x': 0.5, 'center_y': 0.5},
        )
        root.add_widget(col)

        # Katta emoji
        emoji = '+' if is_win else '-'
        emoji_lbl = Label(
            text      = emoji,
            font_size = 80,
            size_hint_y = None,
            height    = 100,
            halign    = 'center',
            opacity   = 0,
        )
        col.add_widget(emoji_lbl)
        self._emoji_lbl = emoji_lbl

        # Sarlavha
        title_text  = "G'ALABA!" if is_win else "DURAK!"
        title_color = COLORS['gold'] if is_win else COLORS['danger']
        title = Label(
            text      = title_text,
            font_size = FONT_SIZES['display'] + 6,
            bold      = True,
            color     = title_color,
            size_hint_y = None,
            height    = 70,
            halign    = 'center',
            opacity   = 0,
        )
        col.add_widget(title)
        self._title_lbl = title

        # ─── Statistika satrlari ──────────────────────────────────────────
        stats_box = BoxLayout(
            orientation = 'vertical',
            spacing     = 8,
            size_hint_y = None,
            height      = 100,
            opacity     = 0,
        )
        self._stats_box = stats_box

        for key, icon, label in [
            ('turns',        '', 'Turlar soni'),
            ('cards_taken',  '', 'Olingan kartalar'),
            ('time_str',     '', 'O\'yin vaqti'),
        ]:
            val = result.get(key, 0)
            if key == 'time_str':
                m, s = divmod(result.get('time_sec', 0), 60)
                val = f"{m}:{s:02d}"
            row = self._stat_row(icon, label, str(val))
            stats_box.add_widget(row)

        col.add_widget(stats_box)

        # ─── Ajratgich ────────────────────────────────────────────────────
        sep = Widget(size_hint_y=None, height=1)
        with sep.canvas:
            Color(*COLORS['gold'][:3], 0.4)
            Rectangle(pos=(32, 0), size=(100, 1))
        col.add_widget(sep)

        # ─── Tugmalar ─────────────────────────────────────────────────────
        play_again = LuxuryButton(text='QAYTADAN O\'YNASH', style='primary')
        play_again.height = 56
        play_again.bind(on_release=lambda *a: self._play_again())
        col.add_widget(play_again)

        menu_btn = LuxuryButton(text='BOSH MENYU', style='secondary')
        menu_btn.bind(on_release=lambda *a: self._go_menu())
        col.add_widget(menu_btn)

        # Balandlikni hisoblash
        col.height = 100 + 70 + 100 + 1 + 56 + 52 + 4 * 18

        # ─── Animatsiya ───────────────────────────────────────────────────
        Clock.schedule_once(lambda dt: self._animate_entrance(), 0.1)

    def _stat_row(self, icon: str, label: str, val: str) -> BoxLayout:
        row = BoxLayout(orientation='horizontal', size_hint_y=None, height=28,
                        spacing=10, padding=[16, 0])
        row.add_widget(Label(text=icon, font_size=16,
                             size_hint_x=None, width=24, halign='center'))
        lbl = Label(text=label, font_size=FONT_SIZES['small'],
                    color=COLORS['text_secondary'], halign='left')
        lbl.bind(size=lambda inst, v: setattr(inst, 'text_size', (v[0], None)))
        row.add_widget(lbl)
        row.add_widget(Label(text=val, font_size=FONT_SIZES['body'], bold=True,
                             color=COLORS['gold'], size_hint_x=None, width=70,
                             halign='center'))
        return row

    def _animate_entrance(self):
        # Emoji scale-in
        self._emoji_lbl.opacity = 0
        anim = Animation(opacity=1, duration=0.5, t='out_back')
        anim.start(self._emoji_lbl)

        # Sarlavha
        Clock.schedule_once(
            lambda dt: Animation(opacity=1, duration=0.4).start(self._title_lbl),
            0.3
        )

        # Statistika
        Clock.schedule_once(
            lambda dt: Animation(opacity=1, duration=0.5).start(self._stats_box),
            0.6
        )

    def _start_effects(self, is_win: bool):
        if is_win and self._particle_layer:
            self._particle_layer.start()

    # ─── Navigatsiya ──────────────────────────────────────────────────────────
    def _play_again(self):
        App.get_running_app().navigate_to('game')

    def _go_menu(self):
        App.get_running_app().navigate_to('main_menu', direction='down')


class _ParticleLayer(Widget):
    """
    G'alaba holatida: oltin konfetti yomg'iri
    Yutqizuvda: kartalar pastga tushadi (kulrang)
    """

    def __init__(self, is_win: bool, **kwargs):
        super().__init__(**kwargs)
        self.is_win     = is_win
        self._particles = []
        self._running   = False
        self.bind(pos=self._redraw, size=self._redraw)

    def start(self):
        self._running = True
        self._spawn_particles()
        Clock.schedule_interval(self._update, 1 / 30)

    def _spawn_particles(self):
        n = 60 if self.is_win else 20
        for _ in range(n):
            self._particles.append({
                'x':     random.random(),
                'y':     1.1,
                'vy':    random.uniform(0.3, 0.9),
                'vx':    random.uniform(-0.1, 0.1),
                'size':  random.uniform(6, 14),
                'color': random.choice([
                    COLORS['gold'], COLORS['gold_light'],
                    COLORS['success'], COLORS['warning'],
                ]),
                'alpha': random.uniform(0.7, 1.0),
                'rot':   random.uniform(0, 360),
                'rot_v': random.uniform(-120, 120),
            })

    def _update(self, dt):
        alive = []
        for p in self._particles:
            p['y']   -= p['vy'] * dt * 0.3
            p['x']   += p['vx'] * dt
            p['rot'] += p['rot_v'] * dt
            if p['y'] > -0.1:
                alive.append(p)
        self._particles = alive
        self._redraw()

        if not alive and self._running:
            self._running = False

    def _redraw(self, *args):
        self.canvas.clear()
        if not self._particles or self.width == 0:
            return
        with self.canvas:
            for p in self._particles:
                px = self.x + p['x'] * self.width
                py = self.y + p['y'] * self.height
                s  = p['size']
                Color(*(p['color'][:3]), p['alpha'])
                Ellipse(pos=(px - s / 2, py - s / 2), size=(s, s))
