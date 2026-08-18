import os
import logging
from pathlib import Path

from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from db import (
    init_db,
    ensure_user,
    get_user,
    get_free_status,
    save_lyric,
    get_lyrics,
    list_beats,
    get_beat,
    add_favorite,
    remove_favorite,
    is_favorite,
    get_stats,
    claim_reward,
)
from ai import generate_lyrics


# =========================================================
# BeatMind v1.0
# =========================================================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN is missing. Add it to Railway Environment Variables."
    )


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger("BeatMind")


DATA_DIR = Path("data")
BEATS_DIR = DATA_DIR / "beats"

DATA_DIR.mkdir(exist_ok=True)
BEATS_DIR.mkdir(exist_ok=True)


# =========================================================
# Main Menu
# =========================================================

def main_menu():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🤖 ساخت تکست",
                    callback_data="lyrics"
                ),
                InlineKeyboardButton(
                    "🎹 Beat Store",
                    callback_data="store"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎧 پیدا کردن بیت",
                    callback_data="match"
                ),
                InlineKeyboardButton(
                    "📂 آثار من",
                    callback_data="works"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎁 جوایز من",
                    callback_data="rewards"
                ),
                InlineKeyboardButton(
                    "💎 کیف پول",
                    callback_data="wallet"
                ),
            ],
            [
                InlineKeyboardButton(
                    "👤 پروفایل",
                    callback_data="profile"
                ),
                InlineKeyboardButton(
                    "🎧 پشتیبانی",
                    callback_data="support"
                ),
            ],
        ]
    )


def home_button():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🏠 منوی اصلی",
                    callback_data="home"
                )
            ]
        ]
    )


# =========================================================
# /start
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    ensure_user(
        user.id,
        user.username or "",
        user.first_name or "",
    )

    message = (
        "🎵 <b>BeatMind</b>\n\n"
        "<i>Your Music. Your Mind. Your Beat.</i>\n\n"
        f"سلام {user.first_name or 'آرتیست'} 👋\n\n"
        "اینجا می‌تونی با هوش مصنوعی تکست بسازی، "
        "بیت پیدا کنی و آثار خودت رو مدیریت کنی.\n\n"
        "🎁 <b>هدیه شروع:</b>\n"
        "🎤 ۱ تکست رایگان\n"
        "🎹 ۱ بیت رایگان\n\n"
        "👇 انتخاب کن:"
    )

    await update.message.reply_text(
        message,
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# =========================================================
# Lyrics Studio
# =========================================================

async def show_lyrics_menu(query):

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎤 Rap",
                    callback_data="style:Rap"
                ),
                InlineKeyboardButton(
                    "🔥 Trap",
                    callback_data="style:Trap"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🖤 R&B",
                    callback_data="style:R&B"
                ),
                InlineKeyboardButton(
                    "🥷 Drill",
                    callback_data="style:Drill"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎶 Pop",
                    callback_data="style:Pop"
                ),
                InlineKeyboardButton(
                    "🌙 Lo-Fi",
                    callback_data="style:Lo-Fi"
                ),
            ],
            [
                InlineKeyboardButton(
                    "✨ Custom",
                    callback_data="style:Custom"
                )
            ],
        ]
    )

    await query.edit_message_text(
        "🤖 <b>AI Lyrics Studio</b>\n\n"
        "سبک آهنگت رو انتخاب کن:",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def show_mood_menu(query):

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "❤️ عاشقانه",
                    callback_data="mood:عاشقانه"
                ),
                InlineKeyboardButton(
                    "💔 غمگین",
                    callback_data="mood:غمگین"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🖤 دارک",
                    callback_data="mood:دارک"
                ),
                InlineKeyboardButton(
                    "🌧 احساسی",
                    callback_data="mood:احساسی"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔥 خشن",
                    callback_data="mood:خشن"
                ),
                InlineKeyboardButton(
                    "🚀 انگیزشی",
                    callback_data="mood:انگیزشی"
                ),
            ],
        ]
    )

    await query.edit_message_text(
        "🎭 حال‌وهوای آهنگ رو انتخاب کن:",
        reply_markup=keyboard,
    )


async def show_flow_menu(query):

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Rap",
                    callback_data="flow:Rap"
                ),
                InlineKeyboardButton(
                    "Melodic",
                    callback_data="flow:Melodic"
                ),
            ],
            [
                InlineKeyboardButton(
                    "Singing",
                    callback_data="flow:Singing"
                ),
                InlineKeyboardButton(
                    "Rap + Melodic",
                    callback_data="flow:Rap + Melodic"
                ),
            ],
        ]
    )

    await query.edit_message_text(
        "🎤 نوع اجرا رو انتخاب کن:",
        reply_markup=keyboard,
    )


# =========================================================
# Callback Handler
# =========================================================

async def callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id
    data = query.data


    # -----------------------------------------------------
    # Home
    # -----------------------------------------------------

    if data == "home":

        await query.edit_message_text(
            "🎵 <b>BeatMind</b>\n\n"
            "آماده‌ای چیزی بسازی؟",
            parse_mode="HTML",
            reply_markup=main_menu(),
        )

        return


    # -----------------------------------------------------
    # Lyrics
    # -----------------------------------------------------

    if data == "lyrics":

        await show_lyrics_menu(query)

        return


    # -----------------------------------------------------
    # Style
    # -----------------------------------------------------

    if data.startswith("style:"):

        style = data.split(":", 1)[1]

        context.user_data["style"] = style

        await show_mood_menu(query)

        return


    # -----------------------------------------------------
    # Mood
    # -----------------------------------------------------

    if data.startswith("mood:"):

        mood = data.split(":", 1)[1]

        context.user_data["mood"] = mood

        context.user_data["state"] = "topic"

        await query.edit_message_text(
            "📝 <b>موضوع آهنگت رو بفرست</b>\n\n"
            "مثال:\n"
            "«یه رابطه تموم شده ولی هنوز فراموشش نکردم.»",
            parse_mode="HTML",
        )

        return


    # -----------------------------------------------------
    # Flow
    # -----------------------------------------------------

    if data.startswith("flow:"):

        flow = data.split(":", 1)[1]

        context.user_data["flow"] = flow

        await query.edit_message_text(
            "⏳ <b>BeatMind</b>\n\n"
            "دارم تکستت رو می‌سازم...",
            parse_mode="HTML",
        )

        style = context.user_data.get(
            "style",
            "Rap",
        )

        mood = context.user_data.get(
            "mood",
            "احساسی",
        )

        topic = context.user_data.get(
            "topic",
            "",
        )

        try:

            lyrics = await generate_lyrics(
                style,
                mood,
                topic,
                flow,
            )

        except Exception as error:

            logger.exception(error)

            lyrics = (
                "❌ متأسفانه هنگام تولید تکست "
                "خطایی رخ داد.\n\n"
                "لطفاً دوباره امتحان کن."
            )


        save_lyric(
            user_id,
            style,
            mood,
            topic,
            flow,
            lyrics,
        )


        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🎧 پیدا کردن بیت",
                        callback_data="match"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📂 آثار من",
                        callback_data="works"
                    ),
                    InlineKeyboardButton(
                        "🏠 منوی اصلی",
                        callback_data="home"
                    ),
                ],
            ]
        )


        await query.edit_message_text(
            "🎵 <b>BeatMind Lyrics</b>\n\n"
            f"<b>Style:</b> {style}\n"
            f"<b>Mood:</b> {mood}\n"
            f"<b>Flow:</b> {flow}\n\n"
            f"{lyrics}",
            parse_mode="HTML",
            reply_markup=keyboard,
        )

        return


    # -----------------------------------------------------
    # Store
    # -----------------------------------------------------

    if data == "store":

        await show_store(query)

        return


    # -----------------------------------------------------
    # Beat
    # -----------------------------------------------------

    if data.startswith("beat:"):

        beat_id = int(
            data.split(":", 1)[1]
        )

        await show_beat(
            query,
            beat_id,
        )

        return


    # -----------------------------------------------------
    # Favorite
    # -----------------------------------------------------

    if data.startswith("fav:"):

        beat_id = int(
            data.split(":", 1)[1]
        )

        if is_favorite(
            user_id,
            beat_id,
        ):

            remove_favorite(
                user_id,
                beat_id,
            )

        else:

            add_favorite(
                user_id,
                beat_id,
            )


        await show_beat(
            query,
            beat_id,
        )

        return


    # -----------------------------------------------------
    # Free Beat
    # -----------------------------------------------------

    if data.startswith("claim:"):

        beat_id = int(
            data.split(":", 1)[1]
        )

        beat = get_beat(
            beat_id
        )

        status = get_free_status(
            user_id
        )


        if (
            beat
            and beat["is_free"]
            and not status["free_beat_claimed"]
        ):

            claim_reward(
                user_id,
                "beat",
                beat_id,
            )

            await query.answer(
                "🎉 بیت رایگان فعال شد!",
                show_alert=True,
            )

        else:

            await query.answer(
                "این جایزه قابل دریافت نیست.",
                show_alert=True,
            )


        await show_beat(
            query,
            beat_id,
        )

        return


    # -----------------------------------------------------
    # Rewards
    # -----------------------------------------------------

    if data == "rewards":

        status = get_free_status(
            user_id
        )

        lyrics_status = (
            "✅ استفاده شده"
            if status["free_lyrics_claimed"]
            else "🎁 آماده"
        )

        beat_status = (
            "✅ استفاده شده"
            if status["free_beat_claimed"]
            else "🎁 آماده"
        )


        await query.edit_message_text(
            "🎁 <b>جوایز BeatMind</b>\n\n"
            f"🎤 تکست رایگان: {lyrics_status}\n"
            f"🎹 بیت رایگان: {beat_status}",
            parse_mode="HTML",
            reply_markup=home_button(),
        )

        return


    # -----------------------------------------------------
    # Works
    # -----------------------------------------------------

    if data == "works":

        works = get_lyrics(
            user_id
        )


        if not works:

            message = (
                "📂 <b>آثار من</b>\n\n"
                "هنوز اثری ذخیره نکردی."
            )

        else:

            parts = []

            for item in works[:8]:

                parts.append(
                    f"🎤 <b>{item['style']}</b>\n"
                    f"{item['lyrics'][:600]}"
                )

            message = (
                "📂 <b>آثار من</b>\n\n"
                + "\n\n".join(parts)
            )


        await query.edit_message_text(
            message,
            parse_mode="HTML",
            reply_markup=home_button(),
        )

        return


    # -----------------------------------------------------
    # Profile
    # -----------------------------------------------------

    if data == "profile":

        user = get_user(
            user_id
        )


        await query.edit_message_text(
            "👤 <b>Artist Profile</b>\n\n"
            f"نام: {user['first_name']}\n"
            f"Username: @{user['username'] or '—'}\n"
            f"💎 Credit: {user['credit']}\n"
            f"💰 موجودی: {user['balance']:,} تومان",
            parse_mode="HTML",
            reply_markup=home_button(),
        )

        return


    # -----------------------------------------------------
    # Wallet
    # -----------------------------------------------------

    if data == "wallet":

        user = get_user(
            user_id
        )


        await query.edit_message_text(
            "💎 <b>کیف پول BeatMind</b>\n\n"
            f"💰 موجودی: {user['balance']:,} تومان\n"
            f"💎 Credit: {user['credit']}\n\n"
            "پرداخت آنلاین در نسخه بعدی فعال می‌شود.",
            parse_mode="HTML",
            reply_markup=home_button(),
        )

        return


    # -----------------------------------------------------
    # Match
    # -----------------------------------------------------

    if data == "match":

        works = get_lyrics(
            user_id
        )


        if not works:

            await query.edit_message_text(
                "🎧 برای پیدا کردن بیت مناسب، "
                "اول یک تکست بساز.",
                reply_markup=home_button(),
            )

            return


        latest = works[0]

        beats = list_beats()

        ranked = sorted(
            beats,
            key=lambda beat:
            beat["genre"].lower()
            != latest["style"].lower(),
        )[:5]


        rows = []

        for index, beat_item in enumerate(
            ranked
        ):

            score = 94 - (
                index * 4
            )

            rows.append(
                [
                    InlineKeyboardButton(
                        f"🎧 {beat_item['title']} — {score}%",
                        callback_data=f"beat:{beat_item['id']}",
                    )
                ]
            )


        message = (
            "🎯 <b>Match My Lyrics</b>\n\n"
            "بیت‌هایی که بیشترین هماهنگی "
            "با تکستت رو دارن:"
        )


        await query.edit_message_text(
            message,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                rows
            ),
        )

        return


    # -----------------------------------------------------
    # Support
    # -----------------------------------------------------

    if data == "support":

        await query.edit_message_text(
            "🎧 <b>پشتیبانی BeatMind</b>\n\n"
            "پیامت رو ارسال کن تا بررسی بشه.",
            parse_mode="HTML",
            reply_markup=home_button(),
        )

        return


# =========================================================
# Beat Store
# =========================================================

async def show_store(query):

    beats = list_beats()

    if not beats:

        await query.edit_message_text(
            "🎹 <b>Beat Store</b>\n\n"
            "هنوز بیتی اضافه نشده.",
            parse_mode="HTML",
            reply_markup=home_button(),
        )

        return


    lines = []

    buttons = []


    for beat in beats:

        price = (
            "🎁 رایگان"
            if beat["is_free"]
            else f"{beat['price']:,} تومان"
        )

        lines.append(
            f"🎧 <b>{beat['title']}</b>\n"
            f"{beat['genre']} • "
            f"{beat['bpm']} BPM\n"
            f"{price}"
        )

        buttons.append(
            [
                InlineKeyboardButton(
                    f"🎹 {beat['title']}",
                    callback_data=f"beat:{beat['id']}",
                )
            ]
        )


    buttons.append(
        [
            InlineKeyboardButton(
                "🏠 منوی اصلی",
                callback_data="home",
            )
        ]
    )


    await query.edit_message_text(
        "🎹 <b>Beat Store</b>\n\n"
        + "\n\n".join(lines),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            buttons
        ),
    )


# =========================================================
# Beat Details
# =========================================================

async def show_beat(
    query,
    beat_id,
):

    beat = get_beat(
        beat_id
    )


    if not beat:

        await query.edit_message_text(
            "❌ بیت پیدا نشد."
        )

        return


    price = (
        "🎁 رایگان"
        if beat["is_free"]
        else f"💰 {beat['price']:,} تومان"
    )


    buttons = []


    if beat["preview_file"]:

        buttons.append(
            [
                InlineKeyboardButton(
                    "▶️ Preview",
                    callback_data=f"preview:{beat_id}",
                )
            ]
        )


    status = get_free_status(
        query.from_user.id
    )


    if (
        beat["is_free"]
        and not status["free_beat_claimed"]
    ):

        buttons.append(
            [
                InlineKeyboardButton(
                    "🎁 دریافت بیت رایگان",
                    callback_data=f"claim:{beat_id}",
                )
            ]
        )


    if beat["file_path"]:

        buttons.append(
            [
                InlineKeyboardButton(
                    "📥 دریافت فایل",
                    callback_data=f"download:{beat_id}",
                )
            ]
        )


    favorite_text = (
        "⭐ حذف از علاقه‌مندی‌ها"
        if is_favorite(
            query.from_user.id,
            beat_id,
        )
        else "☆ افزودن به علاقه‌مندی‌ها"
    )


    buttons.append(
        [
            InlineKeyboardButton(
                favorite_text,
                callback_data=f"fav:{beat_id}",
            )
        ]
    )


    buttons.append(
        [
            InlineKeyboardButton(
                "🔙 Beat Store",
                callback_data="store",
            )
        ]
    )


    message = (
        f"🎹 <b>{beat['title']}</b>\n\n"
        f"Producer: {beat['producer']}\n"
        f"Genre: {beat['genre']}\n"
        f"Mood: {beat['mood']}\n"
        f"🎚 BPM: {beat['bpm']}\n"
        f"🎹 Key: {beat['key']}\n"
        f"⏱ Duration: {beat['duration']}\n\n"
        f"{price}"
    )


    await query.edit_message_text(
        message,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            buttons
        ),
    )


# =========================================================
# Audio Preview / Download
# =========================================================

async def media_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    await query.answer()


    beat_id = int(
        query.data.split(":", 1)[1]
    )

    beat = get_beat(
        beat_id
    )


    if not beat:

        await query.answer(
            "بیت پیدا نشد.",
            show_alert=True,
        )

        return


    if query.data.startswith(
        "preview:"
    ):

        file_path = beat[
            "preview_file"
        ]

    else:

        file_path = beat[
            "file_path"
        ]


    if (
        file_path
        and Path(file_path).exists()
    ):

        await query.message.reply_audio(
            audio=InputFile(
                file_path
            ),
            title=beat["title"],
        )

    else:

        await query.answer(
            "فایل هنوز در سیستم قرار نگرفته.",
            show_alert=True,
        )


# =========================================================
# Text Input
# =========================================================

async def text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if (
        context.user_data.get(
            "state"
        )
        != "topic"
    ):

        return


    topic = update.message.text.strip()

    context.user_data[
        "topic"
    ] = topic

    context.user_data[
        "state"
    ] = "flow"


    await update.message.reply_text(
        "🎤 نوع اجرا رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Rap",
                        callback_data="flow:Rap",
                    ),
                    InlineKeyboardButton(
                        "Melodic",
                        callback_data="flow:Melodic",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "Singing",
                        callback_data="flow:Singing",
                    ),
                    InlineKeyboardButton(
                        "Rap + Melodic",
                        callback_data="flow:Rap + Melodic",
                    ),
                ],
            ]
        ),
    )


# =========================================================
# Admin
# =========================================================

async def admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.effective_user.id not in ADMIN_IDS:

        return


    stats = get_stats()


    await update.message.reply_text(
        "🛠 <b>BeatMind Admin</b>\n\n"
        f"👥 کاربران: {stats['users']}\n"
        f"🎤 تکست‌ها: {stats['lyrics']}\n"
        f"🎹 بیت‌ها: {stats['beats']}",
        parse_mode="HTML",
    )


# =========================================================
# Error Handler
# =========================================================

async def error_handler(
    update,
    context,
):

    logger.exception(
        "Unhandled exception",
        exc_info=context.error,
    )


# =========================================================
# Start Bot
# =========================================================

def main():

    init_db()


    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )


    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )


    application.add_handler(
        CommandHandler(
            "admin",
            admin,
        )
    )


    application.add_handler(
        CallbackQueryHandler(
            media_handler,
            pattern=r"^(preview|download):",
        )
    )


    application.add_handler(
        CallbackQueryHandler(
            callback_handler
        )
    )


    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            text_handler,
        )
    )


    application.add_error_handler(
        error_handler
    )


    logger.info(
        "BeatMind is starting..."
    )


    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":

    main()
