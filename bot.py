from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from telegram.ext import ContextTypes
import logging, requests, json
from pathlib import Path

logging.basicConfig(level=logging.INFO)

BITRIX24_WEBHOOK_URL = "your_bitrix_api"

user_language: dict[int, str] = {}
user_state:    dict[int, str] = {}

LANGUAGES = {'en': '🇬🇧 English', 'ru': '🇷🇺 Русский', 'uz': '🇺🇿 Oʻzbekcha'}

TEXTS = {
    "choose_lang":  {"en": "Please choose your language:", "ru": "Выберите язык:", "uz": "Tilni tanlang:"},
    "available_vacancies": {"en": "Available vacancies:", "ru": "Доступные вакансии:", "uz": "Mavjud bo‘sh ish o‘rinlari:"},
    "start_application":   {"en": "Let's begin your application.\nPlease enter your full name:",
                            "ru": "Давайте начнём заявку.\nВведите полное имя:",
                            "uz": "Arizani boshlaymiz.\nTo‘liq ismingizni kiriting:"},
    "share_phone":  {"en": "Now share your phone number:", "ru": "Поделитесь номером телефона:", "uz": "Telefon raqamingizni ulashing:"},
    "upload_cv":    {"en": "Please upload your CV as a document.", "ru": "Загрузите резюме файлом.", "uz": "Rezyumeni hujjat sifatida yuklang."},
    "record_voice": {"en": "Please record a voice message about your experience.",
                    "ru": "Запишите голосовое сообщение о своём опыте.",
                    "uz": "Tajribangiz haqida ovozli xabar yozing."},
    "application_complete": {"en": "🎉 Your application is complete! Thank you.",
                             "ru": "🎉 Заявка завершена! Спасибо.",
                             "uz": "🎉 Ariza yakunlandi! Rahmat."},
    "great_upload_cv": {"en": "Great 👍 Now upload your CV:", "ru": "Отлично 👍 Загрузите резюме:", "uz": "Zo‘r 👍 Rezyumeni yuklang:"},
    "btn_apply":       {"en": "✅ Apply",        "ru": "✅ Откликнуться",  "uz": "✅ Murojaat"},
    "btn_back":        {"en": "🔙 Go back",      "ru": "🔙 Назад",        "uz": "🔙 Orqaga"},
    "btn_share_phone": {"en": "Share phone",    "ru": "Поделиться телефоном", "uz": "Telefonni ulashish"}
}

VACANCIES = json.loads(Path("vacancies.json").read_text(encoding="utf-8"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton(name, callback_data=f"lang_{code}")]
          for code, name in LANGUAGES.items()]
    await update.message.reply_text(
        TEXTS["choose_lang"]["en"],
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def handle_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid  = q.from_user.id
    lang = q.data.split("_")[1]
    user_language[uid] = lang

    await q.edit_message_text(
        text=f"✅ {LANGUAGES[lang]}.\n\n{TEXTS['available_vacancies'][lang]}"
    )
    await show_vacancies(q.message, context, lang)

async def show_vacancies(msg_source, context: ContextTypes.DEFAULT_TYPE, lang: str):
    kb = [[InlineKeyboardButton(v["titles"][lang], callback_data=f"vacancy_{v['id']}")]
          for v in VACANCIES]
    await msg_source.reply_text(
        text=TEXTS["available_vacancies"][lang],
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def handle_vacancy_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid  = q.from_user.id
    lang = user_language.get(uid, "en")
    vid  = int(q.data.split("_")[1])
    vac  = next(v for v in VACANCIES if v["id"] == vid)
    context.user_data["vacancy"] = vac

    reqs = vac["requirements"][lang]
    qs   = "\n".join(f"❓ {x}" for x in vac["questions"][lang])
    msg  = (
        f"📌 *{vac['titles'][lang]}*\n\n"
        f"✅ *{TEXTS['available_vacancies'][lang]}*\n{reqs}\n\n"
        f"📝 *Questions:*\n{qs}"
    )

    kb = [
        [InlineKeyboardButton(TEXTS["btn_apply"][lang], callback_data="start_application")],
        [InlineKeyboardButton(TEXTS["btn_back"][lang],  callback_data="back_to_vacancies")]
    ]
    await q.message.reply_text(
        text=msg,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )


async def start_application_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid  = q.from_user.id
    lang = user_language.get(uid, "en")

    await context.bot.send_message(uid, TEXTS["start_application"][lang])
    user_state[uid] = "name"


async def handle_back_to_vacancies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid  = q.from_user.id
    lang = user_language.get(uid, "en")

    await q.message.delete()
    await show_vacancies(q.message, context, lang)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    st   = user_state.get(uid)
    lang = user_language.get(uid, "en")

    if st == "name":
        context.user_data["full_name"] = update.message.text
        kb = ReplyKeyboardMarkup(
            [[KeyboardButton(TEXTS["btn_share_phone"][lang], request_contact=True)]],
            resize_keyboard=True
        )
        await update.message.reply_text(TEXTS["share_phone"][lang], reply_markup=kb)
        user_state[uid] = "phone"

    elif st == "cv":
        await update.message.reply_text(TEXTS["upload_cv"][lang])

    elif st == "voice":
        await update.message.reply_text(TEXTS["record_voice"][lang])

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = user_language.get(uid, "en")

    context.user_data["phone"] = update.message.contact.phone_number
    await update.message.reply_text(TEXTS["great_upload_cv"][lang], reply_markup=ReplyKeyboardRemove())
    user_state[uid] = "cv"

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = user_language.get(uid, "en")

    context.user_data["cv_file_id"] = update.message.document.file_id
    await update.message.reply_text(TEXTS["record_voice"][lang])
    user_state[uid] = "voice"

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = user_language.get(uid, "en")

    context.user_data["voice_file_id"] = update.message.voice.file_id
    await update.message.reply_text(TEXTS["application_complete"][lang])


    vac            = context.user_data.get("vacancy", {})
    vacancy_title  = vac.get("titles", {}).get(lang, "Unknown vacancy")
    data = {
        "fields": {
            "TITLE": f"{vacancy_title} — Telegram Application",
            "NAME": context.user_data.get("full_name", ""),
            "PHONE": [{"VALUE": context.user_data.get("phone", ""), "VALUE_TYPE": "WORK"}],
            "COMMENTS": (
                f"Vacancy: {vacancy_title}\n"
                f"CV File ID: {context.user_data.get('cv_file_id','')}\n"
                f"Voice File ID: {context.user_data.get('voice_file_id','')}"
            )
        },
        "params": {"REGISTER_SONET_EVENT": "Y"}
    }
    try:
        r = requests.post(BITRIX24_WEBHOOK_URL, json=data, timeout=10)
        if r.status_code == 200:
            logging.info("✅ Lead sent to Bitrix24.")
        else:
            logging.error(f"❌ Bitrix24 error {r.status_code}: {r.text}")
    except Exception as e:
        logging.error(f"❌ Exception sending to Bitrix24: {e}")

    user_state.pop(uid, None)

