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
cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)')
cur.execute('CREATE TABLE IF NOT EXISTS settings (name TEXT PRIMARY KEY, value INTEGER)')
cur.execute('INSERT OR IGNORE INTO settings VALUES ("total_orders", 0), ("active", 1)')
conn.commit()

# --- ЛОГИКА КЛИЕНТА (ОСНОВНОЙ БОТ) ---
@dp.message(F.bot.token == TOKEN_MAIN)
async def client_handler(m: types.Message):
    cur.execute('SELECT value FROM settings WHERE name="active"')
    is_active = cur.fetchone()[0]
    
    if m.text == "/start":
        cur.execute('INSERT OR IGNORE INTO users VALUES (?)', (m.from_user.id,))
        conn.commit()
        await m.answer("Привет! Это бот с реквизитами Нормиса, выбирай:", reply_markup=client_kb)
    
    elif "руб" in m.text:
        if not is_active:
            return await m.answer("Прием заказов временно приостановлен.")
        
        cur.execute('UPDATE settings SET value = value + 1 WHERE name="total_orders"')
        conn.commit()
        
        nsk = datetime.now(pytz.timezone('Asia/Novosibirsk')).strftime('%H:%M:%S %d.%m.%Y')
        info = f"🎁 НОВЫЙ ЗАКАЗ!\n🛒 Товар: {m.text}\n👤 Юзер: @{m.from_user.username or 'скрыт'}\n🆔 ID: {m.from_user.id}\n⏰ Время: {nsk}"
        
        await m.answer(f"Для оплаты перейдите по ссылке:\n{DONAT_LINK}\n\nПосле оплаты я свяжусь с тобой!")
        await order_bot.send_message(MY_ID, info)

# --- ЛОГИКА АДМИНА (БОТ ЗАКАЗОВ) ---
@dp.message(F.bot.token == TOKEN_ORDERS)
async def admin_handler(m: types.Message, state: FSMContext):
    if m.from_user.id != MY_ID: return
    
    if m.text == "/start" or m.text == "⬅️ Назад":
        await m.answer("Панель админа активирована. Выберите действие:", reply_markup=admin_kb)
    
    elif m.text == "📈 Статистика":
        cur.execute('SELECT COUNT(*) FROM users'); u = cur.fetchone()[0]
        cur.execute('SELECT value FROM settings WHERE name="total_orders"'); o = cur.fetchone()[0]
        await m.answer(f"📊 Статистика:\n👤 Юзеров: {u}\n📦 Заказов: {o}")
    
    elif m.text == "⚙️ Управление":
        await m.answer("Настройки магазина:", reply_markup=settings_kb)
    
    elif m.text == "✅ Включить продажи":
        cur.execute('UPDATE settings SET value = 1 WHERE name="active"'); conn.commit()
        await m.answer("✅ Продажи включены! Пользователи могут делать заказы.")
    
    elif m.text == "❌ Выключить продажи":
        cur.execute('UPDATE settings SET value = 0 WHERE name="active"'); conn.commit()
        await m.answer("❌ Продажи выключены! Пользователи увидят уведомление о паузе.")
    
    elif m.text == "📢 Сделать рассылку":
        await m.answer("Введите текст сообщения для рассылки (или напишите 'Отмена'):")
        await state.set_state(AdminStates.waiting_for_broadcast)

@dp.message(AdminStates.waiting_for_broadcast)
async def process_broadcast(m: types.Message, state: FSMContext):
    if m.text.lower() == "отмена":
        await state.clear()
        return await m.answer("Рассылка отменена.", reply_markup=admin_kb)
    
    cur.execute('SELECT id FROM users'); users = cur.fetchall()
    count = 0
    for u in users:
        try:
            await main_bot.send_message(u[0], m.text)
            count += 1
            await asyncio.sleep(0.05)
        except: pass
    
    await m.answer(f"📢 Рассылка завершена!\n✅ Отправлено: {count} пользователям.", reply_markup=admin_kb)
    await state.clear()

async def main():
    print("Бот запущен...")
    await dp.start_polling(main_bot, order_bot)

if __name__ == "__main__":
    asyncio.run(main())
