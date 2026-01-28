import asyncio, pytz, sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

# --- КОНФИГ (ТВОИ ТОКЕНЫ) ---
TOKEN_MAIN = "8423667056:AAFxOF1jkteghG6PSK3vccwuI54xlbPmmjA" # Бот для клиентов
TOKEN_ORDERS = "8495993622:AAFZMy4dedK8DE0qMD3siNSvulqj78qDyzU" # Бот для админки
MY_ID = 7173827114
DONAT_LINK = "https://www.donationalerts.com"

main_bot = Bot(token=TOKEN_MAIN)
order_bot = Bot(token=TOKEN_ORDERS)
dp = Dispatcher()

class AdminStates(StatesGroup):
    waiting_for_broadcast = State()

# --- КНОПКИ КЛИЕНТА ---
client_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Ролик с рекламой (150 руб)")],
    [KeyboardButton(text="Твой ролик со мной (100 руб)")],
    [KeyboardButton(text="Сменить голос на стриме, старик (25 руб)")],
    [KeyboardButton(text="Просто поддержать")]
], resize_keyboard=True)

# --- КНОПКИ АДМИНА ---
admin_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="📈 Статистика")],
    [KeyboardButton(text="⚙️ Управление")]
], resize_keyboard=True)

settings_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="✅ Включить продажи"), KeyboardButton(text="❌ Выключить продажи")],
    [KeyboardButton(text="📢 Сделать рассылку")],
    [KeyboardButton(text="⬅️ Назад")]
], resize_keyboard=True)

# --- БАЗА ДАННЫХ ---
conn = sqlite3.connect('shop.db', check_same_thread=False)
cur = conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS settings (name TEXT PRIMARY KEY, value INTEGER)')
cur.execute('INSERT OR IGNORE INTO settings VALUES ("total_orders", 0), ("active", 1)')
conn.commit()

# --- ЛОГИКА АДМИНСКОГО БОТА ---
@dp.message(F.bot.token == TOKEN_ORDERS)
async def admin_handler(m: types.Message, state: FSMContext):
    if m.from_user.id != MY_ID: return
    
    # Если мы в режиме рассылки
    if await state.get_state() == AdminStates.waiting_for_broadcast:
        cur.execute('SELECT id, username FROM users'); users = cur.fetchall()
        success, errors = [], []
        await m.answer(f"⏳ Рассылка на {len(users)} чел. пошла...")
        
        for uid, unm in users:
            try:
                if m.photo: await main_bot.send_photo(uid, m.photo[-1].file_id, caption=m.caption)
                else: await main_bot.send_message(uid, m.text)
                success.append(f"✅ @{unm or 'скрыт'} ({uid})")
                await asyncio.sleep(0.05)
            except: errors.append(f"❌ @{unm or 'скрыт'} ({uid})")
        
        report = f"📋 ОТЧЕТ:\n\n🟢 УСПЕШНО: {len(success)}\n🔴 ОШИБКИ: {len(errors)}\n\n" + "\n".join(success[:50])
        for i in range(0, len(report), 4000): await order_bot.send_message(MY_ID, report[i:i+4000])
        await state.clear()
        return await m.answer("✅ Рассылка завершена!", reply_markup=admin_kb)

    # Обычные команды админа
    if m.text in ["/start", "⬅️ Назад"]:
        await m.answer("🛠 Админка активирована", reply_markup=admin_kb)
    elif m.text == "📈 Статистика":
        cur.execute('SELECT COUNT(*) FROM users'); u = cur.fetchone()[0]
        cur.execute('SELECT value FROM settings WHERE name="total_orders"'); o = cur.fetchone()[0]
        await m.answer(f"📊 Статистика:\n👤 Юзеров: {u}\n📦 Заказов: {o}")
    elif m.text == "⚙️ Управление":
        await m.answer("Настройки:", reply_markup=settings_kb)
    elif m.text == "✅ Включить продажи":
        cur.execute('UPDATE settings SET value = 1 WHERE name="active"'); conn.commit()
        await m.answer("✅ Продажи включены")
    elif m.text == "❌ Выключить продажи":
        cur.execute('UPDATE settings SET value = 0 WHERE name="active"'); conn.commit()
        await m.answer("❌ Продажи закрыты")
    elif m.text == "📢 Сделать рассылку":
        await m.answer("Пришли текст или фото — оно уйдет всем!"); await state.set_state(AdminStates.waiting_for_broadcast)

# --- ЛОГИКА КЛИЕНТСКОГО БОТА ---
@dp.message(F.bot.token == TOKEN_MAIN)
async def client_handler(m: types.Message):
    cur.execute('SELECT value FROM settings WHERE name="active"'); active = cur.fetchone()[0]
    if m.text == "/start":
        cur.execute('INSERT OR REPLACE INTO users VALUES (?, ?)', (m.from_user.id, m.from_user.username)); conn.commit()
        await m.answer("Привет! Это бот с реквизитами Нормиса, выбирай:", reply_markup=client_kb)
    elif any(x in (m.text or "") for x in ["руб", "поддержать"]):
        if active == 0: return await m.answer("❌ Продажи временно закрыты.")
        cur.execute('UPDATE settings SET value = value + 1 WHERE name="total_orders"'); conn.commit()
        await m.answer(f"Оплачивай тут: {DONAT_LINK}\nПосле оплаты я свяжусь с тобой!")
        await order_bot.send_message(MY_ID, f"🎁 ЗАКАЗ: {m.text}\nЮзер: @{m.from_user.username or 'нет'}")

async def main():
    await dp.start_polling(main_bot, order_bot)

if __name__ == "__main__":
    asyncio.run(main())
