# bot_core.py — Основная логика и меню Aby Khalid VPN
# Все функции доступны через кнопки, без текстовых команд

import os
import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
import config
from bot_utils import add_user, get_user_status, generate_v2ray_config, extend_subscription, record_payment

# Инициализация
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
add_user_callback = add_user  # при первом запуске

# Состояния (для диалогов)
class CoreStates(StatesGroup):
    waiting_feedback = State()
    waiting_gift = State()
    waiting_language = State()
    waiting_theme = State()
    waiting_survey = State()

# Главное меню (reply-клавиатура)
main_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
buttons = [
    "🔐 Конфиг", "💳 Оплатить",
    "📡 Инструкция", "🤝 Пригласить",
    "👤 Профиль", "📞 Поддержка",
    "❓ FAQ", "⚙️ Настройки",
    "🏆 Лидерборд", "🎁 Бонус"
]
main_menu.add(*buttons)

# Inline меню для настроек
settings_menu = types.InlineKeyboardMarkup(row_width=2)
settings_menu.add(
    types.InlineKeyboardButton("🌐 Язык", callback_data="set_language"),
    types.InlineKeyboardButton("🎨 Тема", callback_data="set_theme")
)

# Inline меню для бонусов
bonus_menu = types.InlineKeyboardMarkup().add(
    types.InlineKeyboardButton("🎁 Ежедневный бонус", callback_data="bonus_daily"),
    types.InlineKeyboardButton("🎉 Промокод", callback_data="bonus_promo")
)

# Обработчик стартового нажатия (вместо /start)
@dp.message_handler(lambda m: m.text == "🔐 Конфиг")
async def handle_all_buttons(message: types.Message):
    text = message.text
    uid = message.from_user.id
    # Регистрация нового пользователя при первом обращении
    add_user(uid, message.from_user.username, None)
    # Обработка пунктов меню
    if text == "🔐 Конфиг":
        status = get_user_status(uid)
        if not status['registered']:
            return await message.answer("⛔ Нажмите сначала кнопку Старт")
        if status['expired']:
            return await message.answer("⛔ Доступ истек. Нажмите Оплатить")
        conf = generate_v2ray_config(uid)
        await message.answer(f"Ваш конфиг:\n`{conf}`", parse_mode='Markdown')

    elif text == "💳 Оплатить":
        # перенаправляем на платежный модуль
        await message.answer("Переходим к оплате...")
        await bot.send_message(uid, "Выберите метод оплаты", reply_markup=bonus_menu)

    elif text == "📡 Инструкция":
        await message.answer("📡 Ссылка на инструкцию: https://yourdomain.com/guide")

    elif text == "🤝 Пригласить":
        link = f"https://t.me/{config.BOT_USERNAME}?start={uid}"
        await message.answer(f"Приглашайте друзей: {link}")

    elif text == "👤 Профиль":
        status = get_user_status(uid)
        end = datetime.datetime.fromisoformat(status['trial_end'])
        left = (end - datetime.datetime.utcnow()).days
        await message.answer(f"👤 Профиль:\nОсталось дней: {left}\nПлатный доступ: {status['is_paid']}")

    elif text == "📞 Поддержка":
        await message.answer("📞 @YourSupportBot")

    elif text == "❓ FAQ":
        await message.answer("❓ Часто задаваемые вопросы:\n1. Как подключиться? ...")

    elif text == "⚙️ Настройки":
        await message.answer("⚙️ Выберите настройку:", reply_markup=settings_menu)

    elif text == "🏆 Лидерборд":
        await message.answer("🏆 Топ реферов:\n1. user1 — 10")

    elif text == "🎁 Бонус":
        await message.answer("🎁 Бонусные возможности:", reply_markup=bonus_menu)

# Обработка inline callback
@dp.callback_query_handler(lambda c: c.data.startswith("set_"))
async def callbacks_settings(callback: types.CallbackQuery):
    data = callback.data
    if data == "set_language":
        await callback.message.answer("Выберите язык")
        await CoreStates.waiting_language.set()
    elif data == "set_theme":
        await callback.message.answer("Выберите тему")
        await CoreStates.waiting_theme.set()

# Ежедневный бонус
@dp.callback_query_handler(lambda c: c.data == "bonus_daily")
async def bonus_daily(callback: types.CallbackQuery):
    uid = callback.from_user.id
    extend_subscription(uid, 1)
    record_payment(uid, 'daily_bonus', 0)
    await callback.message.answer("🎁 Бонус +1 день активирован!")

# Промокод
@dp.callback_query_handler(lambda c: c.data == "bonus_promo")
async def bonus_promo(callback: types.CallbackQuery):
    await callback.message.answer("🏷 Введите промокод в чат:")
    await CoreStates.waiting_custom.set()

# Продолжение: обработка States...

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
