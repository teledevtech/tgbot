import datetime
import sqlite3

import aiosqlite
from aiogram import Router, F, Bot
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from PIL import Image, ImageDraw, ImageFont
import os
from info import HEAD, TOKEN

router = Router()
router.message.filter(F.from_user.id == HEAD)
bot = Bot(token=TOKEN)


@router.message(Command('start'))
async def start_head(message: Message, state: FSMContext):
    await state.clear()
    inline = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Изменить курс", callback_data="changerate"),
                InlineKeyboardButton(text="Изменить реквизиты", callback_data="changerekvisit")
            ],
            [
                InlineKeyboardButton(text="История заявок", callback_data="history_0")
            ],
            [
                InlineKeyboardButton(text="Добавить админа", callback_data="addadmin"),
                InlineKeyboardButton(text="Убрать админа", callback_data="deladmin")
            ],
            [
                InlineKeyboardButton(text="Сформировать отчет", callback_data="document")
            ],
            [
                InlineKeyboardButton(text="История отчет", callback_data="historydocument_0")
            ]
        ]
    )
    await message.answer("Привет! Выбери, что хочешь сделать", reply_markup=inline)


@router.callback_query(F.data == "again")
async def start_head(call: CallbackQuery, state: FSMContext):
    await state.clear()
    inline = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Изменить курс", callback_data="changerate"),
                InlineKeyboardButton(text="Изменить реквизиты", callback_data="changerekvisit")
            ],
            [
                InlineKeyboardButton(text="История заявок", callback_data="history_0")
            ],
            [
                InlineKeyboardButton(text="Добавить администратора", callback_data="addadmin"),
                InlineKeyboardButton(text="Убрать администратора", callback_data="deladmin")
            ],
            [
                InlineKeyboardButton(text="Сформировать отчет", callback_data="document")
            ],
            [
                InlineKeyboardButton(text="История отчет", callback_data="historydocument_0")
            ]
        ]
    )
    try:
        await call.message.edit_text("Привет! Выбери, что хочешь сделать", reply_markup=inline)
    except:
        a = await call.message.answer("Привет! Выбери, что хочешь сделать", reply_markup=inline)
        await bot.delete_message(chat_id=call.from_user.id, message_id=a.message_id-1)


class ClearAdmin(StatesGroup):
    user_id = State()


@router.callback_query(F.data == "deladmin")
async def deladmin(call: CallbackQuery, state: FSMContext):
    tetxt = ""
    admins = []
    async with aiosqlite.connect('database.db') as connection:
        async with connection.execute('SELECT id_admin FROM admin') as cursor:
            results = await cursor.fetchall()
            for row in results:
                admins.append(row[0])
    for i in admins:
        tetxt += f'<pre>{str(i)}</pre>'
    inline = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="again")]])
    await call.message.answer(text=f"Отправьте USER ID админа:\n\n{tetxt}", parse_mode="HTML", reply_markup=inline)
    await state.set_state(ClearAdmin.user_id)


@router.message(ClearAdmin.user_id)
async def ClearAdmin_user_id(message: Message):
    async with aiosqlite.connect('database.db') as connection:
        await connection.execute('DELETE FROM admin WHERE id_admin = ?', (int(message.text),))
        await connection.execute(f'DROP TABLE I{str(message.text)}')
        await connection.commit()
    await message.answer(
        text="Администратор удален!"
    )


class AddAdmin(StatesGroup):
    user_id = State()


@router.callback_query(F.data == "addadmin")
async def addadmin(call: CallbackQuery, state: FSMContext):
    inline = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="again")]])
    await call.message.answer("Отправьте USER ID админа:", reply_markup=inline)
    await state.set_state(AddAdmin.user_id)


@router.message(AddAdmin.user_id)
async def addadmin_user_id(message: Message):
    async with aiosqlite.connect('database.db') as connection:
        await connection.execute('INSERT INTO admin (count, id_admin) VALUES (?, ?)', (0, int(message.text)))
        await connection.execute(f'CREATE TABLE IF NOT EXISTS I{message.text} (order_num TEXT, chat_id INTEGER, photo TEXT, ruble TEXT, azn TEXT, card TEXT, type TEXT)')
        await connection.commit()
    await message.answer(
        text="Администратор добавлен!\n\nДля получения заявок админ должен активировать бот"
    )


class Chcrate1(StatesGroup):
    rate1 = State()
    rate2 = State()


class Chcrate2(StatesGroup):
    card = State()
    type = State()


@router.callback_query(F.data == "changerate")
async def cmd_chc_rate(callback: CallbackQuery, state: FSMContext):
    try:
        async with aiosqlite.connect('database.db') as connection:
            async with connection.execute('SELECT * FROM Rate') as cursor:
                users = await cursor.fetchall()
        await callback.message.edit_text(text=f"Старый курс:\n\nКупить: {users[0][0]}\nПродать: {users[0][1]}\n\nВведите новый курс покупки:")
        await state.set_state(Chcrate1.rate1)
    except Exception as e:
        print(e)


@router.message(Chcrate1.rate1)
async def cmd_chcrate1(message: Message, state: FSMContext):
    try:
        rate = message.text
        await state.update_data(rate1=rate)
        a = await message.answer(f"Новый курс покупки: {rate}\n\nВведите новый курс продажи")
        await bot.delete_message(chat_id=message.from_user.id, message_id=a.message_id-1)
        await bot.delete_message(chat_id=message.from_user.id, message_id=a.message_id-2)
        await state.set_state(Chcrate1.rate2)
    except Exception as e:
        print(e)


@router.message(Chcrate1.rate2)
async def cmd_chcrate1(message: Message, state: FSMContext):
    try:
        rate = message.text
        user_data = await state.get_data()
        async with aiosqlite.connect('database.db') as connection:
            await connection.execute('DELETE FROM Rate')
            await connection.execute('INSERT INTO Rate (rate_buy, rate_sell) VALUES (?, ?)', (user_data['rate1'], rate))
            await connection.commit()
        inline = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Назад", callback_data=f"again")
                ]
            ]
        )
        a = await message.answer(f"Новый курс покупки: {user_data['rate1']}\nНовый курс продажи: {rate}\n\nКурс обновлен.", reply_markup=inline)
        await bot.delete_message(chat_id=message.from_user.id, message_id=a.message_id-1)
        await bot.delete_message(chat_id=message.from_user.id, message_id=a.message_id-2)
        await state.clear()
    except Exception as e:
        print(e)


@router.callback_query(F.data == "changerekvisit")
async def changerekvisit(callback: CallbackQuery):
    async with aiosqlite.connect('database.db') as connection:
        async with connection.execute('SELECT * FROM Bank') as cursor:
            users = await cursor.fetchall()
    await callback.message.edit_text(
        f"Старые реквизиты:\n\n\nРубли: <blockquote><code>{users[0][0]}</code></blockquote>\n\nAZN: <blockquote><code>{users[0][1]}</code></blockquote>",
        parse_mode="HTML"
    )
    replymarkup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Руб.карта", callback_data="card_rub")],
            [InlineKeyboardButton(text="AZN карта", callback_data="card_azn")],
        ]
    )
    await callback.message.answer("Какую карту хотите поменять?", reply_markup=replymarkup)


@router.callback_query(F.data.split("_")[0] == "card")
async def cmd_change_card_rekv(callback: CallbackQuery, state: FSMContext):
    types = callback.data.split("_")[1]
    await state.update_data(type=types)
    a = await callback.message.answer("Введите номер карты:")
    await bot.delete_message(chat_id=callback.from_user.id, message_id=a.message_id-1)
    await bot.delete_message(chat_id=callback.from_user.id, message_id=a.message_id-2)
    await state.set_state(Chcrate2.card)


@router.message(Chcrate2.card)
async def cmd_chc_card(message: Message, state: FSMContext):
    card = message.text
    user_data = await state.get_data()
    if user_data["type"] == "rub":
        async with aiosqlite.connect('database.db') as connection:
            async with connection.execute('SELECT * FROM Bank') as cursor:
                users = await cursor.fetchall()
                azn = users[0][1] if users else None

            await connection.execute('DELETE FROM Bank')
            await connection.execute('INSERT INTO Bank (card1, card2) VALUES (?, ?)', (card, azn))
            await connection.commit()

        a = await message.answer(
            f"Реквизиты:\n\n\nAZN: <code>{str(azn)}</code>\nРУБЛИ: <code>{str(card)}</code>",
            parse_mode="HTML",
        )
    else:
        async with aiosqlite.connect('database.db') as connection:
            async with connection.execute('SELECT * FROM Bank') as cursor:
                users = await cursor.fetchall()
                rub = users[0][1] if users else None

            await connection.execute('DELETE FROM Bank')
            await connection.execute('INSERT INTO Bank (card1, card2) VALUES (?, ?)', (rub, card))
            await connection.commit()
        a = await message.answer(
            f"Реквизиты:\n\n\nAZN: <code>{str(card)}</code>\nРУБЛИ: <code>{str(rub)}</code>",
            parse_mode="HTML",
        )
    await bot.delete_message(chat_id=message.from_user.id, message_id=a.message_id-1)
    await state.clear()


@router.callback_query(F.data.split("_")[0] == "history")
async def history(cacll: CallbackQuery):
    page = int(cacll.data.split("_")[1])
    inline = InlineKeyboardMarkup(inline_keyboard=[])

    async with aiosqlite.connect('database.db') as conn:
        async with conn.execute('SELECT * FROM history') as cursor:
            users = await cursor.fetchall()

    for i in range(page, min(page + 25, len(users))):
        try:
            inline.inline_keyboard.append(
                [
                    InlineKeyboardButton(
                        text=f"{str(users[i][0])}  {str(users[i][-3])}",
                        callback_data=f"open-{str(users[i][0])}"
                    )
                ]
            )
        except IndexError:
            break

    if len(users) == 0:
        inline.inline_keyboard.append(
            [
                InlineKeyboardButton(text="Назад", callback_data=f"again")
            ]
        )
    else:
        if page == 0:
            if len(users) > 25:
                inline.inline_keyboard.append(
                    [
                        InlineKeyboardButton(text="Дальше", callback_data=f"open-{str(page + 25)}")
                    ]
                )
        elif page > 0:
            if page + 25 < len(users):
                inline.inline_keyboard.append(
                    [
                        InlineKeyboardButton(text="Назад", callback_data=f"open-{str(page - 25)}"),
                        InlineKeyboardButton(text="Дальше", callback_data=f"open-{str(page + 25)}")
                    ]
                )
            else:
                inline.inline_keyboard.append(
                    [
                        InlineKeyboardButton(text="Назад", callback_data=f"open-{str(page - 25)}")
                    ]
                )

    await cacll.message.edit_text(
        text="Выберете сделку👇",
        reply_markup=inline
    )


@router.callback_query(F.data.split("-")[0] == "open")
async def open_h(call: CallbackQuery):
    ordernum = call.data.split("-")[1]
    txt = ""

    async with aiosqlite.connect('database.db') as conn:
        async with conn.execute('SELECT * FROM history') as cursor:
            users = await cursor.fetchall()

    for i in users:
        if str(i[0]) == str(ordernum):
            ordernum, admin, user_id, azn, rub, card, date, status, typeorder = i
            txt = (f"Номер сделки №{str(ordernum)}\n\n"
                   f"User ID клиента: {str(user_id)}\n\n"
                   f"Тип покупки: {typeorder}\n"
                   f"Статус сделки: {status}\n"
                   f"{str(azn)} AZN = {str(rub)} руб.\n\n"
                   f"Карта клиента: {str(card)}")
            break

    inline = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Назад",
                    callback_data="history_0"
                )
            ]
        ]
    )

    await call.message.edit_text(text=txt, reply_markup=inline)


def create_check_image(date, order_num, idd, ttype, azn, ruble, num_card):
    img_width, img_height = 800, 400
    background_color = (255, 255, 255)
    text_color = (0, 0, 0)

    image = Image.new("RGB", (img_width, img_height), background_color)
    draw = ImageDraw.Draw(image)

    font_bold_path = os.path.join("Montserrat", "static", "Montserrat-Bold.ttf")
    font_regular_path = os.path.join("Montserrat", "static", "Montserrat-Regular.ttf")

    font_bold = ImageFont.truetype(font_bold_path, 40)
    font_regular = ImageFont.truetype(font_regular_path, 20)

    header_text = "Чек PulPulBot"
    header_bbox = draw.textbbox((0, 0), header_text, font=font_bold)
    header_width = header_bbox[2] - header_bbox[0]
    header_position = ((img_width - header_width) // 2, 20)
    draw.text(header_position, header_text, font=font_bold, fill=text_color)

    body_text = f"{date}\n\nСделка №{order_num}.\n\nTelegram ID пользователя: {idd}\n\n{ttype}\n\n{azn} AZN = {ruble} руб.\n\nНомер карты покупателя: {num_card}"
    body_position = (50, 100)
    draw.text(body_position, body_text, font=font_regular, fill=text_color)

    file_name = f"check_{str(order_num)}.png"
    image.save(file_name)
    return file_name


@router.callback_query(F.data.split("-")[0] == "close1")
async def close1(callback: CallbackQuery):
    await bot.unpin_chat_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
    await callback.message.edit_reply_markup(reply_markup=None)
    order_num = str(callback.data.split("-")[1])

    async with aiosqlite.connect('database.db') as conn:
        async with conn.execute(
            'SELECT order_num, chat_id, photo, ruble, azn, card, type FROM Application WHERE order_num = ?',
            (order_num,)
        ) as cursor:
            results = await cursor.fetchall()

    if results:
        user_id1 = results[0][1]
        ruble1 = results[0][3]
        azn1 = results[0][4]
        card1 = results[0][5]
        ttype1 = results[0][6]
    async with aiosqlite.connect('database.db') as conn:
        await conn.execute('UPDATE users SET buy = ? WHERE userid = ?', ("True", int(user_id1)))
        await conn.commit()

    fp = create_check_image(
        date=datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
        order_num=order_num,
        idd=user_id1,
        ttype=ttype1,
        azn=azn1,
        ruble=ruble1,
        num_card=card1
    )
    photo = FSInputFile(fp)
    await callback.message.answer_photo(
        photo=photo,
        caption=f"Сделка №{str(order_num)} закрыта!"
    )
    inline = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🛡Оспорить", callback_data=f"opendispute_{str(order_num)}")
            ],
            [
                InlineKeyboardButton(text="Оставить отзыв", callback_data=f"feedbback")
            ]
        ]
    )
    try:
        await bot.send_photo(
            chat_id=int(user_id1),
            photo=photo,
            caption=f"Сделка №{str(order_num)} закрыта!",
            reply_markup=inline
        )
    except:
        await callback.message.answer(
            text="Клиент заблокировал бот, сообщение не может быть доставлено"
        )
    async with aiosqlite.connect('database.db') as connection:
        await connection.execute(
            'INSERT INTO history (order_num, admin, user_id, azn, rub, card, date, status, typeorder) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (int(order_num), "CEO", int(user_id1), str(azn1), str(ruble1), str(card1),
             datetime.datetime.now().strftime("%d.%m.%Y %H:%M"), "Сделка состоялась", ttype1)
        )
        await connection.execute('DELETE FROM Application WHERE order_num = ?', (str(order_num),))
        await connection.commit()

    os.remove(path=fp)


@router.callback_query(F.data.split("-")[0] == "cancel1")
async def cmd_cancel1(callback: CallbackQuery):
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        await bot.unpin_chat_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
        await callback.message.answer(
            text=f"Заявка отклонена❌"
        )
        order_num = callback.data.split("-")[1]
        async with aiosqlite.connect('database.db') as conn:
            async with conn.execute('SELECT * FROM Application') as cursor:
                rows = await cursor.fetchall()

        for i in rows:
            if i[0] == order_num:
                chat_id = i[1]
                ruble = i[3]
                azn = i[4]
                card = i[5]
                break
        async with aiosqlite.connect('database.db') as conn:
            await conn.execute('UPDATE users SET buy = ? WHERE userid = ?', ("True", int(chat_id)))
            await conn.commit()

        inline = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🛡Оспорить", callback_data=f"opendispute_{str(order_num)}")
                ],
                [
                    InlineKeyboardButton(text="ℹ️О нас", callback_data="aboutus"),
                    InlineKeyboardButton(text="📊Курс", callback_data="ratenow")
                ],
                [
                    InlineKeyboardButton(text="Создать заявку на обмен", callback_data="makeanorder")
                ],
                [
                    InlineKeyboardButton(text="🛠Связаться с нами", callback_data="callus"),
                    InlineKeyboardButton(text="📋Отзывы клиентов", callback_data="feedbackus")
                ]
            ]
        )
        try:
            await bot.send_message(
                chat_id=int(chat_id),
                text=f"Заявка №<code>{order_num}</code>\n{str(ruble)} руб.\n{str(azn)}AZN\n\nОтклонена. Пожалуйста, оставьте новую заявку или свяжитесь с модератором.",
                parse_mode="HTML",
                reply_markup=inline
            )
        except:
            await callback.message.answer(
                text="Клиент заблокировал бот, сообщение не было доставлено"
            )
        async with aiosqlite.connect('database.db') as connection:
            await connection.execute(
                'INSERT INTO history (order_num, admin, user_id, azn, rub, card, date, status, typeorder) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (int(order_num), "CEO", int(chat_id), str(azn), str(ruble), str(card),
                 datetime.datetime.now().strftime("%d.%m.%Y %H:%M"), "Заявка отменена", "Покупка AZN")
            )
            await connection.execute('DELETE FROM Application WHERE order_num = ?', (str(order_num),))
            await connection.commit()
    except Exception as e:
        await callback.message.answer(
            text=f"Заявка уже отклонена❌"
        )
        print(e)


@router.callback_query(F.data.split("-")[0] == "close2")
async def close2(callback: CallbackQuery):
    try:
        await bot.unpin_chat_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
        await callback.message.edit_reply_markup(reply_markup=None)

        order_num = str(callback.data.split("-")[1])

        async with aiosqlite.connect('database.db') as conn:
            async with conn.execute(
                    'SELECT order_num, chat_id, photo, ruble, azn, card, type FROM Application WHERE order_num = ?',
                    (order_num,)
            ) as cursor:
                results = await cursor.fetchall()

        if results:
            user_id1 = results[0][1]
            ruble1 = results[0][3]
            azn1 = results[0][4]
            card1 = results[0][5]
            ttype1 = results[0][6]
        async with aiosqlite.connect('database.db') as conn:
            await conn.execute('UPDATE users SET sell = ? WHERE userid = ?', ("True", int(user_id1)))
            await conn.commit()

        fp = create_check_image(
            date=datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
            order_num=order_num,
            idd=user_id1,
            ttype=ttype1,
            azn=azn1,
            ruble=ruble1,
            num_card=card1
        )
        photo = FSInputFile(fp)
        await callback.message.answer_photo(
            photo=photo,
            caption=f"Сделка №{str(order_num)} закрыта!"
        )
        inline = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🛡Оспорить", callback_data=f"opendispute_{str(order_num)}")
                ],
                [
                    InlineKeyboardButton(text="Оставить отзыв", callback_data=f"feedbback")
                ]
            ]
        )

        try:
            await bot.send_photo(
                chat_id=int(user_id1),
                photo=photo,
                caption=f"Сделка №{str(order_num)} закрыта!",
                reply_markup=inline
            )
        except:
            await callback.message.answer(
                text="Клиент заблокировал бот, сообщение не может быть доставлено"
            )
        async with aiosqlite.connect('database.db') as connection:
            await connection.execute(
                'INSERT INTO history (order_num, admin, user_id, azn, rub, card, date, status, typeorder) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (int(order_num), "CEO", int(user_id1), str(azn1), str(ruble1), str(card1),
                 datetime.datetime.now().strftime("%d.%m.%Y %H:%M"), "Сделка состоялась", ttype1)
            )
            await connection.execute('DELETE FROM Application WHERE order_num = ?', (str(order_num),))
            await connection.commit()

        os.remove(path=fp)
    except Exception as e:
        print(e)
        await callback.message.answer(
            "Сделка уже закрыта"
        )


@router.callback_query(F.data.split("-")[0] == "cancel2")
async def cmd_cancel2(callback: CallbackQuery):
    try:
        await bot.unpin_chat_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
        await callback.message.edit_reply_markup(reply_markup=None)
        order_num = callback.data.split("-")[1]
        await callback.message.answer(
            text=f"Заявка отклонена❌"
        )

        async with aiosqlite.connect('database.db') as conn:
            async with conn.execute('SELECT * FROM Application') as cursor:
                rows = await cursor.fetchall()

        for i in rows:
            if i[0] == order_num:
                chat_id = i[1]
                ruble = i[3]
                azn = i[4]
                card = i[5]
                break

        async with aiosqlite.connect('database.db') as conn:
            await conn.execute('UPDATE users SET sell = ? WHERE userid = ?', ("True", int(chat_id)))
            await conn.commit()

        inline = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🛡Оспорить", callback_data=f"opendispute_{str(order_num)}")
                ],
                [
                    InlineKeyboardButton(text="ℹ️О нас", callback_data="aboutus"),
                    InlineKeyboardButton(text="📊Курс", callback_data="ratenow")
                ],
                [
                    InlineKeyboardButton(text="Создать заявку на обмен", callback_data="makeanorder")
                ],
                [
                    InlineKeyboardButton(text="🛠Связаться с нами", callback_data="callus"),
                    InlineKeyboardButton(text="📋Отзывы клиентов", callback_data="feedbackus")
                ]
            ]
        )

        try:
            await bot.send_message(
                chat_id=int(chat_id),
                text=f"Заявка №<code>{order_num}</code>\n{str(ruble)} руб.\n{str(azn)}AZN\n\nОтклонена. Пожалуйста, оставьте новую заявку или свяжитесь с нами.",
                parse_mode="HTML",
                reply_markup=inline
            )
        except:
            await callback.message.answer(
                text="Клиент заблокировал бот, сообщение не было доставлено"
            )

        async with aiosqlite.connect('database.db') as connection:
            await connection.execute(
                'INSERT INTO history (order_num, admin, user_id, azn, rub, card, date, status, typeorder) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (int(order_num), "CEO", int(chat_id), str(azn), str(ruble), str(card),
                 datetime.datetime.now().strftime("%d.%m.%Y %H:%M"), "Заявка отменена", "Продажа AZN")
            )
            await connection.execute('DELETE FROM Application WHERE order_num = ?', (str(order_num),))
            await connection.commit()
    except Exception as e:
        print(e)
        await callback.message.answer(
            text=f"Заявка уже отклонена❌"
        )


class AnswerDis(StatesGroup):
    text = State()


@router.callback_query(F.data.split("_")[0] == "giveansdisp")
async def giveans_disp(call: CallbackQuery, state: FSMContext):
    order_num = int(call.data.split("_")[1])
    await state.update_data(order_num=order_num)
    a = await call.message.answer(
        text="Введите ответ, который будет отправлен клиенту:"
    )
    await state.set_state(AnswerDis.text)


@router.message(AnswerDis.text)
async def AnswerDis_text(message: Message, state: FSMContext):
    user_data = await state.get_data()
    text = f"Ответ по спору:\nСделка №{user_data['order_num']}\n\n" + f"<blockquote>{message.html_text}</blockquote>"
    async with aiosqlite.connect('database.db') as connection:
        async with connection.cursor() as cursor:
            await cursor.execute('SELECT * FROM history')
            orders = await cursor.fetchall()

            for i_order in orders:
                if str(i_order[0]) == str(user_data['order_num']):
                    admin = i_order[1]
                    user_id = i_order[2]
                    azn = i_order[3]
                    rub = i_order[4]
                    card = i_order[5]
                    date = i_order[6]
                    status = i_order[7]
                    typeorder = i_order[8]

    await bot.send_message(
        chat_id=int(user_id),
        text=text,
        parse_mode="HTML"
    )
    await message.reply("Сообщение доставлено!")
    inline = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Связаться с клиентом", url=f"tg://user?id={str(user_id)}")
            ],
            [
                InlineKeyboardButton(text="Связаться с админом", url=f"tg://user?id={str(admin)}")
            ],
            [
                InlineKeyboardButton(text="Дать ответ", callback_data=f"giveansdisp_{str(user_data['order_num'])}"),
                InlineKeyboardButton(text="Закрыть спор", callback_data=f"closedisp_{str(user_data['order_num'])}")
            ]
        ]
    )
    await message.answer(
        text=f"Клиент @{str(user_id)} открыл спор по сделке №{str(user_data['order_num'])}\n\n"
             f"Тип сделки: {typeorder}\n{str(rub)} руб. = {str(azn)} AZN\nРеквизиты: \n{card}\n\nСтатус сделки: {status}\n{date}\n\nВремя открытия спора: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}",
        reply_markup=inline
    )


@router.callback_query(F.data.split("_")[0] == "closedisp")
async def closedisp(call: CallbackQuery):
    order_num = int(call.data.split("_")[1])
    await bot.unpin_chat_message(chat_id=call.from_user.id, message_id=call.message.message_id)
    async with aiosqlite.connect('database.db') as connection:
        async with connection.cursor() as cursor:
            await cursor.execute('SELECT * FROM history')
            orders = await cursor.fetchall()

            for i_order in orders:
                if str(i_order[0]) == str(order_num):
                    user_id = i_order[2]
                    azn = i_order[3]
                    rub = i_order[4]
                    card = i_order[5]
                    date = i_order[6]
                    status = i_order[7]
                    typeorder = i_order[8]
    text = f"Спор по сделке №{str(order_num)} закрыт!"
    await bot.send_message(
        chat_id=int(user_id),
        text=text,
        parse_mode="HTML"
    )
    await call.message.edit_text(
        text=f"Спор по сделке №{str(order_num)} закрыт!\n\n"
             f"Тип сделки: {typeorder}\nСтатус сделки: {status}\n{str(rub)} руб. = {str(azn)} AZN\nОтправитель: {card}\n\n"
             f"Дата: {date}"
    )


@router.callback_query(F.data == "document")
async def document(call: CallbackQuery):
    count_buy = 0
    count_sell = 0
    buy_rub, buy_azn, sell_rub, sell_azn = 0, 0, 0, 0
    async with aiosqlite.connect('database.db') as connection:
        async with connection.cursor() as cursor:
            await cursor.execute('SELECT * FROM history')
            documents = await cursor.fetchall()
            now = datetime.datetime.now()
            day_now = now.day
            month_now = now.month
            year_now = now.year

            for i_doc in documents:
                date = datetime.datetime.strptime(i_doc[6], '%d.%m.%Y %H:%M')
                day = date.day
                month = date.month
                year = date.year
                if day == day_now and month_now == month and year_now == year:
                    if i_doc[8] == "Покупка AZN":
                        buy_azn += int(i_doc[3])
                        buy_rub += int(i_doc[4])
                        count_buy += 1
                    else:
                        sell_azn += int(i_doc[3])
                        sell_rub += int(i_doc[4])
                        count_sell += 1
    inline = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Назад", callback_data="again")
            ]
        ]
    )
    text = (f"Отчет за {day_now}.{month_now}.{year_now}\n\n"
            f"Было совершенно {str(count_buy+count_sell)} сделок, из которых покупка AZN {str(count_buy)} и продажа AZN {str(count_sell)}\n\n"
            f"Тип сделок:\n\nПокупка AZN: продано {str(buy_azn)} AZN за {str(buy_rub)} RUB\n"
            f"Продажа AZN: куплено {str(sell_azn)} AZN за {str(sell_rub)} RUB")
    await call.message.edit_text(
        text=text,
        reply_markup=inline
    )


def create_pagination_keyboard(items, page: int = 0, items_per_page: int = 25):
    start = page * items_per_page
    end = start + items_per_page
    current_page_items = items[start:end]

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=current_page_items
    )

    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"historydocument_{page - 1}"))
    if end < len(items):
        navigation_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"historydocument_{page + 1}"))
    keyboard.inline_keyboard.append(
        navigation_buttons
    )
    keyboard.inline_keyboard.append(
        [
            InlineKeyboardButton(text="Назад", callback_data="again")
        ]
    )
    return keyboard


@router.callback_query(F.data.split("_")[0] == "historydocument")
async def historydocument(call: CallbackQuery):
    async with aiosqlite.connect('database.db') as connection:
        async with connection.cursor() as cursor:
            await cursor.execute('SELECT * FROM history')
            users = await cursor.fetchall()

            dates = []
            for user in users:
                date_str = datetime.datetime.strptime(user[6], '%d.%m.%Y %H:%M').strftime("%d.%m.%Y")
                if date_str not in dates:
                    dates.append(date_str)
    inline_lst = []
    for i_d in dates:
        inline_lst.append(
            [
                InlineKeyboardButton(
                    text=i_d,
                    callback_data=f"checkdoc_{i_d}"
                )
            ]
        )
    page = int(call.data.split("_")[1])

    inline_lst_true = create_pagination_keyboard(inline_lst, page)

    await call.message.edit_text(
        text="Выберете дату",
        reply_markup=inline_lst_true
    )


@router.callback_query(F.data.split("_")[0] == "checkdoc")
async def checkdoc(call: CallbackQuery):
    count_buy = 0
    count_sell = 0
    buy_rub, buy_azn, sell_rub, sell_azn = 0, 0, 0, 0
    async with aiosqlite.connect('database.db') as connection:
        async with connection.cursor() as cursor:
            await cursor.execute('SELECT * FROM history')
            documents = await cursor.fetchall()
            now = datetime.datetime.strptime(call.data.split("_")[1], '%d.%m.%Y')
            day_now = now.day
            month_now = now.month
            year_now = now.year

            for i_doc in documents:
                date = datetime.datetime.strptime(i_doc[6], '%d.%m.%Y %H:%M')
                day = date.day
                month = date.month
                year = date.year
                if day == day_now and month_now == month and year_now == year:
                    if i_doc[8] == "Покупка AZN":
                        buy_azn += int(i_doc[3])
                        buy_rub += int(i_doc[4])
                        count_buy += 1
                    else:
                        sell_azn += int(i_doc[3])
                        sell_rub += int(i_doc[4])
                        count_sell += 1
    inline = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Назад", callback_data="historydocument_0")
            ]
        ]
    )
    text = (f"Отчет за {day_now}.{month_now}.{year_now}\n\n"
            f"Было совершенно {str(count_buy+count_sell)} сделок, из которых покупка AZN {str(count_buy)} и продажа AZN {str(count_sell)}\n\n"
            f"Тип сделок:\n\nПокупка AZN: продано {str(buy_azn)} AZN за {str(buy_rub)} RUB\n"
            f"Продажа AZN: куплено {str(sell_azn)} AZN за {str(sell_rub)} RUB")
    await call.message.edit_text(
        text=text,
        reply_markup=inline
    )


