"""
ui/screens/online_setup_screen.py — Online ulanish sozlamalari
O'yin yaratish yoki qidirish.
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout  import FloatLayout
from kivy.uix.boxlayout    import BoxLayout
from kivy.uix.label        import Label
from kivy.app              import App
from kivy.clock            import Clock
from ui.components.luxury_button import LuxuryButton
from ui.components.animated_bg   import AnimatedBackground
from core.constants        import COLORS
from core.network_manager  import NetworkManager

class OnlineSetupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._built = False
        self.net = NetworkManager.get_instance()

    def on_enter(self):
        if not self._built:
            self._build_ui()
            self._built = True
        if self._bg: self._bg.start()
        
        # Tarmoq sozlamalarini boshlash
        self.net.on_peer_found = self._on_peer_found
        self.net.on_connected = self._on_connected
        self._status_lbl.text = "WI-FI TARMOG'INI TEKSHIRING..."

    def on_leave(self):
        if self._bg: self._bg.stop()

    def _build_ui(self):
        root = FloatLayout()
        self.add_widget(root)

        self._bg = AnimatedBackground()
        root.add_widget(self._bg)

        col = BoxLayout(
            orientation='vertical',
            spacing=15,
            padding=[40, 20],
            size_hint=(0.85, None),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        root.add_widget(col)

        self._status_lbl = Label(
            text="TAYYOR",
            font_size=18,
            color=COLORS['gold'],
            size_hint_y=None, height=50
        )
        col.add_widget(self._status_lbl)

        self.btn_host = LuxuryButton(text="O'YIN YARATISH (HOST)", style='primary')
        self.btn_host.bind(on_release=lambda x: self._start_hosting())
        col.add_widget(self.btn_host)

        self.btn_join = LuxuryButton(text="O'YINGA QO'SHILISH (JOIN)", style='secondary')
        self.btn_join.bind(on_release=lambda x: self._start_searching())
        col.add_widget(self.btn_join)

        btn_back = LuxuryButton(text="ORTGA", style='danger')
        btn_back.bind(on_release=lambda x: self._cancel())
        col.add_widget(btn_back)
        
        col.height = 50 + 15 + 3*60 + 2*15

    def _start_hosting(self):
        self._status_lbl.text = "O'YIN YARATILDI. QIDIRILMOQDA..."
        self.btn_host.disabled = True
        self.btn_join.disabled = True
        self.net.start_hosting("O'yinchi1")

    def _start_searching(self):
        self._status_lbl.text = "RAQIB QIDIRILMOQDA..."
        self.btn_host.disabled = True
        self.btn_join.disabled = True
        self.net.start_searching()

    def _on_peer_found(self, ip, name):
        def update_ui(dt):
            self._status_lbl.text = f"TOPILDI: {name} ({ip}). ULANMOQDA..."
        Clock.schedule_once(update_ui)

    def _on_connected(self):
        def go_to_game(dt):
            self._status_lbl.text = "ULANDI! O'YIN BOSHLANMOQDA..."
            app = App.get_running_app()
            app.is_multiplayer = True
            app.navigate_to('game')
        Clock.schedule_once(go_to_game, 0.5)

    def _cancel(self):
        self.net.stop_all()
        # Tugmalarni qayta yoqish
        self.btn_host.disabled = False
        self.btn_join.disabled = False
        App.get_running_app().navigate_to('mode_selection')
