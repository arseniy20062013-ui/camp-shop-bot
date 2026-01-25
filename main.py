import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

logging.basicConfig(level=logging.INFO)

API_TOKEN = '8423588142:AAG18DOaJzwixZZyDiTJInu0dKBTV20u3lQ'
ADMIN_ID = 7173827114  # Твой ID

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Статус работы магазина
store_active = True

# Проверка на админа
def is_admin(message: types.Message):
    return message.from_user.id == ADMIN_ID

# 1. Админ-панель (Пульт)
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if not is_admin(message):
        return
    
    status = "РАБОТАЕТ" if store_active else "ЗАКРЫТ"
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Вкл/Выкл магазин", callback_data="toggle_store"))
    
    await message.answer(f"🛠 **Пульт управления**\nТекущий статус: {status}", reply_markup=builder.as_markup())

# Переключение статуса
@dp.callback_query(F.data == "toggle_store")
async def toggle_store(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("Нет доступа!", show_alert=True)
    
    global store_active
    store_active = not store_active
    status = "РАБОТАЕТ" if store_active else "ЗАКРЫТ"
    
    await callback.message.edit_text(f"🛠 **Пульт управления**\nТекущий статус: {status}", 
                                     reply_markup=callback.message.reply_markup)
    await callback.answer(f"Магазин {status}")

# 2. Стартовое сообщение
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔹 Каталог", callback_data="show_catalog"))
    await message.answer("Привет! Это Десяточка — магазин в лагере!", reply_markup=builder.as_markup())

# 3. Вывод каталога
@dp.callback_query(F.data == "show_catalog")
async def show_catalog(callback: types.CallbackQuery):
    if not store_active:
        return await callback.message.answer("ОЙ! Наш магазин закрыт до лета!")
        
    catalog_text = (
        "**Каталог товаров:**\n\n"
        "*1. Соль* (1-3 купона)\n*2. Хлеб* (3 купона)\n"
        "*3. Вода* (3 купона)\n*4. Сок* (2 купона)"
    )
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Заказать", callback_data="open_menu"))
    await callback.message.answer(catalog_text, parse_mode="Markdown", reply_markup=builder.as_markup())
    await callback.answer()

# 4. Меню выбора
@dp.callback_query(F.data == "open_menu")
async def choose_item(callback: types.CallbackQuery):
    builder = ReplyKeyboardBuilder()
    items = ["Соль (М) — 1", "Соль (С) — 2", "Соль (Б) — 3", "Хлеб — 3", "Вода — 3", "Сок — 2"]
    for item in items:
        builder.add(types.KeyboardButton(text=item))
    builder.adjust(2)
    await callback.message.answer("Что вы хотите заказать?", reply_markup=builder.as_markup(resize_keyboard=True))
    await callback.answer()

# 5. Прием заказа и отправка админу
@dp.message(F.text.contains("—"))
async def process_order(message: types.Message):
    # Отправляем подтверждение пользователю
    await message.answer("Ваш заказ обрабатывается... Ждите лета! 🌲", reply_markup=types.ReplyKeyboardRemove())
    
    # ОТПРАВКА ЗАКАЗА ТЕБЕ (АДМИНУ)
    order_info = (
        f"🔔 **НОВЫЙ ЗАКАЗ!**\n\n"
        f"👤 От: @{message.from_user.username or 'без юзернейма'}\n"
        f"🆔 ID: `{message.from_user.id}`\n"
        f"📦 Товар: {message.text}"
    )
    await bot.send_message(ADMIN_ID, order_info, parse_mode="Markdown")

# Запуск с авто-перезагрузкой
async def main():
    while True:
        try:
            print("Бот 'Десяточка' в сети!")
            await dp.start_polling(bot, skip_updates=True)
        except Exception as e:
            logging.error(f"Ошибка: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
