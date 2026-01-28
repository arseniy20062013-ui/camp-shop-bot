cd ~ && rm -rf camp-shop-bot && \
git clone https://github.com/arseniy20062013-ui/camp-shop-bot && \
cd camp-shop-bot && \
cat <<EOF > main.py
import asyncio, pytz, sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime

TOKEN_MAIN = "8423667056:AAFxOF1jkteghG6PSK3vccwuI54xlbPmmjA"
TOKEN_ORDERS = "8495993622:AAFZMy4dedK8DE0qMD3siNSvulqj78qDyzU"
MY_ID = 7173827114
DONAT_LINK = "https://www.donationalerts.com"

main_bot, order_bot = Bot(token=TOKEN_MAIN), Bot(token=TOKEN_ORDERS)
dp = Dispatcher()

client_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Ролик с рекламой (150 руб)")],
    [KeyboardButton(text="Твой ролик со мной (100 руб)")],
    [KeyboardButton(text="Сменить голос на стриме, старик (25 руб)")]
], resize_keyboard=True)

admin_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="📈 Статистика")], [KeyboardButton(text="⚙️ Управление")]
], resize_keyboard=True)

conn = sqlite3.connect('shop.db')
cur = conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)')
cur.execute('CREATE TABLE IF NOT EXISTS settings (name TEXT, value INTEGER)')
cur.execute('INSERT OR IGNORE INTO settings VALUES ("total_orders", 0)')
conn.commit()

@dp.message(F.bot.token == TOKEN_MAIN)
async def client_handler(m: types.Message):
    if m.text == "/start":
        cur.execute('INSERT OR IGNORE INTO users VALUES (?)', (m.from_user.id,))
        conn.commit()
        await m.answer("Выбери товар:", reply_markup=client_kb)
    elif "руб" in m.text:
        cur.execute('UPDATE settings SET value = value + 1 WHERE name="total_orders"')
        conn.commit()
        nsk = datetime.now(pytz.timezone('Asia/Novosibirsk')).strftime('%H:%M:%S')
        await order_bot.send_message(MY_ID, f"🎁 ЗАКАЗ: {m.text}\nЮзер: @{m.from_user.username}\nВремя: {nsk}")
        await m.answer(f"Оплачивай тут: {DONAT_LINK}")

@dp.message(F.bot.token == TOKEN_ORDERS)
async def admin_handler(m: types.Message):
    if m.from_user.id != MY_ID: return
    if m.text == "/start":
        await m.answer("Админка включена", reply_markup=admin_kb)
    elif m.text == "📈 Статистика":
        cur.execute('SELECT COUNT(*) FROM users'); u = cur.fetchone()[0]
        cur.execute('SELECT value FROM settings WHERE name="total_orders"'); o = cur.fetchone()[0]
        await m.answer(f"Юзеров: {u}\nЗаказов: {o}")

async def main():
    await dp.start_polling(main_bot, order_bot)

if __name__ == "__main__":
    asyncio.run(main())
EOF
pkill -9 python; screen -dmS shop_bot python3 main.py && echo "🚀 ВСЁ ГОТОВО! Проверяй ботов."
