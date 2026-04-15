from __future__ import annotations

import aiosqlite
from config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                first_name  TEXT,
                joined_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sections (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                key         TEXT UNIQUE NOT NULL,
                name        TEXT NOT NULL,
                emoji       TEXT DEFAULT '📁',
                description TEXT,
                is_active   INTEGER DEFAULT 1
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS content (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                section_key TEXT NOT NULL,
                type        TEXT NOT NULL,
                file_id     TEXT,
                text        TEXT,
                caption     TEXT,
                added_by    INTEGER,
                added_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (section_key) REFERENCES sections(key)
            )
        """)
        await db.commit()
        await _seed_sections(db)


async def _seed_sections(db):
    sections = [
        ("scientific",  "المنهج العلمي",        "🔬", "مواد ومحتوى المنهج العلمي"),
        ("literary",    "المنهج الأدبي",         "📖", "مواد ومحتوى المنهج الأدبي"),
        ("exams",       "الامتحانات والأسئلة",    "📝", "أسئلة وامتحانات سابقة"),
        ("summaries",   "الملخصات والملازم",      "📋", "ملخصات وملازم لجميع المواد"),
        ("tips",        "نصائح دراسية",           "💡", "نصائح وإرشادات للدراسة"),
        ("youtube",     "فيديوهات يوتيوب",        "▶️", "شروحات يوتيوب"),
        ("schedule",    "جداول المراجعة",         "🗓", "جداول ومخططات المراجعة"),
        ("quran",       "من القرآن",              "🕌", "آيات وأدعية تخص الطالب"),
        ("problems",    "حلال المشاكل",           "🛠", "حلول للمشاكل الدراسية"),
    ]
    for key, name, emoji, desc in sections:
        await db.execute("""
            INSERT OR IGNORE INTO sections (key, name, emoji, description)
            VALUES (?, ?, ?, ?)
        """, (key, name, emoji, desc))
    await db.commit()


# ── Users ──────────────────────────────────────────────

async def add_user(user_id: int, username: str, first_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
        """, (user_id, username, first_name))
        await db.commit()


async def get_users_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            row = await cur.fetchone()
            return row[0] if row else 0


async def get_all_user_ids() -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cur:
            rows = await cur.fetchall()
            return [r[0] for r in rows]


# ── Sections ────────────────────────────────────────────

async def get_all_sections() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM sections WHERE is_active=1 ORDER BY id"
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_section(key: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM sections WHERE key=?", (key,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


# ── Content ─────────────────────────────────────────────

async def add_content(section_key: str, content_type: str,
                      file_id: str | None, text: str | None,
                      caption: str | None, added_by: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            INSERT INTO content (section_key, type, file_id, text, caption, added_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (section_key, content_type, file_id, text, caption, added_by))
        await db.commit()
        return cur.lastrowid


async def get_section_content(section_key: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM content WHERE section_key=? ORDER BY added_at DESC
        """, (section_key,)) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def delete_content(content_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM content WHERE id=?", (content_id,))
        await db.commit()
        return cur.rowcount > 0


async def get_content_count(section_key: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM content WHERE section_key=?", (section_key,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0
