import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

# НАСТРОЙКИ
TOKEN = "8423667056:AAFxOF1jkteghG6PSK3vccwuI54xlbPmmjA"
ADMIN_ID = 7173827114
DONATE_URL = "https://www.donationalerts.com/r/normiscp"

bot = Bot(token=TOKEN)
dp = Dispatcher()
clicks = []

# КНОПКИ
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

# КЛАВИАТУРА С КНОПКОЙ ВЫХОДА
def get_back_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад в меню", callback_data="back_to_menu")
    return builder.as_markup()

# ОТСЛЕЖИВАНИЕ КЛИКОВ
@dp.callback_query(F.data.startswith("click_"))
async def track_click(callback: types.CallbackQuery):
    user = callback.from_user
    click_type = callback.data.replace("click_", "")
    
    button_info = next((btn for btn in BUTTONS if btn["type"] == click_type), None)
    
    if button_info:
        click_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": user.id,
            "username": f"@{user.username}" if user.username else user.full_name,
            "button_text": button_info["text"],
            "price": button_info["price"],
            "type": click_type
        }
        clicks.append(click_data)
        
        # Уведомление админу ВСЕГДА
        admin_msg = (
            f"🖱️ НОВЫЙ КЛИК!\n\n"
            f"👤 Пользователь: {click_data['username']}\n"
            f"🆔 ID: {user.id}\n"
            f"📝 Кнопка: {button_info['text']}\n"
            f"💰 Цена: {button_info['price']}\n"
            f"⏰ Время: {click_data['timestamp']}"
        )
        
        try:
            await bot.send_message(ADMIN_ID, admin_msg)
            logging.info(f"Отправлено админу: {click_data}")
        except Exception as e:
            logging.error(f"Ошибка отправки админу: {e}")
        
        await callback.answer(f"Переход: {button_info['price']}")
    else:
        await callback.answer("Ошибка!")

# КОМАНДА /START
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    
    if user_id == ADMIN_ID:
        # АДМИН МЕНЮ
        builder = InlineKeyboardBuilder()
        builder.button(text="📊 Статистика", callback_data="stats")
        builder.button(text="📋 Список кликов", callback_data="list_clicks")
        builder.button(text="🧹 Очистить", callback_data="clear_clicks")
        builder.adjust(2)
        
        await message.answer("👑 Админ-панель:", reply_markup=builder.as_markup())
    else:
        # ОБЫЧНОЕ МЕНЮ
        welcome_text = (
            "Заказать рекламу/услуги\n\n"
            "Выберите вариант:\n"
            "• Ролик со мной - 100 рублей за ролик\n"
            "• Реклама в ролик - 150 рублей за ролик\n"
            "• Сменить голос на эфире, старик - 25 рублей\n"
            "• Просто поддержать - любая сумма\n\n"
            "👇 Нажмите на кнопку:"
        )
        
        await message.answer(welcome_text, reply_markup=get_buttons_keyboard())

# СТАТИСТИКА
@dp.callback_query(F.data == "stats")
async def show_stats(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа!")
        return
    
    if not clicks:
        text = "📭 Еще не было кликов"
    else:
        total = len(clicks)
        today = datetime.now().strftime("%Y-%m-%d")
        today_clicks = [c for c in clicks if c['timestamp'].startswith(today)]
        
        text = (
            f"📊 Статистика кликов\n\n"
            f"Всего кликов: {total}\n"
            f"Сегодня: {len(today_clicks)}\n\n"
            f"Последние 5 кликов:\n"
        )
        
        for click in clicks[-5:]:
            time_short = click['timestamp'][11:16]
            text += f"• {click['username']} - {click['button_text']} ({time_short})\n"
    
    await callback.message.edit_text(text, reply_markup=get_back_keyboard())
    await callback.answer()

# СПИСОК ВСЕХ КЛИКОВ
@dp.callback_query(F.data == "list_clicks")
async def show_all_clicks(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа!")
        return
    
    if not clicks:
        text = "📭 Кликов нет"
    else:
        text = "📋 Все клики:\n\n"
        for i, click in enumerate(clicks[-20:], 1):  # Последние 20
            time_short = click['timestamp'][11:19]
            text += f"{i}. {time_short} - {click['username']} - {click['button_text']} ({click['price']})\n"
    
    if len(text) > 4000:
        text = text[:4000] + "\n\n... (список обрезан)"
    
    await callback.message.edit_text(text, reply_markup=get_back_keyboard())
    await callback.answer()

# ОЧИСТКА
@dp.callback_query(F.data == "clear_clicks")
async def clear_all_clicks(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа!")
        return
    
    clicks.clear()
    await callback.message.edit_text("🗑️ Все клики удалены!", reply_markup=get_back_keyboard())
    await callback.answer()

# КНОПКА НАЗАД
@dp.callback_query(F.data == "back_to_menu")
async def back_to_main_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id == ADMIN_ID:
        builder = InlineKeyboardBuilder()
        builder.button(text="📊 Статистика", callback_data="stats")
        builder.button(text="📋 Список кликов", callback_data="list_clicks")
        builder.button(text="🧹 Очистить", callback_data="clear_clicks")
        builder.adjust(2)
        
        await callback.message.edit_text("👑 Админ-панель:", reply_markup=builder.as_markup())
    else:
        welcome_text = (
            "Заказать рекламу/услуги\n\n"
            "Выберите вариант:\n"
            "• Ролик со мной - 100 рублей за ролик\n"
            "• Реклама в ролик - 150 рублей за ролик\n"
            "• Сменить голос на эфире, старик - 25 рублей\n"
            "• Просто поддержать - любая сумма\n\n"
            "👇 Нажмите на кнопку:"
        )
        
        await callback.message.edit_text(welcome_text, reply_markup=get_buttons_keyboard())
    
    await callback.answer()

# ЗАПУСК
async def main():
    logging.info("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
