from telegram import Update
from telegram.ext import ContextTypes

from config import BOT_NAME, BOT_DESCRIPTION, CHANNEL_USERNAME
from database import add_user
from utils.force_subscribe import is_subscribed
from utils.keyboards import main_menu_keyboard, subscribe_keyboard


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await add_user(user.id, user.username or "", user.first_name or "")

    if not await is_subscribed(context.bot, user.id):
        await update.message.reply_text(
            f"⛔️ عذراً عزيزي\n\n"
            f"📢 عليك الاشتراك في قناة البوت أولاً لتتمكن من استخدامه:\n\n"
            f"👉 @{CHANNEL_USERNAME}\n\n"
            f"✅ اشترك ثم اضغط على الزر أدناه للتحقق!",
            reply_markup=subscribe_keyboard(),
        )
        return

    await _send_welcome(update, user.first_name)


async def _send_welcome(update: Update, first_name: str):
    keyboard = await main_menu_keyboard()
    await update.message.reply_text(
        f"🎉 أهلاً وسهلاً بك {first_name} في\n"
        f"<b>{BOT_NAME}</b>\n\n"
        f"📚 {BOT_DESCRIPTION}\n\n"
        f"اختر من القائمة أدناه 👇",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


async def check_subscribe_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if await is_subscribed(context.bot, user.id):
        await query.message.delete()
        keyboard = await main_menu_keyboard()
        await context.bot.send_message(
            chat_id=user.id,
            text=f"✅ تم التحقق!\n\nأهلاً {user.first_name} 🎉\nاختر من القائمة أدناه 👇",
            reply_markup=keyboard,
        )
    else:
        await query.answer(
            "❌ لم تشترك بعد! اشترك في القناة أولاً.",
            show_alert=True
        )
