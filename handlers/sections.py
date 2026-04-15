from telegram import Update
from telegram.ext import ContextTypes

from database import get_all_sections, get_section, get_section_content
from utils.force_subscribe import is_subscribed
from utils.keyboards import main_menu_keyboard, back_keyboard, subscribe_keyboard


async def section_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()

    if text == "🔙 رجوع للقائمة الرئيسية":
        keyboard = await main_menu_keyboard()
        await update.message.reply_text("🏠 القائمة الرئيسية:", reply_markup=keyboard)
        return

    if not await is_subscribed(context.bot, user.id):
        from config import CHANNEL_USERNAME
        await update.message.reply_text(
            f"⛔️ عليك الاشتراك في القناة أولاً!\n👉 @{CHANNEL_USERNAME}",
            reply_markup=subscribe_keyboard(),
        )
        return

    sections = await get_all_sections()
    matched = None
    for sec in sections:
        if text == f"{sec['emoji']} {sec['name']}":
            matched = sec
            break

    if not matched:
        return

    content_list = await get_section_content(matched["key"])

    if not content_list:
        await update.message.reply_text(
            f"{matched['emoji']} <b>{matched['name']}</b>\n\n"
            f"📭 لا يوجد محتوى في هذا القسم بعد.\n"
            f"سيتم إضافة المحتوى قريباً إن شاء الله ✨",
            reply_markup=back_keyboard(),
            parse_mode="HTML",
        )
        return

    await update.message.reply_text(
        f"{matched['emoji']} <b>{matched['name']}</b>\n\n"
        f"📦 يوجد {len(content_list)} عنصر في هذا القسم:",
        reply_markup=back_keyboard(),
        parse_mode="HTML",
    )

    for item in content_list:
        await _send_content_item(update, item)


async def _send_content_item(update: Update, item: dict):
    caption = item.get("caption") or ""
    ctype = item["type"]

    try:
        if ctype == "text":
            await update.message.reply_text(item["text"] or "")
        elif ctype == "photo":
            await update.message.reply_photo(item["file_id"], caption=caption)
        elif ctype == "document":
            await update.message.reply_document(item["file_id"], caption=caption)
        elif ctype == "video":
            await update.message.reply_video(item["file_id"], caption=caption)
        elif ctype == "audio":
            await update.message.reply_audio(item["file_id"], caption=caption)
        elif ctype == "voice":
            await update.message.reply_voice(item["file_id"], caption=caption)
    except Exception:
        pass
