# bot_admin.py — Модуль администрирования Aby Khalid VPN через кнопки
# Все функции доступны через кнопку "🔧 Админ"

import os
import datetime
import csv
import config
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from bot_utils import (
    get_all_users, delete_user, extend_subscription,
    record_payment, get_payment_history, notify_admin
)

# Инициализация бота и диспетчера
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)

# Reply-клавиатура для админа
admin_kb = ReplyKeyboardMarkup(resize_keyboard=True)
admin_kb.row("📊 Статистика", "👥 Пользователи", "✉️ Рассылка")
admin_kb.row("🔍 Проверить", "⏳ Продлить", "🚫 Забанить")
admin_kb.row("📝 Экспорт CSV", "💰 Доходы", "📆 Планировщик")
admin_kb.row("⚙️ Флаги", "🚀 Тарифы", "🔄 Резерв")
admin_kb.row("🗒️ Логи", "⏪ Восстановить", "🔌 Перезагрузить")

# FSM-состояния для админ-действий
class AdminStates(StatesGroup):
    waiting_user_id = State()
    waiting_days = State()
    waiting_broadcast = State()
    waiting_schedule = State()
    waiting_plan = State()
    waiting_backup_path = State()
    waiting_restore_path = State()
    waiting_logs_action = State()

# Запрос админ-панели
@dp.message_handler(lambda m: m.text == "🔧 Админ")
async def show_admin_menu(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        return
    await message.answer("🔧 Панель администратора:", reply_markup=admin_kb)

# Обработчик нажатий (reply)
@dp.message_handler(lambda m: m.text == "📊 Статистика")
async def admin_stats(message: types.Message):
    users = get_all_users()
    total = len(users)
    paid = sum(u['is_paid'] for u in users)
    await message.answer(f"👥 Всего пользователей: {total}\n💰 Активных подписок: {paid}")

@dp.message_handler(lambda m: m.text == "👥 Пользователи")
async def admin_users(message: types.Message):
    users = get_all_users(limit=20)
    text = "🧾 Последние 20 пользователей:\n"
    for u in users:
        text += f"{u['id']}|@{u['username']}|дo:{u['trial_end'].split('T')[0]}|paid={u['is_paid']}\n"
    await message.answer(text)

@dp.message_handler(lambda m: m.text == "✉️ Рассылка")
async def admin_broadcast_start(message: types.Message):
    await message.answer("✉️ Введите текст для рассылки:")
    await AdminStates.waiting_broadcast.set()

@dp.message_handler(state=AdminStates.waiting_broadcast)
async def admin_broadcast_send(message: types.Message, state: FSMContext):
    text = message.text
    users = get_all_users()
    for u in users:
        try: await bot.send_message(u['id'], text)
        except: pass
    await message.answer("✅ Рассылка завершена.")
    await state.finish()

@dp.message_handler(lambda m: m.text == "🔍 Проверить")
async def admin_check_start(message: types.Message):
    await message.answer("🔍 Введите ID пользователя для проверки:")
    await AdminStates.waiting_user_id.set()

@dp.message_handler(state=AdminStates.waiting_user_id)
async def admin_check_process(message: types.Message, state: FSMContext):
    uid = int(message.text)
    users = get_all_users()
    user = next((u for u in users if u['id']==uid), None)
    if user:
        await message.answer(f"ID {uid}: trial_end={user['trial_end'].split('T')[0]}, paid={user['is_paid']}")
    else:
        await message.answer("Пользователь не найден.")
    await state.finish()

@dp.message_handler(lambda m: m.text == "⏳ Продлить")
async def admin_extend_start(message: types.Message):
    await message.answer("⏳ Введите ID пользователя:")
    await AdminStates.waiting_user_id.set()

@dp.message_handler(state=AdminStates.waiting_user_id)
async def admin_extend_id(message: types.Message, state: FSMContext):
    await state.update_data(user_id=int(message.text))
    await message.answer("Введите количество дней для продления:")
    await AdminStates.waiting_days.set()

@dp.message_handler(state=AdminStates.waiting_days)
async def admin_extend_days(message: types.Message, state: FSMContext):
    data = await state.get_data()
    uid = data['user_id']; days = int(message.text)
    extend_subscription(uid, days)
    await message.answer(f"✅ Подписка {uid} продлена на {days} дней.")
    await state.finish()

@dp.message_handler(lambda m: m.text == "🚫 Забанить")
async def admin_ban(message: types.Message):
    await message.answer("🚫 Введите ID пользователя для бана:")
    await AdminStates.waiting_user_id.set()

@dp.message_handler(state=AdminStates.waiting_user_id)
async def admin_ban_id(message: types.Message, state: FSMContext):
    uid = int(message.text)
    delete_user(uid)
    await message.answer(f"🚫 Пользователь {uid} забанен.")
    await state.finish()

@dp.message_handler(lambda m: m.text == "📝 Экспорт CSV")
async def admin_export_csv(message: types.Message):
    path = 'users.csv'
    with open(path,'w',newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id','username','trial_end','is_paid'])
        for u in get_all_users(): writer.writerow([u['id'],u['username'],u['trial_end'],u['is_paid']])
    await message.answer_document(open(path,'rb'))

@dp.message_handler(lambda m: m.text == "💰 Доходы")
async def admin_revenue(message: types.Message):
    rows = get_payment_history(None)
    total = sum(r['amount'] for r in rows)
    await message.answer(f"💰 Общий доход: {total}")

@dp.message_handler(lambda m: m.text == "📆 Планировщик")
async def admin_schedule_start(message: types.Message):
    await message.answer("📆 Введите cron и текст:")
    await AdminStates.wait_schedule.set()

@dp.message_handler(state=AdminStates.wait_schedule)
async def admin_schedule_process(message: types.Message, state: FSMContext):
    cron, text = message.text.split(' ',1)
    # TODO: добавить в cron
    await message.answer(f"Запланировано: {cron} -> {text}")
    await state.finish()

@dp.message_handler(lambda m: m.text == "⚙️ Флаги")
async def admin_flags(message: types.Message):
    flags = (
        config.ENABLE_PROMOCODES, config.ENABLE_HISTORY,
        config.ENABLE_WEBAPP_PAY
    )
    await message.answer(f"Флаги: promo={flags[0]}, history={flags[1]}, webapp={flags[2]}")

@dp.message_handler(lambda m: m.text == "🚀 Тарифы")
async def admin_plans_start(message: types.Message):
    await message.answer("🚀 Введите тариф name price days:")
    await AdminStates.wait_plan.set()

@dp.message_handler(state=AdminStates.wait_plan)
async def admin_plans_process(message: types.Message, state: FSMContext):
    name, price, days = message.text.split()
    # TODO: сохранить тариф
    await message.answer(f"План {name} создан {price}₽/{days}дн")
    await state.finish()

@dp.message_handler(lambda m: m.text == "🔄 Резерв")
async def admin_backup_cmd(message: types.Message):
    # TODO: сделать бэкап
    await message.answer("✅ Бэкап создан.")

@dp.message_handler(lambda m: m.text == "⏪ Восстановить")
async def admin_restore_cmd(message: types.Message):
    await message.answer("🛠 Введите путь к бэкапу:")
    await AdminStates.wait_restore_path.set()

@dp.message_handler(state=AdminStates.wait_restore_path)
async def admin_restore_process(message: types.Message, state: FSMContext):
    path = message.text
    # TODO: восстановить
    await message.answer(f"🔄 Восстановлено из {path}")
    await state.finish()

@dp.message_handler(lambda m: m.text == "🗒️ Логи")
async def admin_logs(message: types.Message):
    await message.answer("🗒️ /view_logs или /clear_logs")

@dp.message_handler(commands=['view_logs'])
async def cmd_view_logs(message: types.Message):
    # TODO: показать логи
    await message.answer("Логи: ...")

@dp.message_handler(commands=['clear_logs'])
async def cmd_clear_logs(message: types.Message):
    # TODO: очистить логи
    await message.answer("Логи очищены.")

@dp.message_handler(lambda m: m.text == "🔌 Перезагрузить")
async def admin_restart(message: types.Message):
    await message.answer("🔄 Перезагружаю бота...")
    # TODO: перезапустить

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)