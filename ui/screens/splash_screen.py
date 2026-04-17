"""
ui/screens/splash_screen.py — Kirish Ekrani
Logo animatsiyasi + orqa fon.
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label     import Label
from kivy.uix.widget    import Widget
from kivy.graphics      import (Color, Ellipse, RoundedRectangle,
                                 Rectangle, Line)
from kivy.animation     import Animation
from kivy.clock         import Clock
from kivy.app           import App
import math, random
from core.constants     import COLORS, FONT_SIZES


class SplashScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._built = False

    def on_enter(self):
        if not self._built:
            self._build_ui()
            self._built = True
        self._start_animation()

    def on_leave(self):
        if hasattr(self, '_bg') and self._bg:
            self._bg.stop()

    def _build_ui(self):
        root = FloatLayout()
        self.add_widget(root)

        # ─── Fon ──────────────────────────────────────────────────────────
        self._bg = _SplashBg()
        root.add_widget(self._bg)

        # ─── Logo konteyner ───────────────────────────────────────────────
        self._logo_box = Widget(
            size_hint=(None, None),
            size=(220, 220),
            pos_hint={'center_x': 0.5, 'center_y': 0.55},
            opacity=0,
        )
        root.add_widget(self._logo_box)

        # Logo doira
        self._logo_circle = _LogoCircle()
        self._logo_box.add_widget(self._logo_circle)

        # ─── Sarlavha ─────────────────────────────────────────────────────
        self._title = Label(
            text      = 'DURAK',
            font_size = FONT_SIZES['display'] + 8,
            bold      = True,
            color     = COLORS['gold'],
            pos_hint  = {'center_x': 0.5, 'center_y': 0.35},
            size_hint = (1, None),
            height    = 60,
            opacity   = 0,
            halign    = 'center',
        )
        root.add_widget(self._title)

        # ─── Tagline ──────────────────────────────────────────────────────
        self._tagline = Label(
            text      = 'Premium Karta O\'yini',
            font_size = FONT_SIZES['body'],
            color     = COLORS['text_secondary'],
            pos_hint  = {'center_x': 0.5, 'center_y': 0.27},
            size_hint = (1, None),
            height    = 30,
            opacity   = 0,
            halign    = 'center',
        )
        root.add_widget(self._tagline)

        # ─── Yuklash matni ────────────────────────────────────────────────
        self._loading = Label(
            text      = 'Yuklanmoqda...',
            font_size = FONT_SIZES['small'],
            color     = COLORS['text_muted'],
            pos_hint  = {'center_x': 0.5, 'y': 0.05},
            size_hint = (1, None),
            height    = 24,
            opacity   = 0,
            halign    = 'center',
        )
        root.add_widget(self._loading)

    def _start_animation(self):
        """Barcha animatsiyalarni boshlash"""
        # Logo paydo bo'ladi
        Animation(opacity=1, duration=0.6, t='out_sine').start(self._logo_box)

        # Sarlavha kechroq paydo bo'ladi
        Clock.schedule_once(lambda dt: (
            Animation(opacity=1, duration=0.5).start(self._title)
        ), 0.4)

        # Tagline
        Clock.schedule_once(lambda dt: (
            Animation(opacity=1, duration=0.5).start(self._tagline)
        ), 0.7)

        # Loading matni
        Clock.schedule_once(lambda dt: (
            Animation(opacity=0.7, duration=0.4).start(self._loading)
        ), 1.0)

        # Asosiy menyuga o'tish
        Clock.schedule_once(self._go_to_main, 2.8)

    def _go_to_main(self, dt):
        app = App.get_running_app()
        if app:
            # Audio
            if hasattr(app, 'audio') and app.audio:
                app.audio.on_main_menu()
            app.navigate_to('main_menu')


class _SplashBg(Widget):
    """Splash ekrani uchun animatsiyali fon"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._t = 0
        self._particles = [
            {'x': random.random(), 'y': random.random(),
             'speed': random.uniform(0.2, 0.8),
             'size': random.uniform(3, 8),
             'alpha': random.uniform(0.3, 0.9)}
            for _ in range(20)
        ]
        self.bind(pos=self._draw, size=self._draw)
        self._clock_ev = Clock.schedule_interval(self._update, 1 / 30)

    def _update(self, dt):
        self._t += dt
        for p in self._particles:
            p['y'] = (p['y'] + p['speed'] * dt * 0.04) % 1.1
        self._draw()

    def stop(self):
        """Animatsiyani to'xtatish"""
        if hasattr(self, '_clock_ev') and self._clock_ev:
            self._clock_ev.cancel()
            self._clock_ev = None

    def _draw(self, *args):
        self.canvas.clear()
        if self.width == 0:
            return
        with self.canvas:
            # Asosiy fon
            Color(*COLORS['background'])
            Rectangle(pos=self.pos, size=self.size)

            # Radial yashil gradient
            cx = self.x + self.width  / 2
            cy = self.y + self.height / 2
            for i in range(6, 0, -1):
                r = min(self.width, self.height) * 0.65 * (i / 6)
                Color(*(COLORS['table'][:3]), 0.08 * i / 6)
                Ellipse(pos=(cx - r, cy - r), size=(r * 2, r * 2))

            # Oltin particle uchqunlar
            for p in self._particles:
                px = self.x + p['x'] * self.width
                py = self.y + p['y'] * self.height
                Color(*COLORS['gold'][:3], p['alpha'] * 0.5)
                Ellipse(pos=(px, py), size=(p['size'], p['size']))


class _LogoCircle(Widget):
    """Durak logo — oltin doirada karta belgilari"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *args):
        self.canvas.clear()
        if self.width == 0:
            return
        r  = min(self.width, self.height) / 2
        cx = self.x + self.width  / 2
        cy = self.y + self.height / 2
        with self.canvas:
            # Tashqi halqa — oltin
            Color(*COLORS['gold'][:3], 0.3)
            Ellipse(pos=(cx - r, cy - r), size=(r * 2, r * 2))

            # Ichki doira — to'q yashil
            ir = r * 0.85
            Color(*COLORS['surface'])
            Ellipse(pos=(cx - ir, cy - ir), size=(ir * 2, ir * 2))

            # Oltin chegara
            Color(*COLORS['gold'])
            Line(circle=(cx, cy, ir), width=2.5)

            # Tashqi oltin halqa
            Color(*COLORS['gold'][:3], 0.6)
            Line(circle=(cx, cy, r), width=1.5)

        # Karta belgilari — har biri mos joyga Label sifatida
        for child in list(self.children):
            self.remove_widget(child)

        from kivy.uix.label import Label as KLabel
        lbl = KLabel(
            text      = 'D',
            font_size = r * 1.2,
            bold      = True,
            color     = COLORS['gold'],
            size      = (r * 2, r * 2),
            pos       = (cx - r, cy - r),
            halign    = 'center',
            valign    = 'middle',
        )
        lbl.text_size = lbl.size
        self.add_widget(lbl)
