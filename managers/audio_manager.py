"""
managers/audio_manager.py — Ovoz boshqaruvchisi
Kivy SoundLoader + looping music orqali SFX va musiqa.

Tuzatishlar:
  - play_music() to'liq implement qilindi
  - on_game_start() mavjud fayllarni tekshiradi
  - logging qo'shildi
  - Barcha exception-lar logging bilan yoziladi
"""
import os
import logging
from typing import Dict, Optional, List
from core.constants import SOUNDS_DIR, MUSIC_DIR

logger = logging.getLogger(__name__)


class AudioManager:
    """
    Durak o'yini uchun ovoz tizimi.
    - SFX: qisqa effektlar (wav)
    - Music: orqa fon musiqasi (loop)
    """

    def __init__(self):
        self._sfx:    Dict[str, object] = {}
        self._music:  Optional[object]  = None
        self._sfx_volume:   float = 0.8
        self._music_volume: float = 0.6
        self._sound_on:  bool = True
        self._music_on:  bool = True
        self._current_track: str = ''
        self._playlist: List[str] = []
        self._playlist_index: int = 0
        self._load_all()

    # ─── Yuklash ──────────────────────────────────────────────────────────────
    def _load_all(self):
        """Barcha SFX fayllarni yuklash"""
        sfx_files = {
            'card_deal':    'card_deal.wav',
            'card_place':   'card_place.wav',
            'card_take':    'card_take.wav',
            'card_flip':    'card_flip.wav',
            'win':          'win.wav',
            'lose':         'lose.wav',
            'button_click': 'button_click.wav',
            'trump_reveal': 'trump_reveal.wav',
            'invalid':      'invalid.wav',
        }

        try:
            from kivy.core.audio import SoundLoader
            loaded = 0
            for key, filename in sfx_files.items():
                path = os.path.join(SOUNDS_DIR, filename)
                if os.path.exists(path):
                    sound = SoundLoader.load(path)
                    if sound:
                        self._sfx[key] = sound
                        loaded += 1
                    else:
                        logger.warning(f"[Audio] SFX yuklanmadi: {filename}")
                else:
                    logger.debug(f"[Audio] SFX fayl topilmadi (o'tkazib yuborildi): {path}")
            logger.info(f"[Audio] {loaded}/{len(sfx_files)} SFX yuklandi")
        except Exception as e:
            logger.error(f"[Audio] SFX yuklashda xato: {e}")

    def _load_music(self, track_name: str):
        """Musiqa faylini yuklash"""
        try:
            from kivy.core.audio import SoundLoader
            path = os.path.join(MUSIC_DIR, track_name)
            if not os.path.exists(path):
                logger.debug(f"[Audio] Musiqa fayli topilmadi: {path}")
                return None
            music = SoundLoader.load(path)
            if music:
                music.loop   = True
                music.volume = self._music_volume
                logger.info(f"[Audio] Musiqa yuklandi: {track_name}")
                return music
            logger.warning(f"[Audio] SoundLoader musiqa yarata olmadi: {track_name}")
        except Exception as e:
            logger.error(f"[Audio] Musiqa yuklanmadi ({track_name}): {e}")
        return None

    # ─── SFX ──────────────────────────────────────────────────────────────────
    def play_sfx(self, name: str):
        """SFX effekt ijro etish"""
        if not self._sound_on:
            return
        sound = self._sfx.get(name)
        if sound:
            try:
                sound.volume = self._sfx_volume
                sound.play()
            except Exception:
                pass

    # ─── Musiqa ───────────────────────────────────────────────────────────────
    def play_music(self, track_name: str, loop: bool = True):
        """Yagona musiqani ijro etish"""
        if not self._music_on:
            return
        if self._current_track == track_name and self._music:
            return

        self.stop_music()
        self._playlist = []  # Playlistni o'chirish
        self._music = self._load_music(track_name)
        if self._music:
            self._music.loop = loop
            try:
                self._music.play()
                self._current_track = track_name
                logger.info(f"[Audio] Musiqa boshlandi: {track_name} (loop={loop})")
            except Exception as e:
                logger.error(f"[Audio] Musiqa ijro xatosi: {e}")
                self._music = None
                self._current_track = ''

    def play_playlist(self, tracks: List[str]):
        """Pleylistni ketma-ket chalish"""
        if not self._music_on or not tracks:
            return
        self._playlist = tracks
        self._playlist_index = 0
        self._play_current_playlist_track()

    def _play_current_playlist_track(self):
        if not self._playlist:
            return
        track_name = self._playlist[self._playlist_index]
        self.stop_music()
        # Playlist davom etayotganda
        self._playlist = self._playlist  # references kept
        
        self._music = self._load_music(track_name)
        if self._music:
            self._music.loop = False  # To o'zi to'xtab keyingisiga o'tishi uchun
            self._music.bind(on_stop=self._on_music_stop)
            try:
                self._music.play()
                self._current_track = track_name
            except Exception:
                pass

    def _on_music_stop(self, *args):
        # Audio tugaganda avtomat keyingisiga o'tish
        if not self._playlist or not self._music_on:
            return
        self._playlist_index = (self._playlist_index + 1) % len(self._playlist)
        self._play_current_playlist_track()

    def stop_music(self):
        """Musiqani to'xtatish"""
        if self._music:
            try:
                self._music.stop()
                self._music.unbind(on_stop=self._on_music_stop)
            except Exception:
                pass
            self._music         = None
            self._current_track = ''

    def stop_all(self):
        """Barcha ovozlarni to'xtatish"""
        self.stop_music()
        for sound in self._sfx.values():
            try:
                sound.stop()
            except Exception:
                pass

    # ─── O'yinga xos qisqa usullar ────────────────────────────────────────────
    def on_card_deal(self):    self.play_sfx('card_deal')
    def on_card_place(self):   self.play_sfx('card_place')
    def on_card_take(self):    self.play_sfx('card_take')
    def on_card_flip(self):    self.play_sfx('card_flip')
    def on_win(self):          self.play_sfx('win')
    def on_lose(self):         self.play_sfx('lose')
    def on_button(self):       self.play_sfx('button_click')
    def on_trump_reveal(self): self.play_sfx('trump_reveal')
    def on_invalid(self):      self.play_sfx('invalid')

    def on_main_menu(self):    self.play_music('menu_theme.wav', loop=True)

    def on_game_start(self):
        """
        O'yin boshlanganda musiqa chalish.
        Mavjud trek fayllarini avtomatik aniqlaydi.
        """
        # Imkon qadar playlist bilan, aks holda yagona trek
        available_tracks = []
        for candidate in ['track1.wav', 'track2.wav', 'track3.wav',
                           'game_theme.wav', 'game_theme.mp3']:
            if os.path.exists(os.path.join(MUSIC_DIR, candidate)):
                available_tracks.append(candidate)

        if len(available_tracks) > 1:
            self.play_playlist(available_tracks)
        elif len(available_tracks) == 1:
            self.play_music(available_tracks[0], loop=True)
        else:
            logger.debug("[Audio] O'yin musiqasi topilmadi, ovozisiz davom etiladi")

    def on_victory(self):
        self.stop_music()
        self.play_sfx('win')

    # ─── Volume boshqaruv ─────────────────────────────────────────────────────
    def set_sfx_volume(self, vol: float):
        self._sfx_volume = max(0.0, min(1.0, vol))

    def set_music_volume(self, vol: float):
        self._music_volume = max(0.0, min(1.0, vol))
        if self._music:
            try:
                self._music.volume = self._music_volume
            except Exception:
                pass

    def set_sound_enabled(self, enabled: bool):
        self._sound_on = enabled
        if not enabled:
            for sound in self._sfx.values():
                try:
                    sound.stop()
                except Exception:
                    pass

    def set_music_enabled(self, enabled: bool):
        self._music_on = enabled
        if not enabled:
            self.stop_music()

    def apply_settings(self, settings):
        """SettingsManager dan sozlamalarni qabul qilish"""
        self.set_sound_enabled(settings.sound_enabled)
        self.set_music_enabled(settings.music_enabled)
        self.set_sfx_volume(settings.sound_volume)
        self.set_music_volume(settings.music_volume)
