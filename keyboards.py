from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from config import OWNER_ID

BTN_USER_1 = "📩 𝗥𝗲𝗸𝗹𝗮𝗺𝗮"
BTN_USER_2 = "🎭 𝗠𝗮𝗳𝗶𝗮 𝗥𝗼𝗹𝗹𝗮𝗿𝗶"
BTN_USER_3 = "⚠️ 𝗦𝗵𝗶𝗸𝗼𝘆𝗮𝘁"

BTN_ADMIN_4 = "👥 𝗥𝗲𝗸𝗹𝗮𝗺𝗮 𝗚𝘂𝗿𝘂𝗵𝗹𝗮𝗿𝗶"
BTN_ADMIN_5 = "📅 𝗕𝘂𝗴𝘂𝗻𝗴𝗶 𝗥𝗲𝗸𝗹𝗮𝗺𝗮𝗹𝗮𝗿"
BTN_ADMIN_6 = "📊 𝗥𝗲𝗸𝗹𝗮𝗺𝗮 𝗦𝘁𝗮𝘁𝗶𝘀𝘁𝗶𝗸𝗮𝘀𝗶"
BTN_ADMIN_7 = "📱 𝗔𝗰𝗰𝗼𝘂𝗻𝘁 𝗥𝗲𝗸𝗹𝗮𝗺𝗮𝘀𝗶"
BTN_ADMIN_8 = "🏆 𝗧𝗼𝗽 𝟱 𝗔𝗸𝘁𝗶𝘃"

BTN_OWNER_9 = "⚙️ 𝗔𝗱𝗺𝗶𝗻 𝗕𝗼𝘀𝗵𝗾𝗮𝗿𝘂𝘃𝗶"
BTN_BACK = "⬅️ 𝗢𝗿𝗾𝗮𝗴𝗮"

back_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=BTN_BACK)]],
    resize_keyboard=True
)

def get_main_menu(user_id: int, admins_list: list) -> InlineKeyboardMarkup:
    """✨ Premium asosiy menyu."""

    try:
        admin_ids = {int(x) for x in admins_list}
    except (TypeError, ValueError):
        admin_ids = set()

    is_admin = (
        int(user_id) == int(OWNER_ID)
        or int(user_id) in admin_ids
    )

    # 👤 Oddiy foydalanuvchi menyusi
    buttons = [
        [
            InlineKeyboardButton(
                text="📱 Account ulash",
                callback_data="acc:menu"
            )
        ],
        [
            InlineKeyboardButton(
                text=BTN_USER_1,
                callback_data="menu_ad"
            )
        ],
        [
            InlineKeyboardButton(
                text=BTN_USER_2,
                callback_data="menu_roles"
            ),
            InlineKeyboardButton(
                text=BTN_USER_3,
                callback_data="menu_complaint"
            )
        ]
    ]

    # 👑 Admin paneli
    if is_admin:
        buttons.extend([
            [
                InlineKeyboardButton(
                    text=BTN_ADMIN_4,
                    callback_data="menu_groups"
                ),
                InlineKeyboardButton(
                    text=BTN_ADMIN_5,
                    callback_data="menu_today_ads"
                )
            ],
            [
                InlineKeyboardButton(
                    text=BTN_ADMIN_6,
                    callback_data="menu_statistics"
                )
            ],
            [
                InlineKeyboardButton(
                    text=BTN_ADMIN_7,
                    callback_data="menu_account_ads"
                ),
                InlineKeyboardButton(
                    text=BTN_ADMIN_8,
                    callback_data="menu_top_active"
                )
            ]
        ])

    # 👑 Faqat bot egasi
    if int(user_id) == int(OWNER_ID):
        buttons.append([
            InlineKeyboardButton(
                text=BTN_OWNER_9,
                callback_data="menu_admin_manage"
            )
        ])

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

def get_roles_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            # 1] TINCH AHOLILAR TOMONDA
            [InlineKeyboardButton(text="👨🏼 Tinch aholi", callback_data="role_fuqaro"), InlineKeyboardButton(text="💃 Kezuvchi", callback_data="role_kezuvchi")],
            [InlineKeyboardButton(text="👮🏻‍♂ Serjant", callback_data="role_serjant"), InlineKeyboardButton(text="🕵🏻‍♂ Komissar katani", callback_data="role_komissar")],
            [InlineKeyboardButton(text="👨🏻‍⚕ Doktor", callback_data="role_doktor"), InlineKeyboardButton(text="🧙‍♂ Daydi", callback_data="role_daydi")],
            [InlineKeyboardButton(text="🧞‍♂️ Afsungar", callback_data="role_afsungar"), InlineKeyboardButton(text="🤞 Omadli", callback_data="role_omadli")],
            [InlineKeyboardButton(text="🎖️ Janob", callback_data="role_janob")],

            # 2] MAFIYA TOMONDA
            [InlineKeyboardButton(text="🤵🏻 Don", callback_data="role_don"), InlineKeyboardButton(text="🤵🏼 Mafiya", callback_data="role_mafia")],
            [InlineKeyboardButton(text="👨‍💼 Advokat", callback_data="role_advokat"), InlineKeyboardButton(text="🕴 Убийца", callback_data="role_ubiyca")],
            [InlineKeyboardButton(text="👩‍💻 Jurnalist", callback_data="role_jurnalist")],

            # 3] ERKIN VA YAKKAXON ROLLAR
            [InlineKeyboardButton(text="🔪 Qotil", callback_data="role_qotil"), InlineKeyboardButton(text="🐺 Bo'ri", callback_data="role_bori")],
            [InlineKeyboardButton(text="🤓 Sotqin", callback_data="role_sotqin"), InlineKeyboardButton(text="🧙‍ Sexrgar", callback_data="role_sehrgar")],
            [InlineKeyboardButton(text="🧟 G'azabkor", callback_data="role_gazabkor"), InlineKeyboardButton(text="🤹 Aferist", callback_data="role_aferist")],

            # 💬 PROFILE LINK TUGMA
            [InlineKeyboardButton(text="💬 Batafsil so'rash uchun", url="https://t.me/skroozy")]
        ]
    )

def get_back_to_roles_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Rollar ro'yxatiga qaytish", callback_data="roles_list")],
            [InlineKeyboardButton(text="💬 Batafsil so'rash uchun", url="https://t.me/skroozy")]
        ]
    )

def get_admin_manage_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="➕ Admin Qo'shish",
                callback_data="admin_add_start"
            )],
            [InlineKeyboardButton(
                text="📜 Adminlar Ro'yxati / Olish",
                callback_data="admin_list_show"
            )],
            [InlineKeyboardButton(
                text="👤 Adminlar Haqida Ma'lumot",
                callback_data="admin_info_list"
            )],
            [InlineKeyboardButton(
                text="🏠 Asosiy menyu",
                callback_data="main_menu"
            )]
        ]
    )

def get_admins_delete_inline(admins_data) -> InlineKeyboardMarkup:
    buttons = []

    for uid, name, username, region, birth_date, phone in admins_data:
        display_name = name if name else f"ID: {uid}"
        buttons.append([
            InlineKeyboardButton(
                text=f"❌ {display_name} ({uid})",
                callback_data=f"admin_del_{uid}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="🔙 Orqaga",
            callback_data="menu_admin_manage"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="main_menu")]
        ]
    )

# ============================================================
# 🗺 ADMIN VILOYAT / DAVLAT TANLASH
# ============================================================

def get_admin_region_keyboard() -> InlineKeyboardMarkup:
    regions = [
        ("🇺🇿 Qoraqalpog‘iston", "admin_region_Qoraqalpog‘iston"),
        ("🏙 Toshkent shahri", "admin_region_Toshkent shahri"),
        ("📍 Andijon viloyati", "admin_region_Andijon viloyati"),
        ("📍 Buxoro viloyati", "admin_region_Buxoro viloyati"),
        ("📍 Jizzax viloyati", "admin_region_Jizzax viloyati"),
        ("📍 Qashqadaryo viloyati", "admin_region_Qashqadaryo viloyati"),
        ("📍 Navoiy viloyati", "admin_region_Navoiy viloyati"),
        ("📍 Namangan viloyati", "admin_region_Namangan viloyati"),
        ("📍 Samarqand viloyati", "admin_region_Samarqand viloyati"),
        ("📍 Sirdaryo viloyati", "admin_region_Sirdaryo viloyati"),
        ("📍 Surxondaryo viloyati", "admin_region_Surxondaryo viloyati"),
        ("📍 Toshkent viloyati", "admin_region_Toshkent viloyati"),
        ("📍 Farg‘ona viloyati", "admin_region_Farg‘ona viloyati"),
        ("📍 Xorazm viloyati", "admin_region_Xorazm viloyati"),
        ("🌍 Boshqa davlat", "admin_region_other"),
    ]

    buttons = []

    for text, callback_data in regions:
        buttons.append([
            InlineKeyboardButton(
                text=text,
                callback_data=callback_data
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data="menu_admin_manage"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

# 🌍 ADMIN UCHUN DAVLATLAR
def get_admin_country_keyboard() -> InlineKeyboardMarkup:
    countries = [
        ("🇺🇿 O‘zbekiston", "admin_country_O‘zbekiston"),
        ("🇷🇺 Rossiya", "admin_country_Rossiya"),
        ("🇰🇿 Qozog‘iston", "admin_country_Qozog‘iston"),
        ("🇰🇬 Qirg‘iziston", "admin_country_Qirg‘iziston"),
        ("🇹🇯 Tojikiston", "admin_country_Tojikiston"),
        ("🇹🇲 Turkmaniston", "admin_country_Turkmaniston"),
        ("🇹🇷 Turkiya", "admin_country_Turkiya"),
        ("🇦🇪 BAA", "admin_country_BAA"),
        ("🇺🇸 AQSh", "admin_country_AQSh"),
        ("🇬🇧 Buyuk Britaniya", "admin_country_Buyuk Britaniya"),
        ("🇩🇪 Germaniya", "admin_country_Germaniya"),
        ("🇫🇷 Fransiya", "admin_country_Fransiya"),
        ("🇰🇷 Janubiy Koreya", "admin_country_Janubiy Koreya"),
        ("🇨🇳 Xitoy", "admin_country_Xitoy"),
        ("🇯🇵 Yaponiya", "admin_country_Yaponiya"),
        ("🌍 Boshqa", "admin_country_other"),
    ]

    buttons = []

    for text, callback_data in countries:
        buttons.append([
            InlineKeyboardButton(
                text=text,
                callback_data=callback_data
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data="admin_region_back"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
