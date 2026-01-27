import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

# ========== НАСТРОЙКИ ==========
TOKEN = "8423667056:AAFxOF1jkteghG6PSK3vccwuI54xlbPmmjA"  # Основной бот
ADMIN_ID = 7173827114  # Твой ID
DONATE_URL = "https://www.donationalerts.com/r/normiscp"
# ===============================

bot = Bot(token=TOKEN)
dp = Dispatcher()

# База кликов
clicks = []

# ========== КНОПКИ С ЦЕНАМИ ==========
BUTTONS = [
    {"text": "Ролик со мной", "price": "100 рублей", "type": "video_with_me"},
    {"text": "Реклама в ролик", "price": "150 рублей", "type": "ad_in_video"},
    {"text": "Сменить голос на эфире, старик", "price": "25 рублей", "type": "voice_change"},
    {"text": "Просто поддержать", "price": "любая сумма", "type": "support"}
]

def get_buttons_keyboard():
    builder = InlineKeyboardBuilder()
    for btn in BUTTONS:
        builder.button(
            text=f"{btn['text']} ({btn['price']})", 
            url=DONATE_URL,
            callback_data=f"click_{btn['type']}"
        )
    builder.adjust(1)
    return builder.as_markup()

# ========== ОБРАБОТКА КЛИКОВ ==========
@dp.callback_query(F.data.startswith("click_"))
async def track_click(callback: types.CallbackQuery):
    user = callback.from_user
    click_type = callback.data.replace("click_", "")
    
    # Находим кнопку по типу
    button_info = next((btn for btn in BUTTONS if btn["type"] == click_type), None)
    
    if button_info:
        # Записываем клик
        click_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.id,
            "username": f"@{user.username}" if user.username else user.full_name,
            "button_text": button_info["text"],
            "price": button_info["price"],
            "type": click_type
        }
        clicks.append(click_data)
        
        # Логируем
        logging.info(f"Клик: {click_data}")
        
        # Отправляем уведомление админу
        admin_msg = (
            f"🖱️ *НОВЫЙ КЛИК!*\n\n"
            f"👤 Пользователь: {click_data['username']}\n"
            f"🆔 ID: `{user.id}`\n"
            f"📝 Кнопка: {button_info['text']}\n"
            f"💰 Цена: {button_info['price']}\n"
            f"⏰ Время: {click_data['timestamp']}"
        )
        
        try:
            await bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Ошибка отправки админу: {e}")
        
        # Открываем ссылку для пользователя
        await callback.answer(f"Переход по ссылке {button_info['price']}...")
    else:
        await callback.answer("Ошибка!")

# ========== КОМАНДА /START ==========
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = (
        "🎮 *Заказать рекламу/услуги*\n\n"
        "Выберите вариант:\n"
        "• Ролик со мной - 100 рублей за ролик\n"
        "• Реклама в ролик - 150 рублей за ролик\n"
        "• Сменить голос на эфире, старик - 25 рублей\n"
        "• Просто поддержать - любая сумма\n\n"
        "👇 Нажмите на кнопку:"
    )
    
    await message.answer(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=get_buttons_keyboard()
    )

# ========== СТАТИСТИКА ДЛЯ АДМИНА ==========
@dp.message(Command("stats"), F.from_user.id == ADMIN_ID)
async def cmd_stats(message: types.Message):
    if not clicks:
        await message.answer("📭 Еще не было кликов")
        return
    
    total_clicks = len(clicks)
    today = datetime.now().strftime("%Y-%m-%d")
    today_clicks = [c for c in clicks if c['timestamp'].startswith(today)]
    
    # Группируем по типам
    from collections import Counter
    types_counter = Counter([c['type'] for c in clicks])
    
    stats_text = (
        f"📊 *Статистика кликов*\n\n"
        f"Всего кликов: {total_clicks}\n"
        f"Сегодня: {len(today_clicks)}\n\n"
        f"*По типам:*\n"
    )
    
    for btn_type, count in types_counter.most_common():
        btn_info = next((b for b in BUTTONS if b["type"] == btn_type), None)
        if btn_info:
            stats_text += f"• {btn_info['text']}: {count}\n"
    
    # Последние 5 кликов
    stats_text += f"\n*Последние клики:*\n"
    for click in clicks[-5:]:
        time_short = click['timestamp'][11:16]
        stats_text += f"• {click['username']} - {click['button_text']} ({time_short})\n"
    
    await message.answer(stats_text, parse_mode="Markdown")

# ========== СПИСОК ВСЕХ КЛИКОВ ==========
@dp.message(Command("clicks"), F.from_user.id == ADMIN_ID)
async def cmd_clicks(message: types.Message):
    if not clicks:
        await message.answer("📭 Кликов нет")
        return
    
    clicks_text = "📋 *Все клики:*\n\n"
    for i, click in enumerate(clicks[-20:], 1):  # Последние 20
        clicks_text += (
            f"{i}. {click['timestamp']}\n"
            f"   👤 {click['username']} (ID: {click['user_id']})\n"
            f"   📝 {click['button_text']}\n"
            f"   💰 {click['price']}\n\n"
        )
    
    if len(clicks_text) > 4000:
        clicks_text = clicks_text[:4000] + "\n\n... (список обрезан)"
    
    await message.answer(clicks_text, parse_mode="Markdown")

# ========== ОЧИСТКА ==========
@dp.message(Command("clear"), F.from_user.id == ADMIN_ID)
async def cmd_clear(message: types.Message):
    clicks.clear()
    await message.answer("🗑️ База кликов очищена!")

# ========== ЗАПУСК ==========
async def main():
    logging.info("🤖 Бот с отслеживанием кликов запускается...")
    logging.info(f"📊 Всего кнопок: {len(BUTTONS)}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
