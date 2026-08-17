from html import escape

from aiogram import F, Router, types
from aiogram.filters import Command

from database import (
    get_group_admin_activity,
    get_top_daily_active,
    get_top_monthly_active,
    log_group_message,
)

router = Router()


def display_name(full_name, username):
    if username:
        return f"@{escape(username)}"

    return escape(full_name or "Noma'lum")


def medal(index):
    if index == 1:
        return "🥇"
    if index == 2:
        return "🥈"
    if index == 3:
        return "🥉"

    return f"{index}."


async def get_admin_ids(bot, chat_id):
    admins = await bot.get_chat_administrators(chat_id)

    return [
        admin.user.id
        for admin in admins
        if not admin.user.is_bot
    ]


def activity_keyboard():
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="👑 Adminlar aktivligi",
                    callback_data="group_admin_activity"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="🔄 Yangilash",
                    callback_data="group_activity_refresh"
                )
            ]
        ]
    )


def build_activity_text(daily, monthly):
    text = "<b>🏆 GURUH FAOLLIGI</b>\n\n"

    text += "<b>📅 Bugungi TOP 5 — oddiy odamlar:</b>\n"

    if daily:
        for i, row in enumerate(daily, 1):
            user_id, full_name, username, count = row

            name = display_name(
                full_name,
                username
            )

            text += (
                f"{medal(i)} <b>{name}</b> — "
                f"{count} ta xabar\n"
            )
    else:
        text += "Hali aktivlik yo'q.\n"

    text += "\n"

    text += "<b>📆 Oylik TOP 5 — oddiy odamlar:</b>\n"

    if monthly:
        for i, row in enumerate(monthly, 1):
            user_id, full_name, username, count = row

            name = display_name(
                full_name,
                username
            )

            text += (
                f"{medal(i)} <b>{name}</b> — "
                f"{count} ta xabar\n"
            )
    else:
        text += "Hali oylik aktivlik yo'q.\n"

    return text


# ============================================================
# 📊 /AKTIV
# ============================================================

@router.message(
    Command("aktiv"),
    F.chat.type.in_({"group", "supergroup"})
)
async def show_group_activity(
    message: types.Message
):
    chat_id = message.chat.id

    # Adminlarni topamiz.
    admin_ids = await get_admin_ids(
        message.bot,
        chat_id
    )

    # /aktiv yozgan odamni BU YERDA alohida sanamaymiz.
    # Chunki pastdagi umumiy tracker uni allaqachon hisoblaydi.
    daily = get_top_daily_active(
        group_id=chat_id,
        limit=5,
        exclude_user_ids=admin_ids
    )

    monthly = get_top_monthly_active(
        group_id=chat_id,
        limit=5,
        exclude_user_ids=admin_ids
    )

    text = build_activity_text(
        daily,
        monthly
    )

    await message.answer(
        text,
        reply_markup=activity_keyboard(),
        parse_mode="HTML"
    )


# ============================================================
# 👑 ADMINLAR AKTIVLIGI
# ============================================================

@router.callback_query(
    F.data == "group_admin_activity"
)
async def show_group_admin_activity(
    callback: types.CallbackQuery
):
    if not callback.message:
        await callback.answer()
        return

    if callback.message.chat.type not in {
        "group",
        "supergroup"
    }:
        await callback.answer(
            "Bu tugma faqat guruhda ishlaydi.",
            show_alert=True
        )
        return

    chat_id = callback.message.chat.id

    admin_ids = await get_admin_ids(
        callback.bot,
        chat_id
    )

    daily = get_group_admin_activity(
        chat_id,
        admin_ids,
        monthly=False
    )

    monthly = get_group_admin_activity(
        chat_id,
        admin_ids,
        monthly=True
    )

    text = "<b>👑 GURUHDAGI ADMINLAR AKTIVLIGI</b>\n\n"

    text += "<b>📅 Bugungi:</b>\n"

    if daily:
        for i, row in enumerate(daily, 1):
            user_id, full_name, username, count = row

            name = display_name(
                full_name,
                username
            )

            text += (
                f"{i}. <b>{name}</b> — "
                f"{count} ta xabar\n"
            )
    else:
        text += "Adminlar topilmadi.\n"

    text += "\n<b>📆 Oylik:</b>\n"

    if monthly:
        for i, row in enumerate(monthly, 1):
            user_id, full_name, username, count = row

            name = display_name(
                full_name,
                username
            )

            text += (
                f"{i}. <b>{name}</b> — "
                f"{count} ta xabar\n"
            )
    else:
        text += "Adminlar topilmadi.\n"

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="⬅️ Aktivlikka qaytish",
                    callback_data="group_activity_refresh"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# 🔄 YANGILASH
# ============================================================

@router.callback_query(
    F.data == "group_activity_refresh"
)
async def refresh_group_activity(
    callback: types.CallbackQuery
):
    if not callback.message:
        await callback.answer()
        return

    if callback.message.chat.type not in {
        "group",
        "supergroup"
    }:
        await callback.answer(
            "Bu tugma faqat guruhda ishlaydi.",
            show_alert=True
        )
        return

    chat_id = callback.message.chat.id

    admin_ids = await get_admin_ids(
        callback.bot,
        chat_id
    )

    daily = get_top_daily_active(
        group_id=chat_id,
        limit=5,
        exclude_user_ids=admin_ids
    )

    monthly = get_top_monthly_active(
        group_id=chat_id,
        limit=5,
        exclude_user_ids=admin_ids
    )

    text = build_activity_text(
        daily,
        monthly
    )

    await callback.message.edit_text(
        text,
        reply_markup=activity_keyboard(),
        parse_mode="HTML"
    )

    try:
        await callback.answer("🔄 Yangilandi")
    except Exception as e:
        # Callback eskirgan bo'lsa Telegram xato qaytarishi mumkin.
        if "query is too old" not in str(e) and "query ID is invalid" not in str(e):
            print(f"⚠️ Callback javobida xato: {e}")


# ============================================================
# 🔨 !unadmin @username
# ============================================================


# ============================================================
# 💬 GURUHDAGI XABARLARNI HISOBLASH
# ============================================================

@router.message(
    F.chat.type.in_({
        "group",
        "supergroup"
    })
)
async def track_group_messages(
    message: types.Message
):
    if not message.from_user:
        return

    if message.from_user.is_bot:
        return

    # /aktiv buyrug'ini bu yerda alohida
    # qayta sanamaymiz.
    if (
        message.text
        and message.text.split()[0].lower()
        in {
            "/aktiv",
            "/aktiv@"
        }
    ):
        return

    log_group_message(
        user_id=message.from_user.id,
        group_id=message.chat.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username or ""
    )

# ============================================================
# 🚫 ADMIN 15 TA ODAMNI KETMA-KET CHIQARISH NAZORATI
# 🤖 BOTLAR HISOBLANMAYDI
# ============================================================

_admin_kick_counts = {}


@router.chat_member()
async def track_admin_kicks(event: types.ChatMemberUpdated):
    # Faqat guruh/superguruh
    if event.chat.type not in {"group", "supergroup"}:
        return

    # Faqat haqiqiy foydalanuvchi chiqarilganda
    if not event.old_chat_member or not event.new_chat_member:
        return

    # Faqat LEFT/KICKED holatini tekshiramiz
    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status

    if new_status not in {"left", "kicked"}:
        return

    # Oldin ham chiqarilgan holatda bo'lsa — qayta hisoblamaymiz
    if old_status in {"left", "kicked"}:
        return

    # Chiqarilgan odam BOT bo'lsa — hisoblanmaydi
    target_user = event.new_chat_member.user

    if target_user.is_bot:
        return

    # Kim bajarganini aniqlaymiz
    actor = event.from_user

    if not actor:
        return

    # Bot bajargan harakat — hisoblanmaydi
    if actor.is_bot:
        return



    # Faqat guruh administratori odam chiqargan bo'lsa
    try:
        actor_member = await event.bot.get_chat_member(
            event.chat.id,
            actor.id
        )
    except Exception as e:
        print(f"⚠️ Adminni tekshirishda xato: {e}")
        return

    if actor_member.status not in {"administrator", "creator"}:
        return

    # Username bo'lsa username, bo'lmasa Telegram ID
    if actor.username:
        target = f"@{actor.username}"
    else:
        target = str(actor.id)

    # Group Help uchun buyruq
    try:
        await event.bot.send_message(
            event.chat.id,
            f"!unadmin {target}"
        )
        print(f"✅ Group Help uchun yuborildi: !unadmin {target}")
    except Exception as e:
        print(f"⚠️ !unadmin yuborishda xato: {e}")
