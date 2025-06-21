# bot_payments.py — Модуль оплаты через кнопки для Aby Khalid VPN
# Реализация через InlineKeyboard, без текстовых команд

import config
datetime = __import__('datetime')
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from bot_utils import record_payment, extend_subscription, get_payment_history

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)

# FSM состояния оплаты
class PaymentStates(StatesGroup):
    awaiting_check = State()
    awaiting_webapp = State()

# Inline меню оплаты
pay_menu = InlineKeyboardMarkup(row_width=2)
pay_menu.add(
    InlineKeyboardButton("💠 TON", callback_data="pay_ton"),
    InlineKeyboardButton("⭐ Stars", callback_data="pay_stars")
).add(
    InlineKeyboardButton("🇷🇺 SBP/Card", callback_data="pay_check"),
    InlineKeyboardButton("💳 WebApp", web_app=WebAppInfo(url=config.WEBAPP_URL))
)

# Кнопка в главном меню для оплаты
@dp.message_handler(lambda m: m.text == "💳 Оплатить")
async def show_payment_methods(message: types.Message):
    await message.answer("💳 Способы оплаты:", reply_markup=pay_menu)

# Обработка TON
@dp.callback_query_handler(lambda c: c.data == 'pay_ton')
async def pay_ton(callback: types.CallbackQuery):
    uid = callback.from_user.id
    await callback.message.answer(
        f"💠 Переведите {config.SUBSCRIPTION_PRICE_TON} TON на адрес:\n{config.TON_ADDRESS}\nКомментарий: {uid}"
    )
    record_payment(uid, 'ton', config.SUBSCRIPTION_PRICE_TON)

# Обработка Stars
@dp.callback_query_handler(lambda c: c.data == 'pay_stars')
async def pay_stars(callback: types.CallbackQuery):
    uid = callback.from_user.id
    await callback.message.answer("⭐ Оплата через Telegram Stars: нажмите кнопку ниже.")
    stars_kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Open Payment WebApp", web_app=WebAppInfo(url=config.WEBAPP_URL + '/stars'))
    )
    await callback.message.answer("Оплатить Stars", reply_markup=stars_kb)

# Обработка SBP/Card
@dp.callback_query_handler(lambda c: c.data == 'pay_check')
async def pay_check(callback: types.CallbackQuery):
    uid = callback.from_user.id
    await callback.message.answer(
        f"🇷🇺 Переведите {int(config.SUBSCRIPTION_PRICE_RUB)}₽ через SBP или карту {config.BANK_CARD}\n"
        "Затем отправьте чек.",
        reply_markup=None
    )
    await PaymentStates.awaiting_check.set()

# Приём чека
@dp.message_handler(state=PaymentStates.awaiting_check, content_types=['photo', 'document'])
async def receive_check(message: types.Message, state: FSMContext):
    uid = (await state.get_data()).get('user_id', message.from_user.id)
    file_id = message.photo[-1].file_id if message.photo else message.document.file_id
    # Отправить админу чек на подтверждение
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Подтвердить", callback_data=f"check_ok:{uid}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"check_no:{uid}")
    )
    await bot.send_photo(config.ADMIN_ID, file_id, caption=f"Чек от {uid}", reply_markup=kb)
    await message.answer("⏳ Чек отправлен на модерацию.")
    await state.finish()

# Подтверждение чека
@dp.callback_query_handler(lambda c: c.data.startswith('check_ok:'))
async def check_ok(callback: types.CallbackQuery):
    uid = int(callback.data.split(':')[1])
    extend_subscription(uid, config.SUBSCRIPTION_PERIOD_DAYS)
    record_payment(uid, 'check', config.SUBSCRIPTION_PRICE_RUB)
    await bot.send_message(uid, "✅ Оплата подтверждена, доступ продлён.")
    await callback.message.edit_caption("✅ Подтверждено")

@dp.callback_query_handler(lambda c: c.data.startswith('check_no:'))
async def check_no(callback: types.CallbackQuery):
    uid = int(callback.data.split(':')[1])
    await bot.send_message(uid, "❌ Чек отклонён.")
    await callback.message.edit_caption("❌ Отклонено")

# Обработка WebApp callback (PostMessage)
@dp.message_handler(content_types=types.ContentType.WEB_APP_DATA)
async def webapp_handler(message: types.Message):
    data = message.web_app_data.data  # JSON строка
    user_id = message.from_user.id
    extend_subscription(user_id, config.SUBSCRIPTION_PERIOD_DAYS)
    record_payment(user_id, 'webapp', config.SUBSCRIPTION_PRICE_RUB)
    await message.answer("✅ Оплата через WebApp принята, подписка продлена.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
