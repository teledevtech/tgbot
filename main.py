import asyncio
import head
import user
import admin
import datetime
from info import TOKEN
import logging
import aiosqlite
from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable


logging.basicConfig(level=logging.INFO, filename="work.log", filemode="w", format="%(asctime)s %(levelname)s %(message)s")


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
                return "admin" if result else "user"


async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.message.middleware(RoleMiddleware())
    dp.include_routers(head.router, user.router, admin.router)
    print(f"Бот успешно активирован! {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
