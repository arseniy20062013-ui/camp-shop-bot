import asyncio
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# --- ВСЕ ТВОИ ТОКЕНЫ ---
SHOP_BOT_TOKEN = '8423588142:AAG18DOaJzwixZZyDiTJInu0dKBTV20u3lQ' # Магазин
LOG_BOT_TOKEN = '8302935804:AAGmtbJb07m3vEJJNEXi6x0to2KMnQfn0VI'  # Сборщик
CTRL_BOT_TOKEN = '8243825486:AAE4muYvMmbWsWBrZDhCWrOw0glgEKlzlWw' # Пульт
MY_CHAT_ID = 7173827114

# Инициализация ботов
shop_bot = Bot(token=SHOP_BOT_TOKEN)
log_bot = Bot(token=LOG_BOT_TOKEN)
ctrl_bot = Bot(token=CTRL_BOT_TOKEN)

dp = Dispatcher()

class Config:
    is_active = False
    stop_time = 0

class OrderState(StatesGroup):
    choosing_item = State()

# --- ЛОГИКА ПУЛЬТА УПРАВЛЕНИЯ (Бот 8243825486) ---
@dp.message(Command("start"), F.bot.id == 8243825486)
async def admin_menu(message: types.Message):
    if message.from_user.id != MY_CHAT_ID: return
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🚀 Запустить на 48ч", callback_data="start_bots"))
    builder.row(types.InlineKeyboardButton(text="🛑 Выключить сейчас", callback_data="stop_bots"))
    status = "✅ Работают" if Config.is_active else "😴 Боты спят"
    await message.answer(f"🎮 ПУЛЬТ УПРАВЛЕНИЯ\nСтатус: {status}", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "start_bots", F.bot.id == 8243825486)
async def start_logic(callback: types.CallbackQuery):
    Config.is_active = True
    Config.stop_time = time.time() + (48 * 3600)
    await callback.message.edit_text("✅ Боты запущены на 48 часов!", reply_markup=callback.message.reply_markup)

@dp.callback_query(F.data == "stop_bots", F.bot.id == 8243825486)
async def stop_logic(callback: types.CallbackQuery):
    Config.is_active = False
    await callback.message.edit_text("😴 Боты уснули. Статус: Команда спит", reply_markup=callback.message.reply_markup)

# --- ЛОГИКА МАГАЗИНА (Бот 8423588142) ---
@dp.message(F.bot.id == 8423588142)
async def shop_messages(message: types.Message, state: FSMContext):
    # Если выключено или время вышло
    if not Config.is_active or (Config.stop_time > 0 and time.time() > Config.stop_time):
        Config.is_active = False
        await message.answer("Команда спит.")
        return

    if message.text == "/start":
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔹 Каталог", callback_data="show_catalog"))
        await message.answer("Привет, рады тебя видеть. Это Десяточка — магазин в лагере!", reply_markup=builder.as_markup())
    
    elif "—" in message.text:
        await state.update_data(chosen_item=message.text)
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="Подтвердить", callback_data="final_confirm"))
        await message.answer(f"Вы выбрали: **{message.text}**\nПодтвердите, что у вас есть столько купонов, чтобы хватило", 
                             parse_mode="Markdown", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "show_catalog", F.bot.id == 8423588142)
async def cat(c: types.CallbackQuery):
    if not Config.is_active: await c.message.answer("Команда спит."); return
    text = ("**Каталог товаров:**\n\n*1.Соль*\n°Малая-1\n°Средняя-2\n°Большая-3\n(Эксклюзив)\n\n"
            "*2.Хлеб*\n°1 Хлеб-3\n(Эксклюзив)\n\n*3.Вода*\n°Тайный жемчуг-3\n\n*4.Сок*\n°1 пачка-2")
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="Заказать", callback_data="order_fail"))
    await c.message.answer(text, parse_mode="Markdown", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "order_fail", F.bot.id == 8423588142)
async def fail(c: types.CallbackQuery):
    builder = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="Заказать", callback_data="real_order"))
    await c.message.answer("ОЙ! Наш магазин закрыт до лета, да и все же мне не разрешили делать для самого магазина бота, так что вот так!", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "real_order", F.bot.id == 8423588142)
async def real(c: types.CallbackQuery, state: FSMContext):
    builder = ReplyKeyboardBuilder()
    items = ["Соль (М) — 1", "Соль (С) — 2", "Соль (Б) — 3", "Хлеб — 3", "Вода — 3", "Сок — 2"]
    for i in items: builder.add(types.KeyboardButton(text=i))
    await c.message.answer("Что вы хотите заказать из списка?", reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(OrderState.choosing_item)

@dp.callback_query(F.data == "final_confirm", F.bot.id == 8423588142)
async def final(c: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    item = data.get('chosen_item', 'Неизвестно')
    await c.message.answer("Ваш заказ обрабатывается...")
    
    # Отправка лога (Бот 8302935804)
    await log_bot.send_message(MY_CHAT_ID, f"📦 **НОВЫЙ ЗАКАЗ!**\n👤 От: @{c.from_user.username}\n🏷 Товар: {item}", parse_mode="Markdown")
    
    await asyncio.sleep(5)
    await c.message.answer("Ваш заказ зарегистрирован в ожидание, как только будет лето вы можете приехать в: Город Тында, лагерь надежда, комната 311.\nУдачного ожидание! Благодарим за заказ!", reply_markup=types.ReplyKeyboardRemove())
    await state.clear()

async def main():
    print("Система запущена! Зайди в ПУЛЬТ и нажми кнопку.")
    await dp.start_polling(shop_bot, ctrl_bot)

if __name__ == "__main__":
    asyncio.run(main())
