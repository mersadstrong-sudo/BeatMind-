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
    get_lyrics,
    list_beats,
    get_beat,
    add_favorite,
    remove_favorite,
    is_favorite,
    get_stats,
    claim_reward,
)


# =========================================================
# BeatMind v1.0
# AI Lyrics temporarily disabled
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
        "BOT_TOKEN is missing."
    )


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger("BeatMind")


DATA_DIR = Path("data")
BEATS_DIR = DATA_DIR / "beats"

DATA_DIR.mkdir(
    exist_ok=True
)

BEATS_DIR.mkdir(
    exist_ok=True
)


# =========================================================
# Main Menu
# =========================================================

def main_menu():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎹 Beat Store",
                    callback_data="store"
                ),
                InlineKeyboardButton(
                    "🎧 پیدا کردن بیت",
                    callback_data="match"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎁 جوایز من",
                    callback_data="rewards"
                ),
                InlineKeyboardButton(
                    "📂 آثار من",
                    callback_data="works"
                ),
            ],
            [
                InlineKeyboardButton(
                    "💎 کیف پول",
                    callback_data="wallet"
                ),
                InlineKeyboardButton(
                    "👤 پروفایل",
                    callback_data="profile"
                ),
            ],
            [
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

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

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
        "به BeatMind خوش اومدی.\n\n"
        "🎹 فروشگاه بیت\n"
        "🎧 پیدا کردن بیت مناسب\n"
        "🎁 بیت رایگان\n"
        "📂 مدیریت آثار\n"
        "💎 کیف پول\n\n"
        "🤖 بخش تولید تکست فعلاً در حال توسعه است "
        "و به‌زودی فعال می‌شود.\n\n"
        "👇 انتخاب کن:"
    )

    await update.message.reply_text(
        message,
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# =========================================================
# Main Callback Handler
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
            "آماده‌ای وارد دنیای بیت‌ها بشی؟",
            parse_mode="HTML",
            reply_markup=main_menu(),
        )

        return


    # -----------------------------------------------------
    # Beat Store
    # -----------------------------------------------------

    if data == "store":

        await show_store(query)

        return


    # -----------------------------------------------------
    # Beat Details
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
    # Claim Free Beat
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

        elif status["free_beat_claimed"]:

            await query.answer(
                "🎁 قبلاً بیت رایگانت رو دریافت کردی.",
                show_alert=True,
            )

        else:

            await query.answer(
                "این بیت رایگان نیست.",
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
            "⏳ فعلاً غیرفعال"
        )

        beat_status = (
            "✅ استفاده شده"
            if status["free_beat_claimed"]
            else "🎁 آماده دریافت"
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


        if not user:

            ensure_user(
                user_id,
                query.from_user.username or "",
                query.from_user.first_name or "",
            )

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
            "درگاه پرداخت در نسخه بعدی اضافه می‌شود.",
            parse_mode="HTML",
            reply_markup=home_button(),
        )

        return


    # -----------------------------------------------------
    # Match My Lyrics
    # -----------------------------------------------------

    if data == "match":

        beats = list_beats()


        if not beats:

            await query.edit_message_text(
                "🎧 هنوز بیتی در فروشگاه وجود ندارد.",
                reply_markup=home_button(),
            )

            return


        buttons = []

        for beat in beats[:8]:

            buttons.append(
                [
                    InlineKeyboardButton(
                        f"🎧 {beat['title']}",
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
            "🎧 <b>Beat Finder</b>\n\n"
            "بیت موردنظرت رو انتخاب کن:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                buttons
            ),
        )

        return


    # -----------------------------------------------------
    # Support
    # -----------------------------------------------------

    if data == "support":

        await query.edit_message_text(
            "🎧 <b>پشتیبانی BeatMind</b>\n\n"
            "پیامت رو ارسال کن تا بررسی بشه.\n\n"
            "بخش پشتیبانی پیشرفته در نسخه بعدی تکمیل می‌شود.",
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
            "❌ بیت پیدا نشد.",
            reply_markup=home_button(),
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
            "فایل بیت هنوز اضافه نشده.",
            show_alert=True,
        )


# =========================================================
# Admin
# =========================================================

async def admin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.effective_user.id not in ADMIN_IDS:

        await update.message.reply_text(
            "⛔ دسترسی غیرمجاز."
        )

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
# Main
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
            lambda update, context: update.message.reply_text(
                "👇 لطفاً یکی از گزینه‌های منو را انتخاب کن.",
                reply_markup=main_menu(),
            ),
        )
    )


    application.add_error_handler(
        error_handler
    )


    logger.info(
        "BeatMind started successfully."
    )


    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":

    main()
