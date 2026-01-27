import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ========== НАСТРОЙКИ ==========
TOKEN = "8423667056:AAFxOF1jkteghG6PSK3vccwuI54xlbPmmjA"  # Твой бот
ADMIN_ID = 7173827114  # Твой ID
DONATE_URL = "https://www.donationalerts.com/r/normiscp"
# ===============================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ========== КНОПКИ РЕКЛАМЫ ==========
def get_ad_keyboard():
    builder = InlineKeyboardBuilder()
    
    # Кнопки с ссылками на донат
    builder.button(
        text="Реклама в видео (100 руб)", 
        url=DONATE_URL
    )
    builder.button(
        text="Ролик со мной (150 руб)", 
        url=DONATE_URL
    )
    builder.button(
        text="Сменить голос на эфире (25 руб)", 
        url=DONATE_URL
    )
    builder.button(
        text="Просто поддержать", 
        url=DONATE_URL
    )
    
    builder.button(
        text="Статистика", 
        callback_data="stats"
    )
    
    builder.adjust(1)  # По одной кнопке в ряд
    return builder.as_markup()

# ========== КОМАНДА /START ==========
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = (
        "🎮 *Донат-бот для стримов*\n\n"
        "💰 *Тарифы:*\n"
        "• 🎬 Реклама в видео — 100 руб/ролик\n"
        "• 🎥 Ролик со мной — 150 руб/ролик\n"
        "• 🎤 Сменить голос на эфире — 25 руб\n"
        "• 💖 Просто поддержать — любая сумма\n\n"
        "👇 Выберите вариант:"
    )
    
    await message.answer(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=get_ad_keyboard()
    )

# ========== СТАТИСТИКА ДЛЯ АДМИНА ==========
donations = []  # Здесь будут храниться донаты

@dp.callback_query(F.data == "stats")
async def show_stats(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Только для админа! ❌", show_alert=True)
        return
    
    total = len(donations)
    today = datetime.now().strftime("%Y-%m-%d")
    today_count = len([d for d in donations if d['date'].startswith(today)])
    
    stats_text = (
        f"📊 *Статистика донатов:*\n\n"
        f"Всего донатов: {total}\n"
        f"Сегодня: {today_count}\n\n"
        f"*Последние 5:*\n"
    )
    
    if donations:
        for i, d in enumerate(donations[-5:], 1):
            stats_text += f"{i}. {d['user']} - {d['type']} - {d['date'][11:16]}\n"
    else:
        stats_text += "Пока нет донатов"
    
    await callback.message.edit_text(
        stats_text,
        parse_mode="Markdown",
        reply_markup=get_ad_keyboard()
    )
    await callback.answer()

# ========== ОБРАБОТКА СООБЩЕНИЙ ==========
@dp.message(F.text)
async def handle_text(message: types.Message):
    # Если админ пишет "донат [юзер] [тип]"
    if message.from_user.id == ADMIN_ID and message.text.startswith("донат "):
        try:
            _, username, donation_type = message.text.split(" ", 2)
            donations.append({
                "user": username,
                "type": donation_type,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            await message.answer(f"✅ Донат от {username} ({donation_type}) записан!")
        except:
            await message.answer("Формат: донат @username тип_доната")
    
    # Для всех остальных - показываем меню
    else:
        await cmd_start(message)

# ========== ЗАПУСК ==========
async def main():
    logger.info("Бот с донатами запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

