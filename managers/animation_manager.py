"""
managers/animation_manager.py — Animatsiya yordamchi
Kivy Animation bilan karta va ekran animatsiyalari.
"""
from kivy.animation import Animation
from kivy.clock    import Clock
from typing import Callable, Optional


class AnimationManager:
    """
    Markazlashgan animatsiya boshqaruvchisi.
    Barcha animatsiya doimiy vaqtlari bu yerda.
    """

    def __init__(self, speed_factor: float = 1.0):
        self.speed = speed_factor   # 0.5 = tez, 1.0 = normal, 2.0 = sekin

    def _t(self, base_time: float) -> float:
        """Tezlikga moslashtirilgan vaqt"""
        return base_time * self.speed

    # ─── Karta animatsiyalari ─────────────────────────────────────────────────
    def card_deal(self, widget, from_x: float, from_y: float,
                  to_x: float, to_y: float, delay: float = 0,
                  on_complete: Optional[Callable] = None):
        """Karta berish animatsiyasi"""
        widget.x = from_x
        widget.y = from_y
        widget.opacity = 0

        def _start(dt):
            anim = (
                Animation(opacity=1, duration=self._t(0.1)) +
                Animation(x=to_x, y=to_y, duration=self._t(0.3), t='out_cubic')
            )
            if on_complete:
                anim.bind(on_complete=lambda *a: on_complete())
            anim.start(widget)

        Clock.schedule_once(_start, delay)

    def card_select(self, widget, selected: bool):
        """Karta tanlash (yuqoriga ko'tarish)"""
        target_y = widget.y + (15 if selected else -15)
        anim = Animation(y=target_y, duration=self._t(0.15), t='out_sine')
        anim.start(widget)

    def card_place(self, widget, to_x: float, to_y: float,
                   on_complete: Optional[Callable] = None):
        """Karta stolga tushishi"""
        anim = Animation(
            x=to_x, y=to_y,
            duration=self._t(0.25),
            t='in_out_quad'
        )
        if on_complete:
            anim.bind(on_complete=lambda *a: on_complete())
        anim.start(widget)

    def card_take(self, widget, to_x: float, to_y: float,
                  on_complete: Optional[Callable] = None):
        """Karta olinishi — pastga siljib yo'qoladi"""
        anim = Animation(
            x=to_x, y=to_y,
            opacity=0,
            duration=self._t(0.4),
            t='in_cubic'
        )
        if on_complete:
            anim.bind(on_complete=lambda *a: on_complete())
        anim.start(widget)

    def card_invalid(self, widget):
        """Noto'g'ri harakat — qizil tebranish"""
        orig_x = widget.x
        anim = (
            Animation(x=orig_x - 8,  duration=0.05) +
            Animation(x=orig_x + 8,  duration=0.05) +
            Animation(x=orig_x - 6,  duration=0.05) +
            Animation(x=orig_x + 6,  duration=0.05) +
            Animation(x=orig_x,      duration=0.05)
        )
        anim.start(widget)

    def card_flip(self, widget, on_complete: Optional[Callable] = None):
        """Karta ag'darilishi"""
        anim = (
            Animation(size_hint_x=0,  duration=self._t(0.1), t='in_sine') +
            Animation(size_hint_x=1,  duration=self._t(0.1), t='out_sine')
        )
        if on_complete:
            anim.bind(on_complete=lambda *a: on_complete())
        anim.start(widget)

    # ─── Widget animatsiyalari ─────────────────────────────────────────────────
    def fade_in(self, widget, duration: float = 0.3,
                on_complete: Optional[Callable] = None):
        """Fade in"""
        widget.opacity = 0
        anim = Animation(opacity=1, duration=self._t(duration))
        if on_complete:
            anim.bind(on_complete=lambda *a: on_complete())
        anim.start(widget)

    def fade_out(self, widget, duration: float = 0.3,
                 on_complete: Optional[Callable] = None):
        """Fade out"""
        anim = Animation(opacity=0, duration=self._t(duration))
        if on_complete:
            anim.bind(on_complete=lambda *a: on_complete())
        anim.start(widget)

    def scale_in(self, widget, from_scale: float = 0.5, duration: float = 0.4):
        """Kichikdan kattalashish"""
        widget.opacity = 0
        widget.scale = from_scale

        anim = Animation(
            opacity=1, scale=1.0,
            duration=self._t(duration),
            t='out_back'
        )
        anim.start(widget)

    def pulse(self, widget, scale: float = 1.05, duration: float = 0.8):
        """Yurak urishi kabi tebranuv (loop)"""
        anim = (
            Animation(scale=scale,  duration=duration / 2, t='in_out_sine') +
            Animation(scale=1.0,    duration=duration / 2, t='in_out_sine')
        )
        anim.repeat = True
        anim.start(widget)

    def slide_in_bottom(self, widget, distance: float = 100, delay: float = 0,
                        on_complete: Optional[Callable] = None):
        """Pastdan kirib kelish"""
        widget.opacity = 0
        orig_y = widget.y
        widget.y = orig_y - distance

        def _start(dt):
            anim = Animation(
                y=orig_y, opacity=1,
                duration=self._t(0.4),
                t='out_cubic'
            )
            if on_complete:
                anim.bind(on_complete=lambda *a: on_complete())
            anim.start(widget)

        Clock.schedule_once(_start, delay)

    def button_press(self, widget, on_complete: Optional[Callable] = None):
        """Tugma bosish animatsiyasi"""
        anim = (
            Animation(scale=0.93, duration=0.07, t='in_quad') +
            Animation(scale=1.0,  duration=0.08, t='out_quad')
        )
        if on_complete:
            anim.bind(on_complete=lambda *a: on_complete())
        anim.start(widget)

    def glow_pulse(self, widget, duration: float = 1.5):
        """Oltin parlaydigan effekt"""
        anim = (
            Animation(opacity=0.6, duration=duration / 2, t='in_out_sine') +
            Animation(opacity=1.0, duration=duration / 2, t='in_out_sine')
        )
        anim.repeat = True
        anim.start(widget)

    # ─── Tezlikni o'zgartirish ────────────────────────────────────────────────
    def set_speed(self, speed_factor: float):
        """Animatsiya tezligini o'rnatish (0.5=tez, 1.0=normal, 2.0=sekin)"""
        self.speed = max(0.1, min(3.0, speed_factor))
