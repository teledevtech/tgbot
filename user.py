import datetime
import aiosqlite
import json
import random
from aiogram import Router, F, Bot
from aiogram.filters import BaseFilter
from aiogram.filters.command import Command, CommandStart
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import text
from info import HEAD, TOKEN, TGCHANNEL
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
        data['role'] = user_role

        return await handler(event, data)

    async def get_user_role(self, user_id: int) -> str:
        async with aiosqlite.connect('database.db') as connection:
            async with connection.execute('SELECT * FROM admin WHERE id_admin = ?', (user_id,)) as cursor:
                result = await cursor.fetchone()
                return "admin" if result else "user"


class RoleFilter(BaseFilter):
    def __init__(self, role: str):
        self.role = role

    async def __call__(self, message: Message, role: str = "user") -> bool:
        print(role == self.role)
        return role == self.role


router = Router()
router.message.middleware(RoleMiddleware())
bot = Bot(token=TOKEN)


async def generate():
    async with aiosqlite.connect('database.db') as conn:
        async with conn.execute('SELECT * FROM Application') as cursor:
            lst1 = await cursor.fetchall()

        async with conn.execute('SELECT * FROM history') as cursor:
            lst2 = await cursor.fetchall()

    lst_all = lst1 + lst2
    numlst = [i[0] for i in lst_all]
    a = str(random.randint(100, 1000000))
    while True:
        if a not in numlst:
            return a


async def addus(user_id: int) -> None:
    async with aiosqlite.connect('database.db') as connection:
        async with connection.execute('SELECT * FROM users') as cursor:
            users = await cursor.fetchall()
            flag = not any(user[0] == user_id for user in users)

    if flag:
        async with aiosqlite.connect('database.db') as connection:
            await connection.execute(
                'INSERT INTO users (userid, buy, sell) VALUES (?, ?, ?)',
                (user_id, "True", "True")
            )
            await connection.commit()


@router.message(RoleFilter(role="user"), CommandStart("start"))
async def cmd_start(message: Message):
    try:
        await addus(user_id=message.from_user.id)
        inline = InlineKeyboardMarkup(
            inline_keyboard=[
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
        a = await message.answer(text=text.start, reply_markup=inline, parse_mode="HTML")
        await bot.delete_message(chat_id=message.from_user.id, message_id=a.message_id - 1)
    except Exception as e:
        print(e)


@router.callback_query(RoleFilter(role="user"), F.data == "back")
async def back(call: CallbackQuery, state: FSMContext):
    await addus(user_id=call.from_user.id)
    await state.clear()
    inline = InlineKeyboardMarkup(
        inline_keyboard=[
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
    await call.message.edit_text(text.start, reply_markup=inline, parse_mode="HTML")


@router.callback_query(RoleFilter(role="user"), F.data == "aboutus")
async def cmd_about_us(call: CallbackQuery):
    await addus(user_id=call.from_user.id)
    inline = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="◀️Назад", callback_data="back")
            ]
        ]
    )

    await call.message.edit_text(text.aboutus, reply_markup=inline)


@router.callback_query(RoleFilter(role="user"), F.data == "makeanorder")
async def makeanorder(callback: CallbackQuery):
    await addus(user_id=callback.from_user.id)

    async with aiosqlite.connect('database.db') as connection:
        async with connection.execute('SELECT * FROM Rate') as cursor:
            rare = await cursor.fetchone()
            rate_buy = float(rare[0])
            rate_sell = float(rare[1])

    async with aiosqlite.connect('database.db') as conn:
        async with conn.execute('SELECT * FROM users') as cursor:
            uss = await cursor.fetchall()
    for i in uss:
        if str(i[0]) == str(callback.from_user.id):
            buy_status = i[1]
            sell_status = i[2]
            break

    if buy_status == 'True' and sell_status == 'True':
        lst = [
            KeyboardButton(
                text="Создать заявку на отправку AZN",
                web_app=WebAppInfo(
                    url=text.link_all1(rate_buy, rate_sell),
            KeyboardButton(
                text="Создать заявку на отправку AZN",
                web_app=WebAppInfo(
                    url=text.link_all2(rate_buy, rate_sell),
        ]
    if buy_status == 'True' and sell_status != 'True':
        lst = [
            KeyboardButton(
                text="Создать заявку на отправку AZN",
                web_app=WebAppInfo(url=text.link1(rate_buy)))
        ]
    if buy_status != 'True' and sell_status == 'True':
        lst = [
            KeyboardButton(
                text="Создать заявку на конвертацию AZN в RUB",
                web_app=WebAppInfo(url=text.link2(rate_sell)))
        ]

    kb = ReplyKeyboardMarkup(
        keyboard=[lst],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    txt = "На данный момента доступна только заявка на отправку <b>AZN</b>, тк предыдущая заявка на продажу <b>AZN</b> еще не закрыта👇" if buy_status and not(sell_status) else "На данный момента доступна только заявка на продажу <b>AZN</b>, тк предыдущая заявка на покупку <b>AZN</b> еще не закрыта👇" if sell_status and not(buy_status) else "Выберете тип заявки👇" if sell_status and buy_status else "К сожалению, вы не можете оставить заявку ни одного типа, тк предыдущие еще не закрыты!("
    if txt == "К сожалению, вы не можете оставить заявку ни одного типа, тк предыдущие еще не закрыты!(":
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="◀️Назад",
                        callback_data="back"
                    )
                ]
            ]
        )
    a = await callback.message.answer(
        text=txt,
        reply_markup=kb
    )
    try: await bot.delete_message(chat_id=callback.from_user.id, message_id=a.message_id-1)
    except: pass


class order_buy(StatesGroup):
    azn = State()
    name = State()
    ruble = State()
    photo = State()

class order_sell(StatesGroup):
    azn = State()
    name = State()
    ruble = State()
    photo = State()


@router.message(RoleFilter(role="user"), F.web_app_data)
async def webappdata(message: Message, state: FSMContext):
    data = json.loads(message.web_app_data.data)
    inline = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌Отменить", callback_data="cancelorder")]])
    if data["type"] == "buy":
        card = data["card"]
        date = data["date"]
        rub = data["rub"]
        azn = data["azn"]
        await state.update_data(azn=azn)
        await state.update_data(card=card)
        await state.update_data(rub=rub)
        await state.update_data(date=date)
        async with aiosqlite.connect('database.db') as connection:
            async with connection.execute('SELECT * FROM Bank') as cursor:
                card_for_pay = str((await cursor.fetchone())[0])
            async with connection.execute('SELECT * FROM Rate') as cursor:
                rare = await cursor.fetchone()
                rate_buy = float(rare[0])

        txt = (f"<b>Итого к оплате:</b> {str(rub)} RUB\n"
               f"<b>Вы получите:</b> {str(azn)} AZN\n"
               f"<b>По курсу:</b> {str(rate_buy)}\n\n"
               f"<b>Карта получателя:</b> {card} ({date})\n\n"
               f"Переведите <b>RUB</b> на <code>{card_for_pay}</code>\n\n"
               f"После перевода отправьте квитанцию о переводе👇")
        a = await message.answer(text=txt, reply_markup=inline, parse_mode="html")
        try: await bot.delete_message(chat_id=message.from_user.id, message_id=a.message_id - 1)
        except: pass
        try: await bot.delete_message(chat_id=message.from_user.id, message_id=a.message_id - 2)
        except: pass
        await state.set_state(order_buy.photo)
    else:
        phone = data["phone"]
        bankget = data["bankget"]
        fullname = data["fullname"]
        rub = data["rub"]
        azn = data["azn"]
        await state.update_data(azn=azn)
        await state.update_data(fullname=fullname)
        await state.update_data(phone=phone)
        await state.update_data(bankget=bankget)
        await state.update_data(rub=rub)
        await state.update_data(fullname=fullname)
        async with aiosqlite.connect('database.db') as connection:
            async with connection.execute('SELECT * FROM Bank') as cursor:
                card_for_pay = str((await cursor.fetchone())[1])
        async with aiosqlite.connect('database.db') as connection:
            async with connection.execute('SELECT * FROM Rate') as cursor:
                rare = await cursor.fetchone()
                rate_sell = float(rare[1])

        txt = (f"<b>Итого к оплате:</b> {str(azn)} AZN\n"
               f"<b>Вы получите:</b> {str(rub)} RUB\n"
               f"<b>По курсу:</b> {str(rate_sell)}\n\n"
               f"<b>Банк получателя:</b> {bankget}\n"
               f"<b>По номеру телефона:</b> {phone}\n\n"
               f"<b>ФИО получателя:</b> {fullname}\n\n"
               f"Переведите <b>AZN</b> на <code>{card_for_pay}</code>\n\n"
               f"После перевода отправьте квитанцию о переводе👇")
        a = await message.answer(text=txt, reply_markup=inline, parse_mode="html")
        try: await bot.delete_message(chat_id=message.from_user.id, message_id=a.message_id - 1)
        except: pass
        try: await bot.delete_message(chat_id=message.from_user.id, message_id=a.message_id - 2)
        except: pass
        await state.set_state(order_sell.photo)


@router.callback_query(RoleFilter(role="user"), F.data == "cancelorder")
async def cmd_cancelorder(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    inline = InlineKeyboardMarkup(
        inline_keyboard=[
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
    a = await callback.message.answer(text.start, reply_markup=inline, parse_mode="HTML")
    await bot.delete_message(chat_id=callback.from_user.id, message_id=a.message_id-1)


@router.message(RoleFilter(role="user"), order_buy.photo)
async def state_order_buy_photo(message: Message, state: FSMContext):
    if message.photo is not None:
        user_data = await state.get_data()
        photo = message.photo[-1].file_id
        order_num = await generate()
        inline = InlineKeyboardMarkup(
            inline_keyboard=[
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

        inline_admin = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Закрыть сделку", callback_data=f"close1-{str(order_num)}")
                ],
                [
                    InlineKeyboardButton(text="Отменить сделку", callback_data=f"cancel1-{str(order_num)}")
                ],
                [
                    InlineKeyboardButton(text="Посмотреть акк юзера", url=f"tg://user?id={str(message.from_user.id)}")
                ]
            ]
        )

        await message.answer("Ваша заявка на рассмотрении.", reply_markup=inline)

        async with aiosqlite.connect('database.db') as conn:
            await conn.execute('UPDATE users SET buy = ? WHERE userid = ?', ("False", message.from_user.id))
            await conn.commit()
        async with aiosqlite.connect('database.db') as conn:
            async with conn.execute('SELECT * FROM admin') as cursor:
                admin_id = await cursor.fetchall()

            admin = None
            a_min = 10000

            for i in admin_id:
                if a_min > i[0]:
                    a_min = i[0]
                    admin = i[1]

            if len(admin_id) == 0:
                admin = HEAD

                await conn.execute(
                    'INSERT INTO Application (order_num, chat_id, photo, ruble, azn, card, type) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (str(order_num), message.from_user.id, photo, str(user_data["rub"]), str(user_data['azn']),
                     str(f'{user_data["card"]} ({user_data["date"]})'), "Покупка AZN")
                )
            else:
                await conn.execute('UPDATE admin SET count = count + 1 WHERE id_admin = ?', (admin,))
                await conn.execute(
                    f'INSERT INTO I{str(admin)} (order_num, chat_id, photo, ruble, azn, card, type) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (str(order_num), message.from_user.id, photo, str(user_data["rub"]), str(user_data['azn']),
                     str(f'{user_data["card"]} ({user_data["date"]})'), "Покупка AZN")
                )

                await conn.execute(
                    'INSERT INTO Application (order_num, chat_id, photo, ruble, azn, card, type) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (str(order_num), message.from_user.id, photo, str(user_data["rub"]), str(user_data['azn']),
                     str(f'{user_data["card"]} ({user_data["date"]})'), "Покупка AZN")
                )

            await conn.commit()

        a = await bot.send_photo(
            chat_id=admin,
            photo=photo,
            caption=f"Пришла заявка на покупку <b>AZN</b>\n\nСумма перевода: \n{str(user_data['rub'])} руб. = {str(user_data['azn'])} AZN\n\nРеквизиты для перевода: <pre>{str(user_data['card'])}</pre>\n<pre>{str(user_data['date'])}</pre>",
            parse_mode="HTML",
            reply_markup=inline_admin
        )
        await bot.pin_chat_message(chat_id=admin, message_id=a.message_id)
        await state.clear()
    else:
        inline = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌Отменить", callback_data="cancelorder")]
            ]
        )
        await message.answer("Вы отправили не тот формат. Попробуйте еще раз:", reply_markup=inline)
        await state.set_state(order_buy.photo)


@router.message(RoleFilter(role="user"), order_sell.photo)
async def state_order_sell_photo(message: Message, state: FSMContext):
    if message.photo is not None:
        user_data = await state.get_data()

        photo = message.photo[-1].file_id
        order_num = await generate()
        inline = InlineKeyboardMarkup(
            inline_keyboard=[
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

        inline_admin = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Закрыть сделку", callback_data=f"close2-{str(order_num)}")
                ],
                [
                    InlineKeyboardButton(text="Отменить сделку", callback_data=f"cancel2-{str(order_num)}")
                ],
                [
                    InlineKeyboardButton(text="Посмотреть акк юзера", url=f"tg://user?id={str(message.from_user.id)}")
                ]
            ]
        )

        await message.answer("Ваша заявка на рассмотрении.", reply_markup=inline)

        fullname = user_data['fullname']
        phone = user_data['phone']
        bankget = user_data['bankget']
        info = f"{str(phone)} ({bankget}) {fullname}"

        async with aiosqlite.connect('database.db') as conn:
            await conn.execute('UPDATE users SET sell = ? WHERE userid = ?', ("False", message.from_user.id))
            await conn.commit()
        async with aiosqlite.connect('database.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('SELECT * FROM admin')
                admin_id = await cursor.fetchall()

                admin = None
                a_min = 10000

                for i in admin_id:
                    if a_min > i[0]:
                        a_min = i[0]
                        admin = i[1]

                if len(admin_id) == 0:
                    admin = HEAD
                    await cursor.execute(
                        'INSERT INTO Application (order_num, chat_id, photo, ruble, azn, card, type) VALUES (?, ?, ?, ?, ?, ?, ?)',
                        (str(order_num), message.from_user.id, photo, str(user_data["rub"]), str(user_data['azn']), info,
                        "Продажа AZN")
                    )
                else:
                    await cursor.execute('UPDATE admin SET count = count + 1 WHERE id_admin = ?', (admin,))
                    await cursor.execute(
                        f'INSERT INTO I{str(admin)} (order_num, chat_id, photo, ruble, azn, card, type) VALUES (?, ?, ?, ?, ?, ?, ?)',
                        (str(order_num), message.from_user.id, photo, str(user_data["rub"]), str(user_data['azn']), info,
                        "Продажа AZN")
                    )
                    await cursor.execute(
                        'INSERT INTO Application (order_num, chat_id, photo, ruble, azn, card, type) VALUES (?, ?, ?, ?, ?, ?, ?)',
                        (str(order_num), message.from_user.id, photo, str(user_data["rub"]), str(user_data['azn']), info,
                        "Продажа AZN")
                    )

                await conn.commit()
        await bot.send_photo(
            chat_id=admin,
            photo=photo,
            caption=f"Пришла заявка на продажу <b>AZN</b>\n\nСумма перевода:\n{str(user_data['azn'])} AZN = {str(user_data['rub'])} руб.\n\nРеквизиты для перевода: \n\n<pre>{str(phone)}</pre>\n{bankget}\n{fullname}",
            parse_mode="HTML",
            reply_markup=inline_admin
        )

        await state.clear()
    else:
        inline = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌Отменить", callback_data="cancelorder")]
            ]
        )
        await message.answer("Вы отправили не тот формат. Попробуйте еще раз:", reply_markup=inline)
        await state.set_state(order_buy.photo)


@router.callback_query(RoleFilter(role="user"), F.data == "callus")
async def cmd_support(call: CallbackQuery):
    await addus(user_id=call.from_user.id)
    inline = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="◀️Назад", callback_data="back")
            ]
        ]
    )
    await call.message.edit_text(text=text.sup, reply_markup=inline)


@router.callback_query(RoleFilter("user"), F.data == "feedbackus")
async def cmd_feedback(call: CallbackQuery):
    await addus(user_id=call.from_user.id)
    inline = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="◀️Назад", callback_data="back")
            ]
        ]
    )

    await call.message.edit_text(text=text.feedback, reply_markup=inline)


@router.callback_query(RoleFilter(role="user"), F.data == "ratenow")
async def cmd_rate_see(call: CallbackQuery):
    await addus(user_id=call.from_user.id)
    inline = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="◀️Назад", callback_data="back")
            ]
        ]
    )
    async with aiosqlite.connect('database.db') as connection:
        async with connection.execute('SELECT * FROM Rate') as cursor:
            users = await cursor.fetchall()
    await call.message.edit_text(
        text=f"Отправить в Азербайджан: \n"
             f"<b>1 AZN = {users[0][0]} руб.</b>\n\n"
             f"Продать нам:\n<b>1 AZN = {users[0][1]} руб.</b>",
        reply_markup=inline,
        parse_mode="HTML"
    )


class Fdeeee(StatesGroup):
    text = State()


@router.callback_query(RoleFilter(role="user"), F.data == "feedbback")
async def cmd_feedbback(callback: CallbackQuery, state: FSMContext):
    inline = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Отменить", callback_data="cancelorder")
            ]
        ]
    )
    await callback.message.edit_text(
        text="Напишите внизу, как прошла сделка:",
        reply_markup=inline
    )
    await state.set_state(Fdeeee.text)


@router.message(RoleFilter(role="user"), Fdeeee.text)
async def cmf_Fdeee_text(message: Message, state: FSMContext):
    global admin
    a = await message.answer("Спасибо за отзыв!")
    await bot.delete_message(chat_id=message.from_user.id,message_id=a.message_id-1)
    await bot.delete_message(chat_id=message.from_user.id,message_id=a.message_id-2)
    await bot.forward_message(
        chat_id=TGCHANNEL,
        from_chat_id=message.from_user.id,
        message_id=message.message_id
    )
    await state.clear()


@router.callback_query(RoleFilter(role="user"), F.data.split("_")[0] == "opendispute")
async def opendispute(call: CallbackQuery):
    order_num = call.data.split("_")[1]

    async with aiosqlite.connect('database.db') as connection:
        async with connection.cursor() as cursor:
            await cursor.execute('SELECT * FROM history')
            orders = await cursor.fetchall()

            for i_order in orders:
                if str(i_order[0]) == str(order_num):
                    admin = i_order[1]
                    azn = i_order[3]
                    rub = i_order[4]
                    card = i_order[5]
                    date = i_order[6]
                    status = i_order[7]
                    typeorder = i_order[8]
    inline = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Связаться с клиентом", url=f"tg://user?id={str(call.from_user.id)}")
            ],
            [
                InlineKeyboardButton(text="Связаться с админом", url=f"tg://user?id={str(admin)}")
            ],
            [
                InlineKeyboardButton(text="Дать ответ", callback_data=f"giveansdisp_{str(order_num)}"),
                InlineKeyboardButton(text="Закрыть спор", callback_data=f"closedisp_{str(order_num)}")
            ]
        ]
    )
    a = await bot.send_message(
        chat_id=HEAD,
        text=f"Клиент @{str(call.from_user.username)} открыл спор по сделке №{str(order_num)}\n\n"
             f"Тип сделки: {typeorder}\n{str(rub)} руб. = {str(azn)} AZN\nРеквизиты: \n{card}\n\nСтатус сделки: {status}\n{date}\n\nВремя открытия спора: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}",
        reply_markup=inline
    )
    await bot.pin_chat_message(chat_id=HEAD, message_id=a.message_id)

    await call.message.edit_reply_markup(
        reply_markup=None
    )
    await call.message.reply(
        text="Спор по сделке открыт.\n"
             "Свяжитесь с нами и отправьте доказательства того, что вы правы.\n"
             "Наши сотрудники никогда не напишут вам первыми!\n\nПоддержка: @telegram"
    )
