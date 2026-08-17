import asyncio

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import OWNER_IDS
from database import (
    get_all_admins,
    get_all_ads_stat,
    get_all_users,
)

router = Router()

class BroadcastState(StatesGroup):
    waiting_for_message = State()

# 📊 1. ADMIN STATISTIKASI (`/stat` buyrug'i)
@router.message(Command("stat"), F.chat.type == "private")
async def show_bot_stats(message: types.Message):
    all_admins = set(get_all_admins())
    all_admins.update(OWNER_IDS)

    if message.from_user.id not in all_admins:
        return

    users_count = len(get_all_users())
    total_ads, total_groups = get_all_ads_stat()

    text = (
        f"<b>📊 BOT UMUMIY STATISTIKASI:</b>\n\n"
        f"👤 <b>Jami foydalanuvchilar:</b> {users_count} ta\n"
        f"📩 <b>Jami topshirilgan reklamalar:</b> {total_ads} ta\n"
        f"👥 <b>Reklama berilgan guruhlar:</b> {total_groups} ta"
    )
    await message.answer(text, parse_mode="HTML")

# 📢 2. BARCHA FOYDALANUVCHILARGA XABAR TARQATISH (`/reklama` yoki `/broadcast`)
@router.message(Command("broadcast"), F.chat.type == "private")
@router.message(Command("reklama"), F.chat.type == "private")
async def start_broadcast(message: types.Message, state: FSMContext):
    all_admins = set(get_all_admins())
    all_admins.update(OWNER_IDS)

    if message.from_user.id not in all_admins:
        return

    await state.set_state(BroadcastState.waiting_for_message)
    await message.answer("<b>📢 Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni (rasm, matn, video) yuboring:</b>", parse_mode="HTML")

@router.message(BroadcastState.waiting_for_message, F.chat.type == "private")
async def process_broadcast_message(message: types.Message, state: FSMContext):
    users = get_all_users()
    await state.clear()

    await message.answer(f"<b>🚀 Xabar {len(users)} ta foydalanuvchiga yuborilmoqda...</b>", parse_mode="HTML")

    success = 0
    failed = 0

    for user_id in users:
        try:
            await message.send_copy(chat_id=user_id)
            success += 1
            await asyncio.sleep(0.05)  # Telegram limitiga tushmaslik uchun kichik tanaffus
        except Exception:
            failed += 1

    await message.answer(
        f"<b>✅ Reklama tarqatish yakunlandi!</b>\n\n"
        f"🟢 <b>Muvaffaqiyatli yetib bordi:</b> {success} ta\n"
        f"🔴 <b>Yetib bormadi (botni bloklagan):</b> {failed} ta",
        parse_mode="HTML"
    )
