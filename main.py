import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# --- КОНФИГУРАЦИЯ ---
ADMIN_ID = 7173827114
TOKEN_ORDERS = "8423588142:AAG18DOaJzwixZZyDiTJInu0dKBTV20u3lQ" # Бот для юзеров
TOKEN_REMOTE = "8243825486:AAE4muYvMmbWsWBrZDhCWrOw0glgEKlzlWw" # Бот-пульт

bot_orders = Bot(token=TOKEN_ORDERS)
bot_remote = Bot(token=TOKEN_REMOTE)

dp_orders = Dispatcher()
dp_remote = Dispatcher()

# Состояние магазина и статистика
app_state = {"is_open": True, "users": set()}

# --- ЛОГИКА БОТА ЗАКАЗОВ (КАТАЛОГ НЕ ИЗМЕНЕН) ---

@dp_orders.message(Command("start"))
async def cmd_start(message: types.Message):
    app_state["users"].add(message.from_user.id)
    if not app_state["is_open"]:
        return await message.answer("🚧 Магазин временно закрыт администратором.")
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔹 Каталог", callback_data="show_catalog"))
    
    await message.answer(
        "Привет, рады тебя видеть. Это Десяточка — магазин в лагере!",
        reply_markup=builder.as_markup()
    )

@dp_orders.callback_query(F.data == "show_catalog")
async def show_catalog(callback: types.CallbackQuery):
    if not app_state["is_open"]:
        return await callback.answer("Магазин закрыт!", show_alert=True)
        
    catalog_text = (
        "**Каталог товаров:**\n\n"
        "*1. Соль*\n°Малая пачка — 1 купон\n°Средняя пачка — 2 купона\n°Большая пачка — 3 купона\n(Товар является эксклюзивом)\n\n"
        "*2. Хлеб*\n°1 Хлеб — 3 купона\n(Товар является эксклюзивом)\n\n"
        "*3. Вода*\n°Бутылка воды \"Тайный жемчуг\" — 3 купона\n\n"
        "*4. Сок*\n°1 пачка — 2 купона"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Заказать", callback_data="open_menu"))
    
    await callback.message.answer(catalog_text, parse_mode="Markdown", reply_markup=builder.as_markup())
    await callback.answer()

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
    builder.row(types.InlineKeyboardButton(text="Подтвердить", callback_data=f"buy_{item[:20]}"))
    await message.answer(f"Подтвердите заказ: {item}", reply_markup=builder.as_markup())

@dp_orders.callback_query(F.data.startswith("buy_"))
async def final_step(callback: types.CallbackQuery):
    item = callback.data.replace("buy_", "")
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
    
    await callback.message.answer("Ваш заказ зарегистрирован в ожидание, как только будет лето вы можете приехать в: Город Тында, лагерь Надежда, комната 311.", reply_markup=types.ReplyKeyboardRemove())
    await callback.answer()


# --- ЛОГИКА БОТА-ПУЛЬТА (ТОЛЬКО ДЛЯ ТЕБЯ, ИНЛАЙН-КНОПКИ) ---

def get_admin_keyboard():
    builder = InlineKeyboardBuilder()
    status_text = "🟢 Выключить магазин" if app_state["is_open"] else "🔴 Включить магазин"
    builder.row(types.InlineKeyboardButton(text="📊 Статистика", callback_data="stats"))
    builder.row(types.InlineKeyboardButton(text=status_text, callback_data="toggle_shop"))
    return builder.as_markup()

@dp_remote.message(Command("start"), F.from_user.id == ADMIN_ID)
async def admin_panel(message: types.Message):
    await message.answer("🕹 Пульт управления магазином", reply_markup=get_admin_keyboard())

@dp_remote.callback_query(F.data == "stats", F.from_user.id == ADMIN_ID)
async def stats(callback: types.CallbackQuery):
    count = len(app_state["users"])
    status = "РАБОТАЕТ" if app_state["is_open"] else "ЗАКРЫТ"
    await callback.message.edit_text(f"📈 Статистика:\n- Уникальных юзеров: {count}\n- Статус: {status}", reply_markup=get_admin_keyboard())
    await callback.answer()

@dp_remote.callback_query(F.data == "toggle_shop", F.from_user.id == ADMIN_ID)
async def shop_off(callback: types.CallbackQuery):
    app_state["is_open"] = not app_state["is_open"]
    status_msg = "✅ Магазин открыт!" if app_state["is_open"] else "❌ Магазин закрыт!"
    
    await callback.message.edit_text(status_msg + "\n\n🕹 Пульт управления магазином", reply_markup=get_admin_keyboard())
    await callback.answer()


# --- ЗАПУСК ОБОИХ БОТОВ ---
async def main():
    print("Система запущена: Пульт и Заказы работают...")
    await asyncio.gather(
        dp_orders.start_polling(bot_orders),
        dp_remote.start_polling(bot_remote)
    )

if __name__ == "__main__":
    asyncio.run(main())
