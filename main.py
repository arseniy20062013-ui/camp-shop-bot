import asyncio
import logging
from datetime import datetime
from collections import Counter
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

# ========== БОТ 1: ЗАКАЗЫ/ПОКУПКИ (8495993622) ==========
TOKEN1 = "8495993622:AAFZMy4dedK8DE0qMD3siNSvulqj78qDyzU"

# ========== БОТ 2: РЕКЛАМА/ДОНАТЫ (8423667056) ==========
TOKEN2 = "8423667056:AAFxOF1jkteghG6PSK3vccwuI54xlbPmmjA"

ADMIN_ID = 7173827114
DONATE_URL = "https://www.donationalerts.com/r/normiscp"

PRODUCTS = {
    "Соль (Малая)": "1 купон",
    "Соль (Средняя)": "2 купона",
    "Соль (Большая)": "3 купона",
    "Хлеб": "3 купона",
    "Вода": "3 купона",
    "Сок": "2 купона"
}

# ========== ОБЩИЕ ПЕРЕМЕННЫЕ ==========
purchases = []  # База покупок для бота 1
orders = []     # База заказов для бота 2

# ========== БОТ 1: ПОКУПКИ ==========
bot1 = Bot(token=TOKEN1)
dp1 = Dispatcher()

def get_products_keyboard():
    builder = InlineKeyboardBuilder()
    for item, price in PRODUCTS.items():
        builder.button(text=f"{item} - {price}", callback_data=f"buy_{item}")
    builder.adjust(2)
    return builder.as_markup()

@dp1.message(Command("start"))
async def bot1_start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        builder = InlineKeyboardBuilder()
        builder.button(text="Статистика покупок", callback_data="stats")
        builder.button(text="Список покупок", callback_data="list")
        builder.adjust(2)
        await message.answer("Админ-панель покупок:", reply_markup=builder.as_markup())
    else:
        await message.answer("Выберите товар:", reply_markup=get_products_keyboard())

@dp1.callback_query(F.data.startswith("buy_"))
async def process_purchase(callback: types.CallbackQuery):
    user = callback.from_user
    item = callback.data.replace("buy_", "")
    price = PRODUCTS.get(item, "?")
    
    purchase = {
        "id": len(purchases) + 1,
        "user": f"@{user.username}" if user.username else user.full_name,
        "item": item,
        "price": price,
        "time": datetime.now().strftime("%H:%M")
    }
    purchases.append(purchase)
    
    await callback.message.edit_text(f"Куплено: {item} за {price}")
    await callback.answer()

@dp1.callback_query(F.data == "stats")
async def show_stats(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа!")
        return
    
    total = len(purchases)
    item_counts = Counter([p["item"] for p in purchases])
    
    text = f"Статистика покупок:\nВсего: {total}\n\nТоп товаров:\n"
    for item, count in item_counts.most_common(5):
        text += f"• {item}: {count}\n"
    
    await callback.message.edit_text(text)
    await callback.answer()

@dp1.callback_query(F.data == "list")
async def show_list(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа!")
        return
    
    if not purchases:
        text = "Покупок нет"
    else:
        text = "Последние покупки:\n"
        for p in purchases[-10:]:
            text += f"• {p['user']} - {p['item']} ({p['time']})\n"
    
    await callback.message.edit_text(text)
    await callback.answer()

# ========== БОТ 2: РЕКЛАМА/ЗАКАЗЫ ==========
bot2 = Bot(token=TOKEN2)
dp2 = Dispatcher()

def get_orders_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Ролик со мной (100 рублей за ролик)", url=DONATE_URL)
    builder.button(text="Реклама в ролик (150 рублей за ролик)", url=DONATE_URL)
    builder.button(text="Сменить голос на эфире, старик (25 рублей)", url=DONATE_URL)
    builder.button(text="Просто поддержать", url=DONATE_URL)
    builder.adjust(1)
    return builder.as_markup()

@dp2.message(Command("start"))
async def bot2_start(message: types.Message):
    text = (
        "Заказать рекламу/услуги:\n\n"
        "• Ролик со мной - 100 рублей за ролик\n"
        "• Реклама в ролик - 150 рублей за ролик\n"
        "• Сменить голос на эфире, старик - 25 рублей\n"
        "• Просто поддержать - любая сумма\n\n"
        "Выберите вариант:"
    )
    await message.answer(text, reply_markup=get_orders_keyboard())

# ========== АДМИН ПАНЕЛЬ ДЛЯ БОТА 2 ==========
@dp2.message(Command("admin"), F.from_user.id == ADMIN_ID)
async def admin_panel(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="Статистика заказов", callback_data="order_stats")
    builder.adjust(1)
    await message.answer("Админ-панель заказов:", reply_markup=builder.as_markup())

# ========== ЗАПУСК ОБОИХ БОТОВ ==========
async def start_bot1():
    """Запуск первого бота (покупки)"""
    await asyncio.sleep(5)  # Задержка 5 секунд
    logging.info("Запуск бота покупок (8495993622)...")
    await dp1.start_polling(bot1)

async def start_bot2():
    """Запуск второго бота (реклама)"""
    logging.info("Запуск бота заказов (8423667056)...")
    await dp2.start_polling(bot2)

async def main():
    logging.info("Запускаю двух ботов...")
    
    # Создаем задачи для каждого бота
    task1 = asyncio.create_task(start_bot1())
    task2 = asyncio.create_task(start_bot2())
    
    # Ждем завершения
    await asyncio.gather(task1, task2)

if __name__ == "__main__":
    asyncio.run(main())
