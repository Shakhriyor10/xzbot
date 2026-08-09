import asyncio
from aiogram import Bot, Dispatcher
from config import TOKEN
from database import init_db
from handlers.group_handlers import router as group_router
from handlers.user_handlers import router as user_router
from handlers.admin_handlers import router as admin_router

async def main():
    # 1. Bazani ishga tushirish
    init_db()

    # 2. Bot va Dispatcher yaratish
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # 3. Routerlarni ulash
    dp.include_router(group_router)
    dp.include_router(user_router)
    dp.include_router(admin_router)

    print("🚀 Bot Termux'da muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

