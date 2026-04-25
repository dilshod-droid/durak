"""
managers/stats_manager.py — Statistika boshqaruvchisi
SQLite orqali o'yin statistikasini saqlaydi.

Tuzatishlar:
  - __del__ o'rniga aniq close() metodi (xavfsiz)
  - Barcha DB operatsiyalari try/except bilan o'ralgan
  - logging qo'shildi
"""
import os
import sqlite3
import logging
from datetime import datetime
from core.constants import BASE_DIR

logger = logging.getLogger(__name__)


DB_FILE = os.path.join(BASE_DIR, 'data', 'stats.db')

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS stats (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    date          TEXT    NOT NULL,
    difficulty    TEXT    NOT NULL,
    mode          TEXT    NOT NULL,
    result        TEXT    NOT NULL,   -- 'win' | 'loss'
    turns         INTEGER DEFAULT 0,
    cards_taken   INTEGER DEFAULT 0,
    duration_sec  INTEGER DEFAULT 0
);
"""


class StatsManager:
    """SQLite asosida o'yin statistikasini saqlash va o'qish."""

    def __init__(self):
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        self._conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        try:
            self._conn.execute(CREATE_TABLE_SQL)
            self._conn.commit()
        except sqlite3.Error as e:
            logger.error(f"[Stats] Jadval yaratishda xato: {e}")

    # ─── Yozish ───────────────────────────────────────────────────────────────
    def record_game(
        self,
        result:       str,
        difficulty:   str,
        mode:         str,
        turns:        int,
        cards_taken:  int,
        duration_sec: int
    ):
        """O'yin natijasini bazaga yozish"""
        sql = """
        INSERT INTO stats (date, difficulty, mode, result, turns, cards_taken, duration_sec)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            self._conn.execute(sql, (now, difficulty, mode, result, turns, cards_taken, duration_sec))
            self._conn.commit()
            logger.debug(f"[Stats] O'yin yozildi: {result}, {difficulty}, {turns} tur")
        except sqlite3.Error as e:
            logger.error(f"[Stats] Yozishda xato: {e}")

    # ─── O'qish ───────────────────────────────────────────────────────────────
    def get_summary(self) -> dict:
        """Umumiy statistika xulosasi"""
        cur = self._conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN result='win'  THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN result='loss' THEN 1 ELSE 0 END) as losses,
                MIN(CASE WHEN result='win' THEN duration_sec END) as best_time,
                AVG(turns) as avg_turns
            FROM stats
        """)
        row = cur.fetchone()
        if not row or row[0] == 0:
            return {
                'total': 0, 'wins': 0, 'losses': 0,
                'win_rate': 0.0, 'best_time': 0, 'avg_turns': 0
            }

        total  = row[0] or 0
        wins   = row[1] or 0
        losses = row[2] or 0
        best   = row[3] or 0
        avg_t  = row[4] or 0

        return {
            'total':     total,
            'wins':      wins,
            'losses':    losses,
            'win_rate':  round(wins / total * 100, 1) if total else 0.0,
            'best_time': int(best),
            'avg_turns': int(avg_t),
        }

    def get_recent_games(self, limit: int = 10) -> list:
        """Oxirgi o'yinlar"""
        cur = self._conn.execute(
            "SELECT date, difficulty, result, turns, duration_sec FROM stats "
            "ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return cur.fetchall()

    def format_time(self, seconds: int) -> str:
        """Sekundlarni MM:SS formatga o'tkazish"""
        m, s = divmod(seconds, 60)
        return f"{m}:{s:02d}"

    # ─── Tozalash ─────────────────────────────────────────────────────────────
    def reset(self):
        """Barcha statistikani o'chirish"""
        try:
            self._conn.execute("DELETE FROM stats")
            self._conn.commit()
            logger.info("[Stats] Barcha statistika o'chirildi")
        except sqlite3.Error as e:
            logger.error(f"[Stats] Tozalashda xato: {e}")

    def close(self):
        """
        DB ulanishini yopish.
        __del__ o'rniga aniq close() ishlating — xavfsizroq.
        """
        try:
            if self._conn:
                self._conn.close()
                self._conn = None
                logger.debug("[Stats] DB ulanishi yopildi")
        except Exception as e:
            logger.warning(f"[Stats] DB yopishda xato: {e}")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
