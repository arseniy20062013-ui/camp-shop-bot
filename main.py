import asyncio
import logging
from datetime import datetime
from collections import Counter
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ========== НАСТРОЙКИ ==========
TOKEN = "8495993622:AAFZMy4dedK8DE0qMD3siNSvulqj78qDyzU"  # Бот покупок
ADMIN_ID = 7173827114  # Твой ID

PRODUCTS = {
    "Соль (Малая)": "1 купон",
    "Соль (Средняя)": "2 купона",
    "Соль (Большая)": "3 купона",
    "Хлеб": "3 купона",
    "Вода": "3 купона",
    "Сок": "2 купона"
}
# ===============================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# База покупок
purchases = []

# ========== КНОПКИ ТОВАРОВ ==========
def get_products_keyboard():
    builder = InlineKeyboardBuilder()
    for item, price in PRODUCTS.items():
        builder.button(text=f"{item} - {price}", callback_data=f"buy_{item}")
    builder.adjust(2)
    return builder.as_markup()

# ========== КНОПКИ АДМИНА ==========
def get_admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Статистика", callback_data="stats")
    builder.button(text="📋 Список покупок", callback_data="list")
    builder.button(text="🧹 Очистить", callback_data="clear")
    builder.adjust(2)
    return builder.as_markup()

# ========== КОМАНДА /START ==========
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    is_admin = user_id == ADMIN_ID
    
    if is_admin:
        welcome = "👑 *Админ-панель магазина*\n\nВыберите действие:"
        await message.answer(welcome, parse_mode="Markdown", reply_markup=get_admin_keyboard())
    else:
        welcome = (
            "🛒 *Магазин Десяточка*\n\n"
            "Выберите товар для покупки:\n"
        )
        await message.answer(welcome, parse_mode="Markdown", reply_markup=get_products_keyboard())

# ========== ПОКУПКА ТОВАРА ==========
@dp.callback_query(F.data.startswith("buy_"))
async def process_purchase(callback: types.CallbackQuery):
    user = callback.from_user
    username = f"@{user.username}" if user.username else user.full_name
    item = callback.data.replace("buy_", "")
    price = PRODUCTS.get(item, "?")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Сохраняем покупку
    purchase = {
        "id": len(purchases) + 1,
        "user_id": user.id,
        "username": username,
        "item": item,
        "price": price,
        "timestamp": timestamp
    }
    purchases.append(purchase)
    
    # Уведомление админу (тебе)
    admin_msg = (
        f"💰 *НОВАЯ ПОКУПКА!*\n\n"
        f"👤 Покупатель: {username}\n"
        f"🆔 ID: `{user.id}`\n"
        f"🛒 Товар: {item}\n"
        f"💵 Цена: {price}\n"
        f"⏰ Время: {timestamp}\n\n"
        f"📊 Всего покупок: {len(purchases)}"
    )
    
    try:
        await bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Ошибка отправки админу: {e}")
    
    # Ответ покупателю
    await callback.message.edit_text(
        f"✅ *Покупка оформлена!*\n\n"
        f"Товар: {item}\n"
        f"Цена: {price}\n"
        f"Статус: 📦 Ожидает выдачи\n\n"
        f"Заберите товар в комнате 311.",
        parse_mode="Markdown"
    )
    await callback.answer()

# ========== СТАТИСТИКА ==========
@dp.callback_query(F.data == "stats")
async def show_stats(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Только для админа! ❌", show_alert=True)
        return
    
    today = datetime.now().strftime("%Y-%m-%d")
    today_purchases = [p for p in purchases if p['timestamp'].startswith(today)]
    
    # Статистика по товарам
    item_counter = Counter([p['item'] for p in purchases])
    top_items = item_counter.most_common(5)
    
    # Общая сумма (в купонах)
    price_map = {"1 купон": 1, "2 купона": 2, "3 купона": 3}
    total_coupons = sum(price_map.get(p['price'], 0) for p in purchases)
    
    stats_text = (
        f"📊 *СТАТИСТИКА МАГАЗИНА*\n\n"
        f"📈 Общая статистика:\n"
        f"• Всего покупок: {len(purchases)}\n"
        f"• Сегодня: {len(today_purchases)}\n"
        f"• Общая сумма: {total_coupons} купонов\n\n"
        f"🏆 Топ товаров:\n"
    )
    
    for item, count in top_items:
        stats_text += f"• {item}: {count} покупок\n"
    
    # Статистика по дням
    if purchases:
        dates = [p['timestamp'][:10] for p in purchases]
        date_counter = Counter(dates)
        last_dates = list(date_counter.items())[-5:]  # Последние 5 дней
        
        stats_text += f"\n📅 Активность по дням:\n"
        for date, count in last_dates:
            stats_text += f"• {date}: {count} покупок\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Список покупок", callback_data="list")
    builder.button(text="🧹 Очистить", callback_data="clear")
    builder.button(text="⬅️ Назад", callback_data="back")
    builder.adjust(2)
    
    await callback.message.edit_text(
        stats_text,
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# ========== СПИСОК ПОКУПОК ==========
@dp.callback_query(F.data == "list")
async def show_list(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Только для админа! ❌", show_alert=True)
        return
    
    if not purchases:
        list_text = "📭 Покупок пока нет"
    else:
        list_text = "📋 *Последние 20 покупок:*\n\n"
        for p in purchases[-20:]:
            time_short = p['timestamp'][11:16]  # Только часы:минуты
            list_text += f"🆔 {p['id']}: {p['username']} - {p['item']} ({p['price']}) - {time_short}\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Статистика", callback_data="stats")
    builder.button(text="🧹 Очистить", callback_data="clear")
    builder.button(text="⬅️ Назад", callback_data="back")
    builder.adjust(2)
    
    await callback.message.edit_text(
        list_text,
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# ========== ОЧИСТКА БАЗЫ ==========
@dp.callback_query(F.data == "clear")
async def clear_database(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Только для админа! ❌", show_alert=True)
        return
    
    purchases.clear()
    await callback.message.edit_text(
        "🗑 *База данных очищена!*\n\nВсе покупки удалены.",
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard()
    )
    await callback.answer("✅ База очищена")

# ========== НАЗАД В МЕНЮ ==========
@dp.callback_query(F.data == "back")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "👑 *Админ-панель магазина*\n\nВыберите действие:",
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()

# ========== ЗАПУСК ==========
async def main():
    logger.info("Бот покупок со статистикой запускается...")
    logger.info(f"Админ ID: {ADMIN_ID}")
    logger.info(f"Всего товаров: {len(PRODUCTS)}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
