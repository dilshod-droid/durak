"""
managers/settings_manager.py — Sozlamalar boshqaruvchisi
JSON fayl orqali sozlamalarni saqlaydi va yuklaydi.
"""
import os
import json
from core.constants import BASE_DIR


SETTINGS_FILE = os.path.join(BASE_DIR, 'data', 'settings.json')

DEFAULT_SETTINGS = {
    'language':    'uz',          # 'uz' | 'ru' | 'en'
    'sound':       True,
    'sound_vol':   0.8,
    'music':       True,
    'music_vol':   0.6,
    'vibration':   True,
    'anim_speed':  1.0,           # 0.5 = tez, 1.0 = normal, 2.0 = sekin
    'theme':       'dark',        # 'dark' | 'light'
    'game_mode':   'podkidnoy',   # 'podkidnoy' | 'perevodnoy'
    'difficulty':  'medium',      # 'easy' | 'medium' | 'hard'
}


class SettingsManager:
    """
    Singleton-like sozlamalar boshqaruvchisi.
    Barcha sozlamalar settings.json da saqlanadi.
    """

    def __init__(self):
        self._settings: dict = dict(DEFAULT_SETTINGS)
        self._ensure_dir()
        self._load()

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)

    # ─── Yuklash / Saqlash ────────────────────────────────────────────────────
    def _load(self):
        """Fayldan sozlamalarni yuklash"""
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # Faqat taniqli kalitlarni qabul qilish
                for key in DEFAULT_SETTINGS:
                    if key in data:
                        self._settings[key] = data[key]
            except (json.JSONDecodeError, IOError):
                pass  # Standart qiymatlar ishlatilinadi

    def save(self):
        """Sozlamalarni faylga saqlash"""
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"[Settings] Saqlashda xato: {e}")

    # ─── Getter / Setter ──────────────────────────────────────────────────────
    def get(self, key: str, default=None):
        return self._settings.get(key, default)

    def set(self, key: str, value):
        if key in DEFAULT_SETTINGS:
            self._settings[key] = value
            self.save()

    def reset(self):
        """Standart sozlamalarga qaytish"""
        self._settings = dict(DEFAULT_SETTINGS)
        self.save()

    # ─── Tezkor kirish ────────────────────────────────────────────────────────
    @property
    def language(self) -> str:
        return self._settings['language']

    @property
    def sound_enabled(self) -> bool:
        return self._settings['sound']

    @property
    def sound_volume(self) -> float:
        return self._settings['sound_vol']

    @property
    def music_enabled(self) -> bool:
        return self._settings['music']

    @property
    def music_volume(self) -> float:
        return self._settings['music_vol']

    @property
    def vibration_enabled(self) -> bool:
        return self._settings['vibration']

    @property
    def anim_speed(self) -> float:
        return self._settings['anim_speed']

    @property
    def game_mode(self) -> str:
        return self._settings['game_mode']

    @property
    def difficulty(self) -> str:
        return self._settings['difficulty']

    def __repr__(self):
        return f"SettingsManager({self._settings})"
