"""
tools/generate_assets.py - Barcha assetlarni yaratish
Karta PNG rasmlari, audio WAV fayllar, shriftlar yuklab olish.

Ishlatish:
    python tools/generate_assets.py
"""
import os
import sys
import math
import wave
import struct
import array
import urllib.request
import urllib.error

# Windows konsoli uchun UTF-8 kodlash
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ─── Yo'llar ──────────────────────────────────────────────────────────────────
ROOT_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(ROOT_DIR, 'assets')
CARDS_DIR  = os.path.join(ASSETS_DIR, 'cards')
FONTS_DIR  = os.path.join(ASSETS_DIR, 'fonts')
SOUNDS_DIR = os.path.join(ASSETS_DIR, 'sounds')
MUSIC_DIR  = os.path.join(ASSETS_DIR, 'music')
IMAGES_DIR = os.path.join(ASSETS_DIR, 'images')
DATA_DIR   = os.path.join(ROOT_DIR,  'data')

def ensure_dirs():
    for d in [CARDS_DIR, FONTS_DIR, SOUNDS_DIR, MUSIC_DIR, IMAGES_DIR, DATA_DIR]:
        os.makedirs(d, exist_ok=True)


# ═════════════════════════════════════════════════════════════════════════════
# 1. PILLOW O'RNATISH VA TEKSHIRISH
# ═════════════════════════════════════════════════════════════════════════════
def ensure_pillow():
    try:
        from PIL import Image, ImageDraw, ImageFont
        return True
    except ImportError:
        print("[Assets] Pillow o'rnatilmoqda...")
        import subprocess
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install',
                                   'Pillow', '--quiet'])
            return True
        except Exception as e:
            print(f"[Assets] Pillow o'rnatib bo'lmadi: {e}")
            return False


# ═════════════════════════════════════════════════════════════════════════════
# 2. KARTA RASMLARI GENERATSIYA
# ═════════════════════════════════════════════════════════════════════════════
CARD_W  = 210   # px (3x scale for quality)
CARD_H  = 300
RADIUS  = 18

SUITS  = ['spades', 'hearts', 'diamonds', 'clubs']
VALUES = [6, 7, 8, 9, 10, 11, 12, 13, 14]
VALUE_NAMES = {11: 'J', 12: 'Q', 13: 'K', 14: 'A'}

SUIT_SYMBOLS = {
    'spades':   '♠',
    'hearts':   '♥',
    'diamonds': '♦',
    'clubs':    '♣',
}

# Ranglar (PIL format)
C_FACE     = (250, 246, 238)     # Krema oq
C_GOLD     = (212, 175,  55)     # Oltin
C_RED      = (192,  57,  43)     # Qizil suit
C_BLACK    = ( 26,  26,  46)     # Qora suit
C_BACK_BG  = ( 26,  46,  31)     # To'q yashil
C_BACK_PAT = ( 40,  72,  52)     # Naqsh rangi


def get_suit_color(suit: str):
    return C_RED if suit in ('hearts', 'diamonds') else C_BLACK


def draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    """Yumaloq burchakli to'rtburchak chizish"""
    from PIL import ImageDraw as PID
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def draw_suit_symbol(draw, cx, cy, suit, size, color):
    """Mast belgisini chizish (♠♥♦♣) poligon orqali"""
    if suit == 'hearts':
        _draw_heart(draw, cx, cy, size, color)
    elif suit == 'diamonds':
        _draw_diamond(draw, cx, cy, size, color)
    elif suit == 'spades':
        _draw_spade(draw, cx, cy, size, color)
    elif suit == 'clubs':
        _draw_club(draw, cx, cy, size, color)


def _draw_heart(draw, cx, cy, size, color):
    r = size // 2
    # Chap doira
    draw.ellipse((cx - r, cy - r // 2, cx, cy + r // 2), fill=color)
    # O'ng doira
    draw.ellipse((cx, cy - r // 2, cx + r, cy + r // 2), fill=color)
    # Pastki uchburchak
    poly = [
        (cx - r, cy),
        (cx + r, cy),
        (cx, cy + r),
    ]
    draw.polygon(poly, fill=color)


def _draw_diamond(draw, cx, cy, size, color):
    h = int(size * 0.65)
    w = int(size * 0.5)
    pts = [
        (cx,     cy - h),
        (cx + w, cy),
        (cx,     cy + h),
        (cx - w, cy),
    ]
    draw.polygon(pts, fill=color)


def _draw_spade(draw, cx, cy, size, color):
    r  = size // 2
    # Yuqori doiralar
    draw.ellipse((cx - r, cy - r, cx, cy), fill=color)
    draw.ellipse((cx, cy - r, cx + r, cy), fill=color)
    # Markaziy uchburchak (tepaga)
    tip_y = int(cy - r * 1.3)
    poly = [
        (cx,     tip_y),
        (cx - r, cy),
        (cx + r, cy),
    ]
    draw.polygon(poly, fill=color)
    # Pastki poya
    stem_w = max(4, size // 8)
    stem_h = int(size * 0.3)
    draw.rectangle((cx - stem_w, cy, cx + stem_w, cy + stem_h), fill=color)
    draw.ellipse((cx - stem_w * 3, cy + stem_h - 2,
                   cx + stem_w * 3, cy + stem_h + stem_w * 2), fill=color)


def _draw_club(draw, cx, cy, size, color):
    r = int(size * 0.33)
    # Uch doira
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)              # Yuqori
    draw.ellipse((cx - r * 2, cy, cx, cy + r * 2), fill=color)              # Chap
    draw.ellipse((cx, cy, cx + r * 2, cy + r * 2), fill=color)              # O'ng
    # Poya
    stem_w = max(3, size // 10)
    draw.rectangle((cx - stem_w, cy + r, cx + stem_w, cy + r * 2 + stem_w), fill=color)
    draw.ellipse((cx - r, cy + r * 2,
                   cx + r, cy + r * 2 + stem_w * 3), fill=color)


def get_font(size: int, bold: bool = False):
    """Shrift olish — Cinzel bo'lmasa sistem shrift"""
    from PIL import ImageFont
    # Cinzel fonti
    cinzel_path = os.path.join(FONTS_DIR,
                                'Cinzel-Bold.ttf' if bold else 'Cinzel-Regular.ttf')
    if os.path.exists(cinzel_path):
        try:
            return ImageFont.truetype(cinzel_path, size)
        except Exception:
            pass

    # Windows tizim shriftlari
    win_fonts = [
        'C:/Windows/Fonts/georgiai.ttf' if not bold else 'C:/Windows/Fonts/georgiab.ttf',
        'C:/Windows/Fonts/timesnewroman.ttf',
        'C:/Windows/Fonts/arial.ttf',
    ]
    for path in win_fonts:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue

    return ImageFont.load_default()


def draw_card_face(suit: str, value: int) -> 'PIL.Image.Image':
    """Karta yuzini chizish"""
    from PIL import Image, ImageDraw

    img  = Image.new('RGBA', (CARD_W, CARD_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    suit_color = get_suit_color(suit)
    val_str    = VALUE_NAMES.get(value, str(value))

    # ─── Fon ──────────────────────────────────────────────────────────────
    draw.rounded_rectangle([(0, 0), (CARD_W - 1, CARD_H - 1)],
                            radius=RADIUS, fill=C_FACE)

    # ─── Oltin chegara ────────────────────────────────────────────────────
    draw.rounded_rectangle([(2, 2), (CARD_W - 3, CARD_H - 3)],
                            radius=RADIUS - 2, outline=C_GOLD, width=2)

    # ─── Yuqori chap: qiymat + mast ───────────────────────────────────────
    font_val  = get_font(32, bold=True)
    font_suit = get_font(24, bold=False)

    # Qiymat
    draw.text((12, 8),  val_str, font=font_val, fill=suit_color)
    # Mast belgisi (chizilgan)
    draw_suit_symbol(draw, 20, 50, suit, 24, suit_color)

    # ─── Markaziy katta mast belgisi ──────────────────────────────────────
    draw_suit_symbol(draw, CARD_W // 2, CARD_H // 2, suit, 72, suit_color)

    # ─── Pastki o'ng: teskari ─────────────────────────────────────────────
    # Yuqori chap matnni 180° aylantirib pastga qo'yamiz
    from PIL import Image as PILImage
    corner_img = Image.new('RGBA', (50, 70), (0, 0, 0, 0))
    cd = ImageDraw.Draw(corner_img)
    cd.text((5, 4), val_str, font=get_font(28, bold=True), fill=suit_color)
    draw_suit_symbol(cd, 14, 42, suit, 20, suit_color)

    corner_rot = corner_img.rotate(180)
    img.paste(corner_rot, (CARD_W - 55, CARD_H - 74), corner_rot)

    return img


def draw_card_back() -> 'PIL.Image.Image':
    """Karta orqa tomoni — dark green + oltin naqsh"""
    from PIL import Image, ImageDraw

    img  = Image.new('RGBA', (CARD_W, CARD_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Asosiy fon
    draw.rounded_rectangle([(0, 0), (CARD_W - 1, CARD_H - 1)],
                            radius=RADIUS, fill=C_BACK_BG)

    # Oltin chegara
    draw.rounded_rectangle([(2, 2), (CARD_W - 3, CARD_H - 3)],
                            radius=RADIUS - 2, outline=C_GOLD, width=2)

    # Ko'ndalang oltin naqsh
    step = 20
    for i in range(-CARD_H, CARD_W + CARD_H, step):
        x1, y1 = i, 0
        x2, y2 = i + CARD_H, CARD_H
        draw.line([(x1, y1), (x2, y2)], fill=(*C_GOLD, 30), width=1)

    for i in range(CARD_W + CARD_H, -CARD_H, -step):
        x1, y1 = i, 0
        x2, y2 = i - CARD_H, CARD_H
        draw.line([(x1, y1), (x2, y2)], fill=(*C_GOLD, 30), width=1)

    # Markaziy doira
    cx, cy = CARD_W // 2, CARD_H // 2
    draw.ellipse([(cx - 40, cy - 55), (cx + 40, cy + 55)],
                  outline=(*C_GOLD, 180), width=2)

    # Ichki mast belgilari
    for angle, suit in [(45, 'spades'), (135, 'hearts'),
                         (225, 'diamonds'), (315, 'clubs')]:
        rad = math.radians(angle)
        sx  = int(cx + 22 * math.cos(rad))
        sy  = int(cy + 30 * math.sin(rad))
        draw_suit_symbol(draw, sx, sy, suit, 14, (*C_GOLD, 120))

    # Markaziy D harfi
    try:
        font = get_font(36, bold=True)
        draw.text((cx, cy), 'D', font=font, fill=(*C_GOLD, 180), anchor='mm')
    except Exception:
        pass

    return img


def draw_empty_slot() -> 'PIL.Image.Image':
    """Bo'sh stol sloti"""
    from PIL import Image, ImageDraw
    img  = Image.new('RGBA', (CARD_W, CARD_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(0, 0), (CARD_W - 1, CARD_H - 1)],
                            radius=RADIUS, fill=(26, 78, 42, 80))
    draw.rounded_rectangle([(3, 3), (CARD_W - 4, CARD_H - 4)],
                            radius=RADIUS - 3, outline=(*C_GOLD, 80), width=2)
    return img


def generate_card_images():
    """Barcha 36 ta karta + yopiq + bo'sh slot rasmlarini yaratish"""
    if not ensure_pillow():
        print("[Cards] Pillow yo'q, kartalar yaratilmaydi")
        return

    count = 0
    for suit in SUITS:
        for value in VALUES:
            path = os.path.join(CARDS_DIR, f"{suit}_{value}.png")
            if not os.path.exists(path):
                img = draw_card_face(suit, value)
                img.save(path, 'PNG')
                count += 1

    # Yopiq karta
    back_path = os.path.join(CARDS_DIR, 'card_back.png')
    if not os.path.exists(back_path):
        img = draw_card_back()
        img.save(back_path, 'PNG')
        count += 1

    # Bo'sh slot
    slot_path = os.path.join(CARDS_DIR, 'empty_slot.png')
    if not os.path.exists(slot_path):
        img = draw_empty_slot()
        img.save(slot_path, 'PNG')
        count += 1

    print(f"[Cards] {count} ta karta rasmi yaratildi ✓")


# ═════════════════════════════════════════════════════════════════════════════
# 3. AUDIO WAV GENERATSIYA
# ═════════════════════════════════════════════════════════════════════════════
SAMPLE_RATE = 44100


def generate_sine(freq: float, duration: float, amplitude: float = 0.5,
                  fade_in: float = 0.05, fade_out: float = 0.1) -> list:
    """Sine to'lqin generatsiya + fade in/out"""
    n_samples = int(SAMPLE_RATE * duration)
    fade_in_n  = int(SAMPLE_RATE * fade_in)
    fade_out_n = int(SAMPLE_RATE * fade_out)
    samples = []
    for i in range(n_samples):
        t   = i / SAMPLE_RATE
        val = amplitude * math.sin(2 * math.pi * freq * t)
        # Fade
        if i < fade_in_n:
            val *= i / fade_in_n
        elif i > n_samples - fade_out_n:
            val *= (n_samples - i) / fade_out_n
        samples.append(int(val * 32767))
    return samples


def mix_samples(*sample_lists) -> list:
    """Bir necha sample-ni aralash"""
    max_len = max(len(s) for s in sample_lists)
    result  = []
    for i in range(max_len):
        val = 0
        for s in sample_lists:
            if i < len(s):
                val += s[i]
        val = max(-32767, min(32767, val))
        result.append(val)
    return result


def save_wav(path: str, samples: list, channels: int = 1):
    """Sample-larni WAV faylga saqlash"""
    with wave.open(path, 'w') as f:
        f.setnchannels(channels)
        f.setsampwidth(2)       # 16-bit
        f.setframerate(SAMPLE_RATE)
        data = struct.pack(f'<{len(samples)}h', *samples)
        f.writeframes(data)


def generate_audio_files():
    """O'yin SFX va musiqa WAV fayllarini yaratish"""
    generated = 0

    # ─── card_deal.wav — yumshoq swish ────────────────────────────────────
    path = os.path.join(SOUNDS_DIR, 'card_deal.wav')
    if not os.path.exists(path):
        s1 = generate_sine(800,  0.05, 0.3, fade_out=0.04)
        s2 = generate_sine(1200, 0.08, 0.2, fade_in=0.02, fade_out=0.05)
        save_wav(path, mix_samples(s1 + [0] * (len(s2) - len(s1)), s2))
        generated += 1

    # ─── card_place.wav — to'mtoq thud ────────────────────────────────────
    path = os.path.join(SOUNDS_DIR, 'card_place.wav')
    if not os.path.exists(path):
        s = generate_sine(200, 0.12, 0.6, fade_in=0.01, fade_out=0.08)
        s2 = generate_sine(150, 0.12, 0.3, fade_in=0.01, fade_out=0.1)
        save_wav(path, mix_samples(s, s2))
        generated += 1

    # ─── card_take.wav — kartalar olish ───────────────────────────────────
    path = os.path.join(SOUNDS_DIR, 'card_take.wav')
    if not os.path.exists(path):
        samples = []
        for i in range(4):
            s = generate_sine(600 - i * 80, 0.06, 0.35,
                              fade_in=0.01, fade_out=0.03)
            samples.extend(s + [0] * 500)
        save_wav(path, samples[:SAMPLE_RATE])
        generated += 1

    # ─── card_flip.wav — karta ag'darish ──────────────────────────────────
    path = os.path.join(SOUNDS_DIR, 'card_flip.wav')
    if not os.path.exists(path):
        s = generate_sine(1500, 0.07, 0.25, fade_out=0.05)
        save_wav(path, s)
        generated += 1

    # ─── win.wav — g'alaba akkord ─────────────────────────────────────────
    path = os.path.join(SOUNDS_DIR, 'win.wav')
    if not os.path.exists(path):
        # Do-Mi-Sol major chord arp
        notes = [261, 329, 392, 523]   # C4, E4, G4, C5
        all_s = []
        for i, freq in enumerate(notes):
            s = generate_sine(freq, 0.3, 0.5, fade_out=0.15)
            # Delay
            s = [0] * int(SAMPLE_RATE * 0.08 * i) + s
            all_s.append(s)
        # Barcha notalar uzunligini tenglashtirish
        max_l = max(len(s) for s in all_s)
        for i in range(len(all_s)):
            all_s[i] = all_s[i] + [0] * (max_l - len(all_s[i]))
        save_wav(path, mix_samples(*all_s))
        generated += 1

    # ─── lose.wav — yutqizuv ──────────────────────────────────────────────
    path = os.path.join(SOUNDS_DIR, 'lose.wav')
    if not os.path.exists(path):
        notes = [392, 349, 330, 294]   # G4, F4, E4, D4 (tushuvchi)
        all_s = []
        for i, freq in enumerate(notes):
            s = generate_sine(freq, 0.25, 0.4, fade_out=0.1)
            s = [0] * int(SAMPLE_RATE * 0.1 * i) + s
            all_s.append(s)
        max_l = max(len(s) for s in all_s)
        for i in range(len(all_s)):
            all_s[i] = all_s[i] + [0] * (max_l - len(all_s[i]))
        save_wav(path, mix_samples(*all_s))
        generated += 1

    # ─── button_click.wav — tugma ─────────────────────────────────────────
    path = os.path.join(SOUNDS_DIR, 'button_click.wav')
    if not os.path.exists(path):
        s = generate_sine(1000, 0.05, 0.4, fade_out=0.03)
        save_wav(path, s)
        generated += 1

    # ─── trump_reveal.wav — kozir reveal ──────────────────────────────────
    path = os.path.join(SOUNDS_DIR, 'trump_reveal.wav')
    if not os.path.exists(path):
        freqs = [392, 494, 587, 784]   # G4 → G5 (dramatik ko'tarilish)
        all_s = []
        for i, freq in enumerate(freqs):
            s = generate_sine(freq, 0.2, 0.45, fade_out=0.08)
            s = [0] * int(SAMPLE_RATE * 0.07 * i) + s
            all_s.append(s)
        max_l = max(len(s) for s in all_s)
        for i in range(len(all_s)):
            all_s[i] = all_s[i] + [0] * (max_l - len(all_s[i]))
        save_wav(path, mix_samples(*all_s))
        generated += 1

    # ─── invalid.wav — noto'g'ri harakat ──────────────────────────────────
    path = os.path.join(SOUNDS_DIR, 'invalid.wav')
    if not os.path.exists(path):
        s1 = generate_sine(200, 0.15, 0.5, fade_out=0.1)
        s2 = generate_sine(180, 0.15, 0.4, fade_out=0.1)
        save_wav(path, mix_samples(s1, s2))
        generated += 1

    # ─── menu_theme.wav — bosh menyu (lo-fi loop) ─────────────────────────
    path = os.path.join(MUSIC_DIR, 'menu_theme.wav')
    if not os.path.exists(path):
        duration = 4.0   # 4 soniyalik loop
        melody_notes = [
            (329, 0.0, 0.5),   # E4
            (392, 0.5, 0.5),   # G4
            (440, 1.0, 0.5),   # A4
            (494, 1.5, 0.5),   # B4
            (440, 2.0, 0.5),   # A4
            (392, 2.5, 0.5),   # G4
            (349, 3.0, 0.5),   # F4
            (329, 3.5, 0.5),   # E4
        ]
        total_samples = int(SAMPLE_RATE * duration)
        all_s = [0] * total_samples
        for freq, start, dur in melody_notes:
            s   = generate_sine(freq, dur, 0.3, fade_in=0.05, fade_out=0.1)
            idx = int(SAMPLE_RATE * start)
            for i, val in enumerate(s):
                if idx + i < total_samples:
                    all_s[idx + i] = max(-32767, min(32767, all_s[idx + i] + val))
        save_wav(path, all_s)
        generated += 1

    # ─── game_theme.wav — o'yin musiqasi ──────────────────────────────────
    path = os.path.join(MUSIC_DIR, 'game_theme.wav')
    if not os.path.exists(path):
        duration = 6.0
        notes = [
            (261, 0.0, 0.4), (294, 0.4, 0.4), (329, 0.8, 0.4),
            (349, 1.2, 0.4), (329, 1.6, 0.4), (294, 2.0, 0.8),
            (261, 2.8, 0.4), (246, 3.2, 0.4), (261, 3.6, 0.4),
            (294, 4.0, 0.4), (329, 4.4, 0.4), (349, 4.8, 0.4),
            (329, 5.2, 0.4), (261, 5.6, 0.4),
        ]
        total_s = int(SAMPLE_RATE * duration)
        result  = [0] * total_s
        for freq, start, dur in notes:
            s   = generate_sine(freq, dur, 0.25, fade_in=0.04, fade_out=0.1)
            idx = int(SAMPLE_RATE * start)
            for i, val in enumerate(s):
                if idx + i < total_s:
                    result[idx + i] = max(-32767, min(32767, result[idx + i] + val))
        save_wav(path, result)
        generated += 1

    print(f"[Audio] {generated} ta audio fayl yaratildi ✓")


# ═════════════════════════════════════════════════════════════════════════════
# 4. SHRIFTLAR YUKLAB OLISH
# ═════════════════════════════════════════════════════════════════════════════
FONT_URLS = {
    'Cinzel-Regular.ttf':
        'https://github.com/google/fonts/raw/main/ofl/cinzel/static/Cinzel-Regular.ttf',
    'Cinzel-Bold.ttf':
        'https://github.com/google/fonts/raw/main/ofl/cinzel/static/Cinzel-Bold.ttf',
    'Raleway-Regular.ttf':
        'https://github.com/google/fonts/raw/main/ofl/raleway/static/Raleway-Regular.ttf',
    'Raleway-Bold.ttf':
        'https://github.com/google/fonts/raw/main/ofl/raleway/static/Raleway-Bold.ttf',
}


def download_fonts():
    """Google Fonts dan shriftlarni yuklab olish (SSL bypass bilan)"""
    import ssl
    # Windows da SSL sertifikat muammosi uchun
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode    = ssl.CERT_NONE

    downloaded = 0
    for filename, url in FONT_URLS.items():
        path = os.path.join(FONTS_DIR, filename)
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            print(f"  [Font] {filename} - allaqachon mavjud")
            continue
        try:
            print(f"  [Font] {filename} yuklanmoqda...")
            req = urllib.request.Request(
                url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0)'}
            )
            with urllib.request.urlopen(req, timeout=20, context=ssl_ctx) as resp:
                data = resp.read()
            if len(data) < 1000:
                raise ValueError(f"Fayl juda kichik: {len(data)} bayt")
            with open(path, 'wb') as f:
                f.write(data)
            print(f"  [Font] {filename} yuklandi ({len(data) // 1024} KB)")
            downloaded += 1
        except Exception as e:
            print(f"  [Font] {filename} yuklanmadi: {e}")

    if downloaded > 0:
        print(f"[Fonts] {downloaded} ta shrift yuklab olindi")
    else:
        print("[Fonts] Internet yo'q yoki yuklanmadi — tizim shriftlari ishlatiladi")


# ═════════════════════════════════════════════════════════════════════════════
# 5. LOGO RASMLAR
# ═════════════════════════════════════════════════════════════════════════════
def generate_logo():
    """App logo yarish (splash va icon uchun)"""
    if not ensure_pillow():
        return

    path = os.path.join(IMAGES_DIR, 'logo.png')
    if os.path.exists(path):
        return

    from PIL import Image, ImageDraw

    SIZE = (512, 512)
    img  = Image.new('RGBA', SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = SIZE[0] // 2, SIZE[1] // 2
    R      = 220

    # Tashqi doira — to'q yashil
    draw.ellipse([(cx - R, cy - R), (cx + R, cy + R)],
                  fill=(13, 27, 18), outline=C_GOLD, width=6)

    # Ichki doira — oltin chegara
    r2 = 200
    draw.ellipse([(cx - r2, cy - r2), (cx + r2, cy + r2)],
                  outline=(*C_GOLD, 180), width=3)

    # 4 ta karta siluet (chapdan yuqori soat yo'nalishida)
    suit_positions = [
        ('spades',   cx - 60, cy - 80),
        ('hearts',   cx + 60, cy - 80),
        ('diamonds', cx + 60, cy + 60),
        ('clubs',    cx - 60, cy + 60),
    ]
    for suit, sx, sy in suit_positions:
        color = C_RED if suit in ('hearts', 'diamonds') else C_FACE
        draw_suit_symbol(draw, sx, sy, suit, 55, color)

    # Markazda 'D'
    font = get_font(90, bold=True)
    try:
        draw.text((cx, cy), 'D', font=font,
                   fill=C_GOLD, anchor='mm')
    except Exception:
        draw.text((cx - 30, cy - 45), 'D', font=font, fill=C_GOLD)

    img.save(path, 'PNG')
    print("[Logo] logo.png yaratildi ✓")


# ═════════════════════════════════════════════════════════════════════════════
# ASOSIY KIRISH NUQTASI
# ═════════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 55)
    print("  DURAK - Asset Generator v1.0")
    print("=" * 55)

    ensure_dirs()

    print("\n[1/4] Shriftlar yuklanmoqda...")
    download_fonts()

    print("\n[2/4] Karta rasmlari yaratilmoqda...")
    generate_card_images()

    print("\n[3/4] Audio fayllar yaratilmoqda...")
    generate_audio_files()

    print("\n[4/4] Logo yaratilmoqda...")
    generate_logo()

    print("\n" + "=" * 55)
    print("  [OK] Barcha assetlar tayyor!")
    print("  >>> Ilovani ishga tushirish: python main.py")
    print("=" * 55)


if __name__ == '__main__':
    # tools/ papkasidan ham, loyiha ildizidan ham ishlatish mumkin
    os.chdir(ROOT_DIR)
    main()
