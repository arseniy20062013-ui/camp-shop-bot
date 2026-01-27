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
        # Мы убрали url из кнопки, чтобы бот мог поймать сигнал (callback_data)
        builder.button(
            text=f"{btn['text']} ({btn['price']})", 
            callback_data=f"buy_{btn['type']}"
        )
    builder.adjust(1)
    return builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("👇 Выберите услугу для покупки:", reply_markup=get_keyboard())

@dp.callback_query(F.data.startswith("buy_"))
async def handle_buy(callback: types.CallbackQuery):
    click_type = callback.data.replace("buy_", "")
    item = next((btn for btn in BUTTONS if btn["type"] == click_type), None)
    
    if item:
        user = callback.from_user
        username = f"@{user.username}" if user.username else f"ID: {user.id}"
        
        # 1. ОТПРАВЛЯЕМ УВЕДОМЛЕНИЕ ТЕБЕ (АДМИНУ)
        admin_report = (
            f"💰 **НОВЫЙ ЗАКАЗ!**\n\n"
            f"👤 Клиент: {username}\n"
            f"📦 Товар: {item['text']}\n"
            f"💸 Цена: {item['price']}"
        )
        await bot.send_message(ADMIN_ID, admin_report, parse_mode="Markdown")
        
        # 2. ОТПРАВЛЯЕМ ССЫЛКУ ПОЛЬЗОВАТЕЛЮ В ОТВЕТ
        await callback.message.answer(
            f"✅ Заказ принят! Чтобы оплатить **{item['text']}**, перейдите по ссылке:\n"
            f"{DONATE_URL}\n\n"
            "Админ получил сигнал и свяжется с вами после оплаты."
        )
        await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
