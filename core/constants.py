"""
Durak O'yini — Umumiy konstantalar
Ranglar, shriftlar, o'lchamlar
"""
import os

# ─── YO'LLAR ──────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR  = os.path.join(BASE_DIR, 'assets')
CARDS_DIR   = os.path.join(ASSETS_DIR, 'cards')
FONTS_DIR   = os.path.join(ASSETS_DIR, 'fonts')
SOUNDS_DIR  = os.path.join(ASSETS_DIR, 'sounds')
MUSIC_DIR   = os.path.join(ASSETS_DIR, 'music')
IMAGES_DIR  = os.path.join(ASSETS_DIR, 'images')
LOCALES_DIR = os.path.join(BASE_DIR, 'locales')

# ─── RANGLAR (Kivy format: 0.0–1.0) ──────────────────────────────────────────
def hex_to_kivy(hex_color: str):
    """#RRGGBB → (r, g, b, 1.0) Kivy formatiga o'tkazish"""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (r / 255, g / 255, b / 255, 1.0)


COLORS = {
    # Asosiy fonlar
    'background':       hex_to_kivy('#0D1B12'),
    'surface':          hex_to_kivy('#1A2E1F'),
    'surface_alt':      hex_to_kivy('#243528'),
    'table':            hex_to_kivy('#0D4F2A'),

    # Oltin aksentlar
    'gold':             hex_to_kivy('#D4AF37'),
    'gold_light':       hex_to_kivy('#F5D060'),
    'gold_dark':        hex_to_kivy('#A07820'),

    # Matn
    'text_primary':     hex_to_kivy('#F5F0E8'),
    'text_secondary':   hex_to_kivy('#A89060'),
    'text_muted':       hex_to_kivy('#5A6B5E'),

    # Holat
    'success':          hex_to_kivy('#4CAF50'),
    'danger':           hex_to_kivy('#F44336'),
    'warning':          hex_to_kivy('#FFC107'),
    'info':             hex_to_kivy('#2196F3'),

    # Mastlar
    'red_suit':         hex_to_kivy('#C0392B'),
    'black_suit':       hex_to_kivy('#1A1A2E'),

    # Karta
    'card_face':        hex_to_kivy('#FAF6EE'),
    'card_back':        hex_to_kivy('#1A2E1F'),
    'card_border':      hex_to_kivy('#D4AF37'),
    'card_shadow':      (0, 0, 0, 0.4),

    # UI elementlar
    'overlay':          (0, 0, 0, 0.6),
    'divider':          hex_to_kivy('#2A3E2F'),
}

# ─── SHRIFT O'LCHAMLARI ───────────────────────────────────────────────────────
FONT_SIZES = {
    'display':  36,
    'h1':       28,
    'h2':       22,
    'h3':       18,
    'body':     15,
    'small':    12,
    'tiny':     10,
}

# ─── KARTA O'LCHAMLARI ────────────────────────────────────────────────────────
CARD_W  = 70    # Standart kenglik (dp)
CARD_H  = 100   # Standart balandlik (dp)
CARD_W_SEL = 77   # Tanlanganda
CARD_H_SEL = 110  # Tanlanganda
CARD_RADIUS = 8   # Burchak radiusi

# ─── ANIMATSIYA VAQTLARI ──────────────────────────────────────────────────────
ANIM = {
    'card_deal':    0.3,
    'card_place':   0.25,
    'card_take':    0.4,
    'card_select':  0.15,
    'card_cover':   0.3,
    'screen_slide': 0.4,
    'screen_fade':  0.5,
    'btn_press':    0.08,
}

# ─── O'YIN SOZLAMALARI ────────────────────────────────────────────────────────
HAND_SIZE       = 6     # Maksimal qo'ldagi kartalar
DECK_SIZE       = 36    # Umumiy kartalar soni
AI_THINK_DELAY  = 1.2   # AI harakatidan oldin kutish (soniya)

# ─── SUIT VA QIYMATLAR ────────────────────────────────────────────────────────
SUITS  = ['spades', 'hearts', 'diamonds', 'clubs']
VALUES = [6, 7, 8, 9, 10, 11, 12, 13, 14]      # 11=J, 12=Q, 13=K, 14=A
VALUE_NAMES = {11: 'J', 12: 'Q', 13: 'K', 14: 'A'}

SUIT_SYMBOLS = {
    'spades':   '♠',
    'hearts':   '♥',
    'diamonds': '♦',
    'clubs':    '♣',
}

SUIT_COLORS = {
    'spades':   'black',
    'hearts':   'red',
    'diamonds': 'red',
    'clubs':    'black',
}
