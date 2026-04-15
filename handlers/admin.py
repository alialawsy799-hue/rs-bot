from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from config import ADMIN_IDS
from database import (
    add_content, get_users_count, get_all_user_ids,
    get_section_content, delete_content, get_all_sections, get_content_count
)
from utils.keyboards import admin_keyboard, sections_choose_keyboard, sections_delete_keyboard

# ConversationHandler states
CHOOSE_SECTION, WAIT_CONTENT, WAIT_CAPTION = range(3)
CHOOSE_DEL_SECTION, CHOOSE_DEL_ITEM = range(3, 5)
WAIT_BROADCAST = 5


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ── لوحة التحكم ─────────────────────────────────────────

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(
        "🔧 <b>لوحة التحكم</b>\n\nاختر العملية المطلوبة:",
        reply_markup=admin_keyboard(),
        parse_mode="HTML",
    )


# ── إحصائيات ────────────────────────────────────────────

async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    users_count = await get_users_count()
    sections = await get_all_sections()
    lines = [f"📊 <b>إحصائيات البوت</b>\n", f"👥 المستخدمون: {users_count}\n"]
    for sec in sections:
        count = await get_content_count(sec["key"])
        lines.append(f"{sec['emoji']} {sec['name']}: {count} عنصر")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


# ── إضافة محتوى (Conversation) ──────────────────────────

async def add_content_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    kb = await sections_choose_keyboard()
    await update.message.reply_text("📂 اختر القسم الذي تريد إضافة محتوى إليه:", reply_markup=kb)
    return CHOOSE_SECTION


async def add_section_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "admin_cancel":
        await query.message.edit_text("❌ تم الإلغاء.")
        return ConversationHandler.END

    section_key = query.data.replace("admin_add_", "")
    context.user_data["add_section_key"] = section_key
    await query.message.edit_text(
        "📤 الآن أرسل المحتوى الذي تريد إضافته:\n\n"
        "يمكنك إرسال:\n"
        "• نص\n• صورة\n• ملف PDF\n• فيديو\n• صوت\n\n"
        "أرسل /cancel للإلغاء"
    )
    return WAIT_CONTENT


async def add_content_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    section_key = context.user_data.get("add_section_key")
    msg = update.message

    ctype = None
    file_id = None
    text = None

    if msg.text and not msg.text.startswith("/"):
        ctype = "text"
        text = msg.text
    elif msg.photo:
        ctype = "photo"
        file_id = msg.photo[-1].file_id
    elif msg.document:
        ctype = "document"
        file_id = msg.document.file_id
    elif msg.video:
        ctype = "video"
        file_id = msg.video.file_id
    elif msg.audio:
        ctype = "audio"
        file_id = msg.audio.file_id
    elif msg.voice:
        ctype = "voice"
        file_id = msg.voice.file_id
    else:
        await msg.reply_text("⚠️ نوع المحتوى غير مدعوم، أرسل نصاً أو ملفاً.")
        return WAIT_CONTENT

    context.user_data["pending_content"] = {
        "section_key": section_key,
        "type": ctype,
        "file_id": file_id,
        "text": text,
    }

    if ctype == "text":
        await add_content(
            section_key, ctype, file_id, text,
            caption=None, added_by=update.effective_user.id
        )
        await msg.reply_text("✅ تمت إضافة النص بنجاح!")
        return ConversationHandler.END

    await msg.reply_text(
        "📝 أرسل وصفاً (caption) للملف، أو أرسل /skip لتخطي الوصف:"
    )
    return WAIT_CAPTION


async def add_caption_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending = context.user_data.get("pending_content", {})
    caption = None

    if update.message.text and update.message.text != "/skip":
        caption = update.message.text

    await add_content(
        pending["section_key"],
        pending["type"],
        pending["file_id"],
        pending["text"],
        caption=caption,
        added_by=update.effective_user.id,
    )
    await update.message.reply_text("✅ تمت إضافة المحتوى بنجاح!")
    context.user_data.clear()
    return ConversationHandler.END


async def add_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ تم الإلغاء.")
    return ConversationHandler.END


# ── حذف محتوى (Conversation) ────────────────────────────

async def delete_content_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    kb = await sections_delete_keyboard()
    await update.message.reply_text("🗑 اختر القسم الذي تريد الحذف منه:", reply_markup=kb)
    return CHOOSE_DEL_SECTION


async def delete_section_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "admin_cancel":
        await query.message.edit_text("❌ تم الإلغاء.")
        return ConversationHandler.END

    section_key = query.data.replace("admin_del_sec_", "")
    items = await get_section_content(section_key)

    if not items:
        await query.message.edit_text("📭 لا يوجد محتوى في هذا القسم.")
        return ConversationHandler.END

    buttons = []
    for item in items[:20]:
        label = item.get("caption") or item.get("text") or f"{item['type']} #{item['id']}"
        label = label[:40]
        buttons.append([
            InlineKeyboardButton(f"🗑 {label}", callback_data=f"del_item_{item['id']}")
        ])
    buttons.append([InlineKeyboardButton("❌ إلغاء", callback_data="admin_cancel")])
    await query.message.edit_text(
        "اختر العنصر الذي تريد حذفه:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return CHOOSE_DEL_ITEM


async def delete_item_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "admin_cancel":
        await query.message.edit_text("❌ تم الإلغاء.")
        return ConversationHandler.END

    item_id = int(query.data.replace("del_item_", ""))
    success = await delete_content(item_id)
    if success:
        await query.message.edit_text("✅ تم الحذف بنجاح!")
    else:
        await query.message.edit_text("⚠️ لم يتم العثور على العنصر.")
    return ConversationHandler.END


# ── رسالة جماعية (Conversation) ─────────────────────────

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    await update.message.reply_text(
        "📢 أرسل الرسالة التي تريد إرسالها لجميع المستخدمين:\n\n"
        "أرسل /cancel للإلغاء"
    )
    return WAIT_BROADCAST


async def broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    user_ids = await get_all_user_ids()
    success = 0
    failed = 0

    await update.message.reply_text(f"⏳ جاري الإرسال لـ {len(user_ids)} مستخدم...")

    for uid in user_ids:
        try:
            await context.bot.copy_message(
                chat_id=uid,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id,
            )
            success += 1
        except Exception:
            failed += 1

    await update.message.reply_text(
        f"✅ تم الإرسال!\n\n"
        f"• نجح: {success}\n"
        f"• فشل: {failed}"
    )
    return ConversationHandler.END
