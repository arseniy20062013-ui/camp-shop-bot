import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

# ========== ВАШИ ТОКЕНЫ ==========
TOKEN_MAIN = "8423667056:AAFxOF1jkteghG6PSK3vccwuI54xlbPmmjA"  # Основной бот с реквизитами
ADMIN_ID = 7173827114  # Ваш ID для уведомлений
DONATE_URL = "https://www.donationalerts.com/r/normiscp"

bot_main = Bot(token=TOKEN_MAIN)
dp_main = Dispatcher()

# База кликов (только в памяти, без записи в файл)
clicks = []

# ========== КНОПКИ БЕЗ СТИКЕРОВ ==========
BUTTONS = [
    {"text": "Ролик со мной", "price": "100 рублей за ролик", "type": "video_with_me"},
    {"text": "Реклама в ролик", "price": "150 рублей за ролик", "type": "ad_in_video"},
    {"text": "Сменить голос на эфире, старик", "price": "25 рублей", "type": "voice_change"},
    {"text": "Просто поддержать", "price": "любая сумма", "type": "support"}
]

def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    for btn in BUTTONS:
        builder.button(
            text=f"{btn['text']} ({btn['price']})", 
            url=DONATE_URL,
            callback_data=f"click_{btn['type']}"
        )
    builder.adjust(1)  # Все кнопки в один столбец
    return builder.as_markup()

# ========== КОМАНДА /START ==========
@dp_main.message(Command("start"))
async def cmd_start_main(message: types.Message):
    welcome = (
        "Заказать рекламу/услуги:\n\n"
        "• Ролик со мной - 100 рублей за ролик\n"
        "• Реклама в ролик - 150 рублей за ролик\n"
        "• Сменить голос на эфире, старик - 25 рублей\n"
        "• Просто поддержать - любая сумма\n\n"
        "👇 Выберите вариант:"
    )
    await message.answer(welcome, reply_markup=get_main_keyboard())

# ========== ОТСЛЕЖИВАНИЕ КЛИКОВ ==========
@dp_main.callback_query(F.data.startswith("click_"))
async def track_click(callback: types.CallbackQuery):
    user = callback.from_user
    click_type = callback.data.replace("click_", "")
    
    button_info = next((btn for btn in BUTTONS if btn["type"] == click_type), None)
    
    if button_info:
        # Только в памяти, без логов
        click_data = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "user_id": user.id,
            "username": f"@{user.username}" if user.username else user.full_name,
            "button_text": button_info["text"],
            "price": button_info["price"]
        }
        clicks.append(click_data)
        
        # МГНОВЕННОЕ УВЕДОМЛЕНИЕ ТЕБЕ (без try/except, пусть падает если нет сети)
        admin_msg = (
            f"🖱️ Клик\n"
            f"От: {click_data['username']}\n"
            f"ID: {user.id}\n"
            f"Кнопка: {button_info['text']}\n"
            f"Цена: {button_info['price']}\n"
            f"Время: {click_data['timestamp']}"
        )
        
        await bot_main.send_message(ADMIN_ID, admin_msg)
        await callback.answer(f"Открываю: {button_info['price']}")

# ========== ЗАПУСК ==========
async def main():
    print(f"🤖 Бот реквизитов запущен (ID: {ADMIN_ID})")
    print(f"📊 Кнопок: {len(BUTTONS)}")
    print(f"🔗 Ссылка: {DONATE_URL}")
    await dp_main.start_polling(bot_main)

if __name__ == "__main__":
    asyncio.run(main())
