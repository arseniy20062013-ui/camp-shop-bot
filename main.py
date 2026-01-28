import asyncio, pytz, sqlite3
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

# --- НАСТРОЙКИ ---
TOKEN_MAIN = "8423667056:AAFxOF1jkteghG6PSK3vccwuI54xlbPmmjA"
TOKEN_ORDERS = "8495993622:AAFZMy4dedK8DE0qMD3siNSvulqj78qDyzU"
MY_ID = 7173827114
DONAT_LINK = "https://www.donationalerts.com"

main_bot = Bot(token=TOKEN_MAIN)
order_bot = Bot(token=TOKEN_ORDERS)
dp = Dispatcher()
router = Router()

class BroadcastState(StatesGroup):
    waiting_for_message = State()

# --- БАЗА ДАННЫХ ---
conn = sqlite3.connect('shop.db')
cur = conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)')
cur.execute('CREATE TABLE IF NOT EXISTS settings (name TEXT, value INTEGER)')
cur.execute('INSERT OR IGNORE INTO settings VALUES ("sales_active", 1)')
cur.execute('INSERT OR IGNORE INTO settings VALUES ("total_orders", 0)')
conn.commit()

# --- КЛАВИАТУРЫ (ИСПРАВЛЕНО) ---
kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Ролик с рекламой (150 руб)")],
    [KeyboardButton(text="Твой ролик со мной (100 руб)")],
    [KeyboardButton(text="Сменить голос на стриме, старик (25 руб)")],
    [KeyboardButton(text="Просто поддержать")]
], resize_keyboard=True)

admin_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Статистика")],
    [KeyboardButton(text="Рассылка")]
], resize_keyboard=True)

cancel_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Отмена")]
], resize_keyboard=True)

# --- ЛОГИКА АДМИНКИ (ЧЕРЕЗ ВТОРОГО БОТА) ---
@router.message(F.text == "/start")
async def start_admin(m: types.Message):
    if m.from_user.id == MY_ID:
        await m.answer("Панель управления активирована", reply_markup=admin_kb)

@router.message(F.text == "Статистика")
async def get_stats(m: types.Message):
    if m.from_user.id == MY_ID:
        cur.execute('SELECT COUNT(*) FROM users')
        u_count = cur.fetchone()[0]
        cur.execute('SELECT value FROM settings WHERE name="total_orders"')
        o_count = cur.fetchone()[0]
        await m.answer(f"👤 Пользователей: {u_count}\n📦 Заказов: {o_count}")

@router.message(F.text == "Рассылка")
async def start_broadcast(m: types.Message, state: FSMContext):
    if m.from_user.id == MY_ID:
        await m.answer("Напишите сообщение для рассылки:", reply_markup=cancel_kb)
        await state.set_state(BroadcastState.waiting_for_message)

@router.message(F.text == "Отмена")
async def cancel_broadcast(m: types.Message, state: FSMContext):
    await state.clear()
    await m.answer("Отменено.", reply_markup=admin_kb)

@router.message(BroadcastState.waiting_for_message)
async def send_broadcast_message(m: types.Message, state: FSMContext):
    if m.from_user.id == MY_ID:
        cur.execute('SELECT id FROM users')
        users = cur.fetchall()
        count = 0
        for u in users:
            try:
                await main_bot.send_message(u[0], m.text)
                count += 1
                await asyncio.sleep(0.05) # Защита от спам-фильтра
            except: pass
        await m.answer(f"✅ Готово! Получили: {count} чел.", reply_markup=admin_kb)
        await state.clear()

# --- ЛОГИКА КЛИЕНТА (ГЛАВНЫЙ БОТ) ---
@dp.message(F.text == "/start")
async def start_main(m: types.Message):
    cur.execute('INSERT OR IGNORE INTO users VALUES (?)', (m.from_user.id,))
    conn.commit()
    await m.answer("Привет! Выбери нужную услугу:", reply_markup=kb)

@dp.message()
async def handle_order(m: types.Message):
    btns = ["Ролик с рекламой (150 руб)", "Твой ролик со мной (100 руб)", "Сменить голос на стриме, старик (25 руб)", "Просто поддержать"]
    if m.text in btns:
        cur.execute('UPDATE settings SET value = value + 1 WHERE name="total_orders"')
        conn.commit()
        
        nsk = datetime.now(pytz.timezone('Asia/Novosibirsk')).strftime('%H:%M:%S %d.%m.%Y')
        info = f"🎁 НОВЫЙ ЗАКАЗ!\n\n👤 Юзер: @{m.from_user.username or 'скрыт'}\n🆔 ID: {m.from_user.id}\n🛒 Товар: {m.text}\n⏰ Время: {nsk}"
        
        await m.answer(f"Для оплаты перейдите по ссылке:\n{DONAT_LINK}\n\nПосле оплаты я свяжусь с тобой!")
        await order_bot.send_message(MY_ID, info)

async def main():
    dp.include_router(router)
    # Запуск обоих ботов одновременно
    await dp.start_polling(main_bot, order_bot)

if __name__ == "__main__":
    asyncio.run(main())
