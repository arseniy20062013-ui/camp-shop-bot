import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# Настройка логирования, чтобы видеть ошибки в консоли
logging.basicConfig(level=logging.INFO)

API_TOKEN = '8423588142:AAG18DOaJzwixZZyDiTJInu0dKBTV20u3lQ'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 1. Стартовое сообщение
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔹 Каталог", callback_data="show_catalog"))
    
    await message.answer(
        "Привет, рады тебя видеть. Это Десяточка — магазин в лагере!",
        reply_markup=builder.as_markup()
    )

# 2. Вывод каталога
@dp.callback_query(F.data == "show_catalog")
async def show_catalog(callback: types.CallbackQuery):
    catalog_text = (
        "**Каталог товаров:**\n\n"
        "*1. Соль*\n°Малая пачка — 1 купон\n°Средняя пачка — 2 купона\n°Большая пачка — 3 купона\n(Товар является эксклюзивом)\n\n"
        "*2. Хлеб*\n°1 Хлеб — 3 купона\n(Товар является эксклюзивом)\n\n"
        "*3. Вода*\n°Бутылка воды \"Тайный жемчуг\" — 3 купона\n\n"
        "*4. Сок*\n°1 пачка — 2 купона"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Заказать", callback_data="first_order_click"))
    
    await callback.message.answer(catalog_text, parse_mode="Markdown", reply_markup=builder.as_markup())
    await callback.answer()

# 3. Первое нажатие на "Заказать"
@dp.callback_query(F.data == "first_order_click")
async def store_closed(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Заказать", callback_data="open_menu"))
    
    await callback.message.answer(
        "ОЙ! Наш магазин закрыт до лета, да и все же мне не разрешили делать для самого магазина бота, так что вот так!",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# 4. Второе нажатие на "Заказать"
@dp.callback_query(F.data == "open_menu")
async def choose_item(callback: types.CallbackQuery):
    builder = ReplyKeyboardBuilder()
    items = ["Соль (М) — 1", "Соль (С) — 2", "Соль (Б) — 3", "Хлеб — 3", "Вода — 3", "Сок — 2"]
    for item in items:
        builder.add(types.KeyboardButton(text=item))
    builder.adjust(2)
    
    await callback.message.answer("Что вы хотите заказать из списка?", reply_markup=builder.as_markup(resize_keyboard=True))
    await callback.answer()

# 5. Подтверждение
@dp.message(F.text.contains("—"))
async def confirm_coupons(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Подтвердить", callback_data="final_processing"))
    await message.answer("Подтвердите, что у вас есть столько купонов, чтобы хватило", reply_markup=builder.as_markup())

# 6. Финальная обработка
@dp.callback_query(F.data == "final_processing")
async def processing(callback: types.CallbackQuery):
    await callback.message.answer("Ваш заказ обрабатывается...")
    await asyncio.sleep(5)
    
    final_text = (
        "Ваш заказ зарегистрирован в ожидание, как только будет лето вы можете приехать в: "
        "Город Тында, лагерь Надежда, комната 311.\n\n"
        "Удачного ожидания! Благодарим за заказ!"
    )
    await callback.message.answer(final_text, reply_markup=types.ReplyKeyboardRemove())
    await callback.answer()

# БЛОК САМОВОССТАНОВЛЕНИЯ
async def main():
    while True: # Бесконечный цикл: если бот упадет, он поднимется
        try:
            print("Магазин 'Десяточка' запущен...")
            await dp.start_polling(bot, skip_updates=True)
        except Exception as e:
            logging.error(f"Критическая ошибка: {e}")
            print("Попытка автоматического перезапуска через 5 секунд...")
            await asyncio.sleep(5) # Пауза перед перезапуском

if __name__ == "__main__":
    asyncio.run(main())
