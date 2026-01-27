import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8423667056:AAFxOF1jkteghG6PSK3vccwuI54xlbPmmjA"
ADMIN_ID = 7173827114
DONATE_URL = "https://www.donationalerts.com"

bot = Bot(token=TOKEN)
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
        # Важно: только callback_data, чтобы сработал сигнал!
        builder.button(
            text=f"{btn['text']} ({btn['price']})", 
            callback_data=f"order_{btn['type']}"
        )
    builder.adjust(1)
    return builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("🛒 **Магазин услуг**\nВыберите нужный пункт:", reply_markup=get_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("order_"))
async def handle_order(callback: types.CallbackQuery):
    order_type = callback.data.replace("order_", "")
    item = next((btn for btn in BUTTONS if btn["type"] == order_type), None)
    
    if item:
        user = callback.from_user
        username = f"@{user.username}" if user.username else f"ID: {user.id}"
        
        # 1. ОТПРАВЛЯЕМ СИГНАЛ ТЕБЕ (АДМИНУ)
        admin_msg = (
            f"🔔 **НОВЫЙ ЗАКАЗ!**\n"
            f"👤 Клиент: {username}\n"
            f"📦 Товар: {item['text']}\n"
            f"💰 Цена: {item['price']}"
        )
        await bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
        
        # 2. ОТПРАВЛЯЕМ ССЫЛКУ ПОЛЬЗОВАТЕЛЮ
        user_msg = (
            f"✅ Вы выбрали: **{item['text']}**\n\n"
            f"🔗 Для оплаты перейдите по ссылке:\n{DONATE_URL}\n\n"
            "После оплаты я (админ) свяжусь с вами!"
        )
        await callback.message.answer(user_msg, parse_mode="Markdown")
        
        # Убираем "часики" на кнопке
        await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
