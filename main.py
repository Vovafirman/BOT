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
import database

bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())


class OrderFSM(StatesGroup):
    product = State()
    color = State()
    address = State()


products = {
    # Названия файлов должны совпадать с изображениями в папке images
    # ===== ФУТБОЛКИ "ЦЕНТР КИНО" =====
    "cinema_1": ("Оригинал", "Фото 1.png"),
    "cinema_2": ("Режиссер", "Фото 2.png"),
    "cinema_3": ("Сценарий", "Фото 3.jpg"),
    "cinema_4": ("Смотри до конца", "Фото 4.jpg"),
    "cinema_5": ("Даже в эпизоде есть смысл", "Фото 5.jpg"),
    "cinema_6": ("После титров", "Фото 6.png"),
    "cinema_7": ("Комедия", "Фото 7.jpg"),

    # ===== ФУТБОЛКИ "КИНОМЕХАНКИ" =====
    "mech_1": ("Смотрящий за проектором", "Фото 8.jpg"),
    "mech_2": ("Не так страшен фильм", "Фото 9.jpg"),
    "mech_3": ("А кино будет?", "Фото 10.jpg"),
    "mech_4": ("А где ключ?", "Фото 11.jpg"),
    "mech_5": ("Киномеханик", "Фото 12.jpg"),
    "mech_6": ("Подписал ЭДО?", "Фото 13.jpg"),

    # ===== НАСТОЛЬНАЯ ИГРА =====
    "board_game": ("Снимим, если сможешь", "Фото 14.png"),
}


@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="Открыть магазин", callback_data="open_shop")
    kb.adjust(1)
    await message.answer(
        "Уважаемые пользователи, рады приветсовать Вас в нашем магазине мерча от компании Центр Кино",
        reply_markup=kb.as_markup(),
    )


@dp.callback_query(F.data == "open_shop")
async def open_shop(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardBuilder()
    kb.button(text="📦 Каталог товаров", callback_data="catalog")
    kb.button(text="📋 Мои заказы", callback_data="orders")
    kb.button(text="🎮 Игра 'Киношлёп'", callback_data="game")
    kb.button(text="💬 Помощь", url="https://t.me/PRdemon")
    kb.adjust(1)
    await callback.message.answer("📍 Главное меню:", reply_markup=kb.as_markup())
    await callback.answer()


@dp.callback_query(F.data == "catalog")
async def show_catalog(callback: CallbackQuery, state: FSMContext):
    await state.clear()
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
    title = "Футболки \"Центр Кино\"" if prefix == "cinema" else "Футболки \"Киномеханки\""

    await callback.message.answer(f"<b>{title}</b>")

    for key, (name, photo) in products.items():
        if not key.startswith(prefix):
            continue
        kb_item = InlineKeyboardBuilder()
        kb_item.button(text=f"Выбрать", callback_data=f"product_{key}")
        kb_item.adjust(1)
        try:
            photo_file = FSInputFile(f"images/{photo}")
            await callback.message.answer_photo(photo_file, caption=name, reply_markup=kb_item.as_markup())
        except FileNotFoundError:
            await callback.message.answer(name, reply_markup=kb_item.as_markup())

    kb_back = InlineKeyboardBuilder()
    kb_back.button(text="↩ Назад", callback_data="catalog")
    kb_back.adjust(1)
    await callback.message.answer("Выбери товар:", reply_markup=kb_back.as_markup())
    await callback.answer()


@dp.callback_query(F.data.startswith("product_"))
async def choose_product(callback: CallbackQuery, state: FSMContext):
    code = callback.data.replace("product_", "")
    name, photo = products[code]
    await state.update_data(product_code=code, product_name=name)

    kb = InlineKeyboardBuilder()
    kb.button(text="🤍 Молочный", callback_data="color_milk")
    kb.button(text="🖤 Чёрный", callback_data="color_black")
    kb.button(text="↩ Назад", callback_data="catalog")
    kb.adjust(1)

    try:
        photo_file = FSInputFile(f"images/{photo}")
        await callback.message.answer_photo(
            photo=photo_file,
            caption=f"<b>{name}</b>\nРазмер: OVERSIZE\nПлотность: 240 г\nХлопок\nЦена: 2 250 ₽",
            reply_markup=kb.as_markup(),
        )
    except FileNotFoundError:
        await callback.message.answer(
            f"<b>{name}</b>\nЦена: 2 250 ₽",
            reply_markup=kb.as_markup(),
        )

    await state.set_state(OrderFSM.color)
    await callback.answer()
@dp.callback_query(F.data.startswith("color_"))
async def select_color(callback: CallbackQuery, state: FSMContext):
    color = "Молочный" if "milk" in callback.data else "Чёрный"
    await state.update_data(color=color)
    await callback.message.answer(
        "Напишите адрес доставки:\nФИО\nГород проживания\nАдрес доставки\nИндекс\nНомер телефона"
    )
    await state.set_state(OrderFSM.address)
    await callback.answer()


@dp.message(OrderFSM.address)
async def input_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    data = await state.get_data()

    text = (
        f"<b>Подтверждение заказа:</b>\n\n"
        f"🧢 {data['product_name']} ({data['color']})\n"
        f"📦 Адрес: {data['address']}\n"
        f"💵 Цена: 2 250 ₽"
    )
    kb = InlineKeyboardBuilder()
    kb.button(text="Подтверждаю", callback_data="confirm_order")
    kb.button(text="↩ Отмена", callback_data="catalog")
    kb.adjust(1)

    name, photo = products[data['product_code']]
    try:
        photo_file = FSInputFile(f"images/{photo}")
        await message.answer_photo(photo_file, caption=text, reply_markup=kb.as_markup())
    except FileNotFoundError:
        await message.answer(text, reply_markup=kb.as_markup())


@dp.callback_query(F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = callback.from_user
    # Сохраняем заказ в базу данных
    order_id = database.add_order(
        user_id=user.id,
        username=user.username,
        product=data["product_name"],
        color=data["color"],
        address=data["address"],
    )

    text_admin = (
        f"🛒 <b>НОВЫЙ ЗАКАЗ</b>\n"
        f"ID: {order_id}\n"
        f"👤 @{user.username or user.id}\n"
        f"🧢 {data['product_name']} ({data['color']})\n"
        f"📦 {data['address']}\n"
        f"🆔 {user.id}"
    )
    kb_admin = InlineKeyboardBuilder()
    kb_admin.button(text="✅ ЗАКАЗ ОПЛАЧЕН", callback_data=f"paid_{order_id}")
    kb_admin.button(text="❌ НЕ ОПЛАЧЕН", callback_data=f"not_paid_{order_id}")
    kb_admin.adjust(1)
    await bot.send_message(
        chat_id=config.ADMIN_ID, text=text_admin, reply_markup=kb_admin.as_markup()
    )

    await callback.message.answer(
        "Спасибо за заказ, брат! Ждём оплату и вышлем мерч 💸"
    )
    await state.clear()
    await callback.answer()


@dp.callback_query(F.data.startswith("paid_"))
async def mark_paid(callback: CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return
    order_id = int(callback.data.split("_", 1)[1])
    database.set_order_paid(order_id, True)
    await callback.message.edit_text(f"Заказ {order_id} оплачен ✅")
    await callback.answer()


@dp.callback_query(F.data.startswith("not_paid_"))
async def mark_not_paid(callback: CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return
    order_id = int(callback.data.split("_", 1)[1])
    database.set_order_paid(order_id, False)
    await callback.message.edit_text(f"Заказ {order_id} не оплачен ❌")
    await callback.answer()


@dp.callback_query(F.data == "board_game")
async def show_board_game(callback: CallbackQuery):
    name, photo = products["board_game"]
    photo_file = FSInputFile(f"images/{photo}")
    kb = InlineKeyboardBuilder()
    kb.button(text="Купить", url="https://vk.com/center.kino.merch?from=groups")
    kb.button(text="↩ Назад", callback_data="catalog")
    kb.adjust(1)
    caption = (
        f"<b>{name}</b>\n"
        "Возрастные ограничения: 12+ лет\n"
        "Классификация: Развлекательная / Стратегия\n"
        "Количество игроков: от 3-ех до 6 человек\n"
        "Цена: 3.500 рублей\n\n"
        "Возможно вы будущий продюсер?! А может ваши друзья?!\n"
        "Кто сможет первый снять 3 фильма?!"
    )
    await callback.message.answer_photo(photo=photo_file, caption=caption, reply_markup=kb.as_markup())
    await callback.answer()


@dp.callback_query(F.data == "game")
async def play_game(callback: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="▶ Играть в 'Киношлёп'", url="https://center-kino.github.io/game_kinoshlep/")
    kb.button(text="↩ Назад", callback_data="open_shop")
    kb.adjust(1)
    await callback.message.answer("🎮 Игра 'Киношлёп':", reply_markup=kb.as_markup())
    await callback.answer()


@dp.callback_query(F.data == "orders")
async def show_orders(callback: CallbackQuery):
    orders = database.get_user_orders(callback.from_user.id)
    if not orders:
        await callback.message.answer("У тебя пока нет заказов 🛒")
    else:
        lines = ["<b>Твои заказы:</b>"]
        for i, o in enumerate(orders, 1):
            status = "✅ Оплачен" if o["paid"] else "❌ Не оплачен"
            lines.append(
                f"{i}. {o['product']} ({o['color']}) - {status}"\
                f"\n   {o['address']}"
            )
        await callback.message.answer("\n".join(lines))
    await callback.answer()


async def main():
    logging.basicConfig(level=logging.INFO)
    database.create_tables()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
