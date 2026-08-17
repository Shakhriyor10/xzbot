import asyncio

from aiogram import Bot, Dispatcher

from account_manager import account_manager
from config import TOKEN
from database import init_db
from handlers.account_handlers import router as account_router
from handlers.admin_handlers import router as admin_router
from handlers.group_handlers import router as group_router
from handlers.user_handlers import router as user_router


async def main():
    # 1. Bazani ishga tushirish
    init_db()

    # 2. Bot va Dispatcher yaratish
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    await account_manager.restore()

    # 3. Routerlarni ulash
    dp.include_router(group_router)
    dp.include_router(account_router)
    dp.include_router(user_router)
    dp.include_router(admin_router)

    print("Bot muvaffaqiyatli ishga tushdi...")
    try:
        await dp.start_polling(bot, drop_pending_updates=True)
    finally:
        await account_manager.shutdown()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())

