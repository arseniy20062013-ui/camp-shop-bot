import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# ================= КОНФИГ =================
TOKEN_REKVIZITI = "8423667056:AAFxOF1jkteghG6PSK3vccwuI54xlbPmmjA"
TOKEN_CONTROL = "8495993622:AAFZMy4dedK8DE0qMD3siNSvulqj78qDyzU"
ADMIN_ID = 7173827114
DONATION_LINK = "https://www.donationalerts.com/r/normiscp"

# ================= БАЗА ДАННЫХ =================
def init_db():
    conn = sqlite3.connect('stats.db')
    cursor = conn.cursor()
    # Таблица пользователей (для уникального трафика)
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
    # Таблица заказов (статистика нажатий на товары)
    cursor.execute('CREATE TABLE IF NOT EXISTS orders (item_name TEXT, count INTEGER DEFAULT 0)')
    
    # Обновленный список товаров
    items = [
        "Ролик с рекламой (150 руб)", 
        "Просто поддержать"
    ]
    for item in items:
        cursor.execute('INSERT OR IGNORE INTO orders (item_name, count) VALUES (?, 0)', (item,))
    
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect('stats.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def log_order(item_name):
    conn = sqlite3.connect('stats.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE orders SET count = count + 1 WHERE item_name = ?', (item_name,))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect('stats.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    cursor.execute('SELECT item_name, count FROM orders')
    orders = cursor.fetchall()
    conn.close()
    return total_users, orders

# ================= ИНИЦИАЛИЗАЦИЯ =================
init_db()
sales_active = True # По умолчанию продажи включены

bot_rekv = Bot(token=TOKEN_REKVIZITI)
bot_ctrl = Bot(token=TOKEN_CONTROL)
dp_rekv = Dispatcher()
dp_ctrl = Dispatcher()

# ================= КЛАВИАТУРЫ =================
def get_main_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="Ролик с рекламой (150 руб)"))
    builder.row(types.KeyboardButton(text="Просто поддержать"))
    return builder.as_markup(resize_keyboard=True)

def get_admin_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="📊 Статистика трафика"))
    status_text = "🔴 Выключить продажи" if sales_active else "🟢 Включить продажи"
    builder.row(types.KeyboardButton(text=status_text))
    return builder.as_markup(resize_keyboard=True)

# ================= ЛОГИКА: БОТ РЕКВИЗИТОВ =================
@dp_rekv.message(Command("start"))
async def rekv_start(message: types.Message):
    add_user(message.from_user.id)
    await message.answer(
        "Привет! Это бот с реквизитами Нормиса, выбирай:\n\n"
        "⚠️ **ВАЖНО: При оплате обязательно указывай свой тег (username) в Telegram, чтобы я мог с тобой связаться!**", 
        reply_markup=get_main_kb(),
        parse_mode="Markdown"
    )

@dp_rekv.message()
async def handle_orders(message: types.Message):
    global sales_active
    
    # Обновленный список товаров
    items = [
        "Ролик с рекламой (150 руб)", 
        "Просто поддержать"
    ]
    
    # Если юзер написал что-то левое, игнорируем
    if message.text not in items:
        return

    # Проверка включены ли продажи
    if not sales_active:
        await message.answer("❌ Прием заказов временно приостановлен.")
        return
    
    # Логируем нажатие в статистику
    log_order(message.text)
    
    # Собираем инфу о юзере для уведомления
    user = message.from_user
    username = f"@{user.username}" if user.username else "Скрыт/Нет юзернейма"
    
    # Отправляем уведомление в БОТ УПРАВЛЕНИЯ админу
    info = (
        f"🛒 **Новое нажатие!**\n"
        f"👤 Юзер: {username} (ID: `{user.id}`)\n"
        f"📦 Выбрано: **{message.text}**"
    )
    try:
        await bot_ctrl.send_message(ADMIN_ID, info, parse_mode="Markdown")
    except Exception as e:
        print(f"Не удалось отправить уведомление админу: {e}")
    
    # Отвечаем юзеру ссылкой на оплату
    await message.answer(
        f"Оплачивай тут: {DONATION_LINK}\n\nВыбранная услуга: {message.text}",
        disable_web_page_preview=False
    )

# ================= ЛОГИКА: БОТ УПРАВЛЕНИЯ =================
@dp_ctrl.message(Command("start"))
async def ctrl_start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(
            "Панель управления доступом и трафиком:", 
            reply_markup=get_admin_kb()
        )

@dp_ctrl.message(F.text == "📊 Статистика трафика")
async def show_stats(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        total_users, orders = get_stats()
        msg = f"📈 **Онлайн Трафик:**\n\nВсего уникальных людей заходило: **{total_users}**\n\n**Запросы по кнопкам:**\n"
        for name, count in orders:
            # Скрываем старые товары из статы, если они остались в базе, чтобы не мозолили глаза
            if name in ["Ролик с рекламой (150 руб)", "Просто поддержать"]:
                msg += f"▪️ {name}: {count} раз(а)\n"
        await message.answer(msg, parse_mode="Markdown")

@dp_ctrl.message(F.text.in_(["🔴 Выключить продажи", "🟢 Включить продажи"]))
async def toggle_logic(message: types.Message):
    global sales_active
    if message.from_user.id == ADMIN_ID:
        # Инвертируем состояние
        sales_active = not sales_active
        status = "ВЫКЛЮЧЕНЫ 🔴" if not sales_active else "ВКЛЮЧЕНЫ 🟢"
        
        # Обновляем клавиатуру с новой кнопкой
        await message.answer(f"Продажи теперь {status}", reply_markup=get_admin_kb())

# ================= ЗАПУСК =================
async def main():
    print("Боты успешно запущены...")
    await asyncio.gather(
        dp_rekv.start_polling(bot_rekv), 
        dp_ctrl.start_polling(bot_ctrl)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Боты выключены вручную.")
