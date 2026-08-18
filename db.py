import sqlite3
from pathlib import Path
from datetime import datetime


# =========================================================
# BeatMind Database
# =========================================================

DB_PATH = Path("data") / "beatmind.db"

DB_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)


# =========================================================
# Connection
# =========================================================

def get_connection():

    connection = sqlite3.connect(
        DB_PATH,
        check_same_thread=False,
    )

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# Initialize Database
# =========================================================

def init_db():

    with get_connection() as connection:

        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT DEFAULT '',
                first_name TEXT DEFAULT '',
                account_type TEXT DEFAULT 'free',
                balance INTEGER DEFAULT 0,
                credit INTEGER DEFAULT 0,
                free_lyrics_claimed INTEGER DEFAULT 0,
                free_beat_claimed INTEGER DEFAULT 0,
                created_at TEXT,
                last_activity TEXT
            );


            CREATE TABLE IF NOT EXISTS lyrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                style TEXT DEFAULT '',
                mood TEXT DEFAULT '',
                topic TEXT DEFAULT '',
                flow TEXT DEFAULT '',
                lyrics TEXT DEFAULT '',
                created_at TEXT
            );


            CREATE TABLE IF NOT EXISTS beats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                producer TEXT DEFAULT '',
                genre TEXT DEFAULT '',
                mood TEXT DEFAULT '',
                bpm INTEGER DEFAULT 0,
                key TEXT DEFAULT '',
                duration TEXT DEFAULT '',
                price INTEGER DEFAULT 0,
                is_free INTEGER DEFAULT 0,
                preview_file TEXT DEFAULT '',
                file_path TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                created_at TEXT
            );


            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER NOT NULL,
                beat_id INTEGER NOT NULL,
                UNIQUE(user_id, beat_id)
            );


            CREATE TABLE IF NOT EXISTS rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                reward_type TEXT NOT NULL,
                item_id INTEGER DEFAULT 0,
                claimed_at TEXT
            );
            """
        )

        connection.commit()


# =========================================================
# Users
# =========================================================

def ensure_user(
    telegram_id,
    username="",
    first_name="",
):

    now = datetime.utcnow().isoformat()

    with get_connection() as connection:

        connection.execute(
            """
            INSERT INTO users (
                telegram_id,
                username,
                first_name,
                created_at,
                last_activity
            )

            VALUES (?, ?, ?, ?, ?)

            ON CONFLICT(telegram_id)

            DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_activity = excluded.last_activity
            """,
            (
                telegram_id,
                username,
                first_name,
                now,
                now,
            ),
        )

        connection.commit()


def get_user(telegram_id):

    with get_connection() as connection:

        row = connection.execute(
            """
            SELECT *
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,),
        ).fetchone()

        if row:

            return dict(row)

        return None


# =========================================================
# Free Rewards
# =========================================================

def get_free_status(telegram_id):

    user = get_user(
        telegram_id
    )

    if not user:

        return {
            "free_lyrics_claimed": False,
            "free_beat_claimed": False,
        }

    return {
        "free_lyrics_claimed": bool(
            user["free_lyrics_claimed"]
        ),

        "free_beat_claimed": bool(
            user["free_beat_claimed"]
        ),
    }


def claim_reward(
    telegram_id,
    reward_type,
    item_id=0,
):

    now = datetime.utcnow().isoformat()

    with get_connection() as connection:

        if reward_type == "beat":

            connection.execute(
                """
                UPDATE users

                SET free_beat_claimed = 1

                WHERE telegram_id = ?
                """,
                (telegram_id,),
            )

        elif reward_type == "lyrics":

            connection.execute(
                """
                UPDATE users

                SET free_lyrics_claimed = 1

                WHERE telegram_id = ?
                """,
                (telegram_id,),
            )


        connection.execute(
            """
            INSERT INTO rewards (
                user_id,
                reward_type,
                item_id,
                claimed_at
            )

            VALUES (?, ?, ?, ?)
            """,
            (
                telegram_id,
                reward_type,
                item_id,
                now,
            ),
        )

        connection.commit()


# =========================================================
# Lyrics
# =========================================================

def save_lyric(
    telegram_id,
    style,
    mood,
    topic,
    flow,
    lyrics,
):

    now = datetime.utcnow().isoformat()

    with get_connection() as connection:

        connection.execute(
            """
            INSERT INTO lyrics (
                user_id,
                style,
                mood,
                topic,
                flow,
                lyrics,
                created_at
            )

            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                telegram_id,
                style,
                mood,
                topic,
                flow,
                lyrics,
                now,
            ),
        )


        user = connection.execute(
            """
            SELECT free_lyrics_claimed
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,),
        ).fetchone()


        if (
            user
            and not user["free_lyrics_claimed"]
        ):

            connection.execute(
                """
                UPDATE users

                SET free_lyrics_claimed = 1

                WHERE telegram_id = ?
                """,
                (telegram_id,),
            )


        connection.commit()


def get_lyrics(telegram_id):

    with get_connection() as connection:

        rows = connection.execute(
            """
            SELECT *
            FROM lyrics

            WHERE user_id = ?

            ORDER BY id DESC
            """,
            (telegram_id,),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]


# =========================================================
# Beats
# =========================================================

def list_beats():

    with get_connection() as connection:

        rows = connection.execute(
            """
            SELECT *
            FROM beats

            WHERE is_active = 1

            ORDER BY id DESC
            """
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]


def get_beat(beat_id):

    with get_connection() as connection:

        row = connection.execute(
            """
            SELECT *
            FROM beats

            WHERE id = ?
            """,
            (beat_id,),
        ).fetchone()

        if row:

            return dict(row)

        return None


# =========================================================
# Add Beat
# =========================================================

def add_beat(
    title,
    producer="BeatMind",
    genre="",
    mood="",
    bpm=0,
    key="",
    duration="",
    price=0,
    is_free=0,
    preview_file="",
    file_path="",
):

    now = datetime.utcnow().isoformat()

    with get_connection() as connection:

        cursor = connection.execute(
            """
            INSERT INTO beats (
                title,
                producer,
                genre,
                mood,
                bpm,
                key,
                duration,
                price,
                is_free,
                preview_file,
                file_path,
                is_active,
                created_at
            )

            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, 1, ?
            )
            """,
            (
                title,
                producer,
                genre,
                mood,
                bpm,
                key,
                duration,
                price,
                is_free,
                preview_file,
                file_path,
                now,
            ),
        )

        connection.commit()

        return cursor.lastrowid


# =========================================================
# Update Beat
# =========================================================

def update_beat_files(
    beat_id,
    preview_file="",
    file_path="",
):

    with get_connection() as connection:

        connection.execute(
            """
            UPDATE beats

            SET
                preview_file = ?,
                file_path = ?

            WHERE id = ?
            """,
            (
                preview_file,
                file_path,
                beat_id,
            ),
        )

        connection.commit()


# =========================================================
# Favorites
# =========================================================

def add_favorite(
    user_id,
    beat_id,
):

    with get_connection() as connection:

        connection.execute(
            """
            INSERT OR IGNORE INTO favorites (
                user_id,
                beat_id
            )

            VALUES (?, ?)
            """,
            (
                user_id,
                beat_id,
            ),
        )

        connection.commit()


def remove_favorite(
    user_id,
    beat_id,
):

    with get_connection() as connection:

        connection.execute(
            """
            DELETE FROM favorites

            WHERE user_id = ?
            AND beat_id = ?
            """,
            (
                user_id,
                beat_id,
            ),
        )

        connection.commit()


def is_favorite(
    user_id,
    beat_id,
):

    with get_connection() as connection:

        row = connection.execute(
            """
            SELECT 1

            FROM favorites

            WHERE user_id = ?
            AND beat_id = ?

            LIMIT 1
            """,
            (
                user_id,
                beat_id,
            ),
        ).fetchone()

        return row is not None


def get_favorites(user_id):

    with get_connection() as connection:

        rows = connection.execute(
            """
            SELECT beats.*

            FROM beats

            INNER JOIN favorites
            ON favorites.beat_id = beats.id

            WHERE favorites.user_id = ?

            ORDER BY beats.id DESC
            """,
            (user_id,),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]


# =========================================================
# Statistics
# =========================================================

def get_stats():

    with get_connection() as connection:

        users = connection.execute(
            """
            SELECT COUNT(*)
            FROM users
            """
        ).fetchone()[0]


        lyrics = connection.execute(
            """
            SELECT COUNT(*)
            FROM lyrics
            """
        ).fetchone()[0]


        beats = connection.execute(
            """
            SELECT COUNT(*)
            FROM beats
            """
        ).fetchone()[0]


        return {
            "users": users,
            "lyrics": lyrics,
            "beats": beats,
        }


# =========================================================
# Seed Demo Beats
# =========================================================

def seed_demo_beats():

    existing = list_beats()

    if existing:

        return


    demo_beats = [

        {
            "title": "NIGHT DRIVE",
            "producer": "BeatMind",
            "genre": "Trap",
            "mood": "Dark",
            "bpm": 142,
            "key": "F# Minor",
            "duration": "2:47",
            "price": 150000,
            "is_free": 1,
        },

        {
            "title": "DARK CITY",
            "producer": "BeatMind",
            "genre": "Trap",
            "mood": "Dark",
            "bpm": 138,
            "key": "E Minor",
            "duration": "2:31",
            "price": 350000,
            "is_free": 0,
        },

        {
            "title": "AFTER MIDNIGHT",
            "producer": "BeatMind",
            "genre": "R&B",
            "mood": "Emotional",
            "bpm": 78,
            "key": "A Minor",
            "duration": "3:02",
            "price": 350000,
            "is_free": 0,
        },

        {
            "title": "SUNSET",
            "producer": "BeatMind",
            "genre": "R&B",
            "mood": "Chill",
            "bpm": 82,
            "key": "C Major",
            "duration": "2:44",
            "price": 0,
            "is_free": 1,
        },
    ]


    for beat in demo_beats:

        add_beat(
            title=beat["title"],
            producer=beat["producer"],
            genre=beat["genre"],
            mood=beat["mood"],
            bpm=beat["bpm"],
            key=beat["key"],
            duration=beat["duration"],
            price=beat["price"],
            is_free=beat["is_free"],
        )


# =========================================================
# Automatically initialize
# =========================================================

init_db()
seed_demo_beats()
