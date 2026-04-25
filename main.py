"""
main.py — DURAK Kivy App Entry Point
Premium Android Karta O'yini v1.0.0

Tuzatishlar:
  - logging.basicConfig qo'shildi (debug va xato xabarlar)
  - is_multiplayer atributi boshlang'ich qiymat bilan
  - on_stop: stats.close() aniq chaqiriladi
"""
import os
import sys
import logging

# ─── Logging sozlash ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level   = logging.DEBUG,
    format  = '[%(levelname)s] %(name)s: %(message)s',
    handlers= [logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger('DurakApp')

# ─── Desktop oyna o'lchamini Android dan oldin o'rnatish ─────────────────────
from kivy.config import Config
if sys.platform != 'android':
    Config.set('graphics', 'width',     '400')
    Config.set('graphics', 'height',    '700')
    Config.set('graphics', 'resizable', False)
    Config.set('graphics', 'minimum_width',  400)
    Config.set('graphics', 'minimum_height', 700)

from kivy.app              import App
from kivy.uix.screenmanager import (ScreenManager, SlideTransition,
                                     FadeTransition, NoTransition)
from kivy.core.window      import Window
from kivy.core.text        import LabelBase
from kivy.clock            import Clock
import json

# ─── Fontlarni ro'yxatga olish ────────────────────────────────────────────────
def register_fonts():
    fonts_dir = os.path.join(os.path.dirname(__file__), 'assets', 'fonts')
    font_map = [
        ('Cinzel',   'Cinzel-Regular.ttf', 'Cinzel-Bold.ttf', None, None),
        ('Raleway',  'Raleway-Regular.ttf', 'Raleway-Bold.ttf', None, None),
    ]
    for name, regular, bold, italic, bold_italic in font_map:
        r = os.path.join(fonts_dir, regular)
        b = os.path.join(fonts_dir, bold)
        if os.path.exists(r):
            try:
                LabelBase.register(
                    name       = name,
                    fn_regular = r,
                    fn_bold    = b if os.path.exists(b) else r,
                )
            except Exception as e:
                print(f"[Font] {name} ro'yxatga olinmadi: {e}")
                
    # Maxsus belgilar (karta mastlari) uchun Kivy ga o'zining ichki shriftini ro'yxatdan o'tkazamiz
    import kivy
    dejavu = os.path.join(os.path.dirname(kivy.__file__), 'data', 'fonts', 'DejaVuSans.ttf')
    if os.path.exists(dejavu):
        LabelBase.register(name='DejaVu', fn_regular=dejavu)


class DurakApp(App):
    """
    Asosiy Kivy ilova sinfi.
    Global managerlar va navigatsiya shu yerda.
    """

    title = 'Durak'

    # ─── Global holatlar ──────────────────────────────────────────────────
    game_difficulty: str  = 'medium'
    game_mode:       str  = 'podkidnoy'
    game_result:     dict = {}
    is_multiplayer:  bool = False      # Multiplayer rejim bayrog'i

    # ─── Managerlar ───────────────────────────────────────────────────────
    audio    = None
    stats    = None
    settings = None
    lang     = {}

    def build(self):
        # Oyna fon rangi
        Window.clearcolor = (0.051, 0.106, 0.071, 1)  # #0D1B12

        # Assetlarni tekshirish va yaratish
        self._ensure_assets()

        # Fontlarni ro'yxatga olish
        register_fonts()

        # Managerlarni ishga tushirish
        self._init_managers()

        # Tilni yuklash
        self._load_language()

        # Ekran menejer
        self.sm = ScreenManager()
        self._setup_screens()

        return self.sm

    def _init_managers(self):
        from managers.audio_manager    import AudioManager
        from managers.stats_manager    import StatsManager
        from managers.settings_manager import SettingsManager

        self.settings = SettingsManager()
        self.stats    = StatsManager()
        self.audio    = AudioManager()
        self.audio.apply_settings(self.settings)

    def _setup_screens(self):
        from ui.screens.splash_screen       import SplashScreen
        from ui.screens.main_menu_screen    import MainMenuScreen
        from ui.screens.difficulty_screen   import DifficultyScreen
        from ui.screens.game_screen         import GameScreen
        from ui.screens.result_screen       import ResultScreen
        from ui.screens.settings_screen     import SettingsScreen
        from ui.screens.stats_screen        import StatsScreen
        from ui.screens.rules_screen        import RulesScreen
        from ui.screens.mode_selection_screen import ModeSelectionScreen
        from ui.screens.online_setup_screen  import OnlineSetupScreen

        screens = [
            SplashScreen(name='splash'),
            MainMenuScreen(name='main_menu'),
            ModeSelectionScreen(name='mode_selection'),
            OnlineSetupScreen(name='online_setup'),
            DifficultyScreen(name='difficulty'),
            GameScreen(name='game'),
            ResultScreen(name='result'),
            SettingsScreen(name='settings'),
            StatsScreen(name='stats'),
            RulesScreen(name='rules'),
        ]
        for screen in screens:
            self.sm.add_widget(screen)

        self.sm.current = 'splash'

    def _load_language(self):
        """Tanlangan til faylini yuklash"""
        lang_code = self.settings.language if self.settings else 'uz'
        lang_file = os.path.join(
            os.path.dirname(__file__), 'locales', f'{lang_code}.json'
        )
        if os.path.exists(lang_file):
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.lang = json.load(f)
            except Exception:
                self.lang = {}

    # ─── Navigatsiya ──────────────────────────────────────────────────────
    def navigate_to(self, screen_name: str, direction: str = 'left'):
        """Ekranlar orasida o'tish"""
        current = self.sm.current

        transition_map = {
            ('splash',     'main_menu'):   FadeTransition(duration=0.5),
            ('main_menu',  'difficulty'):  SlideTransition(direction='left',  duration=0.4),
            ('difficulty', 'game'):        SlideTransition(direction='up',    duration=0.4),
            ('game',       'result'):      FadeTransition(duration=0.5),
            ('result',     'main_menu'):   SlideTransition(direction='down',  duration=0.4),
            ('result',     'game'):        FadeTransition(duration=0.3),
            ('main_menu',  'settings'):    SlideTransition(direction='left',  duration=0.35),
            ('main_menu',  'stats'):       SlideTransition(direction='left',  duration=0.35),
            ('main_menu',  'rules'):       SlideTransition(direction='left',  duration=0.35),
            ('settings',   'main_menu'):   SlideTransition(direction='right', duration=0.35),
            ('stats',      'main_menu'):   SlideTransition(direction='right', duration=0.35),
            ('rules',      'main_menu'):   SlideTransition(direction='right', duration=0.35),
            ('difficulty', 'main_menu'):   SlideTransition(direction='right', duration=0.4),
        }

        key = (current, screen_name)
        transition = transition_map.get(
            key,
            SlideTransition(direction=direction, duration=0.35)
        )

        self.sm.transition = transition
        self.sm.current    = screen_name

    # ─── Assetlarni tekshirish ────────────────────────────────────────────
    def _ensure_assets(self):
        """Agar assetlar yo'q bo'lsa — avtomatik generatsiya qilish"""
        cards_dir = os.path.join(os.path.dirname(__file__), 'assets', 'cards')
        back_img  = os.path.join(cards_dir, 'card_back.png')

        if not os.path.exists(back_img):
            print("[App] Assetlar topilmadi. Generatsiya boshlanmoqda...")
            try:
                script = os.path.join(
                    os.path.dirname(__file__), 'tools', 'generate_assets.py'
                )
                if os.path.exists(script):
                    import subprocess
                    subprocess.run([sys.executable, script], check=True)
                    print("[App] Assetlar yaratildi ✓")
            except Exception as e:
                print(f"[App] Asset generatsiya xatosi: {e}")
                print("[App] Dastur assetlarsiz davom etadi...")

    def on_stop(self):
        """Ilova yopilganda barcha resurslarni tozalash"""
        if self.audio:
            self.audio.stop_all()
        if self.settings:
            self.settings.save()
        if self.stats:
            self.stats.close()   # __del__ ga ishonmasdan aniq yopish
        logger.info("[App] Ilova to'xtatildi, resurslar tozalandi")

    # ─── Android orqa tugmasi ─────────────────────────────────────────────
    def on_key_down(self, window, key, *args):
        ESC = 27
        if key == ESC:
            current = self.sm.current
            back_map = {
                'main_menu':  None,   # Ilovani yopish
                'difficulty': 'main_menu',
                'game':       'main_menu',
                'result':     'main_menu',
                'settings':   'main_menu',
                'stats':      'main_menu',
                'rules':      'main_menu',
            }
            dest = back_map.get(current)
            if dest:
                self.navigate_to(dest, direction='right')
                return True
        return False


if __name__ == '__main__':
    # Assetlar yo'liga o'tish
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    DurakApp().run()
