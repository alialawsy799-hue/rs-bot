import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

from config import BOT_TOKEN, PROXY_URL
from database import init_db
from handlers.start import start_handler, check_subscribe_callback
from handlers.sections import section_handler
from handlers.admin import (
    admin_panel, stats_handler,
    add_content_start, add_section_chosen, add_content_received,
    add_caption_received, add_cancel,
    delete_content_start, delete_section_chosen, delete_item_chosen,
    broadcast_start, broadcast_send,
    CHOOSE_SECTION, WAIT_CONTENT, WAIT_CAPTION,
    CHOOSE_DEL_SECTION, CHOOSE_DEL_ITEM,
    WAIT_BROADCAST,
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)


def build_add_conv() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ إضافة محتوى$"), add_content_start)],
        states={
            CHOOSE_SECTION: [CallbackQueryHandler(add_section_chosen, pattern="^admin_add_|^admin_cancel$")],
            WAIT_CONTENT:   [MessageHandler(filters.ALL & ~filters.COMMAND, add_content_received),
                             CommandHandler("cancel", add_cancel)],
            WAIT_CAPTION:   [MessageHandler(filters.TEXT & ~filters.COMMAND, add_caption_received),
                             CommandHandler("skip", add_caption_received),
                             CommandHandler("cancel", add_cancel)],
        },
        fallbacks=[CommandHandler("cancel", add_cancel)],
        allow_reentry=True,
    )


def build_delete_conv() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🗑 حذف محتوى$"), delete_content_start)],
        states={
            CHOOSE_DEL_SECTION: [CallbackQueryHandler(delete_section_chosen, pattern="^admin_del_sec_|^admin_cancel$")],
            CHOOSE_DEL_ITEM:    [CallbackQueryHandler(delete_item_chosen, pattern="^del_item_|^admin_cancel$")],
        },
        fallbacks=[CommandHandler("cancel", add_cancel)],
        allow_reentry=True,
    )


def build_broadcast_conv() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📢 إرسال رسالة جماعية$"), broadcast_start)],
        states={
            WAIT_BROADCAST: [MessageHandler(filters.ALL & ~filters.COMMAND, broadcast_send),
                             CommandHandler("cancel", add_cancel)],
        },
        fallbacks=[CommandHandler("cancel", add_cancel)],
        allow_reentry=True,
    )


async def post_init(app):
    await init_db()
    logging.info("✅ قاعدة البيانات جاهزة")


def main():
    builder = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
    )
    if PROXY_URL:
        builder = builder.proxy_url(PROXY_URL).get_updates_proxy_url(PROXY_URL)
    app = builder.build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(check_subscribe_callback, pattern="^check_subscribe$"))

    app.add_handler(build_add_conv())
    app.add_handler(build_delete_conv())
    app.add_handler(build_broadcast_conv())

    app.add_handler(MessageHandler(filters.Regex("^📊 إحصائيات$"), stats_handler))
    app.add_handler(MessageHandler(filters.Regex("^🔧 لوحة التحكم$"), admin_panel))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, section_handler))

    logging.info("🚀 البوت يعمل...")
    app.run_polling()


if __name__ == "__main__":
    main()
