import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ОСНОВНОЙ БОТ (где кнопки для людей)
TOKEN_MAIN = "8423667056:AAFxOF1jkteghG6PSK3vccwuI54xlbPmmjA"
# БОТ ДЛЯ ЗАКАЗОВ (куда придут уведомления)
TOKEN_ORDERS = "8495993622:AAFZMy4dedK8DE0qMD3siNSvulqj78qDyzU"
# ТВОЙ ID
ADMIN_ID = 7173827114
DONATE_URL = "https://www.donationalerts.com"

bot_main = Bot(token=TOKEN_MAIN)
bot_orders = Bot(token=TOKEN_ORDERS)
dp = Dispatcher()

BUTTONS = [
    {"text": "Ролик со мной", "price": "100 руб", "type": "video_with_me"},
    {"text": "Реклама в ролик", "price": "150 руб", "type": "ad_in_video"},
    {"text": "Сменить голос", "price": "25 руб", "type": "voice_change"},
    {"text": "Просто поддержать", "price": "любая сумма", "type": "support"}
]

def get_keyboard():
    builder = InlineKeyboardBuilder()
    for btn in BUTTONS:
        builder.button(text=f"{btn['text']} ({btn['price']})", callback_data=f"buy_{btn['type']}")
    builder.adjust(1)
    return builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("🛒 **Магазин услуг**\nВыберите товар:", reply_markup=get_keyboard())

@dp.callback_query(F.data.startswith("buy_"))
async def handle_buy(callback: types.CallbackQuery):
    item_type = callback.data.replace("buy_", "")
    item = next((btn for btn in BUTTONS if btn["type"] == item_type), None)
    
    if item:
        user = callback.from_user
        username = f"@{user.username}" if user.username else f"ID: {user.id}"
        
        # ОТПРАВЛЯЕМ В БОТА ДЛЯ ЗАКАЗОВ
        try:
            await bot_orders.send_message(
                ADMIN_ID, 
                f"💰 **НОВЫЙ ЗАКАЗ!**\n👤 От: {username}\n📦 Товар: {item['text']}\n💸 Цена: {item['price']}"
            )
        except Exception as e:
            print(f"Ошибка отправки в бот-заказы: {e}")
        
        # ОТВЕТ ПОЛЬЗОВАТЕЛЮ В ОСНОВНОМ БОТЕ
        await callback.message.answer(f"✅ Для оплаты **{item['text']}** перейди по ссылке:\n{DONATE_URL}")
        await callback.answer()

async def main():
    await dp.start_polling(bot_main)

if __name__ == "__main__":
    asyncio.run(main())
