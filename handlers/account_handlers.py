import logging
import re
from html import escape

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telethon.errors import (
    PasswordHashInvalidError,
    PhoneCodeExpiredError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
)

from account_credentials import credential_store
from account_manager import AccountError, CollectionFlow, account_manager
from database import (
    delete_account_text,
    get_account_ad_group,
    get_account_ad_groups,
    get_account_text,
    get_connected_account,
    get_connected_accounts,
    save_account_text,
)
from states import AddAccountState

router = Router()
logger = logging.getLogger(__name__)


def _account_label(row) -> str:
    _account_id, username, display_name, _session_name = row
    return f"@{username}" if username else (display_name or str(row[0]))


def _back(callback_data: str):
    return [InlineKeyboardButton(text="◀️ Orqaga", callback_data=callback_data)]


def account_menu_keyboard(owner_user_id: int) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"👤 {_account_label(account)}",
                callback_data=f"acc:open:{account[0]}",
            )
        ]
        for account in get_connected_accounts(owner_user_id)
    ]
    rows.append([InlineKeyboardButton(text="➕ Account ulash", callback_data="acc:add")])
    rows.append(_back("main_menu"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def account_actions_keyboard(account_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📨 Kelgan reklamalar", callback_data=f"acc:groups:{account_id}")],
            [InlineKeyboardButton(text="📝 Text Joylash", callback_data=f"acc:text:{account_id}")],
            _back("acc:menu"),
        ]
    )


def text_menu_keyboard(account_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Text qo‘shish", callback_data=f"acc:textadd:{account_id}")],
            [InlineKeyboardButton(text="👁 Textni ko‘rish", callback_data=f"acc:textshow:{account_id}")],
            [InlineKeyboardButton(text="🗑 Textni o‘chirish", callback_data=f"acc:textdel:{account_id}")],
            _back(f"acc:open:{account_id}"),
        ]
    )


def group_actions_keyboard(account_id: int, row_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Username terish", callback_data=f"acc:collect:{account_id}:{row_id}")],
            [InlineKeyboardButton(text="👑 Admin userlarni terish", callback_data=f"acc:admins:{account_id}:{row_id}")],
            _back(f"acc:groups:{account_id}"),
        ]
    )


def users_keyboard(flow: CollectionFlow, back_data: str) -> InlineKeyboardMarkup:
    rows = []
    for user in list(flow.users.values())[:80]:
        if user.sent is True:
            label = "☑️ Yuborildi"
        elif user.sent is False:
            label = "❌ Yuborilmadi"
        else:
            label = f"👤 {user.label}"
        rows.append([
            InlineKeyboardButton(text=label[:64], callback_data=f"acc:send:{user.user_id}")
        ])
    rows.append(_back(back_data))
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _safe_edit(callback: types.CallbackQuery, text: str, keyboard: InlineKeyboardMarkup):
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "acc:menu")
async def account_menu(callback: types.CallbackQuery, state: FSMContext):
    await account_manager.cancel_login(callback.from_user.id)
    await state.clear()
    accounts = get_connected_accounts(callback.from_user.id)
    text = (
        "<b>📱 Ulangan accountlar</b>\n\nAccountni tanlang:"
        if accounts
        else "<b>📱 Account ulanmagan</b>\n\nAccount ulashni boshlang."
    )
    await _safe_edit(callback, text, account_menu_keyboard(callback.from_user.id))
    await callback.answer()


@router.callback_query(F.data == "acc:add")
async def add_account(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not account_manager.configured_for(callback.from_user.id):
        await state.set_state(AddAccountState.waiting_for_api_id)
        await _safe_edit(
            callback,
            "<b>🔑 Telegram API sozlamasi</b>\n\n"
            "<code>my.telegram.org/apps</code> sahifasidagi raqamli "
            "<b>App api_id</b> qiymatini yuboring.",
            InlineKeyboardMarkup(inline_keyboard=[_back("acc:menu")]),
        )
        await callback.answer()
        return
    await state.set_state(AddAccountState.waiting_for_phone)
    await _safe_edit(
        callback,
        "<b>📱 Account ulash</b>\n\nTelefon raqamingizni xalqaro formatda "
        "yuboring yoki pastdagi tugma orqali ulashing.\n\n"
        "Masalan: <code>+998901234567</code>",
        InlineKeyboardMarkup(inline_keyboard=[_back("acc:menu")]),
    )
    await callback.answer()
    await callback.message.answer(
        "📞 Telefon raqamingiz:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📞 Raqamni yuborish", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )


@router.message(AddAccountState.waiting_for_api_id, F.chat.type == "private")
async def process_api_id(message: types.Message, state: FSMContext):
    value = (message.text or "").strip()
    if not value.isdigit() or int(value) <= 0:
        await message.answer("❌ TELEGRAM_API_ID faqat musbat raqam bo‘lishi kerak.")
        return
    await state.update_data(account_api_id=int(value))
    await state.set_state(AddAccountState.waiting_for_api_hash)
    await message.answer(
        "🔐 Endi <code>my.telegram.org/apps</code> sahifasidagi "
        "<b>App api_hash</b> qiymatini yuboring.\n\n"
        "Xabar darhol o‘chiriladi va API_HASH shifrlangan holda saqlanadi.",
        parse_mode="HTML",
    )


@router.message(AddAccountState.waiting_for_api_hash, F.chat.type == "private")
async def process_api_hash(message: types.Message, state: FSMContext):
    api_hash = (message.text or "").strip()
    try:
        await message.delete()
    except Exception:
        logger.warning("Could not delete API_HASH message", exc_info=True)
    if not re.fullmatch(r"[A-Fa-f0-9]{32}", api_hash):
        await message.answer(
            "❌ TELEGRAM_API_HASH formati noto‘g‘ri. U 32 ta hexadecimal belgidan iborat. "
            "Qayta yuboring."
        )
        return
    data = await state.get_data()
    api_id = data.get("account_api_id")
    if not api_id:
        await state.clear()
        await message.answer("❌ TELEGRAM_API_ID topilmadi. Account ulashni qayta boshlang.")
        return
    try:
        credential_store.save(message.from_user.id, int(api_id), api_hash)
    except Exception as exc:
        logger.exception("Could not securely store API credentials")
        await state.clear()
        await message.answer(f"❌ API sozlamasi saqlanmadi: {type(exc).__name__}")
        return
    finally:
        api_hash = ""
    await state.clear()
    await state.set_state(AddAccountState.waiting_for_phone)
    await message.answer(
        "✅ API sozlamasi xavfsiz saqlandi.\n\n📞 Endi telefon raqamingizni yuboring:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📞 Raqamni yuborish", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )


@router.message(AddAccountState.waiting_for_phone, F.chat.type == "private")
async def process_phone(message: types.Message, state: FSMContext):
    if message.contact:
        if message.contact.user_id and message.contact.user_id != message.from_user.id:
            await message.answer("❌ Faqat o‘zingizning telefon raqamingizni yuboring.")
            return
        raw_phone = message.contact.phone_number
    else:
        raw_phone = message.text or ""
    phone = "+" + re.sub(r"\D", "", raw_phone)
    if not re.fullmatch(r"\+[1-9]\d{7,14}", phone):
        await message.answer("❌ Telefon raqami noto‘g‘ri. Masalan: +998901234567")
        return
    try:
        await account_manager.begin_phone_login(message.from_user.id, phone)
    except PhoneNumberInvalidError:
        await message.answer("❌ Telegram bu telefon raqamini qabul qilmadi.")
        return
    except AccountError as exc:
        await message.answer(str(exc))
        return
    except Exception as exc:
        logger.exception("Phone login could not be started for owner=%s", message.from_user.id)
        await message.answer(f"❌ Login kodi yuborilmadi: {type(exc).__name__}")
        return
    await state.set_state(AddAccountState.waiting_for_code)
    await message.answer(
        "📨 Telegram yuborgan bir martalik kodni kiriting.\n\n"
        "Kod faqat shu so‘rov uchun ishlatiladi va saqlanmaydi.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(AddAccountState.waiting_for_code, F.chat.type == "private")
async def process_login_code(message: types.Message, state: FSMContext):
    code = re.sub(r"\D", "", message.text or "")
    try:
        await message.delete()
    except Exception:
        logger.warning("Could not delete one-time login code message", exc_info=True)
    if not 4 <= len(code) <= 8:
        await message.answer("❌ Kod formati noto‘g‘ri. Telegram yuborgan kodni qayta kiriting.")
        return
    try:
        status, me = await account_manager.finish_code(message.from_user.id, code)
    except PhoneCodeInvalidError:
        await message.answer("❌ Login kodi noto‘g‘ri. Qayta yuboring.")
        return
    except PhoneCodeExpiredError:
        await account_manager.cancel_login(message.from_user.id)
        await state.clear()
        await message.answer("⌛️ Login kodi eskirdi. Account ulashni qayta boshlang.")
        return
    except Exception as exc:
        logger.exception("Login code verification failed for owner=%s", message.from_user.id)
        await account_manager.cancel_login(message.from_user.id)
        await state.clear()
        await message.answer(f"❌ Account ulanmagan: {type(exc).__name__}")
        return
    finally:
        code = ""
    if status == "2fa":
        await state.set_state(AddAccountState.waiting_for_2fa)
        await message.answer(
            "🔐 Accountda 2FA yoqilgan. Parolni yuboring. Xabar darhol o‘chiriladi "
            "va parol DB/FSM/logga yozilmaydi."
        )
        return
    await state.clear()
    await message.answer(
        f"✅ Account ulandi: <b>{escape('@' + me.username if me.username else me.first_name)}</b>",
        parse_mode="HTML",
        reply_markup=account_menu_keyboard(message.from_user.id),
    )


@router.message(AddAccountState.waiting_for_2fa, F.chat.type == "private")
async def process_2fa(message: types.Message, state: FSMContext):
    password = message.text or ""
    try:
        await message.delete()
    except Exception:
        logger.warning("Could not delete one-time 2FA message", exc_info=True)
    try:
        me = await account_manager.finish_2fa(message.from_user.id, password)
    except PasswordHashInvalidError:
        await message.answer("❌ 2FA paroli noto‘g‘ri. Qayta yuboring.")
        return
    except Exception as exc:
        logger.exception("2FA sign-in failed for owner=%s", message.from_user.id)
        await state.clear()
        await account_manager.cancel_login(message.from_user.id)
        await message.answer(f"❌ Account ulanmagan: {type(exc).__name__}")
        return
    finally:
        password = ""
    await state.clear()
    await message.answer(
        f"✅ Account ulandi: <b>{escape('@' + me.username if me.username else me.first_name)}</b>",
        parse_mode="HTML",
        reply_markup=account_menu_keyboard(message.from_user.id),
    )


@router.callback_query(F.data.startswith("acc:open:"))
async def open_account(callback: types.CallbackQuery):
    account_id = int(callback.data.rsplit(":", 1)[1])
    row = get_connected_account(callback.from_user.id, account_id)
    if not row:
        await callback.answer("❌ Account topilmadi.", show_alert=True)
        return
    await _safe_edit(
        callback,
        f"<b>📱 {escape(_account_label(row))}</b>",
        account_actions_keyboard(account_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("acc:text:"))
async def text_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    account_id = int(callback.data.rsplit(":", 1)[1])
    await _safe_edit(callback, "<b>📝 Text Joylash</b>", text_menu_keyboard(account_id))
    await callback.answer()


@router.callback_query(F.data.startswith("acc:textadd:"))
async def text_add(callback: types.CallbackQuery, state: FSMContext):
    account_id = int(callback.data.rsplit(":", 1)[1])
    await state.set_state(AddAccountState.waiting_for_forward)
    await state.update_data(account_text_id=account_id)
    await _safe_edit(
        callback,
        "<b>➕ Text qo‘shish</b>\n\nFaqat boshqa chatdan <b>forward qilingan</b> "
        "textli xabarni yuboring. Oddiy xabar qabul qilinmaydi.",
        InlineKeyboardMarkup(inline_keyboard=[_back(f"acc:text:{account_id}")]),
    )
    await callback.answer()


@router.message(AddAccountState.waiting_for_forward, F.chat.type == "private")
async def receive_forwarded_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    account_id = int(data.get("account_text_id", 0))
    text = message.text or message.caption
    if message.forward_origin is None or not text:
        await message.answer("❌ Faqat forward qilingan textli xabar qabul qilinadi.")
        return
    if not get_connected_account(message.from_user.id, account_id):
        await state.clear()
        await message.answer("❌ Account topilmadi.")
        return
    save_account_text(message.from_user.id, account_id, text)
    await state.clear()
    await message.answer(
        "✅ Forward qilingan text saqlandi.",
        reply_markup=text_menu_keyboard(account_id),
    )


@router.callback_query(F.data.startswith("acc:textshow:"))
async def text_show(callback: types.CallbackQuery):
    account_id = int(callback.data.rsplit(":", 1)[1])
    text = get_account_text(callback.from_user.id, account_id)
    body = escape(text[:3500]) if text else "Text saqlanmagan."
    await _safe_edit(callback, f"<b>👁 Saqlangan text</b>\n\n{body}", text_menu_keyboard(account_id))
    await callback.answer()


@router.callback_query(F.data.startswith("acc:textdel:"))
async def text_delete(callback: types.CallbackQuery):
    account_id = int(callback.data.rsplit(":", 1)[1])
    deleted = delete_account_text(callback.from_user.id, account_id)
    await _safe_edit(
        callback,
        "✅ Text o‘chirildi." if deleted else "ℹ️ O‘chirish uchun text yo‘q.",
        text_menu_keyboard(account_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("acc:groups:"))
async def groups(callback: types.CallbackQuery):
    account_id = int(callback.data.rsplit(":", 1)[1])
    rows = []
    for row_id, group_name, _link, _date in get_account_ad_groups(50):
        name = (group_name or "Noma’lum guruh")[:52]
        rows.append([InlineKeyboardButton(text=f"👥 {name}", callback_data=f"acc:grp:{account_id}:{row_id}")])
    rows.append(_back(f"acc:open:{account_id}"))
    text = "<b>📨 Kelgan reklamalar</b>\n\nGuruhni tanlang:" if len(rows) > 1 else "<b>📨 Hali reklama guruhlari yo‘q.</b>"
    await _safe_edit(callback, text, InlineKeyboardMarkup(inline_keyboard=rows))
    await callback.answer()


async def _join_selected(owner_id: int, account_id: int, row_id: int):
    group = get_account_ad_group(row_id)
    if not group:
        raise AccountError("❌ Guruh topilmadi.")
    name, link = group
    status, group_ref = await account_manager.join_group(owner_id, account_id, link)
    return name or "Noma’lum guruh", link, status, group_ref


@router.callback_query(F.data.startswith("acc:grp:"))
async def select_group(callback: types.CallbackQuery):
    _prefix, _grp, account_raw, row_raw = callback.data.split(":")
    account_id, row_id = int(account_raw), int(row_raw)
    try:
        name, _link, status, group_ref = await _join_selected(callback.from_user.id, account_id, row_id)
    except AccountError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    if status == "requested":
        await _safe_edit(
            callback,
            f"<b>👥 {escape(name)}</b>\n\n✅ Join request yuborildi. Tasdiqlangandan keyin qayta oching.",
            InlineKeyboardMarkup(inline_keyboard=[_back(f"acc:groups:{account_id}")]),
        )
    elif group_ref is None:
        await callback.answer("❌ Guruh identifikatori olinmadi.", show_alert=True)
        return
    else:
        await _safe_edit(callback, f"<b>👥 {escape(name)}</b>", group_actions_keyboard(account_id, row_id))
    await callback.answer()


def _sender_choice(owner_id: int, listen_id: int, row_id: int, action: str):
    accounts = [
        row for row in get_connected_accounts(owner_id) if int(row[0]) != int(listen_id)
    ]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📤 {_account_label(row)}", callback_data=f"acc:{action}:{listen_id}:{row_id}:{row[0]}")]
        for row in accounts
    ] + [_back(f"acc:grp:{listen_id}:{row_id}")])


async def _start_collection(callback, listen_id: int, row_id: int, send_id: int):
    name, _link, status, group_ref = await _join_selected(callback.from_user.id, listen_id, row_id)
    if status == "requested" or group_ref is None:
        raise AccountError("⚠️ Join request hali tasdiqlanmagan.")

    async def render(flow):
        try:
            await callback.bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=users_keyboard(flow, f"acc:grp:{listen_id}:{row_id}"),
            )
        except Exception:
            logger.debug("Collector keyboard refresh failed", exc_info=True)

    flow = await account_manager.start_collection(
        callback.from_user.id, listen_id, send_id, group_ref, render
    )
    flow.back_data = f"acc:grp:{listen_id}:{row_id}"
    await _safe_edit(
        callback,
        f"<b>👤 {escape(name)} — username terish boshlandi.</b>\n\n"
        "To‘xtatish: /usernamestop",
        users_keyboard(flow, f"acc:grp:{listen_id}:{row_id}"),
    )


@router.callback_query(F.data.startswith("acc:collect:"))
async def choose_collection_sender(callback: types.CallbackQuery):
    _a, _b, listen_raw, row_raw = callback.data.split(":")
    listen_id, row_id = int(listen_raw), int(row_raw)
    if callback.from_user.id in account_manager.collections:
        await callback.answer(
            "⚠️ Username terish jarayoni hali davom etmoqda. Avval /usernamestop bilan to‘xtating.",
            show_alert=True,
        )
        return
    accounts = get_connected_accounts(callback.from_user.id)
    if len(accounts) < 2:
        await _safe_edit(
            callback,
            "⚠️ Bu funksiya uchun kamida 2 ta account kerak.",
            InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Account ulash", callback_data="acc:add")],
                _back(f"acc:grp:{listen_id}:{row_id}"),
            ]),
        )
        await callback.answer()
        return
    if len(accounts) > 1:
        await _safe_edit(
            callback,
            "<b>📤 Xabar yuboradigan accountni tanlang</b>\n\n"
            "Username teruvchi account oldingi menyuda tanlangan accountdir.",
            _sender_choice(callback.from_user.id, listen_id, row_id, "sender"),
        )
        await callback.answer()
        return
    try:
        await _start_collection(callback, listen_id, row_id, listen_id)
        await callback.answer()
    except AccountError as exc:
        await callback.answer(str(exc), show_alert=True)


@router.callback_query(F.data.startswith("acc:sender:"))
async def start_with_sender(callback: types.CallbackQuery):
    _a, _b, listen_raw, row_raw, send_raw = callback.data.split(":")
    try:
        await _start_collection(callback, int(listen_raw), int(row_raw), int(send_raw))
        await callback.answer()
    except AccountError as exc:
        await callback.answer(str(exc), show_alert=True)


@router.message(Command("usernamestop"), F.chat.type == "private")
async def username_stop(message: types.Message):
    stopped = await account_manager.stop_collection(message.from_user.id)
    await message.answer("✅ Username terish to‘xtatildi." if stopped else "ℹ️ Faol username terish jarayoni yo‘q.")


@router.callback_query(F.data.startswith("acc:admins:"))
async def choose_admin_sender(callback: types.CallbackQuery):
    _a, _b, listen_raw, row_raw = callback.data.split(":")
    listen_id, row_id = int(listen_raw), int(row_raw)
    accounts = get_connected_accounts(callback.from_user.id)
    if len(accounts) > 1:
        await _safe_edit(
            callback,
            "<b>📤 Adminlarga text yuboradigan accountni tanlang</b>",
            _sender_choice(callback.from_user.id, listen_id, row_id, "admsend"),
        )
        await callback.answer()
        return
    await _show_admins(callback, listen_id, row_id, listen_id)


async def _show_admins(callback, listen_id: int, row_id: int, send_id: int):
    try:
        name, _link, status, group_ref = await _join_selected(callback.from_user.id, listen_id, row_id)
        if status == "requested" or group_ref is None:
            raise AccountError("⚠️ Join request hali tasdiqlanmagan.")
        users = await account_manager.get_admins(callback.from_user.id, listen_id, group_ref)
        flow = await account_manager.set_static_users(
            callback.from_user.id, listen_id, send_id, group_ref, users
        )
        flow.back_data = f"acc:grp:{listen_id}:{row_id}"
    except AccountError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    await _safe_edit(
        callback,
        f"<b>👑 {escape(name)} — admin userlar</b>",
        users_keyboard(flow, f"acc:grp:{listen_id}:{row_id}"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("acc:admsend:"))
async def show_admins_with_sender(callback: types.CallbackQuery):
    _a, _b, listen_raw, row_raw, send_raw = callback.data.split(":")
    await _show_admins(callback, int(listen_raw), int(row_raw), int(send_raw))


@router.callback_query(F.data.startswith("acc:send:"))
async def send_selected(callback: types.CallbackQuery):
    target_user_id = int(callback.data.rsplit(":", 1)[1])
    flow = account_manager.collections.get(callback.from_user.id)
    if not flow:
        await callback.answer("❌ Joriy jarayon topilmadi.", show_alert=True)
        return
    selected = flow.users.get(target_user_id)
    if selected and selected.sent is not None:
        await callback.answer("☑️ Yuborildi" if selected.sent else "❌ Yuborilmadi")
        return
    text = get_account_text(callback.from_user.id, flow.send_account_id)
    if not text:
        await callback.answer(
            "⚠️ Yuboruvchi account uchun avval 📝 Text Joylash orqali text qo‘shing.",
            show_alert=True,
        )
        return
    try:
        sent = await account_manager.send_to_collected_user(callback.from_user.id, target_user_id, text)
    except AccountError as exc:
        await callback.answer(str(exc), show_alert=True)
        return
    await callback.message.edit_reply_markup(reply_markup=users_keyboard(flow, flow.back_data))
    await callback.answer("☑️ Yuborildi" if sent else "❌ Yuborilmadi", show_alert=not sent)
