from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from database import get_all_sections
from config import CHANNEL_USERNAME


async def main_menu_keyboard() -> ReplyKeyboardMarkup:
    sections = await get_all_sections()
    buttons = []
    row = []
    for i, sec in enumerate(sections):
        row.append(f"{sec['emoji']} {sec['name']}")
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def subscribe_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 اشترك في القناة", url=f"https://t.me/{CHANNEL_USERNAME}")],
        [InlineKeyboardButton("✅ اشتركت، تحقق الآن", callback_data="check_subscribe")],
    ])


def back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([["🔙 رجوع للقائمة الرئيسية"]], resize_keyboard=True)


def admin_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        ["➕ إضافة محتوى", "🗑 حذف محتوى"],
        ["📊 إحصائيات", "📢 إرسال رسالة جماعية"],
        ["🔙 رجوع للقائمة الرئيسية"],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


async def sections_choose_keyboard() -> InlineKeyboardMarkup:
    sections = await get_all_sections()
    buttons = []
    for sec in sections:
        buttons.append([
            InlineKeyboardButton(
                f"{sec['emoji']} {sec['name']}",
                callback_data=f"admin_add_{sec['key']}"
            )
        ])
    buttons.append([InlineKeyboardButton("❌ إلغاء", callback_data="admin_cancel")])
    return InlineKeyboardMarkup(buttons)


async def sections_delete_keyboard() -> InlineKeyboardMarkup:
    sections = await get_all_sections()
    buttons = []
    for sec in sections:
        buttons.append([
            InlineKeyboardButton(
                f"{sec['emoji']} {sec['name']}",
                callback_data=f"admin_del_sec_{sec['key']}"
            )
        ])
    buttons.append([InlineKeyboardButton("❌ إلغاء", callback_data="admin_cancel")])
    return InlineKeyboardMarkup(buttons)
