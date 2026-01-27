import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- КОНФИГУРАЦИЯ ---
# ОСНОВНОЙ БОТ (Где люди жмут кнопки)
TOKEN_SHOP = "8423667056:AAFxOF1jkteghG6PSK3vccwuI54xlbPmmjA"
# БОТ-ЛОГГЕР (Куда приходят уведомления о заказах)
TOKEN_LOGS = "8495993622:AAFZMy4dedK8DE0qMD3siNSvulqj78qDyzU"
ADMIN_ID = 7173827114
DONATE_URL = "https://www.donationalerts.com"
# ---------------------

bot_shop = Bot(token=TOKEN_SHOP)
bot_logs = Bot(token=TOKEN_LOGS)
dp = Dispatcher()

BUTTONS =

def get_keyboard():
    builder = InlineKeyboardBuilder()
    for btn in BUTTONS:
        builder.button(text=f"{btn} ({btn['price']})", callback_data=f"buy_{btn['type']}")
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
        
        # ОТПРАВЛЯЕМ ЗАКАЗ ВО ВТОРОГО БОТА (LOGS)
        try:
            await bot_logs.send_message(
                ADMIN_ID, 
                f"💰 **НОВЫЙ ЗАКАЗ!**\n👤 Клиент: {username}\n📦 Товар: {item}\n💸 Цена: {item['price']}"
            )
        except Exception as e:
            print(f"Ошибка уведомления: {e}")
        
        # ОТВЕТ В ОСНОВНОМ БОТЕ
        await callback.message.answer(f"✅ Заказ на '{item}' принят!\n🔗 Оплата тут: {DONATE_URL}")
        await callback.answer()

async def main():
    await dp.start_polling(bot_shop)

if __name__ == "__main__":
    asyncio.run(main())
