from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters
)
from bot import (
    start, handle_language_selection, handle_vacancy_selection,
    start_application_process, handle_back_to_vacancies,
    handle_message, handle_contact, handle_document, handle_voice
)

BOT_TOKEN = "your_bot_token"

def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_language_selection, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(handle_vacancy_selection,  pattern="^vacancy_"))
    app.add_handler(CallbackQueryHandler(start_application_process, pattern="^start_application$"))
    app.add_handler(CallbackQueryHandler(handle_back_to_vacancies,  pattern="^back_to_vacancies$"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.CONTACT,      handle_contact))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.VOICE,        handle_voice))

    print("✅ Bot is running…")
    app.run_polling()

if __name__ == "__main__":
    main()
