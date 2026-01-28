import asyncio, pytz, sqlite3
from aiogram import Bot, Dispatcher, types, F
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

class AdminStates(StatesGroup):
    waiting_for_broadcast = State()

# --- КЛАВИАТУРЫ ---
client_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Ролик с рекламой (150 руб)")],
    [KeyboardButton(text="Твой ролик со мной (100 руб)")],
    [KeyboardButton(text="Сменить голос на стриме, старик (25 руб)")]
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

# --- БАЗА ДАННЫХ ---
conn = sqlite3.connect('shop.db')
cur = conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS settings (name TEXT PRIMARY KEY, value INTEGER)')
cur.execute('INSERT OR IGNORE INTO settings VALUES ("total_orders", 0), ("active", 1)')
conn.commit()

# --- ЛОГИКА КЛИЕНТСКОГО БОТА ---
@dp.message(F.bot.token == TOKEN_MAIN)
async def client_handler(m: types.Message):
    cur.execute('SELECT value FROM settings WHERE name="active"'); res = cur.fetchone()
    active = res[0] if res else 1
    
    if m.text == "/start":
        cur.execute('INSERT OR REPLACE INTO users (id, username) VALUES (?, ?)', (m.from_user.id, m.from_user.username))
        conn.commit()
        await m.answer("Привет! Это бот с реквизитами Нормиса, выбирай:", reply_markup=client_kb)
    elif any(x in m.text for x in ["руб", "поддержать"]):
        if active == 0: return await m.answer("❌ Прием заказов временно приостановлен.")
        cur.execute('UPDATE settings SET value = value + 1 WHERE name="total_orders"'); conn.commit()
        nsk = datetime.now(pytz.timezone('Asia/Novosibirsk')).strftime('%H:%M:%S')
        await m.answer(f"Оплачивай тут: {DONAT_LINK}\nПосле оплаты я свяжусь с тобой!")
        await order_bot.send_message(MY_ID, f"🎁 ЗАКАЗ: {m.text}\nЮзер: @{m.from_user.username or 'нет'}\nID: {m.from_user.id}\nВремя: {nsk}")

# --- ЛОГИКА АДМИНСКОГО БОТА ---
@dp.message(F.bot.token == TOKEN_ORDERS)
async def admin_handler(m: types.Message, state: FSMContext):
    if m.from_user.id != MY_ID: return
    if m.text in ["/start", "⬅️ Назад"]:
        await m.answer("🛠 Панель админа активирована", reply_markup=admin_kb)
    elif m.text == "📈 Статистика":
        cur.execute('SELECT COUNT(*) FROM users'); u = cur.fetchone()[0]
        cur.execute('SELECT value FROM settings WHERE name="total_orders"'); o = cur.fetchone()[0]
        await m.answer(f"📊 Статистика:\n👤 Пользователей: {u}\n📦 Заказов: {o}")
    elif m.text == "⚙️ Управление":
        await m.answer("Настройки:", reply_markup=settings_kb)
    elif m.text == "✅ Включить продажи":
        cur.execute('UPDATE settings SET value = 1 WHERE name="active"'); conn.commit()
        await m.answer("✅ Продажи включены!")
    elif m.text == "❌ Выключить продажи":
        cur.execute('UPDATE settings SET value = 0 WHERE name="active"'); conn.commit()
        await m.answer("❌ Продажи закрыты!")
    elif m.text == "📢 Сделать рассылку":
        await m.answer("Отправь текст или ФОТО с описанием для рассылки:")
        await state.set_state(AdminStates.waiting_for_broadcast)

@dp.message(AdminStates.waiting_for_broadcast)
async def process_broadcast(m: types.Message, state: FSMContext):
    cur.execute('SELECT id, username FROM users'); users = cur.fetchall()
    success, errors = [], []
    await m.answer(f"⏳ Рассылка пошла (всего {len(users)} чел.)...")

    for uid, unm in users:
        try:
            if m.photo:
                await main_bot.send_photo(uid, m.photo[-1].file_id, caption=m.caption)
            else:
                await main_bot.send_message(uid, m.text)
            success.append(f"✅ @{unm or 'no_nick'} ({uid})")
            await asyncio.sleep(0.05)
        except Exception as e:
            errors.append(f"❌ @{unm or 'no_nick'} ({uid}) - {type(e).__name__}")

    report = f"📋 ОТЧЕТ [{datetime.now().strftime('%d.%m %H:%M')}]\n\n"
    report += "🟢 ДОСТАВЛЕНО:\n" + ("\n".join(success) if success else "Пусто") + "\n\n"
    report += "🔴 ОШИБКИ:\n" + ("\n".join(errors) if errors else "Нет")
    
    for i in range(0, len(report), 4000):
        await order_bot.send_message(MY_ID, report[i:i+4000])
    await state.clear()

async def main():
    await dp.start_polling(main_bot, order_bot)

if __name__ == "__main__":
    asyncio.run(main())
