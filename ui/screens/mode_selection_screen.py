"""
ui/screens/mode_selection_screen.py — O'yin rejimini tanlash (Offline/Online)
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout  import FloatLayout
from kivy.uix.boxlayout    import BoxLayout
from kivy.uix.label        import Label
from kivy.app              import App
from ui.components.luxury_button import LuxuryButton
from ui.components.animated_bg   import AnimatedBackground
from core.constants        import COLORS, FONT_SIZES

class ModeSelectionScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._built = False

    def on_enter(self):
        if not self._built:
            self._build_ui()
            self._built = True
        if self._bg: self._bg.start()

    def on_leave(self):
        if self._bg: self._bg.stop()

    def _build_ui(self):
        root = FloatLayout()
        self.add_widget(root)

        # Fon
        self._bg = AnimatedBackground()
        root.add_widget(self._bg)

        # Markaziy blok
        col = BoxLayout(
            orientation='vertical',
            spacing=20,
            padding=[40, 20],
            size_hint=(0.85, None),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        root.add_widget(col)

        # Sarlavha
        lbl = Label(
            text="O'YIN REJIMINI TANLANG",
            font_size=24,
            bold=True,
            color=COLORS['gold'],
            size_hint_y=None, height=60
        )
        col.add_widget(lbl)

        # Tugmalar
        btn_offline = LuxuryButton(text="OFFLINE (AI BILAN)", style='primary')
        btn_offline.bind(on_release=lambda x: self._choose_offline())
        col.add_widget(btn_offline)

        btn_online = LuxuryButton(text="ONLINE (WI-FI ORQALI)", style='secondary')
        btn_online.bind(on_release=lambda x: self._choose_online())
        col.add_widget(btn_online)

        # Ortga
        btn_back = LuxuryButton(text="ORTGA", style='danger')
        btn_back.bind(on_release=lambda x: App.get_running_app().navigate_to('main_menu'))
        col.add_widget(btn_back)

        col.height = 60 + 20 + 3*60 + 2*20
    
    def _choose_offline(self):
        app = App.get_running_app()
        app.is_multiplayer = False
        app.navigate_to('difficulty')

    def _choose_online(self):
        app = App.get_running_app()
        app.is_multiplayer = True
        app.navigate_to('online_setup')
