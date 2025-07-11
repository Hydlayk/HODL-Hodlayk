import os, time, threading, json, queue, sys, traceback
from ai import UltraEvoAI  # ai.py должен быть в той же папке
from telegram import Update, Bot
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8015046873:AAFfJIj_TNa8zr-kc8lgHRdF0ZwU5bX3zz4")  # вставь свой токен!
ADMIN_IDS = [6053770255]  # сюда свой Telegram user_id

ai = UltraEvoAI()
ai.start_background()
task_q = queue.Queue()
HISTORY_LIMIT = 30

def ai_respond(qtype, data, user_id=None):
    # Обертка для ответа ИИ на запрос из Telegram
    return ai.handle_external_query(qtype, data)

def start(update: Update, context: CallbackContext):
    msg = ("🤖 Привет! Я — UltraEvoAI, эволюционирующий искусственный интеллект.\n\n"
           "Просто напиши мне любой вопрос, команду или запрос — я постараюсь ответить максимально осмысленно!\n"
           "Для справки: /help\n")
    context.bot.send_message(chat_id=update.effective_chat.id, text=msg)

def help_cmd(update: Update, context: CallbackContext):
    msg = ai.help_text()
    context.bot.send_message(chat_id=update.effective_chat.id, text=msg)

def status(update: Update, context: CallbackContext):
    s = ai_respond("status", "")
    context.bot.send_message(chat_id=update.effective_chat.id, text=s)

def idea(update: Update, context: CallbackContext):
    s = ai_respond("idea", "")
    context.bot.send_message(chat_id=update.effective_chat.id, text=s)

def code(update: Update, context: CallbackContext):
    s = ai_respond("code", "")
    context.bot.send_message(chat_id=update.effective_chat.id, text=s)

def fact(update: Update, context: CallbackContext):
    s = ai_respond("fact", "")
    context.bot.send_message(chat_id=update.effective_chat.id, text=s)

def project(update: Update, context: CallbackContext):
    s = ai_respond("project", "")
    context.bot.send_message(chat_id=update.effective_chat.id, text=s)

def trends(update: Update, context: CallbackContext):
    s = ai_respond("trends", "")
    context.bot.send_message(chat_id=update.effective_chat.id, text=s)

def skills(update: Update, context: CallbackContext):
    s = ai_respond("skills", "")
    context.bot.send_message(chat_id=update.effective_chat.id, text=s)

def export(update: Update, context: CallbackContext):
    s = ai_respond("state", "")
    context.bot.send_message(chat_id=update.effective_chat.id, text=s[:4096])

def reflect(update: Update, context: CallbackContext):
    s = ai_respond("reflect", "")
    context.bot.send_message(chat_id=update.effective_chat.id, text=s)

def admin_report(update: Update, context: CallbackContext):
    if update.effective_user.id in ADMIN_IDS:
        s = ai.admin_report()
        context.bot.send_message(chat_id=update.effective_chat.id, text=s[:4096])
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Нет доступа.")

def unknown(update: Update, context: CallbackContext):
    q = update.message.text.strip()
    r = ai_respond("search", q)
    context.bot.send_message(chat_id=update.effective_chat.id, text=r[:4096] if r else "Ничего не найдено.")

def feedback(update: Update, context: CallbackContext):
    fb = update.message.text.partition(' ')[2].strip()
    if not fb:
        fb = "Нет текста"
    ai_respond("feedback", fb)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Фидбек получен, спасибо!")

def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', help_cmd))
    dispatcher.add_handler(CommandHandler('status', status))
    dispatcher.add_handler(CommandHandler('idea', idea))
    dispatcher.add_handler(CommandHandler('code', code))
    dispatcher.add_handler(CommandHandler('fact', fact))
    dispatcher.add_handler(CommandHandler('project', project))
    dispatcher.add_handler(CommandHandler('trends', trends))
    dispatcher.add_handler(CommandHandler('skills', skills))
    dispatcher.add_handler(CommandHandler('export', export))
    dispatcher.add_handler(CommandHandler('reflect', reflect))
    dispatcher.add_handler(CommandHandler('admin_report', admin_report))
    dispatcher.add_handler(CommandHandler('feedback', feedback))
    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), unknown))

    print("Telegram AI бот запущен. Ожидание сообщений...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
# --- Расширение: обработка длинных сообщений, chunking, поддержка больших экспортов ---

def send_long_message(bot, chat_id, text, chunk=3900):
    """Разбить и отправить длинный текст несколькими сообщениями."""
    if not text: return
    parts = [text[i:i+chunk] for i in range(0, len(text), chunk)]
    for p in parts:
        bot.send_message(chat_id=chat_id, text=p)

def export_full(update: Update, context: CallbackContext):
    """Полный экспорт всех знаний/состояния — длинными чанками."""
    s = ai.admin_report()
    send_long_message(context.bot, update.effective_chat.id, s)

def history(update: Update, context: CallbackContext):
    """Показать последние вопросы/ответы (история CLI и Telegram)."""
    h = ai.command_history[-HISTORY_LIMIT:]
    msg = "\n\n".join(f"{c['command']}" for c in h if 'command' in c)
    send_long_message(context.bot, update.effective_chat.id, "Последние команды:\n" + msg if msg else "Истории нет.")

def diag(update: Update, context: CallbackContext):
    """Отправить последние диагностические отчёты/мониторинг."""
    d = ai.diag_history[-12:]
    txt = json.dumps(d, ensure_ascii=False, indent=2)
    send_long_message(context.bot, update.effective_chat.id, txt)

def system_diag(update: Update, context: CallbackContext):
    """Глубокий системный отчёт."""
    txt = ai.system_diag_report()
    send_long_message(context.bot, update.effective_chat.id, txt)

def system_reset(update: Update, context: CallbackContext):
    """Сбросить систему (только для ADMIN_IDS)."""
    if update.effective_user.id in ADMIN_IDS:
        res = ai.system_reset(confirm=True)
        context.bot.send_message(chat_id=update.effective_chat.id, text=res)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Нет доступа.")

def custom_commands(dispatcher):
    dispatcher.add_handler(CommandHandler('export_full', export_full))
    dispatcher.add_handler(CommandHandler('history', history))
    dispatcher.add_handler(CommandHandler('diag', diag))
    dispatcher.add_handler(CommandHandler('system_diag', system_diag))
    dispatcher.add_handler(CommandHandler('system_reset', system_reset))

# Для интеграции: просто вызови custom_commands(dispatcher) после основных handler'ов

# --- Хэндлер ошибок, логирование исключений, автоуведомления ---

def error_handler(update: Update, context: CallbackContext):
    tb = "".join(traceback.format_exception(None, context.error, context.error.__traceback__))
    log = f"[TGError] {tb}"
    print(log)
    try:
        context.bot.send_message(chat_id=ADMIN_IDS[0], text=log[:4096])
    except Exception: pass
# --- Inline-ответы, поддержка поиска и генерации идей прямо в чате ---

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def inline_search(update: Update, context: CallbackContext):
    """Поиск по знаниям ИИ через inline-кнопку."""
    query = update.message.text.partition(' ')[2].strip()
    if not query:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Пример: /inline_search python")
        return
    results = ai.search(query)
    if results:
        keyboard = [
            [InlineKeyboardButton(f"Показать {i+1}", callback_data=f"showres_{i}")]
            for i in range(min(len(results), 5))
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.user_data['inline_results'] = results
        context.bot.send_message(chat_id=update.effective_chat.id, text="Результаты поиска:", reply_markup=reply_markup)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Ничего не найдено.")

def button(update: Update, context: CallbackContext):
    """Обработка inline-кнопок для выдачи результатов поиска."""
    query = update.callback_query
    data = query.data
    if data.startswith("showres_"):
        idx = int(data.split("_")[1])
        results = context.user_data.get('inline_results', [])
        if 0 <= idx < len(results):
            query.answer()
            query.edit_message_text(text=results[idx][:4096])
        else:
            query.answer("Результат не найден.")
    else:
        query.answer()

def idea_gen(update: Update, context: CallbackContext):
    """Генерация нескольких идей ИИ прямо в чате."""
    ideas = ai.auto_generate_ideas(3)
    msg = "\n\n—\n\n".join(ideas)
    send_long_message(context.bot, update.effective_chat.id, msg)

def add_inline_commands(dispatcher):
    dispatcher.add_handler(CommandHandler('inline_search', inline_search))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(CommandHandler('idea_gen', idea_gen))

# После основного main() добавить: add_inline_commands(dispatcher)
# --- Планировщик уведомлений, авторассылка отчётов, ответы на частые вопросы ---

def notify_admins(text):
    """Отправить уведомление всем ADMIN_IDS."""
    for admin_id in ADMIN_IDS:
        try:
            ai_log = f"[ADMIN_NOTIFY] {text}"
            print(ai_log)
            Bot(token=TELEGRAM_TOKEN).send_message(chat_id=admin_id, text=text[:4096])
        except Exception as e:
            print(f"[AdminNotifyError] {e}")

def auto_admin_reports():
    """Автоматически отправляет отчёт админу раз в час."""
    def loop():
        while True:
            try:
                txt = ai.admin_report()
                notify_admins("🦾 Автоотчёт AI:\n" + txt[:3500])
                time.sleep(3600)
            except Exception as e:
                print(f"[AutoAdminReportError] {e}")
                time.sleep(120)
    threading.Thread(target=loop, daemon=True).start()

# --- FAQ-ответы ---

FAQS = {
    "как обучается": "ИИ учится онлайн — парсит статьи, код, тренды, репозитории и файлы 24/7.",
    "кто создал": "Этот ИИ написан специально под твои задачи, всегда дорабатывается!",
    "что умеешь": "Генерация кода, идей, анализ знаний, память, проекты, диагностика, CLI и Telegram интеграция.",
    "как задать вопрос": "Просто напиши сообщение или команду: /help /status /idea /code /search ...",
    "чем отличаешься": "Автоматическая эволюция, память, адаптация, открытость к расширению, интеграция с любыми сервисами."
}

def faq(update: Update, context: CallbackContext):
    q = update.message.text.lower()
    for k, v in FAQS.items():
        if k in q:
            context.bot.send_message(chat_id=update.effective_chat.id, text=v)
            return
    context.bot.send_message(chat_id=update.effective_chat.id, text="Вопрос не распознан. Попробуйте по-другому!")

def faq_commands(dispatcher):
    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), faq))

# Для интеграции: просто вызови faq_commands(dispatcher)
# --- Финальный запуск Telegram-модуля ---

def run_bot():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Основные команды
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', help_cmd))
    dispatcher.add_handler(CommandHandler('status', status))
    dispatcher.add_handler(CommandHandler('idea', idea))
    dispatcher.add_handler(CommandHandler('code', code))
    dispatcher.add_handler(CommandHandler('fact', fact))
    dispatcher.add_handler(CommandHandler('project', project))
    dispatcher.add_handler(CommandHandler('trends', trends))
    dispatcher.add_handler(CommandHandler('skills', skills))
    dispatcher.add_handler(CommandHandler('export', export))
    dispatcher.add_handler(CommandHandler('reflect', reflect))
    dispatcher.add_handler(CommandHandler('admin_report', admin_report))
    dispatcher.add_handler(CommandHandler('feedback', feedback))

    # Расширенные команды
    custom_commands(dispatcher)
    add_inline_commands(dispatcher)
    faq_commands(dispatcher)

    # Обработка ошибок
    dispatcher.add_error_handler(error_handler)

    print("Telegram AI бот запущен. Ожидание сообщений...")

    # Авто-отчёты админу
    auto_admin_reports()

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    run_bot()
