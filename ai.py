import os
from openai import AsyncOpenAI


# =========================================================
# BeatMind AI Lyrics Engine v1.1
# OpenAI Responses API
# =========================================================

async def generate_lyrics(
    style,
    mood,
    topic,
    flow,
):

    api_key = os.getenv(
        "OPENAI_API_KEY",
        "",
    ).strip()

    model = os.getenv(
        "OPENAI_MODEL",
        "gpt-5.6-luna",
    ).strip()


    # -----------------------------------------------------
    # API Key Check
    # -----------------------------------------------------

    if not api_key:

        return (
            "❌ اتصال هوش مصنوعی تنظیم نشده است.\n\n"
            "لطفاً OPENAI_API_KEY را در Railway "
            "بررسی کنید."
        )


    try:

        client = AsyncOpenAI(
            api_key=api_key
        )


        # -------------------------------------------------
        # System Instructions
        # -------------------------------------------------

        instructions = """
تو موتور تولید تکست حرفه‌ای BeatMind هستی.

برای خواننده‌ها و هنرمندان مستقل، متن فارسی
کاملاً اورجینال تولید کن.

قوانین مهم:

- متن باید کاملاً جدید و اورجینال باشد.
- متن یک خواننده یا آهنگ مشخص را تقلید نکن.
- از کپی یا بازسازی متن آهنگ‌های موجود خودداری کن.
- زبان خروجی فارسی باشد.
- قافیه‌ها طبیعی و قابل اجرا باشند.
- متن بیش از حد کلیشه‌ای نباشد.
- به سبک، حس، موضوع و Flow انتخاب‌شده وفادار باش.
- Hook باید به‌یادماندنی باشد.
- متن برای اجرای واقعی نوشته شود.

ساختار پیشنهادی:

[INTRO]

[VERSE 1]

[PRE-HOOK]

[HOOK]

[VERSE 2]

[BRIDGE]

[HOOK]

[OUTRO]
"""


        # -------------------------------------------------
        # User Prompt
        # -------------------------------------------------

        prompt = f"""
برای BeatMind یک تکست فارسی اورجینال بساز.

سبک:
{style}

حال‌وهوا:
{mood}

موضوع:
{topic}

نوع اجرا / Flow:
{flow}

یک متن حرفه‌ای، احساسی و قابل اجرا تولید کن.

از توضیح اضافه خودداری کن.
فقط خود تکست آهنگ را ارائه بده.
"""


        # -------------------------------------------------
        # Responses API
        # -------------------------------------------------

        response = await client.responses.create(

            model=model,

            instructions=instructions,

            input=prompt,

        )


        # -------------------------------------------------
        # Output
        # -------------------------------------------------

        result = response.output_text


        if not result:

            return (
                "❌ هوش مصنوعی پاسخی تولید نکرد.\n"
                "لطفاً دوباره امتحان کن."
            )


        return result.strip()


    except Exception as error:

        # Log technical error for Railway
        print(
            f"[BeatMind AI ERROR] {type(error).__name__}: {error}"
        )


        return (
            "❌ هنگام ساخت تکست مشکلی پیش آمد.\n\n"
            "لطفاً چند لحظه بعد دوباره امتحان کن."
        )
