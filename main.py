import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# --- КОНФИГУРАЦИЯ ---
ADMIN_ID = 7173827114
TOKEN_ORDERS = "8302935804:AAGmtbJb07m3vEJJNEXi6x0to2KMnQfn0VI" # Бот для юзеров
TOKEN_REMOTE = "8243825486:AAE4muYvMmbWsWBrZDhCWrOw0glgEKlzlWw" # Бот-пульт

bot_orders = Bot(token=TOKEN_ORDERS)
bot_remote = Bot(token=TOKEN_REMOTE)

dp_orders = Dispatcher()
dp_remote = Dispatcher()

# Состояние магазина и статистика
app_state = {"is_open": True, "users": set()}

# --- ЛОГИКА БОТА ЗАКАЗОВ ---

@dp_orders.message(Command("start"))
async def cmd_start(message: types.Message):
    app_state["users"].add(message.from_user.id)
    if not app_state["is_open"]:
        return await message.answer("🚧 Магазин временно закрыт администратором.")
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔹 Каталог", callback_data="show_catalog"))
    await message.answer("Привет! Это Десяточка — магазин в лагере!", reply_markup=builder.as_markup())

@dp_orders.callback_query(F.data == "show_catalog")
async def show_catalog(callback: types.CallbackQuery):
    if not app_state["is_open"]:
        return await callback.answer("Магазин закрыт!", show_alert=True)
    
    catalog_text = "**Каталог товаров:**\n\n1. Соль\n2. Хлеб\n3. Вода\n4. Сок"
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Заказать", callback_data="open_menu"))
    await callback.message.answer(catalog_text, parse_mode="Markdown", reply_markup=builder.as_markup())

@dp_orders.callback_query(F.data == "open_menu")
async def choose_item(callback: types.CallbackQuery):
    builder = ReplyKeyboardBuilder()
    items = ["Соль (М) — 1", "Соль (С) — 2", "Соль (Б) — 3", "Хлеб — 3", "Вода — 3", "Сок — 2"]
    for item in items:
        builder.add(types.KeyboardButton(text=item))
    builder.adjust(2)
    await callback.message.answer("Что вы хотите заказать?", reply_markup=builder.as_markup(resize_keyboard=True))

@dp_orders.message(F.text.contains("—"))
async def confirm_order(message: types.Message):
    if not app_state["is_open"]: return
    
    item = message.text
    builder = InlineKeyboardBuilder()
    # Кодируем товар в callback_data
    builder.row(types.InlineKeyboardButton(text="Подтвердить", callback_data=f"buy_{item[:20]}"))
    await message.answer(f"Подтвердите заказ: {item}", reply_markup=builder.as_markup())

@dp_orders.callback_query(F.data.startswith("buy_"))
async def final_step(callback: types.CallbackQuery):
    item = callback.data.split("_")[1]
    user = callback.from_user
    dt_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # УВЕДОМЛЕНИЕ В ПУЛЬТ (Сборщику)
    report = (
        f"📦 **НОВЫЙ ЗАКАЗ**\n"
        f"👤 Ник: @{user.username or 'нет'}\n"
        f"🆔 ID: `{user.id}`\n"
        f"🛒 Товар: {item}\n"
        f"⏰ Время: {dt_now}"
    )
    await bot_remote.send_message(ADMIN_ID, report, parse_mode="Markdown")
    
    await callback.message.answer("Заказ принят! Ждем тебя летом в 311 комнате.", reply_markup=types.ReplyKeyboardRemove())

# --- ЛОГИКА БОТА-ПУЛЬТА ---

@dp_remote.message(Command("start"), F.from_user.id == ADMIN_ID)
async def admin_panel(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="📊 Статистика"))
    builder.add(types.KeyboardButton(text="🟢 Включить магазин"))
    builder.add(types.KeyboardButton(text="🔴 Выключить магазин"))
    builder.adjust(1)
    await message.answer("🕹 Пульт управления магазином", reply_markup=builder.as_markup(resize_keyboard=True))

@dp_remote.message(F.text == "📊 Статистика", F.from_user.id == ADMIN_ID)
async def stats(message: types.Message):
    count = len(app_state["users"])
    status = "РАБОТАЕТ" if app_state["is_open"] else "ЗАКРЫТ"
    await message.answer(f"📈 Статистика:\n- Уникальных юзеров: {count}\n- Статус: {status}")

@dp_remote.message(F.text == "🟢 Включить магазин", F.from_user.id == ADMIN_ID)
async def shop_on(message: types.Message):
    app_state["is_open"] = True
    await message.answer("✅ Магазин открыт для заказов!")

@dp_remote.message(F.text == "🔴 Выключить магазин", F.from_user.id == ADMIN_ID)
async def shop_off(message: types.Message):
    app_state["is_open"] = False
    await message.answer("❌ Магазин закрыт (пользователи увидят заглушку).")

# --- ЗАПУСК ОБОИХ БОТОВ ---
async def main():
    print("Система запущена: Пульт и Заказы работают...")
    await asyncio.gather(
        dp_orders.start_polling(bot_orders),
        dp_remote.start_polling(bot_remote)
    )

if __name__ == "__main__":
    asyncio.run(main())
