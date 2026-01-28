import asyncio, pytz, sqlite3
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

TOKEN_MAIN = "8423667056:AAFxOF1jkteghG6PSK3vccwuI54xlbPmmjA"
TOKEN_ORDERS = "8495993622:AAFZMy4dedK8DE0qMD3siNSvulqj78qDyzU"
MY_ID = 7173827114
DONAT_LINK = "https://www.donationalerts.com"

main_bot = Bot(token=TOKEN_MAIN)
order_bot = Bot(token=TOKEN_ORDERS)
dp = Dispatcher()

# --- КЛАВИАТУРА КЛИЕНТА (ДЛЯ ОСНОВНОГО БОТА) ---
client_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Ролик с рекламой (150 руб)")],
    [KeyboardButton(text="Твой ролик со мной (100 руб)")],
    [KeyboardButton(text="Сменить голос на стриме, старик (25 руб)")],
    [KeyboardButton(text="Просто поддержать")]
], resize_keyboard=True)

# --- КЛАВИАТУРА АДМИНА (ДЛЯ БОТА ЗАКАЗОВ) ---
admin_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="📈 Статистика")],
    [KeyboardButton(text="📢 Рассылка")],
    [KeyboardButton(text="⚙️ Управление")]
], resize_keyboard=True)

conn = sqlite3.connect('shop.db')
cur = conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)')
cur.execute('CREATE TABLE IF NOT EXISTS settings (name TEXT, value INTEGER)')
cur.execute('INSERT OR IGNORE INTO settings VALUES ("sales_active", 1)')
cur.execute('INSERT OR IGNORE INTO settings VALUES ("total_orders", 0)')
conn.commit()

# --- ОБРАБОТКА ОСНОВНОГО БОТА ---
@dp.message(F.bot.token == TOKEN_MAIN)
async def main_logic(m: types.Message):
    if m.text == "/start":
        cur.execute('INSERT OR IGNORE INTO users VALUES (?)', (m.from_user.id,))
        conn.commit()
        return await m.answer("Привет! Выбери товар:", reply_markup=client_kb)
    
    btns = ["Ролик с рекламой (150 руб)", "Твой ролик со мной (100 руб)", "Сменить голос на стриме, старик (25 руб)", "Просто поддержать"]
    if m.text in btns:
        cur.execute('UPDATE settings SET value = value + 1 WHERE name="total_orders"')
        conn.commit()
        nsk = datetime.now(pytz.timezone('Asia/Novosibirsk')).strftime('%H:%M:%S %d.%m.%Y')
        info = f"🎁 ЗАКАЗ!\n👤 Юзер: @{m.from_user.username or 'нет'}\n🛒 {m.text}\n⏰ {nsk}"
        await m.answer(f"Оплата тут: {DONAT_LINK}")
        await order_bot.send_message(MY_ID, info)

# --- ОБРАБОТКА БОТА ЗАКАЗОВ (АДМИНКА) ---
@dp.message(F.bot.token == TOKEN_ORDERS)
async def admin_logic(m: types.Message):
    if m.from_user.id != MY_ID: return
    
    if m.text == "/start":
        await m.answer("Панель админа активирована", reply_markup=admin_kb)
    
    elif m.text == "📈 Статистика":
        cur.execute('SELECT COUNT(*) FROM users')
        u_count = cur.fetchone()[0]
        cur.execute('SELECT value FROM settings WHERE name="total_orders"')
        o_count = cur.fetchone()[0]
        await m.answer(f"👤 Юзеров: {u_count}\n📦 Заказов: {o_count}")

async def main():
    await dp.start_polling(main_bot, order_bot)

if __name__ == "__main__":
    asyncio.run(main())
