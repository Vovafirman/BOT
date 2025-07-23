import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

import config

bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())


class OrderFSM(StatesGroup):
    product = State()
    color = State()
    address = State()


products = {
    "cinema_1": ("Оригинал", "Фото 1.jpg"),
    "cinema_2": ("Режиссер", "Фото 2.jpg"),
    "cinema_3": ("Сценарий", "Фото 3.jpg"),
    "cinema_4": ("Смотри до конца", "Фото 4.jpg"),
    "cinema_5": ("Даже в эпизоде есть смысл", "Фото 5.jpg"),
    "cinema_6": ("После титров", "Фото 6.jpg"),
    "cinema_7": ("Комедия", "Фото 7.jpg"),
    "mech_1": ("Киномеханик", "Фото 8.jpg"),
    "mech_2": ("Кино внутри", "Фото 9.jpg"),
    "mech_3": ("Свет в проекции", "Фото 10.jpg"),
    "mech_4": ("Бобина не лопни", "Фото 11.jpg"),
    "mech_5": ("Тёмный зал", "Фото 12.jpg"),
    "mech_6": ("16 мм жив", "Фото 13.jpg"),
    "mech_7": ("Держу плёнку", "Фото 14.png"),
    "board_game": ("Настольная игра Киношлёп", "Фото 15.png"),
}


@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🛍 Открыть магазин", callback_data="open_shop")
    await message.answer("<b>САЛАМ, БРАТ!</b>\nТы в ЦЕНТРЕ КИНО МЕРЧ. Нажимай кнопку:", reply_markup=kb.as_markup())


@dp.callback_query(F.data == "open_shop")
async def open_shop(callback: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="📦 Каталог товаров", callback_data="catalog")
    kb.button(text="📋 Мои заказы", callback_data="orders")
    kb.button(text="🎮 Игра 'Киношлёп'", callback_data="game")
    kb.button(text="💬 Помощь", url="https://t.me/PRdemon")
    kb.adjust(1)
    await callback.message.answer("📍 Главное меню:", reply_markup=kb.as_markup())
    await callback.answer()


@dp.callback_query(F.data == "catalog")
async def show_catalog(callback: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="👕 Футболки Центр Кино", callback_data="cinema")
    kb.button(text="📽 Футболки Киномеханки", callback_data="mech")
    kb.button(text="🎲 Настольная игра", callback_data="board_game")
    kb.button(text="↩ Назад", callback_data="open_shop")
    kb.adjust(1)
    await callback.message.answer("Категории:", reply_markup=kb.as_markup())
    await callback.answer()


@dp.callback_query(F.data.in_(["cinema", "mech"]))
async def show_category(callback: CallbackQuery):
    prefix = callback.data
    kb = InlineKeyboardBuilder()
    for key, (name, _) in products.items():
        if key.startswith(prefix):
            kb.button(text=name, callback_data=f"product_{key}")
    kb.button(text="↩ Назад", callback_data="catalog")
    kb.adjust(1)
    await callback.message.answer("Выбери товар:", reply_markup=kb.as_markup())
    await callback.answer()


@dp.callback_query(F.data.startswith("product_"))
async def choose_product(callback: CallbackQuery, state: FSMContext):
    code = callback.data.replace("product_", "")
    name, photo = products[code]
    await state.update_data(product_code=code, product_name=name)
    photo_file = FSInputFile(f"images/{photo}")
    kb = InlineKeyboardBuilder()
    kb.button(text="🤍 Молочный", callback_data="color_milk")
    kb.button(text="🖤 Чёрный", callback_data="color_black")
    kb.button(text="↩ Назад", callback_data="catalog")
    kb.adjust(1)
    await callback.message.answer_photo(photo=photo_file, caption=f"<b>{name}</b>\nРазмер: OVERSIZE\nПлотность: 240 г\nХлопок\nЦена: 2 250 ₽", reply_markup=kb.as_markup())
    await state.set_state(OrderFSM.color)
    await callback.answer()
@dp.callback_query(F.data.startswith("color_"))
async def select_color(callback: CallbackQuery, state: FSMContext):
    color = "Молочный" if "milk" in callback.data else "Чёрный"
    await state.update_data(color=color)
    await callback.message.answer("✍️ Введи адрес доставки (ФИО, город, улица, дом, индекс):")
    await state.set_state(OrderFSM.address)
    await callback.answer()


@dp.message(OrderFSM.address)
async def input_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    data = await state.get_data()

    text = f"<b>Подтверждение заказа:</b>\n\n🧢 {data['product_name']} ({data['color']})\n📦 Адрес: {data['address']}\n💵 Цена: 2 250 ₽"
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить заказ", callback_data="confirm_order")
    kb.button(text="↩ Отмена", callback_data="catalog")
    kb.adjust(1)
    await message.answer(text, reply_markup=kb.as_markup())


@dp.callback_query(F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = callback.from_user

    text_admin = f"🛒 <b>НОВЫЙ ЗАКАЗ</b>\n👤 @{user.username or user.id}\n🧢 {data['product_name']} ({data['color']})\n📦 {data['address']}\n🆔 {user.id}"
    kb_admin = InlineKeyboardBuilder()
    kb_admin.button(text="✅ ЗАКАЗ ОПЛАЧЕН", callback_data="paid")
    kb_admin.button(text="❌ НЕ ОПЛАЧЕН", callback_data="not_paid")
    kb_admin.adjust(1)
    await bot.send_message(chat_id=config.ADMIN_ID, text=text_admin, reply_markup=kb_admin.as_markup())

    await callback.message.answer("Спасибо за заказ, брат! Ждём оплату и вышлем мерч 💸")
    await state.clear()
    await callback.answer()


@dp.callback_query(F.data == "board_game")
async def show_board_game(callback: CallbackQuery):
    name, photo = products["board_game"]
    photo_file = FSInputFile(f"images/{photo}")
    kb = InlineKeyboardBuilder()
    kb.button(text="🛒 Заказать у @PRdemon", url="https://t.me/PRdemon")
    kb.button(text="↩ Назад", callback_data="catalog")
    kb.adjust(1)
    await callback.message.answer_photo(photo=photo_file, caption=f"<b>{name}</b>\nНастольная игра по теме кино. Весело, стильно, уникально!", reply_markup=kb.as_markup())
    await callback.answer()


@dp.callback_query(F.data == "game")
async def play_game(callback: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="▶ Играть в 'Киношлёп'", url="https://t.me/CinemaGameBot")
    kb.button(text="↩ Назад", callback_data="open_shop")
    kb.adjust(1)
    await callback.message.answer("🎮 Игра 'Киношлёп':", reply_markup=kb.as_markup())
    await callback.answer()


@dp.callback_query(F.data == "orders")
async def show_orders(callback: CallbackQuery):
    await callback.message.answer("📋 История заказов временно недоступна. Скоро будет реализовано.")
    await callback.answer()


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
