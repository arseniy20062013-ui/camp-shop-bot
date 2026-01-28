import asyncio, pytz, sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

# --- КОНФИГ ---
TOKEN_MAIN = "8423667056:AAFxOF1jkteghG6PSK3vccwuI54xlbPmmjA"
TOKEN_ORDERS = "8495993622:AAFZMy4dedK8DE0qMD3siNSvulqj78qDyzU"
MY_ID = 7173827114
DONAT_LINK = "https://www.donationalerts.com/r/normiscp"

main_bot = Bot(token=TOKEN_MAIN)
order_bot = Bot(token=TOKEN_ORDERS)
dp = Dispatcher()

class AdminStates(StatesGroup):
    waiting_for_broadcast = State()

# --- КНОПКИ ---
client_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Ролик с рекламой (150 руб)")],
    [KeyboardButton(text="Твой ролик со мной (100 руб)")],
    [KeyboardButton(text="Сменить голос на стриме, старик (25 руб)")],
    [KeyboardButton(text="Просто поддержать")]
], resize_keyboard=True)

admin_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="📈 Статистика")], [KeyboardButton(text="⚙️ Управление")]
], resize_keyboard=True)

settings_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="✅ Включить продажи"), KeyboardButton(text="❌ Выключить продажи")],
    [KeyboardButton(text="📢 Сделать рассылку")], [KeyboardButton(text="⬅️ Назад")]
], resize_keyboard=True)

# --- БД ---
conn = sqlite3.connect('shop.db', check_same_thread=False)
cur = conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS settings (name TEXT PRIMARY KEY, value INTEGER)')
cur.execute('INSERT OR IGNORE INTO settings VALUES ("total_orders", 0), ("active", 1)')
conn.commit()

# --- АДМИНКА ---
@dp.message(F.bot.token == TOKEN_ORDERS)
async def admin_handler(m: types.Message, state: FSMContext):
    if m.from_user.id != MY_ID: return
    if await state.get_state() == AdminStates.waiting_for_broadcast:
        cur.execute('SELECT id, username FROM users'); users = cur.fetchall()
        success, errors = [], []
        await m.answer(f"⏳ Рассылка на {len(users)} чел. запущена...")
        for uid, unm in users:
            try:
                if m.photo: await main_bot.send_photo(uid, m.photo[-1].file_id, caption=m.caption)
                else: await main_bot.send_message(uid, m.text)
                success.append(f"✅ @{unm or 'no_nick'} ({uid})")
                await asyncio.sleep(0.05)
            except: errors.append(f"❌ @{unm or 'no_nick'} ({uid})")
        report = f"📋 ОТЧЕТ:\n\n🟢 УСПЕШНО: {len(success)}\n🔴 ОШИБКИ: {len(errors)}\n\n" + "\n".join(success[:50])
        for i in range(0, len(report), 4000): await order_bot.send_message(MY_ID, report[i:i+4000])
        await state.clear(); return await m.answer("✅ Готово!", reply_markup=admin_kb)
    if m.text in ["/start", "⬅️ Назад"]: await m.answer("🛠 Админка Нормиса", reply_markup=admin_kb)
    elif m.text == "📈 Статистика":
        cur.execute('SELECT COUNT(*) FROM users'); u = cur.fetchone(); cur.execute('SELECT value FROM settings WHERE name="total_orders"'); o = cur.fetchone()
        await m.answer(f"📊 Статистика:\n👤 Юзеров: {u[0]}\n📦 Заказов: {o[0]}")
    elif m.text == "⚙️ Управление": await m.answer("Настройки:", reply_markup=settings_kb)
    elif m.text == "📢 Сделать рассылку": await m.answer("Пришли пост для рассылки!"); await state.set_state(AdminStates.waiting_for_broadcast)
    elif "Включить" in m.text: cur.execute('UPDATE settings SET value = 1 WHERE name="active"'); conn.commit(); await m.answer("✅ Включено")
    elif "Выключить" in m.text: cur.execute('UPDATE settings SET value = 0 WHERE name="active"'); conn.commit(); await m.answer("❌ Выключено")

# --- КЛИЕНТ ---
@dp.message(F.bot.token == TOKEN_MAIN)
async def client_handler(m: types.Message):
    cur.execute('SELECT value FROM settings WHERE name="active"'); active = cur.fetchone()[0]
    if m.text == "/start":
        cur.execute('INSERT OR REPLACE INTO users VALUES (?, ?)', (m.from_user.id, m.from_user.username)); conn.commit()
        await m.answer("Привет! Это бот с реквизитами Нормиса, выбирай:", reply_markup=client_kb)
    elif any(x in (m.text or "") for x in ["руб", "поддержать"]):
        if not active: return await m.answer("❌ Прием заказов временно приостановлен.")
        cur.execute('UPDATE settings SET value = value + 1 WHERE name="total_orders"'); conn.commit()
        # ТЕКСТ ОБНОВЛЕН (УБРАНО "СВЯЖУСЬ С ТОБОЙ")
        await m.answer(f"Оплачивай тут: {DONAT_LINK}")
        await order_bot.send_message(MY_ID, f"🎁 ЗАКАЗ: {m.text}\nЮзер: @{m.from_user.username or 'нет'}")

async def main(): await dp.start_polling(main_bot, order_bot)
if __name__ == "__main__": asyncio.run(main())

