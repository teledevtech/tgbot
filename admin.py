import datetime
import aiosqlite
from aiogram import Router, F, Bot
from aiogram.filters import BaseFilter
from aiogram.filters.command import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from PIL import Image, ImageDraw, ImageFont
import text
import os
from info import TOKEN
from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable


class RoleMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        user_role = await self.get_user_role(user_id)
        event.role = user_role
        return await handler(event, data)

    async def get_user_role(self, user_id: int) -> str:
        async with aiosqlite.connect('database.db') as connection:
            async with connection.execute('SELECT * FROM admin WHERE id_admin = ?', (user_id,)) as cursor:
                result = await cursor.fetchone()
                print(result)
                return "admin" if result else "user"


class RoleFilter(BaseFilter):
    def __init__(self, role: str):
        self.role = role

    async def __call__(self, message: Message, role: str = "user") -> bool:
        print(role == self.role)
        return role == self.role


router = Router()
bot = Bot(token=TOKEN)


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


@router.callback_query(RoleFilter(role="admin"), F.data.split("-")[0] == "close1")
async def close1(callback: CallbackQuery):
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        await bot.unpin_chat_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
        order_num = str(callback.data.split("-")[1])

        async with aiosqlite.connect('database.db') as conn:
            async with conn.execute(
                    f'SELECT order_num, chat_id, photo, ruble, azn, card, type FROM I{str(callback.from_user.id)} WHERE order_num = ?',
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
                (int(order_num), str(callback.from_user.id), int(user_id1), str(azn1), str(ruble1), str(card1),
                 datetime.datetime.now().strftime("%d.%m.%Y %H:%M"), "Сделка состоялась", ttype1)
            )
            await connection.execute(f'DELETE FROM I{str(callback.from_user.id)} WHERE order_num = ?', (str(order_num),))
            await connection.execute(f'DELETE FROM Application WHERE order_num = ?', (str(order_num),))
            await connection.execute('UPDATE admin SET count = count - 1 WHERE id_admin = ?', (callback.from_user.id,))
            await connection.commit()

        os.remove(path=fp)
    except:
        await callback.message.answer(
            "Сделка уже закрыта"
        )


@router.callback_query(RoleFilter(role="admin"), F.data.split("-")[0] == "cancel1")
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
                (int(order_num), str(callback.from_user.id), int(chat_id), str(azn), str(ruble), str(card),
                 datetime.datetime.now().strftime("%d.%m.%Y %H:%M"), "Заявка отменена", "Покупка AZN")
            )
            await connection.execute(f'DELETE FROM I{str(callback.from_user.id)} WHERE order_num = ?', (str(order_num),))
            await connection.execute(f'DELETE FROM Application WHERE order_num = ?', (str(order_num),))
            await connection.execute('UPDATE admin SET count = count - 1 WHERE id_admin = ?', (callback.from_user.id,))
            await connection.commit()

    except:
        await callback.message.answer(
            text=f"Заявка уже отклонена❌"
        )


@router.callback_query(RoleFilter(role="admin"), F.data.split("-")[0] == "close2")
async def close2(callback: CallbackQuery):
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        await bot.unpin_chat_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)

        order_num = str(callback.data.split("-")[1])

        async with aiosqlite.connect('database.db') as conn:
            async with conn.execute(
                    f'SELECT order_num, chat_id, photo, ruble, azn, card, type FROM I{str(callback.from_user.id)} WHERE order_num = ?',
                    (order_num,)) as cursor:
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
                (int(order_num), str(callback.from_user.id), int(user_id1), str(azn1), str(ruble1), str(card1),
                 datetime.datetime.now().strftime("%d.%m.%Y %H:%M"), "Сделка состоялась", ttype1)
            )
            await connection.execute(f'DELETE FROM I{str(callback.from_user.id)} WHERE order_num = ?', (str(order_num),))
            await connection.execute(f'DELETE FROM Application WHERE order_num = ?', (str(order_num),))
            await connection.execute('UPDATE admin SET count = count - 1 WHERE id_admin = ?', (callback.from_user.id,))
            await connection.commit()

        os.remove(path=fp)
    except:
        await callback.message.answer(
            "Сделка уже закрыта"
        )


@router.callback_query(RoleFilter(role="admin"), F.data.split("-")[0] == "cancel2")
async def cmd_cancel2(callback: CallbackQuery):
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        await bot.unpin_chat_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
        order_num = callback.data.split("-")[1]
        await callback.message.answer(
            text=f"Заявка отклонена❌"
        )

        async with aiosqlite.connect('database.db') as conn:
            async with conn.execute(f'SELECT * FROM I{str(callback.from_user.id)}') as cursor:
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
                (int(order_num), str(callback.from_user.id), int(chat_id), str(azn), str(ruble), str(card),
                 datetime.datetime.now().strftime("%d.%m.%Y %H:%M"), "Заявка отменена", "Продажа AZN")
            )
            await connection.execute(f'DELETE FROM I{str(callback.from_user.id)} WHERE order_num = ?', (str(order_num),))
            await connection.execute(f'DELETE FROM Application WHERE order_num = ?', (str(order_num),))
            await connection.execute('UPDATE admin SET count = count - 1 WHERE id_admin = ?', (callback.from_user.id,))
            await connection.commit()
    except:
        await callback.message.answer(
            text=f"Заявка уже отклонена❌"
        )


@router.message(RoleFilter(role="admin"), Command("start"))
async def cmd_start(message: Message):
    inline = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Мои заявки", callback_data="myorders")
            ]
        ]
    )

    a = await message.answer(text.start, reply_markup=inline, parse_mode="HTML")
    await bot.delete_message(chat_id=message.from_user.id, message_id=a.message_id-1)


@router.callback_query(RoleFilter(role="admin"), F.data == "myorders")
async def cmd_all(call: CallbackQuery):
    async with aiosqlite.connect('database.db') as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(f'SELECT * FROM I{str(call.from_user.id)}')
            info = await cursor.fetchall()

            if len(info) != 0:
                inline = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text=f"{str(i[0])}", callback_data=f"order-{str(i[0])}")] for i in info
                    ]
                )
                await call.message.edit_text(text="📔Все заявки", reply_markup=inline)
            else:
                await call.message.edit_text("Заявок нет.")


@router.callback_query(RoleFilter(role="admin"), F.data.split("-")[0] == "order")
async def cmd_order_all(callback: CallbackQuery):
    async with aiosqlite.connect('database.db') as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(f'SELECT * FROM I{str(callback.from_user.id)}')
            users = await cursor.fetchall()

            order = callback.data.split("-")[1]
            for i in users:
                if i[0] == order:
                    lst = i[:]
                    break
            else:
                lst = None
    inline = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Закрыть сделку", callback_data=f"close1-{str(order)}")
            ],
            [
                InlineKeyboardButton(text="Отменить сделку", callback_data=f"cancel1-{str(order)}")
            ]
        ]
    )
    await callback.message.answer(
        text=f"Заявка №{lst[0]}\n\nТип заявки: {lst[-1]}\n\n{lst[-3]} AZN = {lst[-4]} руб.\n\n\n<blockquote><code>{lst[-2]}</code></blockquote>",
        parse_mode="HTML",
        reply_markup=inline
    )
