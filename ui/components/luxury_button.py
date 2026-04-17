"""
ui/components/luxury_button.py — Premium Oltin Tugma
Dark Luxury uslubida gradient oltin tugma.
"""
from kivy.uix.behaviors   import ButtonBehavior
from kivy.uix.boxlayout   import BoxLayout
from kivy.uix.label       import Label
from kivy.graphics        import (Color, RoundedRectangle, Line,
                                   Rectangle)
from kivy.animation       import Animation
from kivy.properties      import StringProperty, BooleanProperty, ListProperty
from core.constants       import COLORS, FONT_SIZES, FONTS_DIR
import os


class LuxuryButton(ButtonBehavior, BoxLayout):
    """
    Premium oltin tugma.
    Uslublar: 'primary' (oltin), 'secondary' (chegara), 'danger' (qizil)
    """
    text    = StringProperty('')
    style   = StringProperty('primary')    # 'primary' | 'secondary' | 'danger'
    icon    = StringProperty('')
    enabled = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation  = 'horizontal'
        self.size_hint_y  = None
        self.height       = 52
        self.padding      = [20, 0]
        self.spacing      = 8

        self._label = Label(
            font_size   = FONT_SIZES['body'],
            bold        = True,
            color       = COLORS['text_primary'],
            halign      = 'center',
            valign      = 'middle',
        )
        self.add_widget(self._label)

        self.bind(
            pos     = self._redraw,
            size    = self._redraw,
            text    = self._update_text,
            style   = self._redraw,
            enabled = self._redraw,
        )

    def _update_text(self, *args):
        self._label.text = self.text
        self._label.texture_update()

    def _redraw(self, *args):
        self._label.text = self.text
        self.canvas.before.clear()

        alpha = 1.0 if self.enabled else 0.5

        with self.canvas.before:
            if self.style == 'primary':
                # Oltin gradient fon
                Color(*(COLORS['gold_dark'][:3]), alpha)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
                Color(*(COLORS['gold'][:3]), alpha * 0.7)
                RoundedRectangle(
                    pos=(self.x, self.y + self.height * 0.5),
                    size=(self.width, self.height * 0.5),
                    radius=[0, 0, 12, 12]
                )
                # Yuqori yaltiroq chizig'i
                Color(*(COLORS['gold_light'][:3]), alpha * 0.4)
                RoundedRectangle(
                    pos=(self.x + 2, self.y + self.height - 4),
                    size=(self.width - 4, 3),
                    radius=[8]
                )
                self._label.color = (*COLORS['background'][:3], 1)

            elif self.style == 'secondary':
                Color(0, 0, 0, 0)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
                Color(*(COLORS['gold'][:3]), alpha)
                Line(rounded_rectangle=[self.x, self.y,
                                        self.width, self.height, 12],
                     width=1.5)
                self._label.color = (*COLORS['gold'][:3], alpha)

            elif self.style == 'danger':
                Color(0.78, 0.16, 0.16, alpha)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
                self._label.color = (1, 1, 1, alpha)

    # ─── Interaktivlik ────────────────────────────────────────────────────────
    def on_press(self):
        if not self.enabled:
            return
        anim = Animation(opacity=0.75, duration=0.06) + \
               Animation(opacity=1.0,  duration=0.08)
        anim.start(self)

    def on_release(self):
        if not self.enabled:
            return
        # App orqali audio
        try:
            from kivy.app import App
            app = App.get_running_app()
            if app and hasattr(app, 'audio'):
                app.audio.on_button()
        except Exception:
            pass
