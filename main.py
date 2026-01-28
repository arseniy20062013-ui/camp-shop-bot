import asyncio, pytz, sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

# --- ДАННЫЕ ---
TOKEN_MAIN = "8423667056:AAFxOF1jkteghG6PSK3vccwuI54xlbPmmjA"
TOKEN_ORDERS = "8495993622:AAFZMy4dedK8DE0qMD3siNSvulqj78qDyzU"
MY_ID = 7173827114
DONAT_LINK = "https://www.donationalerts.com"

main_bot = Bot(token=TOKEN_MAIN)
order_bot = Bot(token=TOKEN_ORDERS)
dp = Dispatcher()

class AdminStates(StatesGroup):
    waiting_for_broadcast = State()

# --- КЛАВИАТУРЫ ---
client_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Ролик с рекламой (150 руб)")],
    [KeyboardButton(text="Твой ролик со мной (100 руб)")],
    [KeyboardButton(text="Сменить голос на стриме, старик (25 руб)")],
    [KeyboardButton(text="Просто поддержать")]
], resize_keyboard=True)

admin_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="📈 Статистика")],
    [KeyboardButton(text="⚙️ Управление")]
], resize_keyboard=True)

settings_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="✅ Включить продажи"), KeyboardButton(text="❌ Выключить продажи")],
    [KeyboardButton(text="📢 Сделать рассылку")],
    [KeyboardButton(text="⬅️ Назад")]
], resize_keyboard=True)

# --- БД ---
conn = sqlite3.connect('shop.db')
cur = conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS settings (name TEXT PRIMARY KEY, value INTEGER)')
cur.execute('INSERT OR IGNORE INTO settings VALUES ("total_orders", 0), ("active", 1)')
conn.commit()

# --- ОБРАБОТКА АДМИНСКОГО БОТА (TOKEN_ORDERS) ---
@dp.message(F.bot.token == TOKEN_ORDERS)
async def admin_main(m: types.Message, state: FSMContext):
    if m.from_user.id != MY_ID: return
    
    current_state = await state.get_state()
    if current_state == AdminStates.waiting_for_broadcast:
        users_cur = conn.execute('SELECT id, username FROM users').fetchall()
        success, errors = [], []
        await m.answer(f"⏳ Рассылка на {len(users_cur)} чел...")
        
        for uid, unm in users_cur:
            try:
                if m.photo:
                    await main_bot.send_photo(uid, m.photo[-1].file_id, caption=m.caption)
                else:
                    await main_bot.send_message(uid, m.text)
                success.append(f"✅ @{unm or 'no_nick'} ({uid})")
            except Exception as e:
                errors.append(f"❌ @{unm or 'no_nick'} ({uid}) - {type(e).__name__}")
        
        report = f"📋 ОТЧЕТ:\n\n🟢 УСПЕШНО:\n" + "\n".join(success) + "\n\n🔴 ОШИБКИ:\n" + "\n".join(errors)
        for i in range(0, len(report), 4000):
            await order_bot.send_message(MY_ID, report[i:i+4000])
        await state.clear()
        return await m.answer("✅ Готово!", reply_markup=admin_kb)

    if m.text in ["/start", "⬅️ Назад"]:
        await m.answer("🛠 Админка Нормиса", reply_markup=admin_kb)
    elif m.text == "📈 Статистика":
        u = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        o = conn.execute('SELECT value FROM settings WHERE name="total_orders"').fetchone()[0]
        await m.answer(f"📊 Юзеров: {u}\n📦 Заказов: {o}")
    elif m.text == "⚙️ Управление":
        await m.answer("Настройки:", reply_markup=settings_kb)
    elif m.text == "✅ Включить продажи":
        conn.execute('UPDATE settings SET value = 1 WHERE name="active"'); conn.commit()
        await m.answer("✅ Включено")
    elif m.text == "❌ Выключить продажи":
        conn.execute('UPDATE settings SET value = 0 WHERE name="active"'); conn.commit()
        await m.answer("❌ Выключено")
    elif m.text == "📢 Сделать рассылку":
        await m.answer("Пришли текст или фото:")
        await state.set_state(AdminStates.waiting_for_broadcast)

# --- ОБРАБОТКА КЛИЕНТСКОГО БОТА (TOKEN_MAIN) ---
@dp.message(F.bot.token == TOKEN_MAIN)
async def client_main(m: types.Message):
    active = conn.execute('SELECT value FROM settings WHERE name="active"').fetchone()[0]
    if m.text == "/start":
        conn.execute('INSERT OR REPLACE INTO users VALUES (?, ?)', (m.from_user.id, m.from_user.username)); conn.commit()
        await m.answer("Привет! Это бот с реквизитами Нормиса, выбирай:", reply_markup=client_kb)
    elif any(x in (m.text or "") for x in ["руб", "поддержать"]):
        if not active: return await m.answer("❌ Продажи закрыты")
        conn.execute('UPDATE settings SET value = value + 1 WHERE name="total_orders"'); conn.commit()
        await m.answer(f"Оплачивай тут: {DONAT_LINK}")
        await order_bot.send_message(MY_ID, f"🎁 ЗАКАЗ: {m.text}\nЮзер: @{m.from_user.username}")

async def main():
    await dp.start_polling(main_bot, order_bot)

if __name__ == "__main__":
    asyncio.run(main())
