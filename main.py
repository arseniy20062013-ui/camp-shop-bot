import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

API_TOKEN = '8423588142:AAG18DOaJzwixZZyDiTJInu0dKBTV20u3lQ'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Глобальная переменная статуса (True - работает, False - закрыт)
STORE_OPEN = True

# Команда для админа, чтобы менять статус (в реальном проекте лучше ограничить по user_id)
@dp.message(Command("status"))
async def toggle_status(message: types.Message):
    global STORE_OPEN
    STORE_OPEN = not STORE_OPEN
    status_text = "РАБОТАЕТ" if STORE_OPEN else "ЗАКРЫТ"
    await message.answer(f"Статус магазина изменен на: **{status_text}**", parse_mode="Markdown")

# Хендлер для проверки статуса перед любым действием
@dp.callback_query(lambda c: not STORE_OPEN)
@dp.message(lambda m: not STORE_OPEN and m.text != "/status")
async def store_is_closed_msg(event: types.Message | types.CallbackQuery):
    text = "Извините, в данный момент магазин не работает. Приходите позже!"
    if isinstance(event, types.Message):
        await event.answer(text)
    else:
        await event.message.answer(text)
        await event.answer()

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
    builder.row(types.InlineKeyboardButton(text="Заказать", callback_data="open_menu")) # Сразу ведем в меню
    
    await callback.message.answer(catalog_text, parse_mode="Markdown", reply_markup=builder.as_markup())
    await callback.answer()

# 4. Выбор продуктов
@dp.callback_query(F.data == "open_menu")
async def choose_item(callback: types.CallbackQuery):
    builder = ReplyKeyboardBuilder()
    items = ["Соль (М) — 1", "Соль (С) — 2", "Соль (Б) — 3", "Хлеб — 3", "Вода — 3", "Сок — 2"]
    for item in items:
        builder.add(types.KeyboardButton(text=item))
    builder.adjust(2)
    
    await callback.message.answer("Что вы хотите заказать из списка?", reply_markup=builder.as_markup(resize_keyboard=True))
    await callback.answer()

# 5. Подтверждение купонов
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

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
