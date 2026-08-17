import re
from datetime import datetime
from html import escape
from urllib.parse import urlparse

from aiogram import F, Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import DB_NAME, OWNER_ID
from database import (
    add_admin_to_db,
    get_ad_groups,
    get_admins_with_names,
    get_all_admins,
    get_today_ads,
    get_top_ad_groups,
    remove_admin_from_db,
    save_ad_submission,
    save_admin_complaint,
    save_user,
)
from keyboards import (
    get_admin_country_keyboard,
    get_admin_manage_inline,
    get_admin_region_keyboard,
    get_admins_delete_inline,
    get_back_inline,
    get_main_menu,
    get_roles_inline_keyboard,
)

router = Router()


def parse_group_link(value: str) -> tuple[str | None, str] | None:
    """Return a public chat reference (if available) and canonical Telegram URL."""
    value = value.strip()

    if value.startswith("@"):
        username = value[1:].split("/", 1)[0]
    else:
        candidate = value
        if candidate.lower().startswith(("t.me/", "www.t.me/")):
            candidate = f"https://{candidate}"

        parsed = urlparse(candidate)
        if parsed.scheme.lower() not in {"http", "https"}:
            return None
        if parsed.netloc.lower() not in {"t.me", "www.t.me"}:
            return None

        path = parsed.path.strip("/")
        if path.startswith("+") and len(path) > 1 and "/" not in path:
            return None, f"https://t.me/{path}"

        username = path.split("/", 1)[0]

    if not re.fullmatch(r"[A-Za-z0-9_]{5,32}", username):
        return None

    return f"@{username}", f"https://t.me/{username}"


# ============================================================
# FSM HOLATLARI
# ============================================================

class AdminComplaintState(StatesGroup):
    waiting_for_complaint_text = State()


class AdminAddState(StatesGroup):
    waiting_for_admin_id = State()
    waiting_for_full_name = State()
    waiting_for_region = State()
    waiting_for_birth_date = State()
    waiting_for_phone = State()


class AdSubmitState(StatesGroup):
    waiting_for_group_name = State()
    waiting_for_group_link = State()
    waiting_for_screenshot = State()


# ============================================================
# MAFIA ROLLARI
# ============================================================

ROLES_INFO = {
    "tinch_aholi":
        "👨🏼 <b>Tinch aholi:</b>\n\n"
        "Sizning vazifangiz mafiyani topish va ularni shahar yig'ilishida osishdur.",

    "komissar":
        "🕵🏻‍♂️ <b>Komissar Kattani:</b>\n\n"
        "Shaharning asosiy himoyachisi va mafiya kushandasi.",

    "serjant":
        "👮🏻‍♂️ <b>Serjant:</b>\n\n"
        "Komissar Kattaniga yordam beradi. Komissar vafot etsa, uning o'rnini egallaydi.",

    "doktor":
        "👨🏻‍⚕️ <b>Doktor:</b>\n\n"
        "Komissar yoki boshqa tinch aholini davolaydi.",

    "kezuvchi":
        "💃 <b>Kezuvchi:</b>\n\n"
        "Bir kecha davomida shaharni zararsizlantirish uchun mahoratingizdan foydalaning.",

    "daydi":
        "🧙‍♂️ <b>Daydi:</b>\n\n"
        "Tunda qotillikka guvoh bo'ladi.",

    "omadli":
        "🤞 <b>Omadli:</b>\n\n"
        "Bir marta otilsa tirik qolish omadi bor.",

    "afsungar":
        "🧞‍♂️ <b>Afsungar:</b>\n\n"
        "Uni o'ldirganni o'zi bilan olib ketadi.",

    "janob":
        "🎖️ <b>Janob:</b>\n\n"
        "Ovoz berishdagi ovozi 2 ga teng.",

    "don_mafiya":
        "🤵🏻 <b>Don va Mafiya:</b>\n\n"
        "Tunda shaharni o'ldirish bilan shug'ullanadi.",

    "advokat":
        "👨‍💼 <b>Advokat:</b>\n\n"
        "Mafiyani Komissar tekshiruvidan himoya qiladi.",

    "ubiytsa":
        "🕴 <b>Убийца:</b>\n\n"
        "Mafiyaga yordam beradi.",

    "jurnalist":
        "👩‍💻 <b>Jurnalist:</b>\n\n"
        "Mafia uchun intervyu bahonasida ma'lumot yig'adi.",

    "qotil":
        "🔪 <b>Qotil:</b>\n\n"
        "Atrofdagilarni o'ldirib, bir o'zi g'olib bo'lishga intiladi.",

    "bori":
        "🐺 <b>Bo'ri:</b>\n\n"
        "O'lsa mafiya yoki serjantga aylanadi.",

    "sotqin":
        "🤓 <b>Sotqin:</b>\n\n"
        "Tekshirilgan rollarni sotadi.",

    "sexrgar":
        "🧙‍♂️ <b>Sexrgar:</b>\n\n"
        "Erkin rol, kechirish yoki o'ldirish huquqi bor.",

    "gazabkor":
        "🧟 <b>G'azabkor:</b>\n\n"
        "Erkin rol.",

    "aferist":
        "🤹 <b>Aferist:</b>\n\n"
        "Ovozlar bilan nayrang qiladi."
}


# ============================================================
# YORDAMCHI FUNKSIYALAR
# ============================================================

def main_menu(user_id: int):
    admins = get_all_admins()
    return get_main_menu(user_id, admins)


def cancel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="cancel_fsm"
                )
            ]
        ]
    )


def roles_back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Rollarga qaytish",
                    callback_data="roles_list"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Asosiy menyu",
                    callback_data="main_menu"
                )
            ]
        ]
    )


# ============================================================
# 1. /START
# ============================================================

@router.message(CommandStart(), F.chat.type == "private")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()

    save_user(message.from_user)

    await message.answer(
        f"<b>Salom, {escape(message.from_user.full_name)}!</b>\n\n"
        "<b>Asosiy menyudan kerakli bo'limni tanlang:</b>",
        reply_markup=main_menu(message.from_user.id),
        parse_mode="HTML"
    )


# ============================================================
# ASOSIY MENYU CALLBACKLARI
# ============================================================

@router.callback_query(F.data == "main_menu")
async def main_menu_callback(
    callback: types.CallbackQuery,
    state: FSMContext
):
    await state.clear()

    await callback.message.edit_text(
        f"<b>Salom, {escape(callback.from_user.full_name)}!</b>\n\n"
        "<b>Asosiy menyudan kerakli bo'limni tanlang:</b>",
        reply_markup=main_menu(callback.from_user.id),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# 2. MAFIA ROLLARI
# ============================================================

@router.callback_query(F.data == "menu_roles")
async def show_mafia_roles_callback(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "<b>🎭 Qaysi rol haqida ma'lumot olmoqchisiz?</b>",
        reply_markup=get_roles_inline_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# Eski callback nomlari bilan ham ishlashi uchun
@router.message(F.text == "🎭 Mafia Rollari", F.chat.type == "private")
async def show_mafia_roles_old(message: types.Message):
    await message.answer(
        "<b>🎭 Qaysi rol haqida ma'lumot olmoqchisiz?</b>",
        reply_markup=get_roles_inline_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "roles_list")
async def roles_list_callback(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "<b>🎭 Qaysi rol haqida ma'lumot olmoqchisiz?</b>",
        reply_markup=get_roles_inline_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data.startswith("role_"))
async def show_role_info(callback: types.CallbackQuery):
    role_key = callback.data[len("role_"):]

    # Eski callback nomlari uchun moslashtirish
    aliases = {
        "fuqaro": "tinch_aholi",
        "don": "don_mafiya",
        "mafia": "don_mafiya",
        "ubiyca": "ubiytsa",
        "sehrgar": "sexrgar"
    }

    role_key = aliases.get(role_key, role_key)

    info_text = ROLES_INFO.get(
        role_key,
        "Ushbu rol haqida ma'lumot topilmadi."
    )

    await callback.message.edit_text(
        info_text,
        reply_markup=roles_back_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# 3. REKLAMA YUBORISH
# ============================================================

@router.callback_query(F.data == "menu_ad")
async def start_ad_submission_callback(
    callback: types.CallbackQuery,
    state: FSMContext
):
    await state.clear()
    await state.set_state(AdSubmitState.waiting_for_group_link)

    await callback.message.edit_text(
        "<b>🔗 Reklama berilgan guruh havolasini yuboring:</b>\n\n"
        "Bot guruh nomini link orqali aniqlashga harakat qiladi.",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


@router.message(
    F.text == "📩 Reklama Yuborish",
    F.chat.type == "private"
)
async def start_ad_submission_old(
    message: types.Message,
    state: FSMContext
):
    await state.clear()
    await state.set_state(AdSubmitState.waiting_for_group_name)

    await message.answer(
        "<b>📢 Reklama berilayotgan guruh nomini kiriting:</b>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(
    AdSubmitState.waiting_for_group_link,
    F.chat.type == "private"
)
async def process_group_link(
    message: types.Message,
    state: FSMContext
):
    if not message.text:
        await message.answer(
            "⚠️ Guruh linkini matn ko‘rinishida yuboring.",
            reply_markup=cancel_keyboard()
        )
        return

    parsed_link = parse_group_link(message.text)
    if parsed_link is None:
        await message.answer(
            "❌ Guruh havolasi noto‘g‘ri.\n\n"
            "Masalan: <code>@mygroup</code> yoki "
            "<code>https://t.me/mygroup/</code>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML",
        )
        return

    chat_ref, group_link = parsed_link

    group_name = "Yopiq guruh" if chat_ref is None else None

    if chat_ref is not None:
        try:
            chat = await message.bot.get_chat(chat_ref)
            group_name = chat.title
        except Exception as e:
            print(f"⚠️ Guruh nomini aniqlab bo‘lmadi: {e}")

    if not group_name:
        await message.answer(
            "❌ Guruh nomini aniqlab bo‘lmadi.\\n\\n"
            "🔗 Iltimos, guruhning to‘g‘ri username/linkini yuboring.\\n"
            "Masalan: <code>@classic_mafiaa</code>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )
        return

    await state.update_data(
        group_link=group_link,
        group_name=group_name
    )

    await state.set_state(
        AdSubmitState.waiting_for_screenshot
    )

    await message.answer(
        f"<b>✅ Guruh topildi!</b>\n\n"
        f"👥 <b>Guruh:</b> {group_name}\n"
        f"🔗 <b>Link:</b> {group_link}\n\n"
        "📸 Endi reklama joylashtirilganini tasdiqlovchi "
        "skrinshot yuboring.",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(
    AdSubmitState.waiting_for_screenshot,
    F.chat.type == "private"
)
async def process_screenshot(
    message: types.Message,
    state: FSMContext
):
    if not (message.photo or message.document):
        await message.answer(
            "<b>⚠️ Iltimos, skrinshot yuboring!</b>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )
        return

    user_data = await state.get_data()
    group_link = (user_data.get("group_link") or "").strip()

    # Guruh nomini link orqali aniqlash
    group_name = user_data.get("group_name") or "Aniqlanmadi"

    try:
        parsed_link = parse_group_link(group_link)

        if parsed_link and parsed_link[0] is not None:
            chat_ref, _canonical_url = parsed_link
            chat = await message.bot.get_chat(chat_ref)
            group_name = chat.title or chat.full_name or chat_ref.removeprefix("@")
        elif not parsed_link:
            group_name = "Link noto‘g‘ri"

    except Exception as e:
        print(f"Guruh nomini aniqlashda xatolik: {e}")
        group_name = "Aniqlanmadi"

    user = message.from_user

    save_ad_submission(
        user.id,
        user.full_name,
        user.username or "",
        group_name,
        group_link
    )

    caption_text = (
        "<b>📩 YANGI REKLAMA TOPSHIRILDI!</b>\n\n"
        f"<b>👤 Yuboruvchi:</b> {user.full_name} "
        f"(@{user.username or 'username_yoq'})\n"
        f"<b>🆔 Yuboruvchi ID:</b> <code>{user.id}</code>\n\n"
        f"<b>👥 Guruh nomi:</b> {group_name}\n"
        f"<b>🔗 Guruh linki:</b> {group_link}"
    )

    all_admins = set(get_all_admins())
    all_admins.add(OWNER_ID)

    for admin_id in all_admins:
        try:
            if message.photo:
                await message.bot.send_photo(
                    chat_id=admin_id,
                    photo=message.photo[-1].file_id,
                    caption=caption_text,
                    parse_mode="HTML"
                )
            elif message.document:
                await message.bot.send_document(
                    chat_id=admin_id,
                    document=message.document.file_id,
                    caption=caption_text,
                    parse_mode="HTML"
                )
        except Exception as e:
            print(f"Admin ({admin_id}) ga xatolik: {e}")

    await state.clear()

    await message.answer(
        "<b>✅ Reklama ma’lumotlari qabul qilindi!</b>\n\n"
        f"👥 <b>Guruh:</b> {group_name}\n"
        "📩 Ma’lumotlar adminlarga yuborildi.",
        reply_markup=main_menu(message.from_user.id),
        parse_mode="HTML"
    )


# ============================================================
# 4. SHIKOYAT
# ============================================================

@router.callback_query(F.data == "menu_complaint")
async def start_complaint_callback(
    callback: types.CallbackQuery,
    state: FSMContext
):
    await state.clear()

    admins = get_admins_with_names()

    sub_admins = [
        adm for adm in admins
        if adm[0] != OWNER_ID
    ]

    if not sub_admins:
        await callback.answer(
            "⚠️ Hozircha qo'shimcha adminlar mavjud emas.",
            show_alert=True
        )
        return

    keyboard = []

    for admin_id, full_name, username, _region, _birth_date, _phone in sub_admins:
        display_name = full_name or f"Admin ({admin_id})"

        if username:
            display_name += f" (@{username})"

        keyboard.append([
            InlineKeyboardButton(
                text=f"👤 {display_name}",
                callback_data=f"select_admin_{admin_id}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data="main_menu"
        )
    ])

    await callback.message.edit_text(
        "<b>⚠️ Qaysi admin ustidan shikoyat qilmoqchisiz?</b>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        ),
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data.startswith("select_admin_"))
async def process_admin_selection(
    callback: types.CallbackQuery,
    state: FSMContext
):
    target_admin_id = int(
        callback.data.split("_")[-1]
    )

    admins = get_admins_with_names()

    target_admin_name = f"ID: {target_admin_id}"

    for aid, fname, uname, _region, _birth_date, _phone in admins:
        if aid == target_admin_id:
            target_admin_name = (
                fname
                or (f"@{uname}" if uname else f"ID: {aid}")
            )
            break

    await state.update_data(
        target_admin_id=target_admin_id,
        target_admin_name=target_admin_name
    )

    await state.set_state(
        AdminComplaintState.waiting_for_complaint_text
    )

    await callback.message.edit_text(
        f"<b>👤 Tanlangan admin:</b> "
        f"{target_admin_name}\n\n"
        "<b>💬 Shikoyat mazmunini yozing:</b>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


@router.message(
    AdminComplaintState.waiting_for_complaint_text,
    F.chat.type == "private"
)
async def process_complaint_text(
    message: types.Message,
    state: FSMContext
):
    if not message.text and not message.caption:
        await message.answer(
            "⚠️ Shikoyat matnini yuboring.",
            reply_markup=cancel_keyboard()
        )
        return

    user_data = await state.get_data()

    target_admin_name = user_data.get(
        "target_admin_name"
    )

    target_admin_id = user_data.get(
        "target_admin_id"
    )

    user = message.from_user

    complaint_text = (
        message.text
        or message.caption
        or "Media/Fayl yuborildi"
    )

    save_admin_complaint(
        user.id,
        user.full_name,
        user.username or "",
        f"Admin: {target_admin_name} | {complaint_text}"
    )

    report_header = (
        "<b>🚨 ADMINDAN YANGI SHIKOYAT KELDI!</b>\n\n"
        f"<b>👤 Shikoyatchi:</b> "
        f"{user.full_name} "
        f"(@{user.username or 'username_yoq'})\n"
        f"<b>🆔 ID:</b> <code>{user.id}</code>\n\n"
        f"<b>🎯 Qaysi admin ustidan:</b> "
        f"{target_admin_name} "
        f"(ID: <code>{target_admin_id}</code>)\n\n"
        f"<b>💬 Shikoyat:</b>\n{complaint_text}"
    )

    all_admins = set(get_all_admins())
    all_admins.add(OWNER_ID)

    recipients = [
        admin_id
        for admin_id in all_admins
        if admin_id != target_admin_id
    ]

    for admin_id in recipients:
        try:
            if (
                message.photo
                or message.video
                or message.document
            ):
                await message.send_copy(
                    chat_id=admin_id
                )

            await message.bot.send_message(
                chat_id=admin_id,
                text=report_header,
                parse_mode="HTML"
            )

        except Exception as e:
            print(f"Shikoyat yuborishda xatolik: {e}")

    await state.clear()

    await message.answer(
        "<b>✅ Shikoyatingiz yetkazildi.</b>\n\n"
        "Rahmat!",
        reply_markup=main_menu(user.id),
        parse_mode="HTML"
    )


# ============================================================
# 5. ADMIN BOSHQARUVI
# ============================================================

@router.callback_query(F.data == "menu_admin_manage")
async def admin_management_menu_callback(
    callback: types.CallbackQuery
):
    if callback.from_user.id != OWNER_ID:
        await callback.answer(
            "⛔️ Bu bo'lim faqat Owner uchun!",
            show_alert=True
        )
        return

    # Tugma bosilganini darhol tasdiqlaymiz
    await callback.answer()

    try:
        await callback.message.edit_text(
            "<b>⚙️ Adminlarni boshqarish:</b>",
            reply_markup=get_admin_manage_inline(),
            parse_mode="HTML"
        )
    except Exception as e:
        # Xabar allaqachon shu holatda bo'lsa, xatoni e'tiborsiz qoldiramiz
        if "message is not modified" not in str(e):
            print(f"⚠️ Admin menyu xatosi: {e}")


@router.callback_query(F.data == "admin_add_start")
async def cb_admin_add_start(
    callback: types.CallbackQuery,
    state: FSMContext
):
    if callback.from_user.id != OWNER_ID:
        await callback.answer(
            "⛔️ Ruxsat yo'q!",
            show_alert=True
        )
        return

    await state.set_state(AdminAddState.waiting_for_admin_id)

    await callback.message.edit_text(
        "<b>➕ Yangi adminning Telegram ID raqamini kiriting:</b>\n\n"
        "ℹ️ Qolgan ma'lumotlarni adminning o'zi kiritadi.",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


@router.message(
    AdminAddState.waiting_for_admin_id,
    F.chat.type == "private"
)
async def process_add_admin_id(
    message: types.Message,
    state: FSMContext
):
    if message.from_user.id != OWNER_ID:
        return

    if not message.text or not message.text.isdigit():
        await message.answer(
            "❌ <b>Faqat Telegram ID raqamini kiriting!</b>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )
        return

    new_admin_id = int(message.text)

    if new_admin_id == OWNER_ID:
        await message.answer(
            "❌ Ownerni qaytadan admin qilish shart emas.",
            reply_markup=cancel_keyboard()
        )
        return

    await state.clear()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Ro'yxatdan o'tish",
                    callback_data=f"admin_register_{new_admin_id}"
                )
            ]
        ]
    )

    try:
        await message.bot.send_message(
            new_admin_id,
            "👋 <b>Siz botga admin sifatida qo'shilish uchun tanlandingiz.</b>\n\n"
            "Quyidagi tugmani bosib, ma'lumotlaringizni o'zingiz kiriting.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        await message.answer(
            f"✅ <b>Taklif yuborildi!</b>\n\n"
            f"🆔 ID: <code>{new_admin_id}</code>\n\n"
            "Admin o'ziga kelgan xabardagi "
            "<b>📝 Ro'yxatdan o'tish</b> tugmasini bosib ma'lumotlarini kiritadi.",
            parse_mode="HTML"
        )

    except Exception:
        await message.answer(
            "❌ Bu foydalanuvchiga xabar yuborib bo'lmadi.\n\n"
            "ℹ️ Avval u botga /start bosgan bo'lishi kerak.",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("admin_register_"))
async def admin_register_start(
    callback: types.CallbackQuery,
    state: FSMContext
):
    try:
        admin_id = int(callback.data.replace("admin_register_", "", 1))
    except ValueError:
        await callback.answer(
            "❌ Noto'g'ri ma'lumot!",
            show_alert=True
        )
        return

    if callback.from_user.id != admin_id:
        await callback.answer(
            "⛔️ Bu ro'yxatdan o'tish boshqa foydalanuvchi uchun!",
            show_alert=True
        )
        return

    await state.update_data(admin_id=admin_id)

    await state.set_state(AdminAddState.waiting_for_full_name)

    await callback.message.edit_text(
        "👤 <b>Ism va familiyangizni kiriting:</b>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "admin_info_list")
async def cb_admin_info_list(
    callback: types.CallbackQuery
):
    if callback.from_user.id != OWNER_ID:
        await callback.answer(
            "⛔️ Ruxsat faqat Owner uchun!",
            show_alert=True
        )
        return

    # Loadingni darhol yopamiz
    await callback.answer()

    admins = get_admins_with_names()

    if not admins:
        await callback.answer(
            "⚠️ Qo'shimcha adminlar yo'q!",
            show_alert=True
        )
        return

    keyboard = []

    for admin_id, full_name, username, region, birth_date, phone in admins:
        display_name = full_name or f"Admin ({admin_id})"

        keyboard.append([
            InlineKeyboardButton(
                text=f"👤 {display_name}",
                callback_data=f"admin_info_{admin_id}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data="menu_admin_manage"
        )
    ])

    await callback.message.edit_text(
        "<b>👥 ADMINLAR HAQIDA MA'LUMOT</b>\n\n"
        "Ma'lumotlarini ko'rish uchun adminni tanlang:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        ),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_list_show")
async def cb_admin_list_show(
    callback: types.CallbackQuery
):
    if callback.from_user.id != OWNER_ID:
        await callback.answer(
            "⛔️ Ruxsat yo'q!",
            show_alert=True
        )
        return

    await callback.answer()

    admins = get_admins_with_names()

    if not admins:
        await callback.answer(
            "⚠️ Qo'shimcha adminlar yo'q!",
            show_alert=True
        )
        return

    await callback.message.edit_text(
        "<b>👥 Adminlar ro'yxati:</b>\n\n"
        "Adminni o'chirish uchun ustiga bosing:",
        reply_markup=get_admins_delete_inline(admins),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_remove_list")
async def cb_admin_remove_list(
    callback: types.CallbackQuery
):
    if callback.from_user.id != OWNER_ID:
        await callback.answer(
            "⛔️ Ruxsat yo'q!",
            show_alert=True
        )
        return

    admins = get_admins_with_names()

    if not admins:
        await callback.answer(
            "⚠️ Qo'shimcha adminlar yo'q!",
            show_alert=True
        )
        return

    keyboard = []

    for admin_id, full_name, username, region, birth_date, phone in admins:
        display_name = full_name or f"Admin ({admin_id})"

        keyboard.append([
            InlineKeyboardButton(
                text=f"🗑 {display_name}",
                callback_data=f"remove_admin_confirm_{admin_id}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data="menu_admin_manage"
        )
    ])

    await callback.message.edit_text(
        "<b>➖ Adminlikdan olmoqchi bo'lgan adminni tanlang:</b>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        ),
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data.startswith("remove_admin_confirm_"))
async def cb_remove_admin_confirm(
    callback: types.CallbackQuery
):
    if callback.from_user.id != OWNER_ID:
        await callback.answer(
            "⛔️ Ruxsat yo'q!",
            show_alert=True
        )
        return

    admin_id_to_remove = int(
        callback.data.split("_")[-1]
    )

    if admin_id_to_remove == OWNER_ID:
        await callback.answer(
            "⛔️ Ownerni o'chirib bo'lmaydi!",
            show_alert=True
        )
        return

    remove_admin_from_db(admin_id_to_remove)

    await callback.answer(
        f"✅ ID: {admin_id_to_remove} o'chirildi!",
        show_alert=True
    )

    await cb_admin_remove_list(callback)


@router.callback_query(F.data.startswith("admin_del_"))
async def cb_admin_delete_old(
    callback: types.CallbackQuery
):
    if callback.from_user.id != OWNER_ID:
        await callback.answer(
            "⛔️ Ruxsat yo'q!",
            show_alert=True
        )
        return

    admin_id = int(
        callback.data.split("_")[-1]
    )

    if admin_id == OWNER_ID:
        await callback.answer(
            "⛔️ Ownerni o'chirib bo'lmaydi!",
            show_alert=True
        )
        return

    remove_admin_from_db(admin_id)

    await callback.answer(
        "✅ Admin o'chirildi!",
        show_alert=True
    )

    admins = get_admins_with_names()

    await callback.message.edit_text(
        "<b>👥 Adminlar ro'yxati:</b>",
        reply_markup=get_admins_delete_inline(admins),
        parse_mode="HTML"
    )


# ============================================================
# 6. BUGUNGI REKLAMALAR
# ============================================================

@router.callback_query(F.data == "menu_today_ads")
async def show_today_ads_callback(
    callback: types.CallbackQuery
):
    today_data = get_today_ads()

    if not today_data:
        await callback.message.edit_text(
            "<b>📅 Bugun hali reklama topshirilmadi.</b>",
            reply_markup=get_back_inline(),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    text = (
        "<b>📅 BUGUN TOPSHIRILGAN REKLAMALAR:</b>\n\n"
    )

    total = 0

    for i, (g_name, g_link, count) in enumerate(
        today_data,
        1
    ):
        text += (
            f"<b>{i}. {g_name}</b>\n"
            f"🔗 {g_link}\n"
            f"📊 Soni: <b>{count} ta</b>\n\n"
        )

        total += count

    text += f"<b>Jami: {total} ta</b>"

    await callback.message.edit_text(
        text,
        reply_markup=get_back_inline(),
        parse_mode="HTML",
        disable_web_page_preview=True
    )

    await callback.answer()


# ============================================================
# ============================================================
# 7. REKLAMA KELGAN GURUHLAR
# ============================================================

@router.callback_query(F.data == "menu_groups")
async def show_ad_groups_callback(
    callback: types.CallbackQuery
):
    groups = get_ad_groups(limit=50)

    if not groups:
        await callback.message.edit_text(
            "<b>👥 Hali reklama kelgan guruhlar yo'q.</b>",
            reply_markup=get_back_inline(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    buttons = []

    for group_name, group_link, _ in groups:
        name = (group_name or "").strip() or "Noma'lum guruh"

        if len(name) > 55:
            name = name[:52] + "..."

        group_url = None

        if group_link:
            group_link = group_link.strip()

            if group_link.startswith("@"):
                group_url = f"https://t.me/{group_link[1:]}"

            elif group_link.startswith("t.me/"):
                group_url = f"https://{group_link}"

            elif group_link.startswith("https://t.me/"):
                group_url = group_link

            elif group_link.startswith("http://t.me/"):
                group_url = group_link

        if group_url:
            buttons.append([
                InlineKeyboardButton(
                    text=f"👥 {name}",
                    url=group_url
                )
            ])
        else:
            buttons.append([
                InlineKeyboardButton(
                    text=f"👥 {name}",
                    callback_data="no_group_link"
                )
            ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data="main_menu"
        )
    ])

    await callback.message.edit_text(
        "<b>👥 REKLAMA KELGAN GURUHLAR:</b>\n\n"
        "Quyidagi guruhlardan birini tanlang:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
        parse_mode="HTML",
        disable_web_page_preview=True
    )

    await callback.answer()


# ============================================================
# 7.1 ENG KO'P KELGAN REKLAMALAR — TOP 10
# ============================================================

@router.callback_query(F.data == "menu_statistics")
async def show_top_ad_statistics_callback(
    callback: types.CallbackQuery
):
    top_groups = get_top_ad_groups(limit=10)

    if not top_groups:
        await callback.message.edit_text(
            "<b>📊 Hali reklama statistikasi yo'q.</b>",
            reply_markup=get_back_inline(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    text = "<b>📊 ENG KO'P KELGAN REKLAMALAR — TOP 10</b>\n\n"
    buttons = []

    for i, (group_name, group_link, count) in enumerate(top_groups, 1):
        name = (group_name or "").strip() or "Noma'lum guruh"

        if len(name) > 50:
            name = name[:47] + "..."

        if i == 1:
            place = "🥇 1 O'RINDA."
        elif i == 2:
            place = "🥈 2 O'RINDA."
        elif i == 3:
            place = "🥉 3 O'RINDA."
        else:
            place = f"🔹 {i} O'RINDA."

        text += f"<b>{place} {name} — {count} TA</b>\n"

        # Guruh linkini Telegram URL formatiga keltirish
        if group_link:
            group_link = str(group_link).strip()

            if group_link.startswith("@"):
                group_link = "https://t.me/" + group_link[1:]
            elif group_link.startswith("t.me/"):
                group_link = "https://" + group_link
            elif group_link.startswith("https://t.me/"):
                pass
            elif group_link.startswith("http://t.me/"):
                group_link = "https://" + group_link[7:]
            else:
                group_link = None

        if group_link:
            buttons.append([
                InlineKeyboardButton(
                    text=f"{place} {name}",
                    url=group_link
                )
            ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data="main_menu"
        )
    ])

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
        parse_mode="HTML",
        disable_web_page_preview=True
    )

    await callback.answer()

# ============================================================
# 8. GURUH AKTIVLIGI
# ============================================================

@router.callback_query(F.data == "menu_top_active")
async def show_top_active_callback(
    callback: types.CallbackQuery
):
    """
    Botdagi inline tugma orqali aktivlik bo'limini ochadi.
    Bu yerda reklama statistikasi emas,
    guruh aktivligi funksiyasi ishlaydi.
    """

    text = (
        "<b>🏆 GURUH AKTIVLIGI</b>\\n\\n"
        "Guruhdagi aktiv odamlarni ko'rish uchun "
        "quyidagi tugmalardan foydalaning:"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📅 Bugungi TOP 5",
                    callback_data="activity_daily"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📆 Oylik TOP 5",
                    callback_data="activity_monthly"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👑 Adminlar aktivligi",
                    callback_data="activity_admins"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="main_menu"
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
# 8.1 BUGUNGI AKTIVLIK
# ============================================================

@router.callback_query(F.data == "activity_daily")
async def show_activity_daily_callback(
    callback: types.CallbackQuery
):
    await callback.message.edit_text(
        "<b>📅 Bugungi aktivlik</b>\\n\\n"
        "Bu statistika guruhdagi xabarlar asosida "
        "hisoblanadi.\\n\\n"
        "Guruh ichida /aktiv buyrug'ini yuboring.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬅️ Aktivlik menyusiga",
                        callback_data="menu_top_active"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🏠 Asosiy menyu",
                        callback_data="main_menu"
                    )
                ]
            ]
        ),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# 8.2 OYLIK AKTIVLIK
# ============================================================

@router.callback_query(F.data == "activity_monthly")
async def show_activity_monthly_callback(
    callback: types.CallbackQuery
):
    await callback.message.edit_text(
        "<b>📆 Oylik aktivlik</b>\\n\\n"
        "Oylik aktivlik guruh bo'yicha hisoblanadi.\\n\\n"
        "Guruh ichida /aktiv buyrug'ini yuboring.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬅️ Aktivlik menyusiga",
                        callback_data="menu_top_active"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🏠 Asosiy menyu",
                        callback_data="main_menu"
                    )
                ]
            ]
        ),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# 8.3 ADMIN AKTIVLIGI
# ============================================================

@router.callback_query(F.data == "activity_admins")
async def show_activity_admins_callback(
    callback: types.CallbackQuery
):
    await callback.message.edit_text(
        "<b>👑 Adminlar aktivligi</b>\\n\\n"
        "Adminlar aktivligi guruh bo'yicha hisoblanadi.\\n\\n"
        "Guruh ichida /aktiv buyrug'ini yuboring.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬅️ Aktivlik menyusiga",
                        callback_data="menu_top_active"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🏠 Asosiy menyu",
                        callback_data="main_menu"
                    )
                ]
            ]
        ),
        parse_mode="HTML"
    )

    await callback.answer()


# 9. ACCOUNT ULANISH REKLAMASI
# ============================================================

@router.callback_query(F.data == "menu_account_ads")
async def account_ads_callback(
    callback: types.CallbackQuery
):
    await callback.message.edit_text(
        "<b>📱 Account Ulash Reklama Uchun</b>\n\n"
        "Bu bo'lim hozircha sozlanmagan.",
        reply_markup=get_back_inline(),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# 10. INLINE ORQAGA / BEKOR QILISH
# ============================================================

@router.callback_query(F.data == "cancel_fsm")
async def cancel_fsm_callback(
    callback: types.CallbackQuery,
    state: FSMContext
):
    await state.clear()

    await callback.message.edit_text(
        "<b>Asosiy menyuga qaytdingiz.</b>",
        reply_markup=main_menu(callback.from_user.id),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# 11. YOPISH
# ============================================================

@router.callback_query(F.data == "close_menu")
async def close_menu_handler(
    callback: types.CallbackQuery,
    state: FSMContext
):
    await state.clear()

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.answer()
# ============================================================
# ⚠️ ADMINGA SHIKOYAT — INLINE
# ============================================================

@router.callback_query(F.data == "menu_complaint")
async def complaint_menu_callback(
    callback: types.CallbackQuery,
    state: FSMContext
):
    await state.clear()

    admins = get_admins_with_names()

    # Owner ko'rinmaydi
    admins = [
        admin for admin in admins
        if admin[0] != OWNER_ID
    ]

    if not admins:
        await callback.answer(
            "⚠️ Hozircha qo'shimcha adminlar mavjud emas.",
            show_alert=True
        )
        return

    buttons = []

    for admin_id, full_name, username, region, birth_date, phone in admins:
        name = full_name or f"Admin {admin_id}"

        if username:
            name += f" (@{username})"

        buttons.append([
            InlineKeyboardButton(
                text=f"👤 {name}",
                callback_data=f"complaint_admin_{admin_id}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Asosiy menyu",
            callback_data="main_menu"
        )
    ])

    await callback.message.edit_text(
        "<b>⚠️ Adminga shikoyat</b>\n\n"
        "Shikoyat qilmoqchi bo'lgan adminni tanlang:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# 👤 ADMIN TANLASH
# ============================================================

@router.callback_query(
    F.data.startswith("complaint_admin_")
)
async def complaint_admin_selected(
    callback: types.CallbackQuery,
    state: FSMContext
):
    admin_id = int(
        callback.data.replace("complaint_admin_", "")
    )

    # Ownerni tanlashga yo'l qo'ymaymiz
    if admin_id == OWNER_ID:
        await callback.answer(
            "⛔️ Ownerga shikoyat yuborib bo'lmaydi.",
            show_alert=True
        )
        return

    admins = get_admins_with_names()

    selected_admin = None

    for aid, full_name, username, _region, _birth_date, _phone in admins:
        if aid == admin_id:
            selected_admin = (
                full_name or f"Admin {aid}"
            )

            if username:
                selected_admin += f" (@{username})"

            break

    if not selected_admin:
        await callback.answer(
            "⚠️ Admin topilmadi.",
            show_alert=True
        )
        return

    await state.update_data(
        target_admin_id=admin_id,
        target_admin_name=selected_admin
    )

    await state.set_state(
        AdminComplaintState.waiting_for_complaint_text
    )

    await callback.message.edit_text(
        f"<b>👤 Tanlangan admin:</b> {selected_admin}\n\n"
        "<b>💬 Endi shikoyatingizni yozing:</b>\n\n"
        "Shikoyat yuborilganda tanlangan admin "
        "shikoyatni ko'rmaydi.",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# 📝 SHIKOYAT MATNI
# ============================================================

@router.message(
    AdminComplaintState.waiting_for_complaint_text,
    F.chat.type == "private"
)
async def process_complaint_text_inline(
    message: types.Message,
    state: FSMContext
):
    if not message.text:
        await message.answer(
            "⚠️ Iltimos, shikoyatni matn ko'rinishida yuboring.",
            reply_markup=cancel_keyboard()
        )
        return

    data = await state.get_data()

    target_admin_id = data.get("target_admin_id")
    target_admin_name = data.get("target_admin_name")

    user = message.from_user

    complaint_text = message.text

    # Bazaga saqlaymiz
    save_admin_complaint(
        user.id,
        user.full_name,
        user.username or "",
        f"Admin: {target_admin_name} | {complaint_text}"
    )

    report = (
        "<b>🚨 YANGI ADMIN SHIKOYATI</b>\n\n"
        f"<b>👤 Shikoyatchi:</b> "
        f"{user.full_name}\n"
        f"<b>🆔 ID:</b> <code>{user.id}</code>\n\n"
        f"<b>🎯 Shikoyat qilingan admin:</b>\n"
        f"{target_admin_name}\n"
        f"<b>🆔 Admin ID:</b> "
        f"<code>{target_admin_id}</code>\n\n"
        f"<b>💬 Shikoyat:</b>\n"
        f"{complaint_text}"
    )

    # Barcha adminlar + Owner
    all_admins = set(get_all_admins())
    all_admins.add(OWNER_ID)

    # Muhim:
    # Tanlangan admin bu yerda chiqarib tashlanadi
    recipients = [
        admin_id
        for admin_id in all_admins
        if admin_id != target_admin_id
    ]

    for admin_id in recipients:
        try:
            await message.bot.send_message(
                chat_id=admin_id,
                text=report,
                parse_mode="HTML"
            )
        except Exception as e:
            print(
                f"❌ Shikoyat yuborishda xatolik "
                f"({admin_id}): {e}"
            )

    await state.clear()

    await message.answer(
        "<b>✅ Shikoyatingiz yuborildi.</b>\n\n"
        "Adminlar shikoyatni ko'rib chiqishadi.",
        reply_markup=main_menu(user.id),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_menu_back")
async def admin_menu_back_callback(
    callback: types.CallbackQuery
):
    if callback.from_user.id != OWNER_ID:
        await callback.answer(
            "⛔️ Ruxsat yo'q!",
            show_alert=True
        )
        return

    await callback.answer()

    await callback.message.edit_text(
        "<b>⚙️ Adminlarni boshqarish:</b>",
        reply_markup=get_admin_manage_inline(),
        parse_mode="HTML"
    )


@router.message(
    AdminAddState.waiting_for_full_name,
    F.chat.type == "private"
)
async def process_admin_full_name(
    message: types.Message,
    state: FSMContext
):
    if not message.text or not message.text.strip():
        await message.answer(
            "❌ Ism va familiyani kiriting.",
            reply_markup=cancel_keyboard()
        )
        return

    full_name = message.text.strip()

    await state.update_data(full_name=full_name)
    await state.set_state(AdminAddState.waiting_for_region)

    await message.answer(
        "<b>📍 Admin qaysi viloyat yoki davlatdan?</b>\n\n"
        "Quyidagi tugmalardan birini tanlang:",
        reply_markup=get_admin_region_keyboard(),
        parse_mode="HTML"
    )


@router.message(
    AdminAddState.waiting_for_region,
    F.chat.type == "private"
)
async def process_custom_admin_country(
    message: types.Message,
    state: FSMContext
):
    data = await state.get_data()

    if not data.get("waiting_custom_country"):
        return

    if not message.text or not message.text.strip():
        await message.answer(
            "❌ Davlat nomini kiriting.",
            reply_markup=cancel_keyboard()
        )
        return

    country = message.text.strip()

    await state.update_data(
        region=country,
        waiting_custom_country=False
    )

    await state.set_state(AdminAddState.waiting_for_birth_date)

    await message.answer(
        f"<b>🌍 Davlat:</b> {country}\n\n"
        "📅 <b>Tug‘ilgan sanangizni kiriting:</b>\n"
        "Masalan: <code>23.10.2008</code>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin_region_"))
async def process_admin_region(
    callback: types.CallbackQuery,
    state: FSMContext
):
    region = callback.data.replace("admin_region_", "", 1)


    if region == "other":
        await callback.message.edit_text(
            "<b>🌍 Davlatni tanlang:</b>",
            reply_markup=get_admin_country_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    else:
        await state.update_data(region=region)
        await state.set_state(AdminAddState.waiting_for_birth_date)

        await callback.message.edit_text(
            f"<b>📍 Viloyat:</b> {region}\n\n"
            "📅 <b>Tug‘ilgan sanani kiriting.</b>\n"
            "Masalan: <code>23.10.2008</code>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )

    await callback.answer()


@router.callback_query(F.data.startswith("admin_country_"))
async def process_admin_country(
    callback: types.CallbackQuery,
    state: FSMContext
):
    country = callback.data.replace("admin_country_", "", 1)

    if country == "other":
        await state.set_state(AdminAddState.waiting_for_region)
        await state.update_data(waiting_custom_country=True)

        await callback.message.edit_text(
            "<b>🌍 Davlat nomini yozing:</b>\n\n"
            "Masalan: <i>Amerika</i>, <i>Ukraina</i>, <i>Kanada</i>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    await state.update_data(region=country)
    await state.set_state(AdminAddState.waiting_for_birth_date)

    await callback.message.edit_text(
        f"<b>🌍 Davlat:</b> {country}\n\n"
        "📅 <b>Tug‘ilgan sanangizni kiriting:</b>\n"
        "Masalan: <code>23.10.2008</code>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


@router.message(
    AdminAddState.waiting_for_birth_date,
    F.chat.type == "private"
)
async def process_admin_birth_date(
    message: types.Message,
    state: FSMContext
):
    if not message.text:
        await message.answer(
            "❌ Tug‘ilgan sanani kiriting.\n"
            "Masalan: <code>23.10.2008</code>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )
        return

    birth_date = message.text.strip()


    try:
        datetime.strptime(birth_date, "%d.%m.%Y")
    except ValueError:
        await message.answer(
            "❌ Sana formati noto‘g‘ri.\n\n"
            "📅 Masalan: <code>23.10.2008</code>",
            reply_markup=cancel_keyboard(),
            parse_mode="HTML"
        )
        return

    await state.update_data(birth_date=birth_date)
    await state.set_state(AdminAddState.waiting_for_phone)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⏭ Skip",
                    callback_data="admin_phone_skip"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="admin_phone_back"
                )
            ]
        ]
    )

    await message.answer(
        "📱 <b>Telefon raqamini kiriting.</b>\n\n"
        "Agar telefon raqamini bermoqchi bo‘lmasa, "
        "<b>Skip</b> tugmasini bosing.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


async def finish_admin_registration(
    message: types.Message,
    state: FSMContext,
    phone: str = "",
    user: types.User | None = None,
):
    data = await state.get_data()

    admin_id = data.get("admin_id")
    full_name = data.get("full_name", "")
    region = data.get("region", "")
    birth_date = data.get("birth_date", "")

    user = user or message.from_user
    username = user.username or ""

    # Admin ma'lumotlarini bazaga saqlash
    add_admin_to_db(
        admin_id=admin_id,
        full_name=full_name,
        username=username,
        region=region,
        birth_date=birth_date,
        phone=phone
    )

    await state.clear()

    # Yangi adminga xabar
    try:
        await message.bot.send_message(
            admin_id,
            "🎉 <b>Siz admin qilindingiz!</b>\n\n"
            "Siz botning adminlar ro'yxatiga qo'shildingiz.\n"
            "👤 <b>Ism:</b> " + (full_name or "—") + "\n"
            "📍 <b>Hudud:</b> " + (region or "—") + "\n"
            "📅 <b>Tug'ilgan sana:</b> " + (birth_date or "—") + "\n"
            "📱 <b>Telefon:</b> " + (phone or "Berilmagan"),
            parse_mode="HTML"
        )
    except Exception:
        pass

    # Ownerga xabar
    try:
        await message.bot.send_message(
            OWNER_ID,
            "✅ <b>Yangi admin ro'yxatdan o'tdi va admin qilindi!</b>\n\n"
            f"🆔 <b>ID:</b> <code>{admin_id}</code>\n"
            f"👤 <b>Ism-familiya:</b> {full_name or '—'}\n"
            f"📍 <b>Hudud:</b> {region or '—'}\n"
            f"📅 <b>Tug'ilgan sana:</b> {birth_date or '—'}\n"
            f"📱 <b>Telefon:</b> {phone or 'Berilmagan'}",
            parse_mode="HTML"
        )
    except Exception:
        pass

    await message.answer(
        "✅ <b>Admin muvaffaqiyatli qo'shildi!</b>\n\n"
        f"👤 {full_name or '—'}\n"
        f"📍 {region or '—'}",
        reply_markup=main_menu(user.id),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_phone_skip")
async def admin_phone_skip(
    callback: types.CallbackQuery,
    state: FSMContext
):
    data = await state.get_data()
    admin_id = data.get("admin_id")

    if callback.from_user.id != admin_id:
        await callback.answer(
            "⛔️ Ruxsat yo'q!",
            show_alert=True
        )
        return

    if not admin_id:
        await callback.answer(
            "❌ Admin ma'lumotlari topilmadi!",
            show_alert=True
        )
        return

    # Callback orqali yuborilgan xabardan foydalanamiz
    await finish_admin_registration(
        callback.message,
        state,
        phone="",
        user=callback.from_user,
    )

    await callback.answer()


@router.message(
    AdminAddState.waiting_for_phone,
    F.chat.type == "private"
)
async def process_admin_phone(
    message: types.Message,
    state: FSMContext
):
    if not message.text:
        await message.answer(
            "❌ Telefon raqamini matn ko'rinishida yuboring "
            "yoki Skip tugmasini bosing.",
            parse_mode="HTML"
        )
        return

    phone = message.text.strip()

    await finish_admin_registration(
        message,
        state,
        phone=phone
    )

# ============================================================
# 👤 ADMIN HAQIDA TO'LIQ MA'LUMOT
# ============================================================

@router.callback_query(F.data.startswith("admin_info_"))
async def cb_admin_info(callback: types.CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer(
            "⛔️ Ruxsat faqat Owner uchun!",
            show_alert=True
        )
        return

    try:
        admin_id = int(callback.data.replace("admin_info_", "", 1))
    except ValueError:
        await callback.answer(
            "❌ Admin ID noto'g'ri!",
            show_alert=True
        )
        return

    import sqlite3

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT admin_id, full_name, username, region, birth_date, phone
        FROM admins
        WHERE admin_id = ?
    """, (admin_id,))

    admin = cursor.fetchone()
    conn.close()

    if not admin:
        await callback.answer(
            "⚠️ Admin topilmadi!",
            show_alert=True
        )
        return

    uid, full_name, username, region, birth_date, phone = admin

    username_text = f"@{username}" if username else "❌ Yo'q"
    phone_text = phone if phone else "❌ Kiritilmagan"
    region_text = region if region else "❌ Kiritilmagan"
    birth_text = birth_date if birth_date else "❌ Kiritilmagan"
    name_text = full_name if full_name else "❌ Kiritilmagan"

    text = (
        "<b>👤 ADMIN HAQIDA TO'LIQ MA'LUMOT</b>\n\n"
        f"🆔 <b>Telegram ID:</b> <code>{uid}</code>\n"
        f"👨‍💼 <b>Ism/Familiya:</b> {name_text}\n"
        f"🔗 <b>Username:</b> {username_text}\n"
        f"📍 <b>Viloyat/Davlat:</b> {region_text}\n"
        f"🎂 <b>Tug'ilgan sana:</b> {birth_text}\n"
        f"📱 <b>Telefon:</b> {phone_text}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Adminlar ro'yxati",
                    callback_data="admin_info_list"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Admin boshqaruvi",
                    callback_data="menu_admin_manage"
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
